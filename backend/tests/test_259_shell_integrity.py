"""Build 259: the shipped shell has no duplicate ids and the new controls exist."""

import re
from collections import Counter

from app.ui.routes import build_product_shell_html


def test_rendered_shell_has_no_duplicate_element_ids():
    html = build_product_shell_html()
    ids = Counter(re.findall(r'id="([^"]+)"', html))

    duplicates = {name: count for name, count in ids.items() if count > 1}
    assert duplicates == {}


def test_shell_exposes_the_batch_intent_and_takeover_controls():
    html = build_product_shell_html()

    for marker in (
        "client-batch-intent-open",
        "client-batch-intent",
        "client-conversation-takeover",
    ):
        assert marker in html


def test_navigation_script_closes_the_editor_from_the_flip_back_button():
    html = build_product_shell_html()

    # The modal has its own close path; the old button flipped a card that was
    # not on screen, so it looked dead.
    assert "navClosePersonEditor()" in html
    assert "batch-intent" in html
