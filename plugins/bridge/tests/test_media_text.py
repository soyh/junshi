"""A sticker or photo must not silently swallow the turn."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.base import (  # noqa: E402
    MEDIA_IMAGE,
    MEDIA_LINK,
    MEDIA_LOCATION,
    MEDIA_STICKER,
    MEDIA_VOICE,
    media_text,
)


def test_sticker_and_image_bubbles_get_a_description():
    assert media_text({"sticker": True}) == MEDIA_STICKER
    assert media_text({"image": True}) == MEDIA_IMAGE
    assert media_text({"type": "emoji"}) == MEDIA_STICKER
    assert media_text({"content_type": "picture"}) == MEDIA_IMAGE
    assert media_text({"voice": True}) == MEDIA_VOICE


def test_text_bubbles_are_left_alone():
    assert media_text({"text": "在吗", "type": "text"}) == ""
    assert media_text({}) == ""


def test_link_and_location_cards_are_described_instead_of_dropped():
    assert media_text({"place": "杭州西湖区文三路"}) == "[对方分享了一个位置：杭州西湖区文三路]"
    assert media_text({"type": "location"}) == MEDIA_LOCATION
    assert media_text({"url": "https://www.xiaohongshu.com/explore/abc"}) == "[对方发来一个链接：www.xiaohongshu.com]"
    assert (
        media_text({"type": "share", "url": "https://example.com/p/1", "title": "周末去哪儿"})
        == "[对方发来一个链接：example.com（周末去哪儿）]"
    )
    assert media_text({"type": "link"}) == MEDIA_LINK


def test_a_place_card_that_also_has_a_picture_stays_a_place():
    described = media_text({"place": "公司楼下", "image": True, "type": "location"})
    assert described == "[对方分享了一个位置：公司楼下]"


def test_long_card_text_is_trimmed():
    described = media_text({"url": "https://example.com/x", "title": "很" * 200})
    assert len(described) < 120 and described.endswith("]")
