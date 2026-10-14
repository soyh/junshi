"""Email registration and audited admin UI on mobile and desktop, with fake mail/API."""
import json
import os
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML

with sync_playwright() as p:
    browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (390,1280):
        page=browser.new_page(viewport={'width':width,'height':850})
        errors=[];calls=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        def handle(route):
            path=urlparse(route.request.url).path
            if path=='/app':return route.fulfill(content_type='text/html',body=PRODUCT_SHELL_WITH_CONTENT_HTML)
            body=route.request.post_data_json if route.request.post_data else None
            calls.append((path,body))
            data=[]
            if path.endswith('/email/policy'):data={'email_registration_required':True,'mail_available':True}
            elif path.endswith('/email/code'):data={'challenge_id':'a'*36,'message':'已发送测试验证码'}
            elif path.endswith('/email/register'):
                assert body['email']=='a@example.com' and body['code']=='123456'
                data={'access_token':'test-session','expires_at':'2030-01-01T00:00:00Z'}
            elif path.endswith('/email/identity'):data={'email':'a@example.com','administrator':1}
            elif '/data/messages' in path:
                assert 'reason=' in route.request.url
                assert route.request.headers.get('authorization')=='Bearer test-session'
                data=[{'content':'<img src=x onerror="window.attacked=1">'}]
            elif path.endswith('/settings/llm'):data={'configured':False}
            return route.fulfill(content_type='application/json',body=json.dumps(data))
        page.route('**/*',handle);page.goto('http://chat.test/app')
        page.locator('#username').fill('email_user');page.locator('#password').fill('password-12345')
        page.locator('#register').click();expect(page.locator('#email-account-center')).to_be_visible()
        page.locator('#email-address').fill('a@example.com');page.locator('#email-send-code').click()
        expect(page.locator('#email-center-status')).to_contain_text('已发送测试验证码')
        page.locator('#email-code').fill('123456');page.locator('#email-submit').click()
        expect(page.locator('#email-center-status')).to_contain_text('操作完成')
        page.locator('#email-center-close').click()
        page.locator('#client-footer').get_by_text('邮箱与账号管理',exact=True).click()
        expect(page.locator('#email-admin-panel')).to_be_visible()
        page.locator('#email-admin-target').fill('target-user');page.locator('#email-admin-reason').fill('用户请求排查')
        page.locator('#email-admin-kind').select_option('messages');page.locator('#email-admin-view').click()
        expect(page.locator('#email-admin-result')).to_contain_text('window.attacked')
        assert page.evaluate('window.attacked === undefined')
        assert page.evaluate('localStorage.length===0 && sessionStorage.length===0')
        assert not any(path.endswith('/auth/register') for path,_ in calls)
        assert not errors,errors
        page.close()
    browser.close()
print('TEST-228 email registration and admin UI: PASS')
