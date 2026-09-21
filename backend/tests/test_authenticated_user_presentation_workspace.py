from app.ui.user_presentation_workspace import (
    USER_PRESENTATION_SCRIPT,
    USER_PRESENTATION_STYLE,
)


def test_product_shell_exposes_compact_user_presentation(client):
    html = client.get("/app").text

    for marker in (
        "user-long-content",
        "点击展开",
        "双击收起",
        "userPresentationObserver",
        "user-system-message",
        "user-system-copy",
        "userDrawerSelectors",
    ):
        assert marker in html


def test_long_content_drawer_uses_click_expand_and_double_click_collapse():
    assert "const userLongContentThreshold = 260" in USER_PRESENTATION_SCRIPT
    assert "const userLongListRowThreshold = 4" in USER_PRESENTATION_SCRIPT
    assert "node.addEventListener('click'" in USER_PRESENTATION_SCRIPT
    assert "node.classList.add('is-expanded')" in USER_PRESENTATION_SCRIPT
    assert "node.addEventListener('dblclick'" in USER_PRESENTATION_SCRIPT
    assert "node.classList.remove('is-expanded')" in USER_PRESENTATION_SCRIPT
    assert "node.dataset.drawerLabel = '点击展开'" in USER_PRESENTATION_SCRIPT
    assert "node.dataset.drawerLabel = '双击收起'" in USER_PRESENTATION_SCRIPT
    assert "aria-expanded" in USER_PRESENTATION_SCRIPT


def test_comprehensive_drawers_cover_long_user_result_windows(client):
    html = client.get("/app").text

    expected_targets = (
        "manage-message-detail",
        "message-list",
        "interaction-list",
        "timeline-list",
        "analysis-result",
        "strategy-context-summary",
        "strategy-candidate-list",
        "recommendation-list",
        "strategic-reply-context",
        "strategic-reply-recommendations",
        "generated-action-plan-summary",
        "generated-action-plan-list",
        "saved-action-plan-list",
        "action-decision-history",
        "action-execution-decisions",
        "action-outcome-history",
        "action-feedback-items",
        "action-feedback-trend",
        "action-learning-history",
        "action-reanalysis-learning",
        "action-reanalysis-analysis",
        "action-reanalysis-recommendations",
    )

    for target in expected_targets:
        assert f'id="{target}"' in html
        assert f"'#{target}'" in USER_PRESENTATION_SCRIPT


def test_drawer_observer_handles_textcontent_replacement_and_list_growth():
    # textContent assignment commonly arrives as a childList mutation whose
    # added node is a Text node. TEST-160 missed that path for message detail.
    assert "node.nodeType === Node.TEXT_NODE && node.parentElement" in USER_PRESENTATION_SCRIPT
    assert "userEnhanceVisibleContent(node.parentElement)" in USER_PRESENTATION_SCRIPT
    assert "const targetElement = mutation.target instanceof Element" in USER_PRESENTATION_SCRIPT

    # A window with many short records must also collapse even if no individual
    # message exceeds the character threshold.
    assert "const rowCount = node.querySelectorAll(':scope > .session-row').length" in USER_PRESENTATION_SCRIPT
    assert "forceWindow && rowCount > userLongListRowThreshold" in USER_PRESENTATION_SCRIPT


def test_drawer_rechecks_when_dynamic_content_changes():
    assert "node.dataset.userDrawerContentKey" in USER_PRESENTATION_SCRIPT
    assert "const contentChanged" in USER_PRESENTATION_SCRIPT
    assert "if (contentChanged || !node.hasAttribute('aria-expanded'))" in USER_PRESENTATION_SCRIPT
    assert "userSetDrawerExpanded(node, false)" in USER_PRESENTATION_SCRIPT


def test_compact_layout_prevents_large_grid_whitespace():
    assert "align-items: start !important" in USER_PRESENTATION_STYLE
    assert ".workspace-grid { gap: 10px !important; }" in USER_PRESENTATION_STYLE
    assert ".guided-workflow { gap: 12px !important; }" in USER_PRESENTATION_STYLE
    assert ".guided-step {" in USER_PRESENTATION_STYLE
    assert "padding: 14px 16px !important" in USER_PRESENTATION_STYLE
    assert "repeat(auto-fit, minmax(340px, 1fr))" in USER_PRESENTATION_STYLE
    assert ".status {" in USER_PRESENTATION_STYLE
    assert "min-height: 0 !important" in USER_PRESENTATION_STYLE
    assert ".user-drawer-window.user-long-content:not(.is-expanded)" in USER_PRESENTATION_STYLE


def test_user_presentation_hides_system_facing_metadata_without_deleting_data():
    assert ".visual-system-kicker" in USER_PRESENTATION_STYLE
    assert "#conversation-id" in USER_PRESENTATION_STYLE
    assert "canonical API" in USER_PRESENTATION_SCRIPT
    assert "source metadata" in USER_PRESENTATION_SCRIPT
    assert "userUuidPattern" in USER_PRESENTATION_SCRIPT
    assert "/\\b(system|assistant)\\b/i.test(metaText)" in USER_PRESENTATION_SCRIPT
    assert "row.classList.add('user-system-message')" in USER_PRESENTATION_SCRIPT

    # Presentation-only: do not mutate arrays, remove canonical records, or
    # create a hidden second write path.
    for forbidden in (
        "fetch(",
        "api(",
        "method: 'POST'",
        "method: 'PATCH'",
        "method: 'DELETE'",
        ".splice(",
    ):
        assert forbidden not in USER_PRESENTATION_SCRIPT


def test_user_presentation_preserves_existing_explicit_action_controls(client):
    html = client.get("/app").text

    for control_id in (
        "create-message",
        "import-text",
        "load-strategic-reply",
        "copy-strategic-reply",
        "prepare-strategic-reply-message",
        "confirm-action-decision",
        "reject-action-decision",
        "record-action-execution",
        "record-action-outcome",
        "persist-action-learning",
    ):
        assert f'id="{control_id}"' in html


def test_presentation_layer_keeps_privacy_storage_boundaries(client):
    html = client.get("/app").text

    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
