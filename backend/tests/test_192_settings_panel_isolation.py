from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.viewport_safe_ui_polish import VIEWPORT_SAFE_UI_POLISH_STYLE


def test_test192_settings_panels_are_forced_back_into_normal_flow():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    marker = "TEST-192: every settings tab owns one normal-flow panel"
    selector = "#client-settings-host #guided-settings-panel-host > fieldset"

    assert marker in style
    assert selector in style
    assert "position: static !important;" in style
    assert "inset: auto !important;" in style
    assert "top: auto !important;" in style
    assert "right: auto !important;" in style
    assert "bottom: auto !important;" in style
    assert "left: auto !important;" in style
    assert "transform: none !important;" in style
    assert "translate: none !important;" in style
    assert "grid-area: auto !important;" in style
    assert "width: 100% !important;" in style
    assert "max-width: 100% !important;" in style


def test_test192_hidden_and_active_tab_panels_are_strictly_isolated():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    hidden_selector = (
        "#client-settings-host #guided-settings-panel-host > fieldset[hidden]"
    )
    active_selector = (
        "#client-settings-host #guided-settings-panel-host > fieldset:not([hidden])"
    )

    assert hidden_selector in style
    assert active_selector in style
    assert "display: none !important;" in style
    assert "visibility: hidden !important;" in style
    assert "pointer-events: none !important;" in style
    assert "display: block !important;" in style
    assert "visibility: visible !important;" in style
    assert "pointer-events: auto !important;" in style


def test_test192_tabs_stay_above_panels_and_host_is_isolated():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#guided-settings-tabs" in style
    assert "z-index: 4 !important;" in style
    assert "#client-settings-host #guided-settings-panel-host" in style
    assert "isolation: isolate !important;" in style
    assert "overflow-x: hidden !important;" in style
    assert "overflow-y: auto !important;" in style


def test_test192_inner_cards_and_forms_cannot_force_panel_width():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#client-settings-host #guided-settings-panel-host .workspace-grid" in style
    assert "#client-settings-host #guided-settings-panel-host .workspace-card" in style
    assert "#client-settings-host #guided-settings-panel-host input" in style
    assert "#client-settings-host #guided-settings-panel-host select" in style
    assert "#client-settings-host #guided-settings-panel-host textarea" in style
    assert "min-width: 0 !important;" in style
    assert "max-width: 100% !important;" in style


def test_test192_composed_html_keeps_verified_settings_and_test191_polish():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "TEST-191: final viewport-safe customer presentation overrides" in html
    assert "TEST-192: every settings tab owns one normal-flow panel" in html
    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html
    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html
    assert "#client-unified-message-history > summary::before" in html
    assert "#client-media-file::file-selector-button" in html
