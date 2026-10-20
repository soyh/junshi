"""Probe: what does an un-logged-in XHS/Soul browser show?"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.xhs import XhsChannel  # noqa: E402
from lovebridge.channels.soul import SoulChannel  # noqa: E402


async def probe(kind: str) -> None:
    root = Path(__file__).resolve().parents[1]
    profile = root / "profiles" / f"probe-{kind}"
    channel = XhsChannel(profile_dir=profile) if kind == "xhs" else SoulChannel(profile_dir=profile)
    print(f"== {kind}: starting with fresh profile {profile}", flush=True)
    try:
        await asyncio.wait_for(channel.start(), timeout=90)
        print(f"{kind}.start ok", flush=True)
    except Exception as exc:
        print(f"{kind}.start FAILED: {exc!r}", flush=True)
    try:
        print(f"{kind}.healthy => {await channel.healthy()}", flush=True)
        page = channel._page
        print("url:", page.url, flush=True)
        html = await page.content()
        for token in ("扫码登录", "手机号登录", "登录", "conv-list", "xhs-im-conv-list", "消息"):
            print(f"  contains {token!r}: {token in html}", flush=True)
        await page.screenshot(path=str(root / "screenshots" / f"probe-{kind}.png"))
    except Exception as exc:
        print(f"{kind} probe FAILED: {exc!r}", flush=True)
    await asyncio.sleep(5)
    await channel.stop()


async def main() -> None:
    for kind in ("xhs", "soul"):
        try:
            await probe(kind)
        except Exception as exc:
            print(f"{kind} outer FAILED: {exc!r}", flush=True)


asyncio.run(main())
