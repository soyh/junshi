"""A sticker or photo must not silently swallow the turn."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge.channels.base import (  # noqa: E402
    MEDIA_IMAGE,
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
