"""Standalone TEST-202 browser acceptance for phone-sized settings pages."""
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


PHONE = {"width": 390, "height": 844}
ARTIFACT_DIR = Path("/tmp")


def assert_no_horizontal_overflow(page):
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
    )


def assert_inside(node, container, tolerance=2):
    box = node.bounding_box()
    host = container.bounding_box()
    assert box is not None and host is not None
    assert box["x"] >= host["x"] - tolerance
    assert box["x"] + box["width"] <= host["x"] + host["width"] + tolerance


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport=PHONE)

    page.route(
        "http://settings.test/",
        lambda route: route.fulfill(
            status=200,
            content_type="text/html; charset=utf-8",
            body=PRODUCT_SHELL_WITH_CONTENT_HTML,
        ),
    )
    page.goto("http://settings.test/", wait_until="domcontentloaded")
    page.wait_for_function(
        "document.querySelectorAll('#guided-settings-tabs .settings-tab-button').length === 4"
    )

    page.evaluate("document.querySelector('#guided-settings').open = true")
    page.locator("#guided-settings-content").wait_for(state="visible")

    tabs = page.locator("#guided-settings-tabs")
    panel_host = page.locator("#guided-settings-panel-host")
    assert tabs.locator(".settings-tab-button").count() == 4
    assert page.evaluate(
        "document.querySelector('#guided-settings-tabs').scrollWidth <= "
        "document.querySelector('#guided-settings-tabs').clientWidth + 1"
    )
    assert page.evaluate(
        "getComputedStyle(document.querySelector('#guided-settings-tabs')).gridTemplateColumns"
        ".trim().split(/\\s+/).length === 2"
    )
    assert panel_host.evaluate("el => getComputedStyle(el).overflowY") == "auto"
    assert_no_horizontal_overflow(page)

    account_tab = tabs.get_by_role("tab", name="账号安全")
    account_tab.click()
    assert account_tab.get_attribute("aria-selected") == "true"
    account_style = account_tab.evaluate(
        "el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundImage})"
    )
    assert account_style["color"] == "rgb(255, 255, 255)"
    assert account_style["background"] != "none"

    account = page.locator("#account-security")
    assert account.is_visible()
    cards = account.locator(".workspace-card")
    assert cards.count() == 2
    first_card = cards.first
    second_card = cards.nth(1)
    first_box = first_card.bounding_box()
    second_box = second_card.bounding_box()
    assert first_box is not None and second_box is not None
    assert second_box["y"] >= first_box["y"] + first_box["height"] - 2
    for selector in ("input", "select", "button"):
        for i in range(account.locator(selector).count()):
            assert_inside(account.locator(selector).nth(i), panel_host)
    assert_no_horizontal_overflow(page)
    page.screenshot(path=str(ARTIFACT_DIR / "test202-account-security-mobile.png"), full_page=True)

    model_tab = tabs.get_by_role("tab", name="模型设置")
    model_tab.click()
    assert model_tab.get_attribute("aria-selected") == "true"
    assert page.locator("#provider").is_visible()
    page.wait_for_function("document.querySelectorAll('#dual-model-settings .dual-model-card').length === 2")

    model_grid = page.locator("#dual-model-settings")
    model_cards = model_grid.locator(".dual-model-card")
    first_model = model_cards.first.bounding_box()
    second_model = model_cards.nth(1).bounding_box()
    assert first_model is not None and second_model is not None
    assert second_model["y"] >= first_model["y"] + first_model["height"] - 2

    for i in range(model_grid.locator(".dual-model-fields").count()):
        fields = model_grid.locator(".dual-model-fields").nth(i)
        assert fields.evaluate(
            "el => getComputedStyle(el).gridTemplateColumns.trim().split(/\\s+/).length === 1"
        )
    for i in range(model_grid.locator(".dual-model-actions button").count()):
        button = model_grid.locator(".dual-model-actions button").nth(i)
        assert_inside(button, panel_host)
        assert button.bounding_box()["height"] >= 43

    last_action = model_grid.locator(".dual-model-actions button").last
    initial_scroll_top = panel_host.evaluate("el => el.scrollTop")
    last_action.scroll_into_view_if_needed()
    page.wait_for_timeout(100)
    final_scroll_top = panel_host.evaluate("el => el.scrollTop")
    assert final_scroll_top >= initial_scroll_top
    assert_inside(last_action, panel_host)
    last_box = last_action.bounding_box()
    host_box = panel_host.bounding_box()
    assert last_box is not None and host_box is not None
    assert last_box["y"] >= host_box["y"] - 3
    assert last_box["y"] + last_box["height"] <= host_box["y"] + host_box["height"] + 3

    assert_no_horizontal_overflow(page)
    page.screenshot(path=str(ARTIFACT_DIR / "test202-model-settings-mobile.png"), full_page=True)

    browser.close()

print("TEST-202 mobile Account Security and Model Settings browser acceptance: PASS")
