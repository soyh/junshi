from app.ui.china_time import CHINA_TIME_SCRIPT
"""Real renderer and lifecycle functions, deterministic out-of-order responses."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.ui.strategic_reply_workspace import STRATEGIC_REPLY_HTML, STRATEGIC_REPLY_SCRIPT
from app.ui.lifecycle_v2_workspace import LIFECYCLE_V2_SCRIPT

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (390,1280):
        page = browser.new_page(viewport={'width':width,'height':844})
        page.set_content(STRATEGIC_REPLY_HTML + '<select id="conversation-select"></select><select id="person-select"></select><div id="automation"></div>')
        page.add_script_tag(content=CHINA_TIME_SCRIPT + '''
            const byId=id=>document.getElementById(id);
            let selectedConversationId='c1', selectedPersonId='p1', currentAccessToken='t1';
            function bind() {}
            function resetWorkspace() {}
            window.requests=[];window.results=[];
            // Real page installs the lifecycle listener BEFORE the reply fragment.
            window.addEventListener('junshi:evidence-changed',()=>{
              if(typeof lifecycleAfterEvidenceChanged==='function') lifecycleAfterEvidenceChanged('消息');
            });
            function api(url) {return new Promise((resolve,reject)=>requests.push({url,resolve,reject}));}
            function launch() { loadStrategicReply().then(()=>results.push('ok')).catch(e=>results.push(e.superseded?'stale':'error')); }
        ''' + STRATEGIC_REPLY_SCRIPT)
        page.evaluate('launch()')
        page.evaluate('resetStrategicReply()')
        page.evaluate('launch()')
        page.evaluate("requests[1].resolve({draft:'最新建议'})")
        page.wait_for_function("document.getElementById('strategic-reply-draft').value==='最新建议'")
        page.evaluate("requests[0].resolve({draft:'旧建议'})")
        page.wait_for_function("results.includes('stale')")
        assert page.locator('#strategic-reply-draft').input_value() == '最新建议'
        page.evaluate("launch(); selectedConversationId='c2'; requests[2].resolve({draft:'跨会话旧建议'})")
        page.wait_for_function("results.length===3")
        assert page.locator('#strategic-reply-draft').input_value() == ''
        page.evaluate("launch(); requests[3].resolve({draft:'  '})")
        page.wait_for_function("results.length===4")
        assert page.evaluate('results[3]') == 'error'
        assert page.locator('#strategic-reply-draft').input_value() == ''

        lifecycle = LIFECYCLE_V2_SCRIPT.split('  let lifecyclePendingEvidence = null;')[1].split('  async function lifecycleAfterDecisionRecorded')[0]
        page.add_script_tag(content='''
            let lifecycleAutomationBusy=false;
            const lifecycleAutomationStatus=byId('automation');
            async function generateActionPlan() {}
            async function loadSavedActionPlan() {}
            async function loadActionDecisionContext() {}
            let lifecyclePendingEvidence=null;
        ''' + lifecycle + '''

        ''')
        page.evaluate("window.dispatchEvent(new CustomEvent('junshi:evidence-changed'))")
        page.wait_for_function('requests.length===5')
        page.evaluate("window.dispatchEvent(new CustomEvent('junshi:evidence-changed')); window.dispatchEvent(new CustomEvent('junshi:evidence-changed'))")
        page.evaluate("requests[4].resolve({draft:'新增消息前的旧建议'})")
        page.wait_for_function('requests.length===6')
        assert page.locator('#strategic-reply-draft').input_value() == ''
        page.evaluate("requests[5].resolve({draft:'你呢？',reply_inputs:{conversation_focus:{reply_target_message:{content:'你在干嘛呐',sent_at:'2026-09-26T20:00:00+00:00'}}}})")
        page.wait_for_function("document.getElementById('strategic-reply-draft').value==='你呢？'")
        assert '你在干嘛呐' in page.locator('#strategic-reply-context').inner_text()
        assert page.evaluate('requests.length') == 6
        page.close()
    browser.close()
print('TEST-205 reply ordering, blank rejection, scope and pending evidence: PASS')
