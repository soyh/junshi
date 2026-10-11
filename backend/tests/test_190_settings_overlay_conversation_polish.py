from app.ui.card_client_compact_surface import (
    CARD_CLIENT_COMPACT_SURFACE_SCRIPT,
    CARD_CLIENT_COMPACT_SURFACE_STYLE,
)
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.settings_tab_workspace import (
    SETTINGS_TAB_WORKSPACE_SCRIPT,
    SETTINGS_TAB_WORKSPACE_STYLE,
)


def test_test190_customer_settings_open_as_wide_fixed_workspace():
    style = SETTINGS_TAB_WORKSPACE_STYLE

    assert "#client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace" in style
    assert "position: fixed !important;" in style
    assert "width: min(1180px, calc(100vw - 48px)) !important;" in style
    assert "transform: translateX(-50%) !important;" in style
    assert "max-height: calc(100vh - 132px) !important;" in style
    assert "backdrop-filter: blur(24px);" in style
    assert "#client-settings-host #guided-settings[open]::before" in style


def test_test190_settings_tabs_use_short_localized_labels():
    script = SETTINGS_TAB_WORKSPACE_SCRIPT

    assert "'Session management': '登录会话'" in script
    assert "'Account Security': '账号安全'" in script
    assert "'LLM 模型设置': '模型设置'" in script
    assert "tab.dataset.sourceLabel = sourceLabel;" in script
    assert "tab.textContent = tabLabels[sourceLabel] || sourceLabel;" in script


def test_test190_current_conversation_chip_matches_sky_blue_language():
    style = CARD_CLIENT_COMPACT_SURFACE_STYLE

    assert ".client-conversation-chip.is-current" in style
    assert "var(--sky-900, #0b2f50)" in style
    assert "rgba(228,248,255,.98)" in style
    assert ".client-conversation-chip-state" in style
    assert ".client-conversation-chip-label" in style
    assert "background: var(--sky-500, #19a7e8);" in style

    # The old dark indigo/teal selected chip is intentionally retired.
    assert "linear-gradient(135deg, #4f46e5, #0891b2)" not in style


def test_test190_conversation_chip_hides_backend_state_suffix_and_marks_current():
    script = CARD_CLIENT_COMPACT_SURFACE_SCRIPT

    assert "replace(/\\s*·\\s*(active|archived)\\s*$/i, '')" in script
    assert "label.className = 'client-conversation-chip-label';" in script
    assert "state.className = 'client-conversation-chip-state';" in script
    assert "state.textContent = '当前';" in script
    assert "button.title = isCurrent ? `当前会话：${labelText}`" in script
    assert "button.classList.toggle('is-current', option.value === selectedConversationId);" in script


def test_test190_composed_shell_contains_wide_settings_and_polished_conversation_contract():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "width: min(1180px, calc(100vw - 48px)) !important;" in html
    assert "'Session management': '登录会话'" in html
    assert "'Account Security': '账号安全'" in html
    assert ".client-conversation-chip-state" in html
    assert "state.textContent = '当前';" in html
    assert "active|archived" in html

    # Preserve TEST-189's dual-model runtime mount and roles.
    assert 'id="provider"' in html
    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html
    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html
