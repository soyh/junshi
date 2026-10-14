import json
import os
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, expect
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (1440, 390):
        page = browser.new_page(viewport={'width': width, 'height': 950}, reduced_motion='reduce')
        errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
        accounts = []
        person = {'id': 'p1', 'name': 'Synthetic person'}
        def handle(route):
            path = urlparse(route.request.url).path
            if path == '/app': return route.fulfill(content_type='text/html', body=PRODUCT_SHELL_WITH_CONTENT_HTML)
            result = []
            if path.endswith('/auth/login'): result = {'access_token': 'synthetic-session', 'expires_at': '2030-01-01T00:00:00Z'}
            elif path == '/api/v1/persons': result = [person]
            elif path == '/api/v1/persons/p1': result = person
            elif path.endswith('/platform-accounts'):
                if route.request.method == 'POST': accounts.append({'id': str(len(accounts)+1), **route.request.post_data_json})
                result = accounts if route.request.method == 'GET' else accounts[-1]
            elif path.endswith('/memory'): result = {'summary': {}, 'processed_count': 0, 'total_count': 0}
            elif path.endswith('/settings/llm'): result = {'provider': 'qwen', 'model': 'mock', 'configured': False}
            route.fulfill(content_type='application/json', body=json.dumps(result))
        page.route('**/*', handle)
        page.goto('http://chat.test/app')
        page.locator('#username').fill('synthetic'); page.locator('#password').fill('synthetic-password')
        page.locator('#login').click()
        if width == 1440:
            expect(page.locator('body')).to_have_attribute('data-client-view','people')
            assert page.locator('#pc-transfer').evaluate('(el)=>getComputedStyle(el).backgroundColor') == 'rgba(0, 0, 0, 0)'
            assert page.locator('#pc-transfer > summary').evaluate('(el)=>getComputedStyle(el).fontSize') == page.locator('#guided-settings > summary').evaluate('(el)=>getComputedStyle(el).fontSize')
            page.locator('#pc-transfer > summary').click()
            expect(page.locator('#pc-transfer-password')).to_be_visible()
            expect(page.locator('#pc-export')).to_be_visible()
            expect(page.locator('#pc-import')).to_be_visible()
            assert page.locator('#pc-transfer').evaluate('(el)=>getComputedStyle(el).color') == 'rgb(25, 50, 73)'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            page.locator('#pc-transfer > summary').click()
        page.locator('[data-person-id="p1"] .client-card-front').click()
        expect(page.locator('body')).to_have_attribute('data-client-view', 'person')
        if width == 1440:
            page.locator('#pc-platform-panel > summary').click()
            page.locator('#pc-handle').fill('synthetic-wechat')
            page.locator('#pc-display').fill('<script>synthetic</script>')
            page.locator('#pc-add-account').click()
            expect(page.locator('#pc-account-list')).to_contain_text('synthetic-wechat')
            page.locator('#pc-platform').select_option('douyin')
            page.locator('#pc-handle').fill('synthetic-douyin')
            page.locator('#pc-add-account').click()
            expect(page.locator('#pc-account-list li')).to_have_count(2)
            assert page.locator('#pc-account-list script').count() == 0
            expect(page.locator('#pc-transfer')).to_be_visible()
        else:
            expect(page.locator('#pc-platform-panel')).not_to_be_visible()
            expect(page.locator('#pc-transfer')).not_to_be_visible()
        assert not errors, errors
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        page.close()
    browser.close()
print('PC multi-account binding, escaped labels, transfer entry and unchanged mobile surface: PASS')
