"""Personal WeChat channel via wechatauto-replica (WeChat 4.1.12+).

Why this adapter exists:
  * Open-source hooks (wxhook / wcferry) only target WeChat 3.9.x.
  * wechatauto-replica supports 4.1.12+ by combining
      - reading new messages from the local SQLCipher message DB (Listener), and
      - sending through UI automation (activate window, paste, click send).

Consequences you must live with:
  * The Windows session must stay unlocked; the WeChat window is driven by the
    sender (it takes focus for a second while sending).
  * Sending needs the display name (remark/nickname), not the wxid, because the
    GUI searches by text.
  * This is still automation; WeChat's terms forbid it and the account can be
    restricted. Use the dedicated account only.
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid

from .base import Handler, InboundEvent


class AccountMismatch(RuntimeError):
    """The logged-in WeChat account is not the one this bridge is pinned to."""


class WechatautoChannel:
    def __init__(
        self,
        interval: float = 1.0,
        account: str | None = None,
        nickname: str | None = None,
        guard_interval: float = 30.0,
    ) -> None:
        self._interval = float(interval)
        self._expected_account = (account or "").strip() or None
        self._expected_nickname = (nickname or "").strip() or None
        self._guard_interval = float(guard_interval)
        self._db = None
        self._listener = None
        self._handler: Handler | None = None
        self._names: dict[str, str] = {}
        self._last_check = 0.0
        self._identity: dict[str, str] | None = None
        self._self_wxid: str | None = None
        self._outbox: dict[str, list[tuple[str, float]]] = {}

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        try:
            import wechatauto  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "wechatauto-replica is not installed. Run: "
                "pip install wechatauto-replica (Windows + WeChat 4.1.12+)"
            ) from exc

        self._db = await asyncio.to_thread(wechatauto.WeChatDB)
        await asyncio.to_thread(self._check_identity)
        listener_cls = self._listener_cls(wechatauto)
        self._listener = listener_cls(self._db, interval=self._interval)
        self._listener.add_all(self._on_message, discover=True)
        self._listener.start()

    @staticmethod
    def _listener_cls(module):
        """The real Listener lives in wechatauto.db; the top-level name differs."""
        try:
            import wechatauto.db as db_module  # type: ignore

            listener = getattr(db_module, "Listener", None)
            if listener is not None:
                return listener
        except Exception:
            pass
        return getattr(module, "Listener")

    def _check_identity(self) -> None:
        """Refuse to run if the live WeChat account is not the pinned one.

        wechatauto always follows whichever account is logged in, so switching
        back to the main account mid-run would otherwise make the bridge reply
        as that account.
        """
        import wechatauto  # type: ignore

        db = wechatauto.WeChatDB()
        info = db.get_self_info() or {}
        wxid = str(info.get("username") or "")
        nickname = str(info.get("nick_name") or "")
        self._self_wxid = wxid or None
        self._identity = {"wxid": wxid, "nickname": nickname, "dir": getattr(db, "account", "")}

        if self._expected_account:
            wanted = self._expected_account
            matched = wxid == wanted or wanted in (getattr(db, "account", "") or "")
            if not matched:
                raise AccountMismatch(
                    f"logged-in account is {wxid} ({nickname}), expected {wanted}"
                )
        if self._expected_nickname and nickname != self._expected_nickname:
            raise AccountMismatch(
                f"logged-in nickname is {nickname!r}, expected {self._expected_nickname!r}"
            )
        self._last_check = time.monotonic()

    @staticmethod
    def _is_system_account(username: str) -> bool:
        """Official accounts / system sessions must never become Persons."""
        if username.startswith("gh_"):
            return True
        return username.lower() in {
            "filehelper",
            "weixin",
            "fmessage",
            "medianote",
            "floatbottle",
            "qqmail",
            "qqsafe",
            "mphelper",
            "newsapp",
            "brandsessionholder",
            "brandservicesessionholder",
            "notifymessage",
            "weixinreminder",
            "officialaccounts",
        }

    def _is_echo(self, contact_id: str, content: str) -> bool:
        """Skip messages we just sent ourselves (DB echo fallback)."""
        now = time.monotonic()
        bucket = [item for item in self._outbox.get(contact_id, ()) if now - item[1] < 180.0]
        if bucket:
            self._outbox[contact_id] = bucket
        text = content.strip()
        return any(item[0] == text for item in bucket)

    def _guard(self, force: bool = False) -> None:
        if force or (time.monotonic() - self._last_check) > self._guard_interval:
            self._check_identity()

    def _on_message(self, msg: dict, listener) -> None:
        username = str(msg.get("username") or "")
        if not username or username.endswith("@chatroom"):
            return
        if self._is_system_account(username):
            return
        # Our own outgoing messages must never come back as inbound.
        sender_username = str(msg.get("sender_username") or "")
        if self._self_wxid and sender_username == self._self_wxid:
            return
        if msg.get("sender_id") == 2:  # legacy sentinel
            return

        content = msg.get("content")
        if not isinstance(content, str) or not content.strip():
            return
        if self._is_echo(username, content):
            return

        try:
            self._guard()
        except AccountMismatch:
            return

        name = self._names.get(username)
        if name is None:
            try:
                name = self._db.get_nickname(username) or username
            except Exception:
                name = username
            self._names[username] = name

        local_id = msg.get("local_id")
        sort_seq = msg.get("sort_seq")
        message_id = f"wa-{username}-{local_id if local_id is not None else uuid.uuid4().hex}-{sort_seq or 0}"
        created = msg.get("create_time")

        event = InboundEvent(
            contact_id=username,
            contact_name=name,
            text=content,
            message_id=message_id,
            is_group=False,
            timestamp=float(created) if created else time.time(),
        )
        if self._handler:
            self._handler(event)

    async def healthy(self) -> bool:
        try:
            await asyncio.to_thread(self._check_identity)
            return True
        except Exception:
            return False

    async def stop(self) -> None:
        listener = self._listener
        if listener is not None:
            try:
                await asyncio.to_thread(listener.stop)
            except Exception:
                pass

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        try:
            from wechatauto import quick_send  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("wechatauto-replica is not installed") from exc

        await asyncio.to_thread(self._guard, True)

        who = self._names.get(contact_id) or contact_id
        response = await asyncio.to_thread(quick_send, text, who)
        success = getattr(response, "is_success", None)
        if success is None and isinstance(response, dict):
            success = response.get("status") == "成功"
        if success is False:
            raise RuntimeError(f"wechatauto send failed: {response!r}")
        if not await asyncio.to_thread(self._verify_sent, contact_id, text.strip()):
            raise RuntimeError(f"wechat send not found in target chat {contact_id}")
        self._outbox.setdefault(contact_id, []).append((text.strip(), time.monotonic()))

    def _verify_sent(self, contact_id: str, text: str) -> bool:
        """Confirm the message landed in the intended chat (guards mis-sends)."""
        import wechatauto  # type: ignore

        for _ in range(6):
            try:
                messages = wechatauto.WeChatDB().get_messages(contact_id, limit=3)
            except Exception:
                messages = []
            for message in messages:
                if (
                    str(message.get("sender_username") or "") == (self._self_wxid or "")
                    and (message.get("content") or "").strip() == text
                ):
                    return True
            time.sleep(0.5)
        return False
