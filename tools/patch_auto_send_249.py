"""Add the explicit auto-send authorization flag end to end (build 249)."""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path("C:/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo")


def patch(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (relative, text.count(old), old[:60])
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1. migration
(ROOT / "backend/migrations/029_user_profile_auto_send.sql").write_text(
    "-- The signed-in user's explicit permission for the companion client to send\n"
    "-- drafts on their behalf. Off by default: the product rule stays\n"
    "-- \"a human sends the message\" until the user opts in.\n"
    "ALTER TABLE user_profiles ADD COLUMN auto_send_authorized INTEGER NOT NULL DEFAULT 0;\n",
    encoding="utf-8",
)

# 2. schema
patch(
    "backend/app/schemas/user_profile.py",
    '    reply_rules: str = Field(default="", max_length=1500)\n',
    '    reply_rules: str = Field(default="", max_length=1500)\n'
    "    # Explicit opt-in for the desktop bridge sending drafts unchanged.\n"
    "    auto_send_authorized: bool = False\n",
)

# 3. service get
patch(
    "backend/app/services/user_profile.py",
    '        data = {field: str(row[field] or "") for field in FIELDS}\n'
    '        return UserProfileResponse(**data, updated_at=str(row["updated_at"] or ""))\n',
    '        data = {field: str(row[field] or "") for field in FIELDS}\n'
    '        data["auto_send_authorized"] = bool(row["auto_send_authorized"])\n'
    '        return UserProfileResponse(**data, updated_at=str(row["updated_at"] or ""))\n',
)

# 4. service save
patch(
    "backend/app/services/user_profile.py",
    '        values = {field: value.strip() for field, value in values.items()}\n',
    '        values = {field: value.strip() for field, value in values.items()}\n'
    "        authorized = int(bool(payload.auto_send_authorized))\n",
)
patch(
    "backend/app/services/user_profile.py",
    '            assignments = ", ".join(f"{field} = ?" for field in FIELDS)\n'
    '            conn.execute(\n'
    '                f"UPDATE user_profiles SET {assignments},"\n'
    '                " updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",\n'
    '                [*(values[field] for field in FIELDS), user_id],\n'
    "            )\n",
    '            assignments = ", ".join(f"{field} = ?" for field in FIELDS)\n'
    '            conn.execute(\n'
    '                f"UPDATE user_profiles SET {assignments},"\n'
    '                " auto_send_authorized = ?,"\n'
    '                " updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",\n'
    '                [*(values[field] for field in FIELDS), authorized, user_id],\n'
    "            )\n",
)
patch(
    "backend/app/services/user_profile.py",
    '            columns = ", ".join(("user_id", *FIELDS))\n'
    '            marks = ", ".join("?" for _ in range(len(FIELDS) + 1))\n'
    '            conn.execute(\n'
    '                f"INSERT INTO user_profiles ({columns}) VALUES ({marks})",\n'
    '                [user_id, *(values[field] for field in FIELDS)],\n'
    "            )\n",
    '            columns = ", ".join(("user_id", *FIELDS, "auto_send_authorized"))\n'
    '            marks = ", ".join("?" for _ in range(len(FIELDS) + 2))\n'
    '            conn.execute(\n'
    '                f"INSERT INTO user_profiles ({columns}) VALUES ({marks})",\n'
    '                [user_id, *(values[field] for field in FIELDS), authorized],\n'
    "            )\n",
)

# 5. generation context: downgrade the constraint only when the user opted in.
patch(
    "backend/app/services/analysis_strategic_reply.py",
    "def _resolve_rules(conn: sqlite3.Connection, user_id: str, override: str) -> str:",
    "def _auto_send_authorized(conn: sqlite3.Connection, user_id: str) -> bool:\n"
    '    """True when the account opted into the bridge sending drafts itself."""\n'
    "    stored = _stored_profile(conn, user_id)\n"
    "    return bool(getattr(stored, \"auto_send_authorized\", False)) if stored else False\n"
    "\n"
    "\n"
    "def _resolve_rules(conn: sqlite3.Connection, user_id: str, override: str) -> str:",
)
patch(
    "backend/app/services/analysis_strategic_reply.py",
    "        generation_context = {\n            \"person_memory\"",
    "        auto_send = _auto_send_authorized(conn, user_id)\n"
    "        generation_context = {\n            \"person_memory\"",
)
patch(
    "backend/app/services/analysis_strategic_reply.py",
    '                "must_not_auto_send": True,\n',
    '                # The product rule is "a human sends the message"; only an\n'
    '                # explicit per-account opt-in downgrades it to a note.\n'
    '                "must_not_auto_send": not auto_send,\n'
    '                "auto_send_authorized": auto_send,\n',
)

# 6. prompt clause
patch(
    "backend/app/services/openai_chat_provider.py",
    '"a natural human voice is "\n            "expected; the draft is the user\'s own message, so do not describe it as a "',
    '"a natural human voice is "\n            "expected. constraints.auto_send_authorized=true means the user explicitly "\n'
    '"authorized their companion client to send this draft unchanged, so write it "\n'
    '"as a ready-to-send message; that permission never relaxes the evidence, "\n'
    '"provenance or safety rules, and you must still not claim it was sent. "\n'
    '"the draft is the user\'s own message, so do not describe it as a "',
)

# 7. web workspace: checkbox + load/save
patch(
    "backend/app/ui/my_profile_workspace.py",
    '        <textarea id="mp-rules" maxlength="1500" placeholder="例如：短句、口语、允许倒装；不要破折号，不要设问后自答。"></textarea>\n      </div>\n',
    '        <textarea id="mp-rules" maxlength="1500" placeholder="例如：短句、口语、允许倒装；不要破折号，不要设问后自答。"></textarea>\n      </div>\n'
    '      <div id="my-profile-auto-send">\n'
    '        <label class="my-profile-check" for="mp-auto-send"><input id="mp-auto-send" type="checkbox"> 我授权电脑客户端自动代发</label>\n'
    '        <p class="my-profile-hint">勾选后，服务端把「必须由本人发送」这条约束降级为提示：通道插件生成的回复可以直接发出，统计里记为已授权。不勾选时保持原样。</p>\n'
    "      </div>\n",
)
patch(
    "backend/app/ui/my_profile_workspace.py",
    "    const templateSelect = byId('mp-template');\n",
    "    const autoSend = byId('mp-auto-send');\n"
    "    const templateSelect = byId('mp-template');\n",
)
patch(
    "backend/app/ui/my_profile_workspace.py",
    "        profileSetStatus(data && data.updated_at ? `上次保存：${data.updated_at}` : '还没有填写过。');\n",
    "        if (autoSend) { autoSend.checked = !!(data && data.auto_send_authorized); }\n"
    "        profileSetStatus(data && data.updated_at ? `上次保存：${data.updated_at}` : '还没有填写过。');\n",
)
patch(
    "backend/app/ui/my_profile_workspace.py",
    "      Object.entries(profileFields).forEach(([key, node]) => { payload[key] = node.value; });\n",
    "      Object.entries(profileFields).forEach(([key, node]) => { payload[key] = node.value; });\n"
    "      payload.auto_send_authorized = !!(autoSend && autoSend.checked);\n",
)
patch(
    "backend/app/ui/my_profile_workspace.py",
    "  .my-profile-hint { margin: 6px 0; color: #6b8497; font-size: .78rem; line-height: 1.5; }\n",
    "  .my-profile-hint { margin: 6px 0; color: #6b8497; font-size: .78rem; line-height: 1.5; }\n"
    "  #my-profile-auto-send { border-top: 1px dashed #d6e2ec; padding-top: 10px; }\n"
    "  .my-profile-check { display: flex; align-items: center; gap: 8px; font-size: .88rem; color: #23485f; cursor: pointer; }\n"
    "  .my-profile-check input { width: 16px; height: 16px; margin: 0; }\n",
)

# 8. desktop plugin: cache the flag and send it with the profile payload
patch(
    "desktop/bridge_plugin.py",
    '    return {\n        "person": {key: str(person.get(key, "")) for key in PERSON_FIELDS if str(person.get(key, "")).strip()},\n        "rules": str(data.get("rules", "") or ""),\n    }\n',
    '    return {\n        "person": {key: str(person.get(key, "")) for key in PERSON_FIELDS if str(person.get(key, "")).strip()},\n        "rules": str(data.get("rules", "") or ""),\n        "auto_send": bool(data.get("auto_send", False)),\n    }\n',
)
patch(
    "desktop/bridge_plugin.py",
    'def save_global(person: dict[str, str] | None = None, rules: str | None = None) -> Path:\n',
    'def save_global(\n    person: dict[str, str] | None = None,\n    rules: str | None = None,\n    auto_send: bool | None = None,\n) -> Path:\n',
)
patch(
    "desktop/bridge_plugin.py",
    '    if rules is not None:\n        current["rules"] = rules\n',
    '    if rules is not None:\n        current["rules"] = rules\n    if auto_send is not None:\n        current["auto_send"] = bool(auto_send)\n',
)
patch(
    "desktop/bridge_plugin.py",
    'def api_payload(person: dict[str, str], rules: str) -> dict[str, str]:\n    """Build the account profile body from local person fields and rules."""\n    payload = {API_FIELDS.get(key, key): str(person.get(key, "") or "").strip()\n               for key in PERSON_FIELDS}\n    payload["reply_rules"] = str(rules or "")\n    return payload\n',
    'def api_payload(person: dict[str, str], rules: str, auto_send: bool = False) -> dict:\n    """Build the account profile body from local person fields and rules."""\n    payload = {API_FIELDS.get(key, key): str(person.get(key, "") or "").strip()\n               for key in PERSON_FIELDS}\n    payload["reply_rules"] = str(rules or "")\n    payload["auto_send_authorized"] = bool(auto_send)\n    return payload\n',
)

# 9. desktop dialog: the checkbox itself
patch(
    "desktop/bridge_dialog.py",
    '        self.widgets.append((self.global_rules, "normal"))\n',
    '        self.widgets.append((self.global_rules, "normal"))\n'
    '        self.auto_send = tk.BooleanVar(value=False)\n'
    '        consent = ttk.Frame(shared.body)\n'
    '        consent.pack(fill="x", pady=(6, 0))\n'
    '        ttk.Checkbutton(\n'
    '            consent,\n'
    '            text="我授权本机通道插件自动代发（写进账号，服务端同步降级「必须本人发送」）",\n'
    '            variable=self.auto_send,\n'
    '        ).pack(anchor="w")\n'
    '        ttk.Label(\n'
    '            consent,\n'
    '            text="不勾选也能用，只是服务端会继续按「必须由本人发送」提示；勾选后网页、手机、电脑看到的是同一个授权状态。",\n'
    '            foreground="#666",\n'
    '            wraplength=660,\n'
    '        ).pack(anchor="w")\n',
)
patch(
    "desktop/bridge_dialog.py",
    '        shared = bp.load_global()\n        person = shared["person"]\n        rules = shared["rules"]\n',
    '        shared = bp.load_global()\n        person = shared["person"]\n        rules = shared["rules"]\n        auto_send = bool(shared.get("auto_send"))\n',
)
patch(
    "desktop/bridge_dialog.py",
    '            person = bp.person_from_api(remote)\n            rules = str(remote.get("reply_rules") or "")\n            try:\n                bp.save_global(person=person, rules=rules)\n',
    '            person = bp.person_from_api(remote)\n            rules = str(remote.get("reply_rules") or "")\n            auto_send = bool(remote.get("auto_send_authorized"))\n            try:\n                bp.save_global(person=person, rules=rules, auto_send=auto_send)\n',
)
patch(
    "desktop/bridge_dialog.py",
    '        self.global_rules.delete("1.0", "end")\n        if rules:\n            self.global_rules.insert("1.0", rules)\n',
    '        self.global_rules.delete("1.0", "end")\n        if rules:\n            self.global_rules.insert("1.0", rules)\n        self.auto_send.set(auto_send)\n',
)
patch(
    "desktop/bridge_dialog.py",
    '        person = self._person_values()\n        rules = self.global_rules.get("1.0", "end").strip()\n        try:\n            bp.save_global(person=person, rules=rules)\n',
    '        person = self._person_values()\n        rules = self.global_rules.get("1.0", "end").strip()\n        auto_send = bool(self.auto_send.get())\n        try:\n            bp.save_global(person=person, rules=rules, auto_send=auto_send)\n',
)
patch(
    "desktop/bridge_dialog.py",
    '            return self.client.request("PUT", "/settings/profile", bp.api_payload(person, rules), timeout=20)\n',
    '            return self.client.request(\n'
    '                "PUT", "/settings/profile", bp.api_payload(person, rules, auto_send), timeout=20\n'
    "            )\n",
)
patch(
    "desktop/bridge_dialog.py",
    '                self.message.set(f"已保存到账号（网页/手机同一步生效{(\'，\' + stamp) if stamp else \'\'}）。")\n',
    '                self.message.set(\n'
    '                    "已保存到账号（网页/手机同一步生效"\n'
    '                    + ("，已授权自动代发" if auto_send else "，未授权自动代发")\n'
    '                    + (f"，{stamp}" if stamp else "")\n'
    '                    + "）。"\n'
    "                )\n",
)

print("patched")
