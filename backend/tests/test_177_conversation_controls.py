from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_main_app_server_renders_all_provider_choices():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    expected = {
        'value="qwen"': "Qwen / 阿里云百炼",
        'value="deepseek"': "DeepSeek",
        'value="kimi"': "Kimi / Moonshot",
        'value="openai"': "OpenAI",
        'value="gemini"': "Gemini / Google",
        'value="openai_compatible"': "其他 OpenAI-compatible",
    }
    for value, label in expected.items():
        assert value in html
        assert label in html


def test_main_app_exposes_conversation_edit_delete_controls():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert 'id="client-edit-conversation"' in html
    assert 'id="client-save-conversation"' in html
    assert 'id="client-delete-conversation"' in html
    assert "method: 'PATCH'" in html
    assert "method: 'DELETE'" in html


def test_message_time_window_is_display_only():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert 'id="client-message-from"' in html
    assert 'id="client-message-to"' in html
    assert '按时间显示' in html
    assert '显示全部' in html
    assert 'AI 分析始终参考该会话完整历史' in html
    assert "/analysis/structured" in html


def test_provider_api_key_safety_copy_remains_visible():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert "API Key 仍只在服务端加密保存" in html
    assert "API Key 只提交给服务端加密保存" in html
