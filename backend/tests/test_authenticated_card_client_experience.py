from app.ui.card_client_experience import (
    CARD_CLIENT_EXPERIENCE_SCRIPT,
    CARD_CLIENT_EXPERIENCE_STYLE,
)


def test_app_exposes_card_game_client_shell(client):
    html = client.get('/app').text

    for marker in (
        'client-experience-shell',
        'client-person-deck',
        'client-conversation-host',
        'client-results-grid',
        'client-reality-checks',
        '人物卡组',
        '当前会话',
        '军师结果',
    ):
        assert marker in html

    assert 'perspective: 1200px' in CARD_CLIENT_EXPERIENCE_STYLE
    assert 'transform: rotateY(180deg)' in CARD_CLIENT_EXPERIENCE_STYLE
    assert '@keyframes clientCardFloat' in CARD_CLIENT_EXPERIENCE_STYLE
    assert 'animation: clientCardFloat' in CARD_CLIENT_EXPERIENCE_STYLE


def test_person_and_relationship_are_merged_into_flippable_cards():
    assert '#guided-step-1,' in CARD_CLIENT_EXPERIENCE_STYLE
    assert '#guided-step-2,' in CARD_CLIENT_EXPERIENCE_STYLE
    assert "clientEl('h2', '', '人物卡组')" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "clientEl('div', 'client-card-section-title', '人物资料')" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "clientEl('div', 'client-card-section-title', '人物关系')" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "card.classList.add('is-flipped')" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "card.classList.remove('is-flipped')" in CARD_CLIENT_EXPERIENCE_SCRIPT


def test_person_card_edits_reuse_canonical_person_and_relationship_apis():
    for marker in (
        "api(`/api/v1/persons/${encodeURIComponent(personId)}`)",
        "api(`/api/v1/persons/${encodeURIComponent(personId)}`, {",
        "api('/api/v1/persons', {",
        "api('/api/v1/relationships')",
        "api(`/api/v1/relationships/${encodeURIComponent(relationSelect.value)}`, {",
        "api('/api/v1/relationships', {",
    ):
        assert marker in CARD_CLIENT_EXPERIENCE_SCRIPT

    assert "method: 'PATCH'" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "method: 'POST'" in CARD_CLIENT_EXPERIENCE_SCRIPT


def test_person_deck_contains_history_cards_and_one_new_person_card_only():
    assert "const options = Array.from(select.options).filter((option) => option.value);" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "deck.replaceChildren();" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "deck.appendChild(clientBuildPersonCard" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "deck.appendChild(clientBuildNewPersonCard(options.length));" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "client-card-name', isNew ? '新建人物'" in CARD_CLIENT_EXPERIENCE_SCRIPT


def test_conversation_entry_reuses_test166_multi_session_and_single_batch_content(client):
    html = client.get('/app').text

    for marker in (
        'conversation-select',
        'create-conversation',
        'message-content',
        'create-message',
        'text-import-body',
        'import-text',
        'Import into current conversation',
    ):
        assert marker in html

    assert "conversationHost.appendChild(conversationCard)" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "conversationHost.appendChild(conversationContent)" in CARD_CLIENT_EXPERIENCE_SCRIPT


def test_customer_result_surface_keeps_only_reply_action_review_and_needed_confirmation():
    for marker in (
        "replyHost.id = 'client-reply-host'",
        "actionCard.id = 'client-action-result'",
        "reviewCard.id = 'client-review-result'",
        "reality.id = 'client-reality-checks'",
        "'回复建议'",
        "'下一步行动'",
        "'最新复盘'",
        "'需要你确认的下一步'",
        "'现实执行确认'",
        "'实际结果'",
    ):
        assert marker in CARD_CLIENT_EXPERIENCE_SCRIPT


def test_non_reality_work_is_automatic_but_real_world_facts_stay_explicit(client):
    html = client.get('/app').text

    for marker in (
        "junshi:evidence-changed",
        'await loadStrategicReply()',
        'await generateActionPlan()',
        'await loadSavedActionPlan()',
        'await loadActionDecisionContext()',
        'await loadActionFeedback()',
        'await loadActionLearning()',
        'await loadPersistedActionLearning()',
        'await loadActionReanalysisInputs()',
        'await runActionReanalysis()',
    ):
        assert marker in html

    # The customer layer may read contexts automatically, but must never invent
    # a user decision, execution or real-world outcome.
    assert "submitActionDecision('confirmed')" not in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert 'recordActionExecution()' not in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert 'recordActionOutcome()' not in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "loadActionDecisionContext()" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "loadActionExecutionContext()" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "loadActionOutcomeContext()" in CARD_CLIENT_EXPERIENCE_SCRIPT


def test_settings_remain_available_without_restoring_full_workspace():
    assert "settingsHost.id = 'client-settings-host'" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert "settingsHost.appendChild(settings)" in CARD_CLIENT_EXPERIENCE_SCRIPT
    assert '#client-settings-host #guided-settings-content' in CARD_CLIENT_EXPERIENCE_STYLE
