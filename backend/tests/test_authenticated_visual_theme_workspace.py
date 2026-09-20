from app.ui.visual_theme_workspace import VISUAL_THEME_SCRIPT, VISUAL_THEME_STYLE


def test_product_shell_exposes_sky_blue_technology_theme(client):
    html = client.get("/app").text

    for marker in (
        "--sky-500: #19a7e8",
        "RELATIONSHIP INTELLIGENCE SYSTEM",
        "person-card",
        "person-card-avatar",
        "person-card-signal",
        "人物卡组",
        "列表模式 / 键盘选择",
    ):
        assert marker in html

    assert "radial-gradient" in VISUAL_THEME_STYLE
    assert "backdrop-filter: blur" in VISUAL_THEME_STYLE
    assert "#person-card-deck" in VISUAL_THEME_STYLE


def test_person_card_deck_reuses_canonical_person_select(client):
    html = client.get("/app").text

    assert 'id="person-select"' in html
    assert "const select = byId('person-select')" in VISUAL_THEME_SCRIPT
    assert "select.value = option.value" in VISUAL_THEME_SCRIPT
    assert "select.dispatchEvent(new Event('change', {bubbles: true}))" in VISUAL_THEME_SCRIPT
    assert "visualPersonObserver.observe(visualPersonSelect" in VISUAL_THEME_SCRIPT


def test_visual_layer_does_not_create_a_second_person_api_or_write_path():
    assert "/api/v1/persons" not in VISUAL_THEME_SCRIPT
    assert "method: 'POST'" not in VISUAL_THEME_SCRIPT
    assert "method: 'PATCH'" not in VISUAL_THEME_SCRIPT
    assert "method: 'DELETE'" not in VISUAL_THEME_SCRIPT
    assert "fetch(" not in VISUAL_THEME_SCRIPT
    assert "api(" not in VISUAL_THEME_SCRIPT


def test_visual_layer_preserves_privacy_and_existing_confirmed_boundaries(client):
    html = client.get("/app").text

    for control_id in (
        "create-person",
        "update-selected-person",
        "delete-selected-person",
        "confirm-action-decision",
        "reject-action-decision",
        "record-action-execution",
        "record-action-outcome",
        "persist-action-learning",
    ):
        assert f'id="{control_id}"' in html

    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html


def test_person_cards_are_accessible_buttons_with_selected_state():
    assert "card.type = 'button'" in VISUAL_THEME_SCRIPT
    assert "card.setAttribute('aria-label'" in VISUAL_THEME_SCRIPT
    assert "card.setAttribute('aria-pressed'" in VISUAL_THEME_SCRIPT
    assert "card.disabled = select.disabled" in VISUAL_THEME_SCRIPT
