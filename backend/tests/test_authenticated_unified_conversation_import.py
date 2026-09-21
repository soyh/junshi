from app.ui.card_client_unified_import import (
    CARD_CLIENT_UNIFIED_IMPORT_SCRIPT,
    CARD_CLIENT_UNIFIED_IMPORT_STYLE,
)


def test_client_exposes_one_unified_conversation_importer(client):
    html = client.get('/app').text

    assert 'client-unified-import-card' in html
    assert '导入会话内容' in html
    assert '添加到当前会话' in html
    assert '无需选择单条或批量模式' in html
    assert 'client-legacy-message-card' in CARD_CLIENT_UNIFIED_IMPORT_STYLE
    assert 'client-legacy-batch-card' in CARD_CLIENT_UNIFIED_IMPORT_STYLE
    assert 'display: none !important' in CARD_CLIENT_UNIFIED_IMPORT_STYLE


def test_unified_import_reuses_verified_single_and_batch_paths():
    assert 'clientUnifiedLooksLikeStructuredImport' in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert "await importTextBatch()" in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert "byId('message-content').value = text.trim()" in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert 'await createMessage()' in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert "new Set(['user', 'person', 'system', 'assistant'])" in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT


def test_unified_import_keeps_current_conversation_scope_and_automation_boundary():
    assert "if (!selectedConversationId) throw new Error('请先选择会话')" in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert "api('/api/" not in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert 'fetch(' not in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert "method: 'POST'" not in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert 'recordActionExecution(' not in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert 'recordActionOutcome(' not in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT


def test_unified_import_preserves_legacy_controls_for_verified_internal_paths(client):
    html = client.get('/app').text
    for control_id in (
        'message-sender',
        'message-sent-at',
        'message-content',
        'create-message',
        'text-import-body',
        'import-text',
        'load-messages',
        'message-list',
    ):
        assert f'id="{control_id}"' in html


def test_conversation_stage_copy_describes_automatic_mode_detection():
    assert '系统自动识别一条或多条' in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert '普通文本会作为一条消息添加' in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
    assert '时间 | 发送者 | 内容' in CARD_CLIENT_UNIFIED_IMPORT_SCRIPT
