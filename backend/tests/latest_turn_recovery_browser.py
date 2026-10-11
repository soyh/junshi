"""The real recovery observer must not restart an exhausted paid pipeline."""
import os
from playwright.sync_api import sync_playwright
from app.ui.card_client_generation_recovery import CARD_CLIENT_GENERATION_RECOVERY_SCRIPT

script = CARD_CLIENT_GENERATION_RECOVERY_SCRIPT.split('  function clientInstallAutomaticReplyRecovery()')[1]
script = 'function clientInstallAutomaticReplyRecovery()' + script.split("  byId('conversation-select')")[0]
with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (390, 1280):
        page = browser.new_page(viewport={'width': width, 'height': 844})
        page.set_content('<div id="client-automation-status"></div>')
        page.add_script_tag(content='''
          const byId=id=>document.getElementById(id);
          let selectedConversationId='c1', selectedPersonId='p1', currentAccessToken='t1';
          let clientReplyRecoveryBusy=false, clientAutoReplyRecoveryKey='', strategicReplyRevision=0;
          window.attempts=0;
          function clientRunReplyRecovery(){window.attempts++}
        ''' + script + 'clientInstallAutomaticReplyRecovery();')
        page.evaluate("byId('client-automation-status').textContent='自动跟进未完全完成：分析阶段未形成基于最新消息的建议；已自动纠正一次，仍未通过校验。'")
        page.wait_for_timeout(650)
        assert page.evaluate('attempts') == 0
        page.evaluate("byId('client-automation-status').textContent='自动跟进未完全完成：网络失败'")
        page.wait_for_function('attempts===1')
        page.evaluate("byId('client-automation-status').textContent='自动跟进未完全完成：网络失败'")
        page.wait_for_timeout(650)
        assert page.evaluate('attempts') == 1
        page.close()
    browser.close()
print('TEST-206 exhausted freshness recovery and existing one-shot retry: PASS')
