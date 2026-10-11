"""Full composed UI acceptance; no production or paid model requests."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, expect
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML

OUT = Path(os.environ.get('BROWSER_OUTPUT', '/tmp/test211-browser'))
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (390, 1440):
        page = browser.new_page(viewport={'width': width, 'height': 900}, reduced_motion='reduce' if width == 390 else 'no-preference')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        people = [{'id': 'p1', 'name': '小林', 'nickname': '林'}, {'id': 'p2', 'name': '小唐'}]

        def handle(route):
            path = urlparse(route.request.url).path
            if path == '/app':
                route.fulfill(content_type='text/html', body=PRODUCT_SHELL_WITH_CONTENT_HTML)
                return
            result = []
            if path.endswith('/auth/login') or path.endswith('/auth/register'):
                result = {'access_token': 'mock-session', 'expires_at': '2030-01-01T00:00:00Z'}
            elif path == '/api/v1/persons':
                if route.request.method == 'POST':
                    result = {'id': 'p3', **route.request.post_data_json}
                    people.append(result)
                else:
                    result = people
            elif path in ('/api/v1/persons/p1', '/api/v1/persons/p2', '/api/v1/persons/p3'):
                result = next(x for x in people if path.endswith(x['id']))
            elif path.endswith('/memory'):
                result = {'summary': {}, 'processed_count': 0, 'total_count': 0}
            elif path.endswith('/settings/llm'):
                result = {'provider': 'qwen', 'model': 'mock', 'configured': False}
            route.fulfill(content_type='application/json', body=json.dumps(result))

        page.route('**/*', handle)
        page.goto('http://chat.test/app')
        expect(page.locator('#client-auth-screen')).to_be_visible()
        expect(page.locator('#client-person-stage')).not_to_be_visible()
        page.screenshot(path=str(OUT / f'auth-{width}.png'), full_page=True)
        page.locator('#username').fill('demo')
        page.locator('#password').fill('mock-password')
        page.locator('#login').click()
        expect(page.locator('#client-person-deck [data-person-id="p1"]')).to_be_visible()
        expect(page.locator('body')).to_have_attribute('data-client-view', 'people')
        expect(page.locator('#client-conversation-stage')).not_to_be_visible()
        expect(page.locator('#person-memory-panel')).not_to_be_visible()
        page.screenshot(path=str(OUT / f'people-{width}.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        card=page.locator('#client-person-deck [data-person-id="p1"]')
        assert card.evaluate("e=>getComputedStyle(e,'::after').content") == 'none'
        if width == 1440:
            card.locator('.client-card-front').hover()
            page.wait_for_timeout(400)
            assert card.evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).a') > 1.04
            page.screenshot(path=str(OUT / 'hover-desktop.png'), full_page=True)
        else:
            assert card.evaluate('e=>getComputedStyle(e).animationName') == 'none'
        page.locator('#client-person-deck [data-person-id="p1"] .client-card-front').click()
        if width == 1440 and page.locator('body').get_attribute('data-client-view') == 'people':
            expect(card).to_have_class(__import__('re').compile('is-entering'))
        expect(page.locator('body')).to_have_attribute('data-client-view', 'person')
        expect(page.locator('#client-conversation-stage')).to_be_visible()
        expect(page.locator('#person-memory-panel')).to_be_visible()
        page.get_by_role('button', name='人物资料与关系', exact=True).click()
        expect(page.locator('#client-person-deck [data-person-id="p1"] .client-card-back')).to_be_visible()
        page.screenshot(path=str(OUT / f'person-{width}.png'), full_page=True)
        page.locator('#client-back-people').click()
        expect(page.locator('body')).to_have_attribute('data-client-view', 'people')
        page.locator('#guided-settings > summary').click()
        expect(page.locator('#guided-settings-content')).to_be_visible()
        expect(page.get_by_role('tab', name='账号登录', exact=True)).to_have_count(0)
        page.get_by_role('tab', name='模型设置', exact=True).click()
        expect(page.locator('#provider')).to_be_visible()
        page.get_by_role('tab', name='模型设置', exact=True).press('Home')
        expect(page.get_by_role('tab', name='登录会话', exact=True)).to_have_attribute('aria-selected', 'true')
        page.get_by_role('tab', name='账号安全', exact=True).click()
        page.screenshot(path=str(OUT / f'settings-{width}.png'), full_page=True)
        page.locator('#guided-settings > summary').click()
        page.locator('.client-new-card .client-card-front').click()
        page.locator('.client-new-card input').first.fill('新人物')
        page.get_by_role('button', name='创建人物卡', exact=True).click()
        expect(page.locator('body')).to_have_attribute('data-client-view', 'person')
        expect(page.locator('#client-workbar h2')).to_have_text('新人物')
        page.locator('#client-back-people').click()
        expect(page.locator('#client-person-deck [data-person-id="p3"]')).to_be_visible()
        page.locator('#logout').click()
        expect(page.locator('#client-auth-screen')).to_be_visible()
        page.go_back()
        expect(page.locator('#client-person-stage')).not_to_be_visible()
        assert not errors, errors
        page.close()
    browser.close()
print('TEST-213 hover, no projection, flip/zoom and workspace transitions; full-page login, cards, flip navigation, profile, settings, logout and mobile: PASS')

