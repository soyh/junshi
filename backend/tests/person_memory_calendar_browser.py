"""Real UI fragments: calendars, persistent help, audit escaping and tenant scope."""
import os
from playwright.sync_api import sync_playwright
from app.ui.china_time import CHINA_TIME_SCRIPT
from app.ui.china_calendar import CHINA_CALENDAR_SCRIPT
from app.ui.person_memory import PERSON_MEMORY_SCRIPT

with sync_playwright() as p:
    browser=p.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
    for width in (390,1280):
        page=browser.new_page(viewport={'width':width,'height':844},timezone_id='America/New_York')
        page.set_content('<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<input id="message-sent-at"><input id="client-media-sent-at">'
            '<select id="person-select"><option value="p1">甲</option><option value="p2">乙</option></select>'
            '<section id="client-person-stage"></section>')
        page.add_script_tag(content='const byId=id=>document.getElementById(id);'+CHINA_TIME_SCRIPT+CHINA_CALENDAR_SCRIPT)
        assert '年' in page.locator('#message-sent-at').input_value()
        assert page.get_by_text('北京时间 · 24小时制',exact=False).count()==2
        page.locator('details').first.locator('summary').click()
        page.get_by_label('北京时间日期').first.fill('2026-09-26')
        page.get_by_label('小时（24小时制）').first.select_option('20')
        page.get_by_label('分钟',exact=True).first.select_option('05')
        page.get_by_label('秒',exact=True).first.select_option('06')
        assert page.locator('#message-sent-at').input_value()=='2026年09月26日 20:05:06'
        assert page.evaluate("chinaTimeIso(byId('message-sent-at').value)")=='2026-09-26T20:05:06+08:00'
        page.locator('#message-sent-at').fill('2026年09月27日 10:00:00')
        assert page.get_by_text('北京时间 · 24小时制',exact=False).first.is_visible()
        page.add_script_tag(content='''
          let selectedPersonId='p1',selectedConversationId='c1',currentAccessToken='test';
          function clearSession(){}
          window.paths=[];
          async function api(path){paths.push(path);
            if(path.includes('/memory/profile'))return {items:[{id:'entry',kind:'constraints',text:'本周不见面，下周待确认。',active:true,legacy:true,evidence:[]}],total:1,has_more:false};
            return {summary:{description:'内部摘要'},covered_count:1,total_count:1,
            context_budget_bytes:4096,context_bytes:600,omitted_entry_count:2,
            stale:false,running:false,has_more:false,events:[{created_at:'2026-09-26T20:00:00Z',source:'ai',outcome:'updated',
            reason:'<img src=x onerror="window.injected=true">证据支持状态变化',before:{relationship:{status:'unknown'}},
            after:{relationship:{status:'互动积极'},summary:{description:'新摘要'}}}]};}
        '''+PERSON_MEMORY_SCRIPT)
        page.locator('#person-select').dispatch_event('change')
        page.wait_for_function('paths.length===1')
        assert page.get_by_text('已分析 1/1 条聊天。',exact=False).is_visible()
        assert not page.locator('#person-memory-details').evaluate('(e)=>e.open')
        assert page.locator('#person-memory-panel').bounding_box()['height'] < 250
        page.get_by_text('展开档案与更新记录',exact=True).click()
        page.get_by_text('查看完整档案条目与依据',exact=True).click()
        page.get_by_text('约定与边界 · 有效：本周不见面，下周待确认。',exact=True).wait_for()
        page.get_by_text('查看内部人物摘要',exact=True).click()
        assert page.get_by_text('所有人物使用相同预算规则。',exact=False).is_visible()
        assert page.get_by_text('内部摘要',exact=True).is_visible()
        page.get_by_text('2026年09月27日 04:00:00（北京时间） · AI 分析 · 已更新',exact=True).click()
        assert page.get_by_text('关系状态：unknown → 互动积极',exact=True).is_visible()
        assert page.locator('#person-memory-panel img').count()==0
        assert not page.evaluate('Boolean(window.injected)')
        page.evaluate('memoryLoad()')
        assert page.get_by_text('关系状态：unknown → 互动积极',exact=True).is_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.evaluate("selectedPersonId='p2'")
        page.locator('#person-select').dispatch_event('change')
        page.wait_for_function("paths.some(x=>x.includes('/persons/p2/memory'))")
        page.evaluate('clearSession()')
        assert '本周不见面，下周待确认。' not in page.locator('#person-memory-panel').inner_text()
        page.close()
    browser.close()
print('TEST-207 desktop/mobile calendar and memory audit UI: PASS')
