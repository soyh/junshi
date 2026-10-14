"""Composed page: desktop grant succeeds once; failures leave usable login UI."""
import json
import os
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for valid in (True, False):
        page = browser.new_page()
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def handle(route):
            path = urlparse(route.request.url).path
            requests.append(route.request.url)
            assert 'desktop-login' not in route.request.url
            if path == '/app':
                return route.fulfill(content_type='text/html', body=PRODUCT_SHELL_WITH_CONTENT_HTML)
            result = []
            if path.endswith('/browser-handoff/redeem'):
                assert route.request.post_data_json == {'ticket': 'a' * 43}
                assert 'desktop-login' not in page.url
                return route.fulfill(status=200 if valid else 401, content_type='application/json',
                    body=json.dumps({'access_token': 'browser-session', 'expires_at': '2030-01-01T00:00:00Z'} if valid else {'detail': 'expired'}))
            if path.endswith('/persons'):
                assert route.request.headers.get('authorization') == 'Bearer browser-session'
                result = [{'id': 'p1', 'name': '客户端人物'}]
            if path.endswith('/settings/llm'):
                result = {'configured': False}
            route.fulfill(content_type='application/json', body=json.dumps(result))
        page.route('**/*', handle)
        page.goto('http://chat.test/app#desktop-login=' + 'a' * 43)
        if valid:
            expect(page.locator('#client-person-deck [data-person-id="p1"]')).to_be_visible()
            expect(page.locator('body')).to_have_attribute('data-client-view', 'people')
        else:
            expect(page.locator('#auth-status')).to_contain_text('登录衔接已失效')
            expect(page.locator('#client-auth-screen')).to_be_visible()
        assert page.evaluate('localStorage.length === 0 && sessionStorage.length === 0')
        page.reload()
        expect(page.locator('#client-auth-screen')).to_be_visible()
        assert sum('/browser-handoff/redeem' in x for x in requests) == 1
        assert not errors, errors
        page.close()
    browser.close()
print('TEST-219 browser handoff: PASS')
