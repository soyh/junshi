from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.viewport_safe_ui_polish import VIEWPORT_SAFE_UI_POLISH_STYLE


def test_test191_settings_overlay_is_bound_to_real_viewport():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#client-settings-host #guided-settings[open]" in style
    assert "position: fixed !important;" in style
    assert "inset: 0 !important;" in style
    assert "overflow: hidden !important;" in style

    assert "#client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace" in style
    assert "left: clamp(10px, 2.2vw, 30px) !important;" in style
    assert "right: clamp(10px, 2.2vw, 30px) !important;" in style
    assert "bottom: clamp(10px, 2.2vh, 24px) !important;" in style
    assert "width: auto !important;" in style
    assert "max-width: none !important;" in style
    assert "transform: none !important;" in style
    assert "grid-template-rows: auto minmax(0, 1fr) !important;" in style


def test_test191_conversation_history_is_card_button_not_long_strip():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#client-unified-message-history > summary" in style
    assert "display: inline-flex !important;" in style
    assert "width: auto !important;" in style
    assert "min-height: 42px !important;" in style
    assert "border-radius: 14px !important;" in style
    assert "#client-unified-message-history > summary::before" in style

    assert "#client-conversation-tabs" in style
    assert "grid-template-columns: repeat(auto-fill, minmax(190px, 240px)) !important;" in style
    assert ".client-conversation-chip" in style
    assert "min-height: 58px !important;" in style
    assert "grid-template-columns: auto minmax(0, 1fr) auto !important;" in style


def test_test191_media_file_picker_matches_sky_blue_theme():
    style = VIEWPORT_SAFE_UI_POLISH_STYLE

    assert "#client-media-file" in style
    assert "#client-media-file::file-selector-button" in style
    assert "border-radius: 13px !important;" in style
    assert "var(--sky-800, #075985)" in style
    assert "#client-media-actions #client-media-upload" in style
    assert "linear-gradient(135deg, var(--sky-500, #19a7e8), var(--sky-700, #0877b9))" in style
    assert "#client-media-actions #client-media-refresh" in style


def test_test191_polish_is_composed_after_older_ui_layers():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    old_settings = html.index("width: min(1180px, calc(100vw - 48px)) !important;")
    dual_model = html.index("#dual-model-settings")
    final_polish = html.index("TEST-191: final viewport-safe customer presentation overrides")

    assert old_settings < final_polish
    assert dual_model < final_polish

    assert "body:has(#guided-settings[open])" in html
    assert "#client-unified-message-history > summary::before" in html
    assert "#client-media-file::file-selector-button" in html
    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html


def test_test191_does_not_replace_verified_business_scripts():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html
    assert "clientInstallUnifiedConversationImport();" in html
    assert "clientInstallMediaUpload();" in html
    assert "clientRenderConversationBar();" in html
