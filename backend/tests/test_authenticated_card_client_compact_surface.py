def test_compact_surface_replaces_legacy_conversation_management(client):
    html = client.get('/app').text

    assert 'id="client-conversation-bar"' in html or "client-conversation-bar" in html
    assert 'client-legacy-conversation-card' in html
    assert '#client-conversation-host .client-legacy-conversation-card' in html
    assert 'display: none !important' in html
    assert 'client-conversation-tabs' in html
    assert 'client-conversation-chip' in html
    assert '＋ 新会话' in html


def test_compact_surface_keeps_unified_import_as_primary_customer_input(client):
    html = client.get('/app').text

    assert 'client-unified-import-card' in html
    assert '添加到当前会话' in html
    assert '#client-unified-import-actions #load-messages' in html
    assert 'display: none !important' in html
    assert 'clientSubmitUnifiedConversationImport' in html


def test_compact_surface_quick_new_conversation_is_explicit(client):
    html = client.get('/app').text

    marker = "create.addEventListener('click', async () => {"
    assert marker in html
    segment = html[html.index(marker):]
    assert "await createConversation();" in segment
    assert "byId('conversation-title').value = `会话 ${count + 1}`;" in segment
    assert "byId('conversation-state').value = 'active';" in segment

    # The compact surface itself reuses the verified createConversation path;
    # it does not add a second POST implementation or create on person selection.
    compact_start = html.index('function clientConversationChipLabel')
    compact_end = html.index("const messagesStatus = byId('messages-status')")
    compact = html[compact_start:compact_end]
    assert "method: 'POST'" not in compact
    assert "api('/api/v1/conversations'" not in compact


def test_compact_surface_conversation_switch_reuses_canonical_select(client):
    html = client.get('/app').text

    assert "select.value = option.value;" in html
    assert "select.dispatchEvent(new Event('change', { bubbles: true }));" in html
    assert "button.dataset.conversationId = option.value;" in html
    assert "button.classList.toggle('is-current', option.value === selectedConversationId);" in html


def test_compact_surface_hides_success_pipeline_status_but_keeps_failures_visible(client):
    html = client.get('/app').text

    assert '#client-automation-status' in html
    assert '#client-reply-host #strategic-reply-status' in html
    assert '#client-action-result #action-plan-generate-status' in html
    assert 'client-runtime-alert' in html
    assert 'clientMirrorRuntimeStatus' in html
    assert 'failed|failure|error|timeout|失败|错误|异常|超时|未完全完成' in html
    assert "alert.classList.add('is-visible')" in html


def test_compact_surface_preserves_reality_confirmation_boundaries(client):
    html = client.get('/app').text

    assert '确认采用' in html
    assert '我已执行' in html
    assert '保存结果并自动复盘' in html
    assert '系统不会自动执行' in html
    assert 'client-reality-checks' in html
