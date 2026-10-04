"""Standalone browser acceptance, run explicitly by the UI workflow."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.ui.reference_context_workspace import REFERENCE_CONTEXT_SCRIPT, REFERENCE_CONTEXT_STYLE

items = [dict(id=str(i), name=f'参考文件 {i} 很长的完整文件名.md',
    original_filename=f'original-{i}.md', content_preview='内容摘要', content_chars=5000,
    reference_type='document', enabled_by_default=True, priority=100,
    effective_enabled=True, effective_priority=100) for i in range(25)]
text = '# 完整内容\n' + '正文\n' * 1000 + '<script>window.injected=true</script>'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    requests = []
    def handle(route):
        requests.append((route.request.method, route.request.url, route.request.post_data))
        if route.request.url.endswith('/batch'):
            payload = route.request.post_data_json
            if payload['action'] == 'delete':
                items[:] = [x for x in items if x['id'] not in payload['reference_ids']]
            result = {'updated_count': len(payload['reference_ids'])}
        else:
            result = {'id': '0', 'content': text} if route.request.url.endswith('/content') else items
        route.fulfill(content_type='application/json', body=json.dumps(result))
    page.route('**/api/v1/**', handle)
    page.route('http://reference.test/', lambda route: route.fulfill(body='<html><body></body></html>', content_type='text/html'))
    page.goto('http://reference.test/')
    page.set_content('<style>body{margin:16px}.status{max-height:100px;overflow:hidden}' +
        REFERENCE_CONTEXT_STYLE + '</style><div id="provider"></div>')
    page.add_script_tag(content="const byId=id=>document.getElementById(id); let currentAccessToken='test'; let selectedConversationId='c1'; const requireToken=()=>currentAccessToken;" + REFERENCE_CONTEXT_SCRIPT)
    page.wait_for_function("document.querySelectorAll('.reference-row').length===25")
    assert page.locator('#reference-list').bounding_box()['height'] >= 360
    assert page.locator('.reference-preview').count() == 0
    assert not any(url.endswith('/content') for _, url, _ in requests)
    assert page.locator('.reference-meta-grid:visible').count() == 0
    page.locator('#reference-select-all').click()
    assert page.locator('.reference-select:checked').count() == 25
    page.locator('#reference-select-invert').click()
    assert page.locator('.reference-select:checked').count() == 0
    page.locator('#reference-search').fill('original-0.md')
    page.locator('#reference-select-all').click()
    assert page.locator('.reference-select:checked').count() == 1
    page.locator('#reference-search').fill('original-1.md')
    page.locator('#reference-select-invert').click()
    assert page.locator('.reference-select:checked').count() == 2
    assert '1 项不在当前筛选' in page.locator('#reference-selected-count').text_content()
    page.locator('#reference-batch-disable').click()
    page.wait_for_function("document.querySelector('#reference-status').textContent.includes('已完成 2')")
    payload = json.loads(next(data for method, url, data in requests if url.endswith('/batch')))
    assert set(payload['reference_ids']) == {'0', '1'}
    assert payload['scope'] == 'conversation' and payload['conversation_id'] == 'c1'
    assert page.locator('.reference-select:disabled').count() == 0
    page.locator('#reference-search').fill('')
    page.locator('#reference-type-filter').select_option('skill')
    assert page.locator('.reference-row:visible').count() == 0
    page.locator('#reference-type-filter').select_option('all')
    page.locator('.reference-select').first.check()
    before = len(requests)
    page.once('dialog', lambda dialog: dialog.dismiss())
    page.locator('#reference-batch-delete').click()
    assert len(requests) == before
    page.locator('#reference-select-clear').click()
    page.locator('#reference-search').fill('original-0.md')
    assert page.locator('.reference-row:visible').count() == 1
    page.locator('.reference-reader summary').first.click()
    try:
        page.wait_for_function("document.querySelector('.reference-fulltext').textContent.includes('<script>')", timeout=5000)
    except Exception:
        print('READER DEBUG', page.locator('.reference-reader').first.evaluate('(e)=>e.outerHTML'), flush=True)
        print('PAGE URL', page.url, flush=True)
        raise
    assert page.locator('.reference-fulltext').first.text_content() == text
    assert page.evaluate('window.injected') is None
    page.locator('.reference-reader summary').first.click()
    page.wait_for_function("document.querySelector('.reference-fulltext').textContent === ''")
    page.locator('#reference-search').fill('没有此文件')
    assert page.locator('.reference-row:visible').count() == 0
    assert '没有匹配' in page.locator('#reference-filter-count').text_content()
    page.locator('#reference-search').fill('')
    assert page.locator('.reference-row:visible').count() == 25
    page.screenshot(path='/tmp/reference-reader-desktop.png')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/reference-reader-mobile.png')
    browser.close()
print('Reference reader desktop/mobile, search, full content and literal rendering: PASS')
