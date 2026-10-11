from app.ui.conversation_session_workspace import (
    CONVERSATION_SESSION_SCRIPT,
    CONVERSATION_SESSION_STYLE,
)
from app.ui.lifecycle_v2_workspace import LIFECYCLE_V2_SCRIPT, LIFECYCLE_V2_STYLE


def test_settings_are_horizontal_tabs_with_scrollable_content(client):
    html = client.get('/app').text
    assert 'lifecycle-settings-panel' in html
    assert '#guided-settings-content' in LIFECYCLE_V2_STYLE
    assert 'repeat(4, minmax(150px, 1fr))' in LIFECYCLE_V2_STYLE
    assert '#guided-settings-content > .lifecycle-settings-panel {' in LIFECYCLE_V2_STYLE
    assert 'display: contents' in LIFECYCLE_V2_STYLE
    assert 'grid-row: 1' in LIFECYCLE_V2_STYLE
    assert 'grid-column: 1 / -1' in LIFECYCLE_V2_STYLE
    assert 'max-height: min(72vh, 760px)' in LIFECYCLE_V2_STYLE
    assert 'overflow-y: auto' in LIFECYCLE_V2_STYLE
    assert 'overflow-x: auto' in LIFECYCLE_V2_STYLE
    assert 'scrollbar-gutter: stable' in LIFECYCLE_V2_STYLE
    assert "settings.querySelectorAll(':scope > .lifecycle-settings-panel')" in LIFECYCLE_V2_SCRIPT
    assert 'other.open = false' in LIFECYCLE_V2_SCRIPT


def test_collapsed_long_content_remains_scrollable():
    assert '.user-long-content:not(.is-expanded)' in LIFECYCLE_V2_STYLE
    assert '.user-long-list:not(.is-expanded)' in LIFECYCLE_V2_STYLE
    assert 'max-height: 12rem !important' in LIFECYCLE_V2_STYLE
    assert 'overflow-y: auto !important' in LIFECYCLE_V2_STYLE
    assert 'overscroll-behavior: contain' in LIFECYCLE_V2_STYLE


def test_duplicate_product_shell_header_is_hidden_but_not_deleted(client):
    html = client.get('/app').text
    assert '<header>' in html
    assert 'body > header' in LIFECYCLE_V2_STYLE
    assert 'display: none !important' in LIFECYCLE_V2_STYLE
    assert '<h1>AI Love Strategist</h1>' in html


def test_daily_workflow_is_restored_to_vertical_layout():
    assert 'grid-template-columns: repeat(4, minmax(0, 1fr)) !important' not in LIFECYCLE_V2_STYLE
    assert 'max-height: calc(100vh - 245px)' not in LIFECYCLE_V2_STYLE
    assert '#guided-workflow > .guided-step:not(.lifecycle-hidden-step)' not in LIFECYCLE_V2_STYLE
    assert 'grid-template-columns: repeat(2, minmax(0, 1fr)) !important' not in LIFECYCLE_V2_STYLE


def test_guided_flow_is_recomposed_to_four_user_stages():
    assert "['#guided-step-1', '1 选择人物']" in LIFECYCLE_V2_SCRIPT
    assert "['#guided-step-2', '2 编辑关系']" in LIFECYCLE_V2_SCRIPT
    assert "['#guided-step-3', '3 主会话与 AI']" in LIFECYCLE_V2_SCRIPT
    assert "['#guided-step-5', '4 行动与复盘']" in LIFECYCLE_V2_SCRIPT
    assert "step4.classList.add('lifecycle-hidden-step')" in LIFECYCLE_V2_SCRIPT
    assert "step6.classList.add('lifecycle-hidden-step')" in LIFECYCLE_V2_SCRIPT


def test_multi_conversation_presentation_overrides_legacy_primary_conversation_without_deleting_history(client):
    html = client.get('/app').text

    # The older lifecycle layer is retained for compatibility and still contains no
    # destructive history operation, but TEST-166 removes its single-primary UI rule.
    assert 'lifecycle-primary-conversation-only' in LIFECYCLE_V2_STYLE
    for forbidden in ("method: 'DELETE'", '.splice(', 'removeChild('):
        assert forbidden not in LIFECYCLE_V2_SCRIPT

    assert "card.classList.remove('lifecycle-primary-conversation-only')" in CONVERSATION_SESSION_SCRIPT
    assert "select.size = 8" in CONVERSATION_SESSION_SCRIPT
    assert "options.find((option) => option.value === selectedConversationId)" in CONVERSATION_SESSION_SCRIPT
    assert "options[0]" in CONVERSATION_SESSION_SCRIPT
    assert "await loadConversations();" in CONVERSATION_SESSION_SCRIPT
    assert "api('/api/v1/conversations'" not in CONVERSATION_SESSION_SCRIPT
    assert "method: 'POST'" not in CONVERSATION_SESSION_SCRIPT
    assert '当前人物可以保留多个会话' in html
    assert '#conversation-select' in CONVERSATION_SESSION_STYLE


def test_evidence_change_automatically_refreshes_reply_and_action_plan():
    for marker in (
        "junshi:evidence-changed",
        'await loadStrategicReply()',
        'await generateActionPlan()',
        'await loadSavedActionPlan()',
        'await loadActionDecisionContext()',
    ):
        assert marker in LIFECYCLE_V2_SCRIPT


def test_decision_execution_outcome_keep_reality_boundaries():
    assert "detail.decision !== 'confirmed'" in LIFECYCLE_V2_SCRIPT
    assert 'await loadActionExecutionContext()' in LIFECYCLE_V2_SCRIPT
    assert 'await loadActionOutcomeContext()' in LIFECYCLE_V2_SCRIPT
    assert '系统不会猜测现实结果' in LIFECYCLE_V2_SCRIPT
    assert 'recordActionExecution(' not in LIFECYCLE_V2_SCRIPT
    assert 'recordActionOutcome(' not in LIFECYCLE_V2_SCRIPT


def test_outcome_automatically_refreshes_feedback_learning_and_reanalysis():
    for marker in (
        'await loadActionFeedback()',
        'await loadActionLearning()',
        'await loadPersistedActionLearning()',
        'await loadActionReanalysisInputs()',
        'await runActionReanalysis()',
    ):
        assert marker in LIFECYCLE_V2_SCRIPT
    assert 'persistSelectedActionLearning(' not in LIFECYCLE_V2_SCRIPT


def test_existing_explicit_user_controls_remain_available(client):
    html = client.get('/app').text
    for control_id in (
        'update-selected-relationship',
        'create-message',
        'import-text',
        'copy-strategic-reply',
        'prepare-strategic-reply-message',
        'confirm-action-decision',
        'reject-action-decision',
        'record-action-execution',
        'record-action-outcome',
        'persist-action-learning',
    ):
        assert f'id="{control_id}"' in html


def test_lifecycle_layer_has_no_second_direct_api_write_path():
    for forbidden in (
        "api('/api/",
        'fetch(',
        "method: 'POST'",
        "method: 'PATCH'",
        "method: 'DELETE'",
    ):
        assert forbidden not in LIFECYCLE_V2_SCRIPT
