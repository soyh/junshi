import os
from playwright.sync_api import sync_playwright
from app.ui.china_time import CHINA_TIME_SCRIPT

with sync_playwright() as p:
    browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for zone in ['Asia/Shanghai','America/New_York']:
        page=browser.new_page(timezone_id=zone,locale='en-US')
        page.add_script_tag(content=CHINA_TIME_SCRIPT)
        assert page.evaluate("chinaTimeText('2026-09-26T20:00:00Z')") == '2026年09月27日 04:00:00（北京时间）'
        assert page.evaluate("chinaTimeText('2026-09-26T16:00:00Z')") == '2026年09月27日 00:00:00（北京时间）'
        assert page.evaluate("chinaTimeIso('2026年09月26日 20:00:00')") == '2026-09-26T20:00:00+08:00'
        assert page.evaluate("chinaTimeText('2026-09-26T10:40:00+08:00','minute')") == '2026年09月26日 10:40（北京时间）'
        for value in ['2026年02月30日 20:00:00','2026年09月26日 24:00:00']:
            assert page.evaluate("v=>{try{chinaTimeIso(v);return false}catch(e){return true}}",value)
        page.close()
    browser.close()
print('TEST-205 China time across browser timezones: PASS')
