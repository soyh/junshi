from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.viewport_safe_ui_polish import VIEWPORT_SAFE_UI_POLISH_STYLE


def test_test193_settings_workspace_is_explicitly_one_column_two_rows():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "TEST-193: settings navigation and its active operation page" in style
    assert "grid-template-columns: minmax(0, 1fr) !important;" in style
    assert "grid-template-rows: max-content minmax(0, 1fr) !important;" in style
    assert "row-gap: 14px !important;" in style


def test_test193_tab_bar_is_locked_to_first_row():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    selector = "#client-settings-host #guided-settings-tabs"
    assert selector in style
    assert "grid-column: 1 / -1 !important;" in style
    assert "grid-row: 1 !important;" in style
    assert "width: 100% !important;" in style
    assert "margin: 0 !important;" in style


def test_test193_operation_panel_is_locked_to_second_row():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    selector = "#client-settings-host #guided-settings-panel-host"
    assert selector in style
    assert "grid-row: 2 !important;" in style
    assert "align-self: stretch !important;" in style
    assert "justify-self: stretch !important;" in style
    assert "width: 100% !important;" in style


def test_test193_keeps_test192_panel_isolation_contract():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "TEST-192: every settings tab owns one normal-flow panel" in style
    assert "#client-settings-host #guided-settings-panel-host > fieldset[hidden]" in style
    assert "#client-settings-host #guided-settings-panel-host > fieldset:not([hidden])" in style
    assert "position: static !important;" in style
    assert "inset: auto !important;" in style


def test_test193_composed_product_shell_contains_two_row_contract_and_verified_ui():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "TEST-193: settings navigation and its active operation page" in html
    assert "grid-template-columns: minmax(0, 1fr) !important;" in html
    assert "grid-template-rows: max-content minmax(0, 1fr) !important;" in html
    assert "#client-settings-host #guided-settings-tabs" in html
    assert "#client-settings-host #guided-settings-panel-host" in html

    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html
    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html
    assert "#client-unified-message-history > summary::before" in html
    assert "#client-media-file::file-selector-button" in html
