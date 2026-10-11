from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.viewport_safe_ui_polish import VIEWPORT_SAFE_UI_POLISH_STYLE


def test_test202_phone_tabs_are_two_column_without_horizontal_scrolling():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "TEST-202: settings navigation stays visible and touch-friendly on phones" in style
    assert "#client-settings-host #guided-settings-tabs" in style
    assert "grid-template-columns: repeat(2, minmax(0, 1fr)) !important;" in style
    assert "overflow-x: visible !important;" in style
    assert "scrollbar-gutter: auto !important;" in style


def test_test202_phone_tab_selected_state_has_explicit_contrast():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    selector = '#client-settings-host #guided-settings-tabs .settings-tab-button[aria-selected="true"]'
    assert selector in style
    selected = style[style.index(selector):]
    assert "color: #fff !important;" in selected
    assert "background: linear-gradient(135deg, var(--sky-500, #19a7e8), var(--sky-700, #0877b9)) !important;" in selected
    assert "white-space: normal !important;" in style
    assert "text-overflow: clip !important;" in style


def test_test202_phone_panel_is_touch_scrollable_to_bottom_actions():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "The second row is the only scrolling surface so bottom actions remain reachable" in style
    assert "padding: 11px 10px calc(18px + env(safe-area-inset-bottom)) !important;" in style
    assert "overflow-y: auto !important;" in style
    assert "overscroll-behavior: contain !important;" in style
    assert "-webkit-overflow-scrolling: touch;" in style


def test_test202_account_security_is_single_column_and_touch_sized():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#client-settings-host #guided-settings-panel-host #account-security .workspace-grid" in style
    assert "grid-template-columns: minmax(0, 1fr) !important;" in style
    assert "#client-settings-host #guided-settings-panel-host #account-security button" in style
    assert "min-height: 44px !important;" in style


def test_test202_model_settings_stack_fields_headers_and_actions_on_phones():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#client-settings-host #guided-settings-panel-host #dual-model-settings .dual-model-card-header" in style
    assert "flex-wrap: wrap !important;" in style
    assert "#client-settings-host #guided-settings-panel-host #dual-model-settings .dual-model-fields" in style
    assert "#client-settings-host #guided-settings-panel-host #dual-model-settings .dual-model-actions" in style
    assert "#client-settings-host #guided-settings-panel-host #dual-model-settings .dual-model-actions button" in style
    assert "width: 100% !important;" in style


def test_test202_final_override_is_composed_after_verified_settings_layers():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert style.index("TEST-193: settings navigation") < style.index("TEST-202: settings navigation")
    assert "TEST-202: settings navigation stays visible and touch-friendly on phones" in html
    assert html.index("#dual-model-settings .dual-model-actions {") < html.index("TEST-202: settings navigation")
    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html
    assert 'id="account-security"' in html
    assert 'id="provider"' in html
    assert "dual-model-settings" in html
