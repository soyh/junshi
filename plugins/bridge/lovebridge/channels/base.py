"""Channel abstraction: anything that can deliver inbound messages and send text."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass
class InboundEvent:
    contact_id: str
    contact_name: str
    text: str
    message_id: str
    is_group: bool = False
    #: True when the bubble is *ours* — a reply the user typed by hand.
    is_self: bool = False
    timestamp: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


Handler = Callable[[InboundEvent], None]

# A bubble without text is still a message the other person sent: describe it so
# the bridge answers instead of silently dropping the turn.
MEDIA_STICKER = "[对方发了一个表情]"
MEDIA_IMAGE = "[对方发了一张图片]"
MEDIA_VOICE = "[对方发了一条语音]"
MEDIA_VIDEO = "[对方发了一段视频]"
MEDIA_LINK = "[对方发来一个链接]"
MEDIA_LOCATION = "[对方分享了一个位置]"
MEDIA_CARD = "[对方分享了一张卡片]"

_STICKER_HINTS = ("sticker", "emoji", "emoticon")
_IMAGE_HINTS = ("image", "img", "picture", "photo")
_VOICE_HINTS = ("voice", "audio")
_VIDEO_HINTS = ("video", "movie")
_LINK_HINTS = ("link", "url", "share", "article", "note", "webpage")
_LOCATION_HINTS = ("location", "position", "map", "geo", "poi")
_CARD_HINTS = ("card", "product", "goods", "item")

# Shared chats hide links behind cards, so a bubble with no text is still a
# message worth answering. Describe it instead of dropping the turn.
_DETAIL_LIMIT = 60


def _short(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= _DETAIL_LIMIT else text[:_DETAIL_LIMIT] + "…"


def _domain(url: str) -> str:
    rest = url.split("://", 1)[-1]
    return rest.split("/", 1)[0][:40]


def link_text(item: dict[str, Any]) -> str:
    """Describe a link / location / card bubble, or '' when it is none of them."""
    url = str(item.get("url") or item.get("link") or item.get("href") or "").strip()
    title = _short(item.get("title") or item.get("name"))
    place = _short(item.get("location") or item.get("address") or item.get("poi"))
    if place:
        return f"[对方分享了一个位置：{place}]"
    if url:
        suffix = f"（{title}）" if title else ""
        return f"[对方发来一个链接：{_domain(url)}{suffix}]"
    if title and str(item.get("type") or "").lower() in _CARD_HINTS:
        return f"[对方分享了一张卡片：{title}]"
    return ""


def media_text(item: dict[str, Any]) -> str:
    """Return a Chinese description for a non-text bubble, else ''."""
    kind = str(item.get("type") or item.get("content_type") or "").lower()

    def hit(flag: str, hints: tuple[str, ...]) -> bool:
        return bool(item.get(flag)) or any(hint in kind for hint in hints)

    if hit("sticker", _STICKER_HINTS):
        return MEDIA_STICKER
    # A place card can also carry a picture, so read the card before the image.
    place = _short(item.get("place") or item.get("location") or item.get("address") or item.get("poi"))
    if place:
        return f"[对方分享了一个位置：{place}]"
    if hit("location", _LOCATION_HINTS):
        return MEDIA_LOCATION
    if hit("link", _LINK_HINTS) or hit("card", _CARD_HINTS):
        return link_text(item) or (MEDIA_LINK if hit("link", _LINK_HINTS) else MEDIA_CARD)
    if hit("image", _IMAGE_HINTS):
        return MEDIA_IMAGE
    if hit("voice", _VOICE_HINTS):
        return MEDIA_VOICE
    if hit("video", _VIDEO_HINTS):
        return MEDIA_VIDEO
    if str(item.get("url") or "").strip():
        return link_text(item)
    return ""


class Channel(Protocol):
    def set_handler(self, handler: Handler) -> None: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None: ...


async def attach_file(page, path: str) -> bool:
    """Hand a local file to a chat composer, whatever hook the page offers.

    Most web chats keep a hidden ``input[type=file]``; some only open the picker
    from a toolbar button. Both are tried, and a False return means the channel
    cannot send files here (the caller then falls back to words).
    """
    inputs = page.locator("input[type=file]")
    if await inputs.count():
        try:
            await inputs.first.set_input_files(path)
            return True
        except Exception:
            pass
    selectors = (
        "[aria-label*='图片']", "[title*='图片']", "[aria-label*='相册']",
        "button[class*='image']", "[class*='image-btn']", "[class*='upload']",
        "input[accept*='image']",
    )
    for selector in selectors:
        locator = page.locator(selector).first
        if not await locator.count():
            continue
        try:
            async with page.expect_file_chooser(timeout=4000) as chooser:
                await locator.click(timeout=4000)
            await (await chooser.value).set_files(path)
            return True
        except Exception:
            continue
    return False
