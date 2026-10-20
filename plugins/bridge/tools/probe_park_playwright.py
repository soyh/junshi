"""Probe: park a Playwright-launched Edge window and bring it back.

    python plugins/bridge/tools/probe_park_playwright.py

Requires the bridge environment (playwright + msedge).
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import ctypes.wintypes as wt
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lovebridge import window  # noqa: E402
from lovebridge.channels.xhs import XhsChannel  # noqa: E402


def rects(pid: int) -> list[tuple[int, int, int, int]]:
    out = []
    for hwnd in window._find([pid], wait=10):
        box = wt.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(box))
        out.append((box.left, box.top, box.right, box.bottom))
    return out


async def main() -> None:
    from playwright.async_api import async_playwright

    profile = Path(tempfile.mkdtemp(prefix="probe-park-"))
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        str(profile),
        channel="msedge",
        headless=False,
        viewport={"width": 1100, "height": 800},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://example.com", wait_until="domcontentloaded")
    channel = XhsChannel(profile_dir=profile, headless=True, window_mode="hide")
    channel._ctx = context
    channel._page = page
    channel._headed = True
    channel._logged = lambda message: print(message)

    before = rects(os.getpid())
    print("before:", before)
    await channel._park_if_logged_in()
    print("parked:", channel._parked)
    after = rects(os.getpid())
    print("after hide:", after)
    # Windows clamps one axis for some helper windows; either axis off-screen
    # is enough for the window to be invisible.
    assert after and all(x <= -10000 or y <= -10000 for x, y, *_ in after), after
    # The page must still answer while parked.
    assert await page.title() == "Example Domain", await page.title()
    print("page still alive while parked")

    await channel._reveal_window()
    restored = rects(os.getpid())
    print("after show:", restored)
    assert restored and any(x > -1000 and y > -1000 for x, y, *_ in restored), restored

    await context.close()
    await pw.stop()
    print("PASS: park keeps the page usable, show restores the window")


asyncio.run(main())
