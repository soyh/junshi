"""Xiaohongshu (小红书) private-message channel via browser automation.

Why Playwright instead of the app:
  * XHS has a web IM at xiaohongshu.com; the DOM is semantic and stable enough.
  * Browser automation keeps working while the desktop is locked, unlike the
    WeChat UI-automation path.

Flow:
  1. keep the message list open;
  2. poll every few seconds, compare each conversation's summary/time;
  3. when it changes, open the conversation and read new left-side messages;
  4. reply by typing into the contenteditable editor and pressing Enter.

Contact ids are ``xhs:<conv_id>`` so they never collide with other platforms.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from .base import Handler, InboundEvent

CONV_ITEM = '.xhs-im-conv-item[data-conv-kind="c2c"]'
EDITOR = ".xhs-im-input-bar-editor"

CONV_JS = """() => Array.from(document.querySelectorAll('.xhs-im-conv-item[data-conv-kind="c2c"]'))
  .map(el => ({
    id: el.getAttribute('data-conv-id') || '',
    name: (el.querySelector('.xhs-im-conv-item__name') || {}).textContent || '',
    summary: (el.querySelector('.xhs-im-conv-item__summary-text') || {}).textContent || '',
    time: (el.querySelector('.xhs-im-conv-item__time') || {}).textContent || '',
    unread: !!((el.querySelector('.xhs-im-conv-item__bottom-right') || {}).children || []).length
  }))"""

MSG_JS = """() => Array.from(document.querySelectorAll('.xhs-im-msg-list .chat-item'))
  .map(el => ({
    id: el.getAttribute('data-message-id') || '',
    type: el.getAttribute('data-content-type') || '',
    me: !!el.querySelector('.chat-item__content--right'),
    text: (el.querySelector('.xhs-im-bubble__text') || {}).textContent || ''
  }))"""

STATE_JS = """() => {
  const active = document.querySelector('.xhs-im-conv-item--active');
  return {
    active: active ? (active.getAttribute('data-conv-id') || '') : '',
    url: location.pathname
  };
}"""

LOGIN_JS = """() => {
  const text = document.body ? document.body.innerText : '';
  return !!document.querySelector('.login-container, .login-modal, .login-mask, .login-box')
    || /扫码登录|手机号登录|登录后推荐更懂你的笔记/.test(text);
}"""


class XhsChannel:
    def __init__(
        self,
        profile_dir: str | Path | None = None,
        interval: float = 4.0,
        headless: bool = False,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        self._profile = Path(profile_dir) if profile_dir else root / "profiles" / "xhs"
        self._interval = float(interval)
        self._headless = bool(headless)
        self._handler: Handler | None = None
        self._pw = None
        self._ctx = None
        self._page = None
        self._running = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._last: dict[str, tuple[str, str]] = {}
        self._last_index: dict[str, str] = {}
        self._warned_login = False
        self._logged = print

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    # -- lifecycle --------------------------------------------------------
    @property
    def _login_marker(self) -> Path:
        return self._profile / ".logged-in"

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self._profile.mkdir(parents=True, exist_ok=True)
        self._pw = await async_playwright().start()
        await self._launch(headless=self._headless)
        await self._ensure_list()
        # Already-logged-in profiles stay headless; a fresh profile gets one
        # visible window so the user can scan.
        if self._headless and not self._login_marker.is_file():
            if not await self._page.locator(".xhs-im-conv-list").count():
                self._logged("[xhs] 首次登录：已弹出扫码窗口；登录成功后自动转为无头运行")
                await self._relaunch_headed()
                await self._ensure_list()
        await self._baseline()
        self._running = True
        self._task = asyncio.create_task(self._poll())

    async def _launch(self, headless: bool) -> None:
        self._ctx = await self._pw.chromium.launch_persistent_context(
            str(self._profile),
            channel="msedge",
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else await self._ctx.new_page()

    async def _relaunch_headed(self) -> None:
        try:
            await self._ctx.close()
        except Exception:
            pass
        await self._launch(headless=False)
        try:
            await self._page.bring_to_front()
        except Exception:
            pass

    async def healthy(self) -> bool:
        return await self.status() == "online"

    async def status(self) -> str:
        """online / 未登录 / 异常 — what the browser actually shows right now."""
        try:
            page = self._page
            if page is None:
                return "启动中"
            if await page.locator(".xhs-im-conv-list").count():
                return "online"
            if await page.evaluate(LOGIN_JS):
                return "未登录"
            await self._ensure_list()
            await asyncio.sleep(1.0)
            if await page.locator(".xhs-im-conv-list").count():
                return "online"
            if await page.evaluate(LOGIN_JS):
                return "未登录"
            return "异常"
        except Exception:
            return "异常"

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        if self._ctx:
            await self._ctx.close()
        if self._pw:
            await self._pw.stop()

    # -- page helpers -----------------------------------------------------
    async def _ensure_list(self) -> None:
        page = self._page
        if await page.locator(".xhs-im-conv-list").count():
            return
        try:
            await page.goto("https://www.xiaohongshu.com/explore", wait_until="commit", timeout=20000)
        except Exception:
            pass
        await asyncio.sleep(3)
        try:
            await page.locator("text=消息").first.click(timeout=6000)
        except Exception:
            pass
        await asyncio.sleep(2)
        try:
            if await page.evaluate(LOGIN_JS):
                if not self._warned_login:
                    self._warned_login = True
                    try:
                        await page.bring_to_front()
                    except Exception:
                        pass
                    self._logged(
                        "[xhs] 需要登录：请在弹出的浏览器窗口里用小红书 App 扫码；"
                        "登录成功后状态会自动变成 在线"
                    )
                return
            if not await page.locator(".xhs-im-conv-list").count():
                await self._surface_login(page)
        except Exception:
            pass

    async def _surface_login(self, page) -> None:  # noqa: ANN001
        """Bring the login wall to the foreground so the user can scan."""
        try:
            await page.bring_to_front()
        except Exception:
            pass
        if await page.evaluate(LOGIN_JS):
            return
        for selector in ('button:has-text("登录")', '.login-btn', '.side-bar .login'):
            button = page.locator(selector).first
            try:
                if await button.count():
                    await button.click(timeout=4000)
                    await asyncio.sleep(1.5)
                    if await page.evaluate(LOGIN_JS):
                        return
            except Exception:
                continue
        try:
            await page.goto("https://www.xiaohongshu.com/login", wait_until="commit", timeout=20000)
        except Exception:
            pass

    async def _conversations(self) -> list[dict]:
        return await self._page.evaluate(CONV_JS)

    async def _messages(self) -> list[dict]:
        return await self._page.evaluate(MSG_JS)

    async def _open(self, conv_id: str) -> None:
        item = self._page.locator(f'.xhs-im-conv-item[data-conv-id="{conv_id}"]')
        if not await item.count():
            raise RuntimeError(f"conversation not in list: {conv_id}")
        await item.first.click(timeout=6000)
        await asyncio.sleep(1.2)

    async def _baseline(self) -> None:
        for conv in await self._conversations():
            self._last[conv["id"]] = (conv["summary"], conv["time"])

    # -- polling ----------------------------------------------------------
    async def _poll(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as exc:  # keep polling
                self._logged(f"[xhs] poll error: {exc!r}")
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        async with self._lock:
            await self._ensure_list()
            conversations = await self._conversations()
            if conversations and not self._login_marker.is_file():
                self._login_marker.write_text("ok", encoding="ascii")
                self._logged("[xhs] 登录态已记录，下次将以无头模式运行")
            for conv in conversations:
                key = (conv["summary"], conv["time"])
                if self._last.get(conv["id"]) == key:
                    continue
                self._last[conv["id"]] = key
                await self._open(conv["id"])
                messages = await self._messages()
                self._emit_new(conv, messages)

    def _emit_new(self, conv: dict, messages: list[dict]) -> None:
        last_id = self._last_index.get(conv["id"])
        if last_id:
            start = 0
            for index, message in enumerate(messages):
                if message["id"] == last_id:
                    start = index + 1
                    break
            fresh = messages[start:]
        else:
            # First time we open this conversation: only the trailing burst of
            # inbound messages can be new, never the whole history.
            fresh = []
            for message in reversed(messages):
                if message.get("me"):
                    break
                fresh.insert(0, message)
            fresh = fresh[-5:]
        if not fresh:
            return
        self._last_index[conv["id"]] = fresh[-1]["id"]

        for message in fresh:
            text = (message.get("text") or "").strip()
            if message.get("me") or not text:
                continue
            event = InboundEvent(
                contact_id=f"xhs:{conv['id']}",
                contact_name=conv["name"] or conv["id"],
                text=text,
                message_id=f"xhs-{conv['id']}-{message['id']}",
                is_group=False,
                timestamp=time.time(),
            )
            if self._handler:
                self._handler(event)

    # -- sending ----------------------------------------------------------
    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        conv_id = contact_id.split(":", 1)[1] if ":" in contact_id else contact_id
        wanted = text.strip()
        async with self._lock:
            await self._ensure_list()
            for _ in range(3):
                await self._open(conv_id)
                editor = self._page.locator(EDITOR)
                await editor.click(timeout=6000)
                await self._page.keyboard.insert_text(text)
                await asyncio.sleep(0.3)

                state = await self._page.evaluate(STATE_JS)
                typed = (await editor.inner_text()).strip()
                safe = (
                    state["active"] == conv_id
                    and f"/chat/{conv_id}" in state["url"]
                    and typed == wanted
                )
                if safe:
                    await self._page.keyboard.press("Enter")
                    await asyncio.sleep(1.2)
                    if (await editor.inner_text()).strip() == "":
                        messages = (await self._messages())[-3:]
                        if any(m["me"] and wanted in (m["text"] or "") for m in messages):
                            return
                    raise RuntimeError("xiaohongshu send verification failed after Enter")

                # Someone switched the conversation mid-send: abort this attempt.
                await self._page.keyboard.press("Control+A")
                await self._page.keyboard.press("Backspace")
                await asyncio.sleep(0.6)

            raise RuntimeError("xiaohongshu send aborted: conversation focus kept changing")
