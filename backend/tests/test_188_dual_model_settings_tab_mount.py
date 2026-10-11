from app.ui.dual_model_settings_workspace import DUAL_MODEL_SETTINGS_SCRIPT
from app.ui.multi_provider_settings_workspace import MULTI_PROVIDER_SETTINGS_SCRIPT
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.settings_tab_workspace import SETTINGS_TAB_WORKSPACE_SCRIPT


def test_test188_settings_tabs_preserve_existing_fieldset_mount_ids():
    script = SETTINGS_TAB_WORKSPACE_SCRIPT

    assert "const existingPanelId = fieldset.id.trim();" in script
    assert "const panelId = existingPanelId || `guided-settings-panel-${index}`;" in script
    assert "tab.setAttribute('aria-controls', panelId);" in script
    assert "fieldset.id = panelId;" in script
    assert "fieldset.id = `guided-settings-panel-${index}`;" not in script


def test_test188_provider_mount_survives_for_multi_and_dual_model_installers():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert 'id="provider"' in html
    assert "const providerFieldset = byId('provider');" in MULTI_PROVIDER_SETTINGS_SCRIPT
    assert "const providerFieldset = byId('provider');" in DUAL_MODEL_SETTINGS_SCRIPT
    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html

    assert html.index("installSharedSettingsTabs();") < html.index("installMultiProviderSettings();")
    assert html.index("installMultiProviderSettings();") < html.index("installDualModelSettings();")


def test_test188_dual_model_cards_remain_visible_contract():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html
    assert "savePrimary.id = 'dual-primary-save'" in html
    assert "saveVision.id = 'dual-vision-save'" in html
    assert "testVision.id = 'dual-vision-test'" in html
    assert "follow.id = 'dual-vision-follow-primary'" in html
