"""Tk dialog for the bundled multi-profile auto-reply channel plugin."""

import tkinter as tk
from tkinter import messagebox, ttk

import bridge_plugin as bp
import field_templates as ft
import reply_rules as rr
from management import Dialog, Section, scrollable

NAMES = rr.NAMES


WINDOW_MODES = {"hide": "移出桌面（不占任务栏）", "minimize": "最小化", "show": "保持显示"}
WINDOW_LABELS = {label: key for key, label in WINDOW_MODES.items()}
RULES_HINT = (
    "只影响语气、称呼、长度、用词、表情和话题偏好；真人感优先于泛泛的礼貌。\n"
    "不能覆盖证据、安全边界和发送前确认，写了也会被忽略。"
)


class BridgeDialog(Dialog):
    def __init__(self, app):
        super().__init__(app, "自动回复通道插件（多开）")
        self.profiles = {}
        self.current = None
        self.window.minsize(880, 520)
        self.fit(1120, 720)
        # 768 高的笔记本屏幕上 720 的窗口会贴着任务栏，直接最大化更稳。
        if self.window.winfo_screenheight() <= 800:
            try:
                self.window.state("zoomed")
            except tk.TclError:
                pass

        ttk.Label(
            self.frame,
            text="每个通道独立账号、独立浏览器登录态与独立进程，可同时运行；微信一个 Windows 会话只能登一个号。",
            wraplength=900,
        ).grid(row=0, column=0, sticky="w")

        # The action bar is a fixed grid row: the scrollable body may shrink on
        # small screens, the buttons never get clipped.
        bar = ttk.Frame(self.frame)
        bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        body = ttk.Frame(self.frame)
        body.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        right_wrap = ttk.Frame(body)
        right_wrap.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self._build_left(left)
        queue_host = ttk.Frame(right_wrap)
        queue_host.pack(side="bottom", fill="x", pady=(6, 0))
        self._build_right(scrollable(right_wrap))
        self._build_queue(queue_host)

        actions = ttk.Frame(bar)
        actions.pack(fill="x")
        for index, (text, command) in enumerate(
            (
                ("保存配置", self.save),
                ("启动", self.start_profile),
                ("停止", self.stop_profile),
                ("启动全部", self.start_all),
                ("显示浏览器", self.show_browser),
                ("隐藏浏览器", self.hide_browser),
                ("刷新状态", self.refresh),
                ("关闭", self.close),
            )
        ):
            button = ttk.Button(actions, text=text, command=command)
            button.grid(row=index // 4, column=index % 4, sticky="ew", padx=(0, 6), pady=2)
        for column in range(4):
            actions.grid_columnconfigure(column, weight=1)
        ttk.Label(bar, textvariable=self.message, wraplength=980).pack(fill="x", pady=(4, 0))
        ttk.Label(
            bar,
            text="首次启动或登录态过期会弹出浏览器扫码；状态每 15 秒刷新。",
            wraplength=980,
        ).pack(anchor="w")
        self.load_shared(announce=True)
        self.reload()
        self.window.after(15000, self._auto_refresh)

    # -- layout -----------------------------------------------------------
    def _build_left(self, parent):
        channels = Section(parent, "通道列表", open=True)
        list_row = ttk.Frame(channels.body)
        list_row.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(list_row, height=11, width=38, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_row, command=self.listbox.yview)
        scroll.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self.load_selected())

        row = ttk.Frame(channels.body)
        row.pack(fill="x", pady=(4, 0))
        self.button(row, "新建通道", self.new_profile)
        self.button(row, "删除当前", self.delete_profile)
        self.button(row, "全部停止", self.stop_all)

        logs = Section(parent, "运行日志", open=False)
        text_row = ttk.Frame(logs.body)
        text_row.pack(fill="both", expand=True)
        self.text = tk.Text(text_row, height=8, width=38, wrap="word", state="disabled")
        self.text.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(text_row, command=self.text.yview)
        bar.pack(side="left", fill="y")
        self.text.configure(yscrollcommand=bar.set)

    def _build_shared(self, parent):
        """Identity and default rules: one copy for every channel."""
        shared = Section(parent, "全局设置（跟随账号：本人信息 + 默认规则）", open=False)
        self.shared_section = shared
        note = ttk.Label(
            shared.body,
            text="这些内容保存在你的账号里：网页、手机、电脑看到的是同一份；改了所有通道下次启动都生效。",
            foreground="#666",
            wraplength=660,
        )
        note.pack(anchor="w")
        grid = ttk.Frame(shared.body)
        grid.pack(fill="x", pady=(4, 6))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        ttk.Label(
            grid,
            text="本人信息：填了才会用；没填的项模型保持模糊，不会自己编年龄、职业或城市。可在网页或手机「我的资料」里改。",
            foreground="#666",
            wraplength=620,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 4))
        self.person = {}
        for index, key in enumerate(bp.PERSON_FIELDS):
            row, column = divmod(index + 1, 2)
            self.person[key] = self._cell(
                grid, row, column, key, bp.PERSON_LABELS[key], "",
                sample=ft.person_sample(key),
            )

        rules_head = ttk.Frame(shared.body)
        rules_head.pack(fill="x")
        ttk.Label(rules_head, text="默认回复规则（通道没写规则时用这份）：").pack(side="left")
        self.global_template = ttk.Combobox(rules_head, values=NAMES, state="readonly", width=26)
        self.global_template.pack(side="left", padx=(4, 0))
        self.global_template.set(NAMES[0])
        self.global_template.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.fill_template(insert_only=True, target=self.global_rules),
        )
        ttk.Button(
            rules_head,
            text="填入模板",
            command=lambda: self.fill_template(insert_only=True, target=self.global_rules),
        ).pack(side="left", padx=(4, 0))
        row = ttk.Frame(shared.body)
        row.pack(fill="both", expand=True, pady=(3, 0))
        self.global_rules = tk.Text(row, height=5, wrap="word", spacing1=2, spacing3=2)
        self.global_rules.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(row, command=self.global_rules.yview)
        bar.pack(side="left", fill="y")
        self.global_rules.configure(yscrollcommand=bar.set)
        self.widgets.append((self.global_rules, "normal"))
        self.auto_send = tk.BooleanVar(value=False)
        consent = ttk.Frame(shared.body)
        consent.pack(fill="x", pady=(6, 0))
        ttk.Checkbutton(
            consent,
            text="我授权本机通道插件自动代发（写进账号，服务端同步降级「必须本人发送」）",
            variable=self.auto_send,
        ).pack(anchor="w")
        ttk.Label(
            consent,
            text="不勾选也能用，只是服务端会继续按「必须由本人发送」提示；勾选后网页、手机、电脑看到的是同一个授权状态。",
            foreground="#666",
            wraplength=660,
        ).pack(anchor="w")
        self.handoff = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            consent,
            text="对方主动要联系方式时，可以把「我的微信号」直接发给他（写进账号，三端同步）",
            variable=self.handoff,
        ).pack(anchor="w", pady=(6, 0))
        ttk.Label(
            consent,
            text="不勾选就不发号、也不问对方要号；勾选后只在对方明确开口时给，且不会主动塞过去。",
            foreground="#666",
            wraplength=660,
        ).pack(anchor="w")
        bar_row = ttk.Frame(shared.body)
        bar_row.pack(fill="x", pady=(4, 0))
        self.button(bar_row, "保存全局设置", self.save_shared)
        self.button(bar_row, "从账号重新读取", self.reload_shared)
        self.shared_status = tk.StringVar(value="账号同步状态：打开时自动读取")
        ttk.Label(bar_row, textvariable=self.shared_status, foreground="#666").pack(side="left", padx=(8, 0))

    def _build_right(self, parent):
        account = Section(parent, "基础连接", open=True)
        grid = account.body
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        self.name = self._cell(grid, 0, 0, "name", "配置名称", "新通道", sample=lambda: ft.name_sample(
            bp.CHANNEL_LABELS.get(self.channel.get(), "wechat")
        ))
        self.channel = self._cell(grid, 0, 1, "channel", "平台通道", "微信", choices=list(bp.CHANNELS.values()))
        self.server = self._cell(grid, 1, 0, "server", "服务器", self.app.server.get())
        self.username = self._cell(grid, 1, 1, "username", "军师账号", self.app.username.get())
        self.password = self._cell(grid, 2, 0, "password", "军师密码", "", secret=True)

        policy = Section(parent, "运行策略", open=True)
        grid = policy.body
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        self.dry_run = self._cell(grid, 0, 0, "dry_run", "先试运行（只生成不发送）", "是", choices=["是", "否"])
        self.headless = self._cell(
            grid, 0, 1, "headless", "登录后隐藏浏览器（后台运行）", "是", choices=["是", "否"]
        )
        self.window_mode = self._cell(
            grid, 1, 0, "window_mode", "隐藏方式", WINDOW_MODES["hide"], choices=list(WINDOW_MODES.values())
        )
        self.quiet = self._cell(
            grid, 1, 1, "quiet", "静默时段（开始-结束）", "03:00-05:30",
            choices=ft.QUIET_PRESETS, sample=ft.QUIET_PRESETS[0], free=True,
        )
        self.cap = self._cell(
            grid, 2, 0, "cap", "每日回复上限", "30",
            choices=ft.CAP_PRESETS, sample=ft.CAP_PRESETS[1], free=True,
        )
        self.verify = self._cell(grid, 2, 1, "verify", "校验 HTTPS 证书", "是", choices=["是", "否"])

        rules = Section(parent, "本通道回复规则（留空则用全局默认）", open=False)
        self.rules_section = rules
        ttk.Label(rules.body, text=RULES_HINT, foreground="#555").pack(anchor="w")
        picker = ttk.Frame(rules.body)
        picker.pack(fill="x", pady=(3, 2))
        ttk.Label(picker, text="模板：").pack(side="left")
        self.template = ttk.Combobox(picker, values=NAMES, state="readonly", width=28)
        self.template.pack(side="left")
        self.template.set(NAMES[0])
        ttk.Button(picker, text="填入模板", command=self.fill_template).pack(side="left", padx=(4, 0))
        self.template_note = ttk.Label(rules.body, text="", foreground="#666", wraplength=820)
        self.template_note.pack(anchor="w")
        self.template.bind("<<ComboboxSelected>>", lambda _event: self.fill_template(insert_only=False))
        text_row = ttk.Frame(rules.body)
        text_row.pack(fill="both", expand=True, pady=(2, 0))
        self.rules = tk.Text(text_row, height=5, wrap="word", spacing1=2, spacing3=2)
        self.rules.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(text_row, command=self.rules.yview)
        bar.pack(side="left", fill="y")
        self.rules.configure(yscrollcommand=bar.set)
        self.widgets.append((self.rules, "normal"))
        ttk.Button(rules.body, text="恢复默认（清空）", command=lambda: self.rules.delete("1.0", "end")).pack(
            anchor="e", pady=(4, 0)
        )
        self.fill_template(insert_only=False)

        self._build_shared(parent)

    def _build_queue(self, parent):
        """Pinned below the scroll area: the queue is why the dialog is open."""
        queue = Section(parent, "待发 / 失败（仅当前通道）", open=True)
        queue_row = ttk.Frame(queue.body)
        queue_row.pack(fill="both", expand=True)
        self.queue_text = tk.Text(queue_row, height=5, wrap="char", state="disabled")
        self.queue_text.pack(side="left", fill="both", expand=True)
        queue_bar = ttk.Scrollbar(queue_row, command=self.queue_text.yview)
        queue_bar.pack(side="left", fill="y")
        self.queue_text.configure(yscrollcommand=queue_bar.set)
        queue_buttons = ttk.Frame(queue.body)
        queue_buttons.pack(fill="x", pady=(3, 0))
        for index, (text, command) in enumerate(
            (
                ("立即重试", self.retry_outbox),
                ("刷新队列", self.refresh_queue),
                ("计入已回", self.resolve_contact),
                ("清除失败记录", self.clear_failed),
            )
        ):
            ttk.Button(queue_buttons, text=text, command=command).grid(
                row=0, column=index, sticky="ew", padx=(0, 6), pady=2
            )
        ttk.Label(queue_buttons, text="已手动回复：").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.queue_contact = tk.StringVar()
        self.queue_picker = ttk.Combobox(
            queue_buttons, textvariable=self.queue_contact, state="readonly", width=18
        )
        self.queue_picker.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(4, 0))
        for column in range(4):
            queue_buttons.grid_columnconfigure(column, weight=1)


    def _cell(self, grid, row, column, key, label, value="", choices=None, secret=False,
              sample=None, free=False):
        holder = ttk.Frame(grid)
        holder.grid(row=row, column=column, sticky="ew", padx=4, pady=1)
        return self.entry(
            key, label, value, choices, secret, parent=holder, sample=sample, free=free
        )

    # -- refresh ----------------------------------------------------------
    def _auto_refresh(self):
        try:
            if self.window.winfo_exists():
                self.refresh()
                self.window.after(15000, self._auto_refresh)
        except Exception:
            pass

    def reload(self, select=None):
        self._render_list(items={item["id"]: item for item in bp.list_profiles()}, select=select)

    def _render_list(self, items, select=None, load=True):
        self.profiles = items
        self.listbox.delete(0, "end")
        order = list(self.profiles)
        for profile_id in order:
            item = self.profiles[profile_id]
            dot = "●" if item["running"] else "○"
            label = bp.CHANNELS.get(item["channel"], item["channel"])
            self.listbox.insert("end", f"{dot} {item['name']} · {label} · {item.get('status', '')}")
        if not order:
            self.current = None
            return
        target = select or self.current or order[0]
        if target not in self.profiles:
            target = order[0]
        index = order.index(target)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        if load:
            self.load_selected()

    def load_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        profile_id = list(self.profiles)[selection[0]]
        item = self.profiles[profile_id]
        self.current = profile_id
        self._fill(self.name, item["name"])
        self._fill(self.server, item["server"])
        self._fill(self.username, item["username"])
        self._fill(self.password, item["password"])
        self.channel.set(bp.CHANNELS.get(item["channel"], "微信"))
        self.dry_run.set("是" if item["dry_run"] else "否")
        self.quiet.delete(0, "end"); self.quiet.insert(0, f"{item['quiet'][0]}-{item['quiet'][1]}")
        self.cap.delete(0, "end"); self.cap.insert(0, str(item["daily_cap"]))
        self.verify.set("是" if item["verify_tls"] else "否")
        self.headless.set("是" if item.get("headless", True) else "否")
        self.window_mode.set(WINDOW_MODES.get(item.get("browser_window", "hide"), WINDOW_MODES["hide"]))
        self.rules.delete("1.0", "end")
        if item.get("rules"):
            self.rules.insert("1.0", item["rules"])
        state = item.get("status") or ("运行中" if item["running"] else "未运行")
        self.message.set(f"{item['name']}：{state}")
        self.refresh_queue()

    def _person_values(self):
        return {key: widget.get().strip() for key, widget in self.person.items()}

    def reload_shared(self):
        self.load_shared(announce=True)

    def load_shared(self, announce=False):
        """Identity lives on the account; the local file is only an offline cache."""
        shared = bp.load_global()
        person = shared["person"]
        rules = shared["rules"]
        auto_send = bool(shared.get("auto_send"))
        handoff = bool(shared.get("handoff"))
        remote, error = self._fetch_shared()
        if remote is not None:
            person = bp.person_from_api(remote)
            rules = str(remote.get("reply_rules") or "")
            auto_send = bool(remote.get("auto_send_authorized"))
            handoff = bool(remote.get("contact_handoff_enabled"))
            try:
                bp.save_global(person=person, rules=rules, auto_send=auto_send,
                               handoff=handoff)
            except OSError:
                pass
            if announce:
                stamp = str(remote.get("updated_at") or "")
                self.shared_status.set("账号同步状态：已从账号读取" + (f"（{stamp}）" if stamp else ""))
        elif announce:
            self.shared_status.set(f"账号同步状态：读取失败——{error or '未登录'}")
        for key, widget in self.person.items():
            self._fill(widget, person.get(key, ""))
        self.global_rules.delete("1.0", "end")
        if rules:
            self.global_rules.insert("1.0", rules)
        self.auto_send.set(auto_send)
        self.handoff.set(handoff)

    def _fetch_shared(self):
        """Return (profile, error). The client already prefixes /api/v1."""
        if not self.client:
            return None, "未登录"
        try:
            data = self.client.request("GET", "/settings/profile", timeout=20)
        except Exception as exc:
            return None, str(exc)
        return (data, "") if isinstance(data, dict) else (None, "返回格式不正确")

    def save_shared(self):
        person = self._person_values()
        rules = self.global_rules.get("1.0", "end").strip()
        auto_send = bool(self.auto_send.get())
        handoff = bool(self.handoff.get())
        try:
            bp.save_global(person=person, rules=rules, auto_send=auto_send, handoff=handoff)
        except OSError as exc:
            self.message.set(f"全局设置保存失败：{exc}")
            return
        if not self.client:
            self.message.set("已保存到本机（未登录，暂时只在本机生效）。")
            self.shared_status.set("账号同步状态：未登录，仅本机")
            return
        def work():
            return self.client.request(
                "PUT", "/settings/profile", bp.api_payload(person, rules, auto_send, handoff),
                timeout=20
            )

        def done(result, error):
            if error:
                self.message.set(f"已存本机，但同步到账号失败：{error}")
                self.shared_status.set(f"账号同步状态：保存失败——{error}")
            else:
                stamp = result.get("updated_at", "") if isinstance(result, dict) else ""
                self.message.set(
                    "已保存到账号（网页/手机同一步生效"
                    + ("，已授权自动代发" if auto_send else "，未授权自动代发")
                    + (f"，{stamp}" if stamp else "")
                    + "）。"
                )
                self.shared_status.set("账号同步状态：已保存到账号" + (f"（{stamp}）" if stamp else ""))

        self.perform(work, done)

    @staticmethod
    def _fill(widget, value):
        widget.delete(0, "end")
        widget.insert(0, value or "")

    # -- actions ----------------------------------------------------------
    def _values(self):
        try:
            start, end = [part.strip() for part in self.quiet.get().split("-", 1)]
        except ValueError:
            raise ValueError("静默时段格式应为 03:00-05:30") from None
        try:
            cap = int(self.cap.get().strip() or "30")
        except ValueError:
            raise ValueError("每日回复上限必须是数字") from None
        return {
            "name": self.name.get(),
            "server": self.server.get(),
            "username": self.username.get(),
            "password": self.password.get(),
            "channel": bp.CHANNEL_LABELS.get(self.channel.get(), "wechat"),
            "dry_run": self.dry_run.get() == "是",
            "daily_cap": cap,
            "quiet": (start, end),
            "verify_tls": self.verify.get() == "是",
            "headless": self.headless.get() == "是",
            "browser_window": WINDOW_LABELS.get(self.window_mode.get(), "hide"),
            "rules": self.rules.get("1.0", "end").strip(),
            "person": self._person_values(),
        }

    def new_profile(self):
        try:
            values = self._values()
        except ValueError as exc:
            self.message.set(str(exc))
            return
        label = self.channel.get()
        values["name"] = f"{label}通道"
        values["channel"] = bp.CHANNEL_LABELS.get(label, "wechat")
        try:
            profile_id = bp.create_profile(**values)
        except (ValueError, OSError) as exc:
            self.message.set(str(exc))
            return
        self.current = profile_id
        self.reload(select=profile_id)
        self.message.set("已新建通道配置，可直接点「启动」。")

    def delete_profile(self):
        if not self.current:
            return
        item = self.profiles.get(self.current, {})
        if not messagebox.askyesno("删除通道", f"删除「{item.get('name', self.current)}」及其登录态？", parent=self.window):
            return
        bp.delete_profile(self.current)
        self.current = None
        self.reload()
        self.message.set("已删除。")

    def save(self):
        if not self.current:
            self.message.set("请先新建通道配置。")
            return
        before = self.profiles.get(self.current, {})
        try:
            bp.save_global(
                person=self._person_values(),
                rules=self.global_rules.get("1.0", "end").strip(),
            )
            bp.save_profile(self.current, **self._values())
        except ValueError as exc:
            self.message.set(str(exc))
            return
        changed = before.get("running") and before.get("channel") != self._values()["channel"]
        self.reload(select=self.current)
        self.message.set(
            "配置已保存；平台通道变更需先「停止」再「启动」才会生效。" if changed else "配置已保存。"
        )

    def start_profile(self):
        if not self.current:
            self.message.set("请先新建并保存通道配置。")
            return
        if self.profiles.get(self.current, {}).get("running"):
            self.message.set("该通道已在运行；如更换了平台，请先「停止」再「启动」。")
            return
        try:
            bp.save_global(
                person=self._person_values(),
                rules=self.global_rules.get("1.0", "end").strip(),
            )
            bp.save_profile(self.current, **self._values())
            pid = bp.start(self.current)
        except (ValueError, OSError) as exc:
            self.message.set(str(exc))
            return
        self.reload(select=self.current)
        self.message.set(f"已启动（进程 {pid}）；首次登录会自动弹出浏览器窗口。")

    def stop_profile(self):
        if not self.current:
            return
        stopped = bp.stop(self.current)
        self.reload(select=self.current)
        self.message.set("已停止。" if stopped else "该通道未在运行。")

    def stop_all(self):
        count = bp.stop_all()
        self.reload()
        self.message.set(f"已停止 {count} 个通道。")

    def start_all(self):
        started, failed = 0, []
        for profile_id, item in list(self.profiles.items()):
            if item.get("running"):
                continue
            try:
                bp.start(profile_id)
                started += 1
            except (ValueError, OSError) as exc:
                failed.append(f"{item['name']}：{exc}")
        self.reload(select=self.current)
        self.message.set(
            f"已启动 {started} 个通道。" + (" 失败：" + "；".join(failed) if failed else "")
        )

    def show_browser(self):
        profile_id = self.current
        if not profile_id:
            messagebox.showinfo("提示", "先选择一个通道")
            return
        if not bp.is_running(profile_id):
            messagebox.showinfo("提示", "该通道未在运行，启动后浏览器窗口会自动出现")
            return
        if bp.show_browser(profile_id):
            self._log("已把浏览器窗口移回桌面")
        else:
            messagebox.showwarning(
                "没找到窗口",
                "这个通道的浏览器窗口不在（可能已退出或还没登录）。可以「停止」再「启动」重建窗口。",
            )

    def hide_browser(self):
        profile_id = self.current
        if not profile_id:
            messagebox.showinfo("提示", "先选择一个通道")
            return
        if not bp.is_running(profile_id):
            messagebox.showinfo("提示", "该通道未在运行")
            return
        if bp.hide_browser(profile_id):
            self._log("已把浏览器窗口移出桌面")
            self.message.set("浏览器已隐藏，通道继续在后台运行。")
        else:
            messagebox.showwarning(
                "没找到窗口",
                "这个通道没有可见的浏览器窗口（可能已经在后台，或还没登录）。",
            )

    def fill_template(self, insert_only=True, target=None):
        picker = self.global_template if target is not None else self.template
        note, text = rr.template(picker.get())
        if target is None:
            self.template_note.configure(text=note)
        if insert_only:
            box = target if target is not None else self.rules
            box.delete("1.0", "end")
            box.insert("1.0", text)

    def _log(self, message):
        self.text.configure(state="normal")
        self.text.insert("end", message + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def refresh(self):
        """Update list/status only: whatever the user typed in the form stays."""
        if self.busy:
            return
        self.perform(self._scan, self._refreshed)

    def _scan(self):
        items = {item["id"]: item for item in bp.list_profiles()}
        current = items.get(self.current or "")
        if current is None:
            return items, ["先在上面选择一个通道。"], []
        lines = bp.outbox_lines(
            [current], empty=f"{current['name']}：当前没有待发或失败的消息。"
        )
        return items, lines, bp.pending_contacts(self.current)

    def _refreshed(self, payload):
        items, queue, contacts = payload
        self._render_list(items=items, select=self.current, load=False)
        self._set_contacts(contacts)
        self.render_queue(queue)
        running = sum(1 for item in items.values() if item["running"])
        self.message.set(f"状态以本机当前为准；运行中的通道：{running} 个。")

    def refresh_queue(self):
        current = self.profiles.get(self.current or "", None)
        if current is None:
            self.render_queue(["先在上面选择一个通道。"])
            return
        self.perform(
            lambda: (bp.outbox_lines([current], empty=f"{current['name']}：当前没有待发或失败的消息。"),
                     bp.pending_contacts(self.current)),
            self._queue_loaded,
        )

    def _queue_loaded(self, payload):
        lines, contacts = payload
        self.render_queue(lines)
        self._set_contacts(contacts)

    def _set_contacts(self, contacts):
        labels = [f"{row.get('contact_name') or row['contact_id']}" for row in contacts]
        self.queue_picker.configure(values=labels)
        if self.queue_contact.get() not in labels:
            self.queue_contact.set(labels[0] if labels else "")
        self._contact_ids = {
            f"{row.get('contact_name') or row['contact_id']}": row["contact_id"] for row in contacts
        }

    def resolve_contact(self):
        contact = getattr(self, "_contact_ids", {}).get(self.queue_contact.get())
        if not self.current or not contact:
            self.message.set("先在队列里选择一个人（只有待发/失败的才会列出）。")
            return
        if not messagebox.askyesno(
            "计入已回",
            f"确认你已经在 {self.profiles[self.current]['name']} 里手动回复了"
            f"「{self.queue_contact.get()}」？\n该人的待发与失败记录会被清掉，不再自动发送。",
            parent=self.window,
        ):
            return
        removed = bp.clear_outbox(self.current, contact, only_failed=False)
        self.message.set(f"已清掉「{self.queue_contact.get()}」的 {removed} 条待发/失败记录。")
        self.refresh_queue()

    def clear_failed(self):
        if not self.current:
            return
        if not messagebox.askyesno(
            "清除失败记录",
            "确认清掉本通道所有「重试 3 次仍失败」的记录？\n只是不再显示，不会补发。",
            parent=self.window,
        ):
            return
        removed = bp.clear_outbox(self.current, only_failed=True)
        self.message.set(f"已清掉 {removed} 条失败记录。")
        self.refresh_queue()

    def render_queue(self, lines):
        self.queue_text.configure(state="normal")
        self.queue_text.delete("1.0", "end")
        self.queue_text.insert("1.0", "\n".join(lines))
        self.queue_text.configure(state="disabled")

    def retry_outbox(self):
        if not self.current:
            self.message.set("请先选择一个通道。")
            return
        if not self.profiles.get(self.current, {}).get("running"):
            self.message.set("该通道未在运行；启动后待发消息会自动补发。")
            return
        self.perform(lambda: bp.retry_outbox(self.current), self._retried)

    def _retried(self, result):
        self.message.set(f"已请求重试：{result}")
        self.refresh_queue()

    def render(self, lines):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")
        running = sum(1 for item in self.profiles.values() if item["running"])
        self.message.set(f"状态以本机当前为准；运行中的通道：{running} 个。")
