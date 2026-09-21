from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.ui.single_open_interaction_workspace import (
    SINGLE_OPEN_INTERACTION_SCRIPT,
    SINGLE_OPEN_INTERACTION_STYLE,
)


def test_app_includes_test173_interaction_layer(client):
    html = client.get('/app').text

    assert 'test173-single-open-surfaces' in html
    assert 'singleOpenCloseDetails' in html
    assert 'singleOpenClosePersonCards' in html
    assert 'button:not(:disabled):hover' in html
    assert 'details > summary:hover' in html


def test_all_action_buttons_receive_visible_hover_and_keyboard_focus_feedback():
    assert 'button:not(:disabled):hover' in SINGLE_OPEN_INTERACTION_STYLE
    assert 'details > summary:hover' in SINGLE_OPEN_INTERACTION_STYLE
    assert '.client-card-front:hover' in SINGLE_OPEN_INTERACTION_STYLE
    assert 'button:focus-visible' in SINGLE_OPEN_INTERACTION_STYLE
    assert 'details > summary:focus-visible' in SINGLE_OPEN_INTERACTION_STYLE
    assert '.client-card-front:focus-visible' in SINGLE_OPEN_INTERACTION_STYLE
    assert 'button:disabled' in SINGLE_OPEN_INTERACTION_STYLE
    assert 'cursor: not-allowed' in SINGLE_OPEN_INTERACTION_STYLE


def test_opening_a_second_details_surface_closes_the_previous_surface():
    for marker in (
        "document.querySelectorAll('details[open]')",
        'if (details !== activeDetails) details.open = false;',
        "event.target.closest('summary')",
        'singleOpenActivateDetails(details);',
        "document.addEventListener('toggle'",
        'if (!(details instanceof HTMLDetailsElement) || !details.open) return;',
    ):
        assert marker in SINGLE_OPEN_INTERACTION_SCRIPT


def test_opening_person_card_closes_previous_expanded_panel_and_card():
    for marker in (
        "document.querySelectorAll('.client-person-card.is-flipped')",
        "if (card !== activeCard) card.classList.remove('is-flipped');",
        "event.target.closest('.client-card-front')",
        "cardFront.closest('.client-person-card')",
        'singleOpenActivatePersonCard(card);',
        'singleOpenCloseDetails();',
    ):
        assert marker in SINGLE_OPEN_INTERACTION_SCRIPT


def test_settings_keep_native_click_to_toggle_while_joining_single_open_contract():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert 'id="guided-settings"' in html
    assert '<summary>账号、安全与模型设置</summary>' in html
    assert 'guided-settings-content' in html
    assert "event.preventDefault()" not in SINGLE_OPEN_INTERACTION_SCRIPT
    assert "details.open = true" not in SINGLE_OPEN_INTERACTION_SCRIPT


def test_interaction_layer_is_presentation_only_and_has_no_business_io():
    lowered = SINGLE_OPEN_INTERACTION_SCRIPT.lower()

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
