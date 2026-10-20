"""Soul (SoulApp) private-message channel via browser automation.

Soul's web client (home.soulapp.cn) syncs conversations when the account has
PC membership; this adapter assumes that is enabled.

DOM notes:
  * conversation rows:  .conv-list .conversation  (.conv-name/.conv-preview/.conv-time)
  * message row:        .bubble-row (own messages add .is-self)
  * text:               .bubble-text
  * composer:           .ProseMirror[contenteditable]
  * send button:        .send-btn

Soul exposes no stable conversation id in the DOM, so conversations are keyed
by display name (``soul:<name>``). Renaming a contact creates a new Person.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path

from .base import Handler, InboundEvent

CONV_JS = """() => Array.from(document.querySelectorAll('.conv-list .conversation')).map(el => ({
  name: (el.querySelector('.conv-name') || {}).textContent || '',
  preview: (el.querySelector('.conv-preview') || {}).textContent || '',
  time: (el.querySelector('.conv-time') || {}).textContent || '',
  avatar: (el.querySelector('img.soul-avatar__img') || {}).src || ''
}))"""

MSG_JS = """() => Array.from(document.querySelectorAll('.bubble-row')).map(el => ({
  self: el.classList.contains('is-self'),
  text: (el.querySelector('.bubble-text') || {}).textContent || '',
  time: (el.querySelector('.bubble-time, time') || {}).textContent || ''
}))"""


class SoulChannel:
    def __init__(
        self,
        profile_dir: str | Path | None = None,
        interval: float = 4.0,
        headless: bool = False,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        self._profile = Path(profile_dir) if profile_dir else root / "profiles" / "soul"
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
        self._counts: dict[str, int] = {}
        self._logged = print

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    # -- lifecycle --------------------------------------------------------
    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self._profile.mkdir(parents=True, exist_ok=True)
        self._pw = await async_playwright().start()
        self._ctx = await self._pw.chromium.launch_persistent_context(
            str(self._profile),
            channel="msedge",
            headless=self._headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else await self._ctx.new_page()
        await self._ensure_chat()
        await self._baseline()
        self._running = True
        self._task = asyncio.create_task(self._poll())

    async def healthy(self) -> bool:
        try:
            if self._page is None:
                return False
            if await self._page.locator(".conv-list").count():
                return True
            await self._ensure_chat()
            return await self._page.locator(".conv-list").count() > 0
        except Exception:
            return False

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        if self._ctx:
            await self._ctx.close()
        if self._pw:
            await self._pw.stop()

    # -- page helpers -----------------------------------------------------
    async def _ensure_chat(self) -> None:
        page = self._page
        try:
            await page.goto("https://home.soulapp.cn/", wait_until="commit", timeout=30000)
        except Exception:
            pass
        await asyncio.sleep(6)
        if await page.locator(".sync-scrim").count():
            try:
                await page.locator(".sync-action-button--secondary").click(timeout=4000)
            except Exception:
                pass
            await asyncio.sleep(2)
        if not await page.locator(".conv-list").count():
            try:
                await page.goto("https://home.soulapp.cn/chat", wait_until="commit", timeout=20000)
            except Exception:
                pass
            await asyncio.sleep(4)

    async def _conversations(self) -> list[dict]:
        return await self._eval(CONV_JS)

    async def _messages(self) -> list[dict]:
        return await self._eval(MSG_JS)

    async def _eval(self, script: str, arg=None, retries: int = 3):
        """React SPAs navigate underneath us; retry when the context dies."""
        for attempt in range(retries):
            try:
                return await self._page.evaluate(script, arg)
            except Exception as exc:
                if attempt == retries - 1:
                    raise
                message = str(exc)
                if "context was destroyed" not in message and "navigation" not in message:
                    raise
                await asyncio.sleep(1.5)
                try:
                    await self._ensure_chat()
                except Exception:
                    pass

    async def _open(self, name: str) -> None:
        clicked = await self._eval(
            """(name) => {
                const rows = Array.from(document.querySelectorAll('.conv-list .conversation'));
                const row = rows.find(el => {
                    const n = el.querySelector('.conv-name');
                    return n && n.textContent.trim() === name;
                });
                if (!row) return false;
                row.click();
                return true;
            }""",
            name,
        )
        if not clicked:
            raise RuntimeError(f"soul conversation not found: {name}")
        # The chat pane loads messages asynchronously; wait for the bubbles.
        for _ in range(20):
            await asyncio.sleep(0.5)
            if await self._page.locator(".bubble-row").count():
                break
        await asyncio.sleep(0.5)

    async def _baseline(self) -> None:
        for conv in await self._conversations():
            self._last[conv["name"]] = (conv["preview"], conv["time"])

    # -- polling ----------------------------------------------------------
    async def _poll(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as exc:
                self._logged(f"[soul] poll error: {exc!r}")
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        async with self._lock:
            await self._ensure_chat()
            conversations = await self._conversations()
            for conv in conversations:
                name = conv["name"]
                key = (conv["preview"], conv["time"])
                if self._last.get(name) == key:
                    continue
                self._last[name] = key
                await self._open(name)
                messages = await self._messages()
                self._emit_new(name, messages)

    def _emit_new(self, name: str, messages: list[dict]) -> None:
        previous = self._counts.get(name)
        if previous is not None and len(messages) >= previous:
            fresh = messages[previous:]
        else:
            fresh = []
            for message in reversed(messages):
                if message["self"]:
                    break
                fresh.insert(0, message)
            fresh = fresh[-5:]

        self._counts[name] = len(messages)
        for message in fresh:
            text = (message.get("text") or "").strip()
            if message["self"] or not text:
                continue
            digest = hashlib.md5(f"{name}|{text}|{int(time.time() // 60)}".encode()).hexdigest()[:12]
            event = InboundEvent(
                contact_id=f"soul:{name}",
                contact_name=name,
                text=text,
                message_id=f"soul-{digest}",
                is_group=False,
                timestamp=time.time(),
            )
            if self._handler:
                self._handler(event)

    # -- sending ----------------------------------------------------------
    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        name = contact_id.split(":", 1)[1] if ":" in contact_id else contact_id
        wanted = text.strip()
        async with self._lock:
            await self._ensure_chat()
            for _ in range(3):
                await self._open(name)
                editor = self._page.locator(".ProseMirror").first
                await editor.click(timeout=6000)
                await self._page.keyboard.insert_text(text)
                await asyncio.sleep(0.4)
                typed = (await editor.inner_text()).strip()
                active = await self._eval(
                    "() => { const el = document.querySelector('.conversation.is-active .conv-name'); return el ? el.textContent.trim() : ''; }"
                )
                if typed != wanted or active != name:
                    await self._page.keyboard.press("Control+A")
                    await self._page.keyboard.press("Backspace")
                    await asyncio.sleep(0.6)
                    continue

                await self._page.locator(".send-btn").first.click(timeout=6000)
                await asyncio.sleep(1.5)
                messages = (await self._messages())[-3:]
                if any(m["self"] and wanted in (m["text"] or "") for m in messages):
                    return
                raise RuntimeError("soul send verification failed")

            raise RuntimeError("soul send aborted: conversation focus kept changing")
