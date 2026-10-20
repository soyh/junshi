"""Verify the XHS channel detects and surfaces the login wall on a fresh profile."""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.xhs import XhsChannel  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"


async def main() -> None:
    profile = Path(tempfile.mkdtemp(prefix="xhs-fresh-"))
    channel = XhsChannel(profile_dir=profile, headless=False)
    try:
        await channel.start()
        await asyncio.sleep(3)
        status = await channel.status()
        print("STATUS:", status, flush=True)
        page = channel._page
        print("URL:", page.url, flush=True)
        await page.screenshot(path=str(SHOTS / "xhs-login-wall.png"))
        (SHOTS / "xhs-login-wall.html").write_text(await page.content(), encoding="utf-8")
        locators = await page.evaluate(
            """() => ['input[placeholder*=手机号]', '.login-container', '.login-modal',
                     '[class*=login]', '[class*=Login]']
                .map(s => s + ':' + document.querySelectorAll(s).length)"""
        )
        print("LOCATORS:", locators, flush=True)
        print("TEXT:", (await page.evaluate("() => (document.body?.innerText || '').slice(0, 300)")))
        await asyncio.sleep(8)
    finally:
        await channel.stop()
        shutil.rmtree(profile, ignore_errors=True)


asyncio.run(main())
