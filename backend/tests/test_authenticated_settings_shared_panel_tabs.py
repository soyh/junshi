from app.ui.settings_tab_workspace import (
    SETTINGS_TAB_WORKSPACE_SCRIPT,
    SETTINGS_TAB_WORKSPACE_STYLE,
)


def test_app_includes_shared_settings_tab_workspace(client):
    html = client.get('/app').text

    for marker in (
        'guided-settings-tabs',
        'guided-settings-panel-host',
        'settings-tab-button',
        'installSharedSettingsTabs',
    ):
        assert marker in html


def test_settings_menu_is_one_horizontal_row_with_one_shared_content_host():
    for marker in (
        'grid-template-columns: repeat(4, minmax(150px, 1fr))',
        "tabs.id = 'guided-settings-tabs'",
        "panelHost.id = 'guided-settings-panel-host'",
        "settings.replaceChildren(tabs, panelHost);",
    ):
        assert marker in SETTINGS_TAB_WORKSPACE_STYLE + SETTINGS_TAB_WORKSPACE_SCRIPT


def test_each_settings_fieldset_moves_into_same_shared_panel_host():
    for marker in (
        "const fieldset = details.querySelector(':scope > fieldset');",
        'panelHost.appendChild(fieldset);',
        'details.remove();',
        'entry.fieldset.hidden = !active;',
    ):
        assert marker in SETTINGS_TAB_WORKSPACE_SCRIPT


def test_clicking_tab_switches_visible_panel_without_collapsing_outer_settings():
    assert "entry.tab.addEventListener('click', () => activate(index));" in SETTINGS_TAB_WORKSPACE_SCRIPT
    assert "entry.tab.setAttribute('aria-selected', active ? 'true' : 'false');" in SETTINGS_TAB_WORKSPACE_SCRIPT
    assert '.open = false' not in SETTINGS_TAB_WORKSPACE_SCRIPT
    assert "byId('guided-settings').open" not in SETTINGS_TAB_WORKSPACE_SCRIPT


def test_settings_panels_use_full_width_shared_area():
    for marker in (
        '#guided-settings-panel-host {',
        'width: 100%;',
        '#guided-settings-panel-host > fieldset {',
        'max-width: none !important;',
    ):
        assert marker in SETTINGS_TAB_WORKSPACE_STYLE


def test_keyboard_tab_navigation_is_supported():
    for marker in (
        "['ArrowLeft', 'ArrowRight', 'Home', 'End']",
        "event.key === 'ArrowLeft'",
        "event.key === 'ArrowRight'",
        "event.key === 'Home'",
        "event.key === 'End'",
        'entries[next].tab.focus();',
    ):
        assert marker in SETTINGS_TAB_WORKSPACE_SCRIPT


def test_shared_settings_tab_layer_is_presentation_only():
    lowered = SETTINGS_TAB_WORKSPACE_SCRIPT.lower()

    for forbidden in (
        'fetch(',
        'api(',
        'xmlhttprequest',
        "method: 'post'",
        "method: 'patch'",
        "method: 'delete'",
        'localstorage',
        'sessionstorage',
    ):
        assert forbidden not in lowered
