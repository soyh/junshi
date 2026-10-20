"""Check a logged-in browser profile stays headless and reports online."""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.xhs import XhsChannel  # noqa: E402

SOURCE = Path(
    r"C:\Users\12274\Documents\deepseek-harness\default-workspace\wechat-bridge\profiles\xhs"
)


async def main() -> None:
    target = Path(tempfile.mkdtemp(prefix="xhs-headless-")) / "profile"
    shutil.copytree(SOURCE, target)
    channel = XhsChannel(profile_dir=target, headless=True, interval=3.0)
    try:
        await channel.start()
        await asyncio.sleep(4)
        print("STATUS:", await channel.status(), flush=True)
        print("MARKER:", (target / ".logged-in").is_file(), flush=True)
        print("VISIBLE:", getattr(channel, "_visible_for_login", None), flush=True)
    finally:
        await channel.stop()
        shutil.rmtree(target.parent, ignore_errors=True)


asyncio.run(main())
