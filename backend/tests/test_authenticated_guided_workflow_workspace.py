from app.ui.guided_workflow_workspace import GUIDED_WORKFLOW_SCRIPT


def test_guided_workflow_exposes_six_steps_in_real_usage_order(client):
    html = client.get("/app").text

    step_ids = [f'guided-step-{index}' for index in range(1, 7)]
    positions = [html.index(f'id="{step_id}"') for step_id in step_ids]

    assert positions == sorted(positions)
    for label in (
        "1 选择人物",
        "2 维护关系",
        "3 会话与证据",
        "4 AI 分析与回复",
        "5 行动计划与执行",
        "6 结果、学习与复盘",
    ):
        assert label in html


def test_guided_workflow_keeps_user_crud_and_explicit_lifecycle_controls(client):
    html = client.get("/app").text

    for control_id in (
        "create-person",
        "update-selected-person",
        "delete-selected-person",
        "create-relationship",
        "update-selected-relationship",
        "delete-selected-relationship",
        "create-conversation",
        "update-selected-conversation",
        "delete-selected-conversation",
        "create-message",
        "delete-selected-message",
        "create-interaction",
        "update-selected-interaction",
        "delete-selected-interaction",
        "prepare-strategic-reply-message",
        "confirm-action-decision",
        "reject-action-decision",
        "record-action-execution",
        "record-action-outcome",
        "persist-action-learning",
    ):
        assert f'id="{control_id}"' in html


def test_guided_workflow_uses_strategic_reply_as_primary_analysis_to_reply_action(client):
    html = client.get("/app").text

    assert 'id="guided-analysis-primary"' in html
    assert 'id="strategic-reply-workspace"' in html
    assert "guidedMoveNode('strategic-reply-workspace', 'guided-analysis-primary')" in html
    assert "guidedMoveNode('analysis', 'guided-analysis-advanced')" in html
    assert "guidedMoveNode('strategy-recommendation', 'guided-analysis-advanced')" in html
    assert "'load-strategic-reply': '分析并生成回复建议'" in html


def test_guided_action_plan_combines_only_generation_and_safe_reads(client):
    html = client.get("/app").text

    assert 'id="guided-generate-action-plan"' in html
    assert "await generateActionPlan();" in GUIDED_WORKFLOW_SCRIPT
    assert "await loadSavedActionPlan();" in GUIDED_WORKFLOW_SCRIPT
    assert "await loadActionDecisionContext();" in GUIDED_WORKFLOW_SCRIPT
    assert "submitActionDecision(" not in GUIDED_WORKFLOW_SCRIPT
    assert "recordActionExecution(" not in GUIDED_WORKFLOW_SCRIPT
    assert "recordActionOutcome(" not in GUIDED_WORKFLOW_SCRIPT
    assert "persistSelectedActionLearning(" not in GUIDED_WORKFLOW_SCRIPT


def test_guided_feedback_learning_consolidation_is_read_only(client):
    html = client.get("/app").text

    assert 'id="guided-load-feedback-learning"' in html
    assert "await loadActionFeedback();" in GUIDED_WORKFLOW_SCRIPT
    assert "await loadActionLearning();" in GUIDED_WORKFLOW_SCRIPT
    assert "await loadPersistedActionLearning();" in GUIDED_WORKFLOW_SCRIPT
    assert "persistSelectedActionLearning(" not in GUIDED_WORKFLOW_SCRIPT


def test_guided_reanalysis_combines_input_read_with_one_explicit_llm_action(client):
    html = client.get("/app").text

    assert 'id="guided-run-reanalysis"' in html
    assert "await loadActionReanalysisInputs();" in GUIDED_WORKFLOW_SCRIPT
    assert "await runActionReanalysis();" in GUIDED_WORKFLOW_SCRIPT
    assert "重新分析仍需显式触发" in html


def test_guided_composition_layer_does_not_bypass_canonical_api_or_write_directly():
    assert "/api/v1/" not in GUIDED_WORKFLOW_SCRIPT
    assert "method: 'POST'" not in GUIDED_WORKFLOW_SCRIPT
    assert "method: 'PATCH'" not in GUIDED_WORKFLOW_SCRIPT
    assert "method: 'DELETE'" not in GUIDED_WORKFLOW_SCRIPT
    assert "fetch(" not in GUIDED_WORKFLOW_SCRIPT


def test_guided_workflow_does_not_auto_run_business_actions_on_initialization():
    initialization = GUIDED_WORKFLOW_SCRIPT.rsplit("guidedReorganizeLayout();", 1)[1]

    assert "guidedLocalizeStaticUI();" in initialization
    assert "bind('guided-generate-action-plan'" in initialization
    assert "bind('guided-load-feedback-learning'" in initialization
    assert "bind('guided-run-reanalysis'" in initialization
    assert "guidedGenerateActionPlan();" not in initialization
    assert "guidedLoadFeedbackLearning();" not in initialization
    assert "guidedRunReanalysis();" not in initialization
