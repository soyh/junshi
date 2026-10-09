from app.ui.china_time import CHINA_TIME_SCRIPT
"""Exercise the real reply renderer's coverage notice on desktop and mobile."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.ui.strategic_reply_workspace import STRATEGIC_REPLY_HTML, STRATEGIC_REPLY_SCRIPT

out = Path(os.environ.get('BROWSER_OUTPUT', '/tmp'))
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (390, 1280):
        page = browser.new_page(viewport={'width': width, 'height': 844})
        page.set_content('<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<style>body{font:16px sans-serif;margin:12px}fieldset{min-width:0}'
            'textarea{max-width:100%}.session-row{overflow-wrap:anywhere}</style>' + STRATEGIC_REPLY_HTML)
        page.add_script_tag(content=CHINA_TIME_SCRIPT + 'const byId=id=>document.getElementById(id);' +
            STRATEGIC_REPLY_SCRIPT.split('  async function loadStrategicReply()')[0])
        notice = '[历史窗口] 分析阶段使用 8/150 条聊天；原始记录未删除。<img src=x onerror="window.injected=true">'
        page.evaluate('data => renderStrategicReply(data)', {
            'draft': '今晚一起吃饭吧', 'structured_analysis': {'summary': '近期邀约',
            'analysis_constraints': [notice]}, 'recommendations': [], 'evidence': [],
        })
        assert notice in page.locator('#strategic-reply-context').inner_text()
        assert page.locator('#strategic-reply-context img').count() == 0
        assert not page.evaluate('Boolean(window.injected)')
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.locator('#strategic-reply-context').screenshot(path=str(out / f'test204-history-{width}.png'))
        page.evaluate('renderStrategicReply({structured_analysis: {summary:"short"}})')
        assert '[历史窗口]' not in page.locator('#strategic-reply-context').inner_text()
        page.close()
    browser.close()
print('TEST-204 browser coverage notice: PASS')
