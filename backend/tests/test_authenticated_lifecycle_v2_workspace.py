from app.ui.lifecycle_v2_workspace import LIFECYCLE_V2_SCRIPT, LIFECYCLE_V2_STYLE


def test_settings_are_nested_compact_panels_with_scrollable_content(client):
    html = client.get('/app').text
    assert 'lifecycle-settings-panel' in html
    assert '#guided-settings-content' in LIFECYCLE_V2_STYLE
    assert 'repeat(auto-fit, minmax(280px, 1fr))' in LIFECYCLE_V2_STYLE
    assert 'max-height: min(72vh, 760px)' in LIFECYCLE_V2_STYLE
    assert 'overflow-y: auto' in LIFECYCLE_V2_STYLE
    assert 'scrollbar-gutter: stable' in LIFECYCLE_V2_STYLE


def test_collapsed_long_content_remains_scrollable():
    assert '.user-long-content:not(.is-expanded)' in LIFECYCLE_V2_STYLE
    assert '.user-long-list:not(.is-expanded)' in LIFECYCLE_V2_STYLE
    assert 'max-height: 12rem !important' in LIFECYCLE_V2_STYLE
    assert 'overflow-y: auto !important' in LIFECYCLE_V2_STYLE
    assert 'overscroll-behavior: contain' in LIFECYCLE_V2_STYLE


def test_guided_flow_is_recomposed_to_four_user_stages():
    assert "['#guided-step-1', '1 选择人物']" in LIFECYCLE_V2_SCRIPT
    assert "['#guided-step-2', '2 编辑关系']" in LIFECYCLE_V2_SCRIPT
    assert "['#guided-step-3', '3 主会话与 AI']" in LIFECYCLE_V2_SCRIPT
    assert "['#guided-step-5', '4 行动与复盘']" in LIFECYCLE_V2_SCRIPT
    assert "step4.classList.add('lifecycle-hidden-step')" in LIFECYCLE_V2_SCRIPT
    assert "step6.classList.add('lifecycle-hidden-step')" in LIFECYCLE_V2_SCRIPT


def test_one_primary_conversation_is_presented_without_deleting_history():
    assert 'lifecycle-primary-conversation-only' in LIFECYCLE_V2_STYLE
    assert 'lifecycleEnsurePrimaryConversation' in LIFECYCLE_V2_SCRIPT
    assert 'lifecycleSelectPrimaryConversation' in LIFECYCLE_V2_SCRIPT
    assert "options[options.length - 1]" in LIFECYCLE_V2_SCRIPT
    assert '已有历史会话不会删除' in LIFECYCLE_V2_SCRIPT
    for forbidden in ("method: 'DELETE'", '.splice(', 'removeChild('):
        assert forbidden not in LIFECYCLE_V2_SCRIPT


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
