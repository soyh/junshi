from app.ui.dual_model_settings_workspace import (
    DUAL_MODEL_SETTINGS_SCRIPT,
    DUAL_MODEL_SETTINGS_STYLE,
)
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.settings_tab_workspace import SETTINGS_TAB_WORKSPACE_STYLE


def test_test189_settings_workspace_expands_across_guided_hero():
    style = SETTINGS_TAB_WORKSPACE_STYLE

    assert "#guided-settings[open]" in style
    assert "grid-column: 1 / -1;" in style
    assert "max-height: min(70vh, 760px);" in style
    assert "grid-template-columns: repeat(2, minmax(150px, 1fr));" in style


def test_test189_dual_model_cards_have_clear_roles_and_independent_fields():
    script = DUAL_MODEL_SETTINGS_SCRIPT

    assert "文本推理与视觉理解独立配置" in script
    assert "TEXT · 主路由" in script
    assert "VISION · 多模态" in script
    assert "主文本 / 分析模型" in script
    assert "视觉 / 图片视频模型" in script

    assert "dualMakeInput(role, 'provider', '模型服务')" in script
    assert "dualMakeInput(role, 'model', '模型名称')" in script
    assert "dualMakeInput(role, 'baseUrl', '接口地址（Base URL）')" in script
    assert "dualMakeInput(role, 'apiKey', 'API Key', 'password')" in script
    assert "dualMakeInput(role, 'timeout', '超时时间（秒）', 'number')" in script

    assert "savePrimary.id = 'dual-primary-save'" in script
    assert "testPrimary.id = 'dual-primary-test'" in script
    assert "saveVision.id = 'dual-vision-save'" in script
    assert "testVision.id = 'dual-vision-test'" in script
    assert "follow.id = 'dual-vision-follow-primary'" in script


def test_test189_dual_model_role_state_is_visible_and_runtime_driven():
    script = DUAL_MODEL_SETTINGS_SCRIPT

    assert "state: `dual-${role}-state`" in script
    assert "function dualSetRoleState(role, text, state = 'empty')" in script
    assert "active ? '当前生效' : '未配置'" in script
    assert "vision ? '独立视觉' : active ? '跟随主模型' : '未配置'" in script
    assert "roleState.textContent = '等待登录'" in script


def test_test189_visual_style_matches_existing_sky_blue_product_language():
    style = DUAL_MODEL_SETTINGS_STYLE

    assert "var(--sky-500, #19a7e8)" in style
    assert "var(--sky-950, #08233d)" in style
    assert "linear-gradient(145deg" in style
    assert "dual-model-card" in style
    assert "dual-model-role-state" in style
    assert "dual-model-fields" in style
    assert "@media (max-width: 980px)" in style
    assert "@media (max-width: 620px)" in style


def test_test189_composed_product_shell_keeps_mount_fix_and_new_ui():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert 'id="provider"' in html
    assert "const existingPanelId = fieldset.id.trim();" in html
    assert "installSharedSettingsTabs();" in html
    assert "installMultiProviderSettings();" in html
    assert "installDualModelSettings();" in html
    assert html.index("installSharedSettingsTabs();") < html.index("installMultiProviderSettings();")
    assert html.index("installMultiProviderSettings();") < html.index("installDualModelSettings();")

    assert "文本推理与视觉理解独立配置" in html
    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html
    assert "高级：Profile 管理、角色切换与兼容设置" in html
