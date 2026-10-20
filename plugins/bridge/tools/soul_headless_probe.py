"""Check the Soul channel's headless/login-wall fallback on a copied profile."""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.soul import SoulChannel  # noqa: E402

SOURCE = Path(
    r"C:\Users\12274\Documents\deepseek-harness\default-workspace\wechat-bridge\profiles\soul"
)


async def main() -> None:
    target = Path(tempfile.mkdtemp(prefix="soul-headless-")) / "profile"
    shutil.copytree(SOURCE, target)
    channel = SoulChannel(profile_dir=target, headless=True, interval=3.0)
    try:
        await channel.start()
        await asyncio.sleep(5)
        print("STATUS:", await channel.status(), flush=True)
        print("MARKER:", (target / ".logged-in").is_file(), flush=True)
    finally:
        await channel.stop()
        shutil.rmtree(target.parent, ignore_errors=True)


asyncio.run(main())
