from app.ui.card_client_automation import CARD_CLIENT_AUTOMATION_SCRIPT


def test_real_outcome_continues_from_review_into_next_proposed_action_plan(client):
    html = client.get('/app').text

    for marker in (
        'clientBaseLifecycleAfterOutcomeRecorded',
        'await clientBaseLifecycleAfterOutcomeRecorded()',
        'await generateActionPlan()',
        'await loadSavedActionPlan()',
        'await loadActionDecisionContext()',
        '新的行动仍需你确认，系统不会自动执行',
    ):
        assert marker in CARD_CLIENT_AUTOMATION_SCRIPT
        assert marker in html


def test_post_outcome_automation_does_not_cross_reality_boundaries():
    for forbidden in (
        "submitActionDecision(",
        "recordActionExecution(",
        "recordActionOutcome(",
        "persistSelectedActionLearning(",
        "method: 'POST'",
        "method: 'PATCH'",
        "method: 'DELETE'",
        "fetch(",
        "api('/api/",
    ):
        assert forbidden not in CARD_CLIENT_AUTOMATION_SCRIPT
