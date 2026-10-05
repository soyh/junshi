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
editor_state = {'content': text, 'revision': 'a' * 64}
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    requests = []
    def handle(route):
        requests.append((route.request.method, route.request.url, route.request.post_data))
        if route.request.url.endswith('/references/guide'):
            payload = route.request.post_data_json
            result = {'id': 'new-guide', 'content': payload['content'], 'revision': 'd' * 64}
        elif route.request.url.endswith('/editor'):
            result = {'id': '0', **editor_state}
        elif route.request.url.endswith('/content') and route.request.method == 'PUT':
            payload = route.request.post_data_json
            if payload['expected_revision'] != editor_state['revision']:
                route.fulfill(status=409, content_type='application/json', body=json.dumps({'detail': '文件已在其他窗口更新，未覆盖。'}))
                return
            editor_state.update(content=payload['content'], revision='b' * 64)
            result = {'id': '0', **editor_state}
        elif route.request.url.endswith(('/references/context', '/references/catalog')):
            result = {'items': [{'name': '冲突指南.md', 'truncated': True}],
                      'retrieval': {'enabled_count': 25, 'candidate_count': 24, 'guide_count': 1,
                                    'omitted_from_catalog': 1,
                                    'warnings': [{'filename': '<script>window.injected=true</script>.md', 'reason': 'not_enabled_or_missing'}]}}
        elif route.request.url.endswith('/batch'):
            payload = route.request.post_data_json
            if payload['action'] == 'delete':
                items[:] = [x for x in items if x['id'] not in payload['reference_ids']]
            result = {'updated_count': len(payload['reference_ids'])}
        else:
            result = {'id': '0', 'content': editor_state['content']} if route.request.url.endswith('/content') else items
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
    page.locator('#reference-preview-selection').click()
    page.wait_for_function("document.querySelector('#reference-retrieval-preview').textContent.includes('冲突指南.md')")
    assert '未匹配到已启用文件' in page.locator('#reference-retrieval-preview').text_content()
    assert '不表示模型已读取' in page.locator('#reference-retrieval-preview').text_content()
    assert page.evaluate('window.injected') is None
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
    # Editing is available only after expansion; draft cancellation is explicit.
    page.locator('.reference-reader summary').first.click()
    page.locator('.reference-edit-content').first.click()
    page.wait_for_function("!document.querySelector('#reference-editor-input').disabled")
    assert page.locator('#reference-editor-input').input_value() == text
    updated = '# 主题指南\n- 冲突与修复：`冲突.md`\n<script>window.injected=true</script>'
    page.locator('#reference-editor-input').fill(updated)
    page.once('dialog', lambda dialog: dialog.dismiss())
    page.locator('#reference-editor-close').click()
    assert page.locator('#reference-editor').is_visible()
    page.locator('#reference-editor-save').click()
    page.wait_for_function("document.querySelector('#reference-editor-status').textContent.includes('保存成功')")
    assert editor_state['content'] == updated
    assert page.locator('#reference-editor-input').input_value() == updated
    assert page.evaluate('window.injected') is None
    assert page.locator('#reference-editor-save').is_disabled()
    # Concurrent update must retain the unsaved local draft after a conflict.
    editor_state.update(content='external update', revision='c' * 64)
    page.locator('#reference-editor-input').fill('local unsaved draft')
    page.locator('#reference-editor-save').click()
    page.wait_for_function("document.querySelector('#reference-editor-status').textContent.includes('未覆盖')")
    assert page.locator('#reference-editor-input').input_value() == 'local unsaved draft'
    assert editor_state['content'] == 'external update'
    page.once('dialog', lambda dialog: dialog.accept())
    page.locator('#reference-editor-close').click()
    assert page.locator('#reference-editor').count() == 0
    page.screenshot(path='/tmp/reference-global-desktop.png')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('.reference-reader summary').first.click()
    page.locator('.reference-edit-content').first.click()
    page.wait_for_function("!document.querySelector('#reference-editor-input').disabled")
    assert page.locator('#reference-editor-input').input_value() == 'external update'
    assert page.locator('#reference-editor').bounding_box()['width'] <= 390
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/reference-global-mobile.png')
    page.locator('#reference-editor-close').click()
    # Global creation and preview work without a selected conversation.
    page.evaluate("selectedConversationId = null")
    page.locator('#reference-preview-selection').click()
    page.wait_for_function("document.querySelector('#reference-retrieval-preview').textContent.includes('无需选择会话')")
    page.locator('#reference-create-guide').click()
    page.wait_for_function("!document.querySelector('#reference-editor-input').disabled")
    assert 'original-24.md' in page.locator('#reference-editor-input').input_value()
    assert page.locator('#reference-editor-save').is_enabled()
    page.locator('#reference-editor-name').fill('全局指南.md')
    page.locator('#reference-editor-input').fill('# 导读\n- 修复：`original-0.md`')
    page.locator('#reference-editor-save').click()
    page.wait_for_function("document.querySelector('#reference-editor-status').textContent.includes('保存成功')")
    creation = json.loads(next(data for method, url, data in requests if url.endswith('/references/guide')))
    assert creation['name'] == '全局指南.md'
    assert 'original-0.md' in creation['content']
    assert 'conversation_id' not in creation
    page.locator('#reference-editor-close').click()
    browser.close()
print('Global guide creation and preview without conversation; editing and batch regression: PASS')
