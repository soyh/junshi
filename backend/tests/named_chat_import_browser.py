from app.ui.china_time import CHINA_TIME_SCRIPT
"""Browser acceptance using the real parser and UI, with all HTTP mocked."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.ui.named_chat_import import NAMED_CHAT_SCRIPT, NAMED_CHAT_STYLE
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML
from app.services.named_chat_parser import parse_named_chat

SAMPLE = "ID1\n2026年09月26日 10:40\n早早早\n第二行 <script>window.injected=true</script>\n\nID2\n2026年09月26日 10:40\n早呀"
OUT = Path(os.environ.get("BROWSER_OUTPUT", "/tmp"))
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get("BROWSER_CHANNEL") or None)
    # Ensure the new fragment composes successfully with every existing installer.
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.route("**/*", lambda route: route.fulfill(content_type="text/html", body=PRODUCT_SHELL_WITH_CONTENT_HTML)
               if route.request.url.endswith("/app") else route.fulfill(content_type="application/json", body="[]"))
    page.goto("http://chat.test/app")
    assert page.locator("#named-chat-file").count() == 1
    assert page.locator("#named-chat-recognize").is_disabled()
    assert not errors, errors
    page.close()

    for width in [390, 1280]:
        page = browser.new_page(viewport={"width": width, "height": 844})
        imports = []
        def handle(route):
            if route.request.url.endswith("/preview"):
                try:
                    payload = route.request.post_data_json
                    result = parse_named_chat(payload["text"], payload["utc_offset"])
                except ValueError as error:
                    route.fulfill(status=422, content_type="application/json", body=json.dumps({"detail": str(error)}))
                    return
            elif route.request.url.endswith("/text-imports"):
                imports.append(route.request.post_data_json)
                result = {"conversation_id": "c1", "imported_count": 2}
            else:
                route.fulfill(content_type="text/html", body="<body></body>")
                return
            route.fulfill(content_type="application/json", body=json.dumps(result))
        page.route("**/*", handle)
        page.goto("http://chat.test/")
        page.set_content('<style>body{margin:12px}button,input,select{max-width:100%}' + NAMED_CHAT_STYLE + '</style>'
            '<section id="client-unified-import-card"><textarea id="text-import-body"></textarea>'
            '<div id="client-unified-import-actions"><button id="submit">添加到当前会话</button></div>'
            '<div id="client-unified-import-status"></div></section>'
            '<select id="conversation-select"><option value="c1">c1</option><option value="c2">c2</option></select>'
            '<select id="person-select"></select>')
        page.add_script_tag(content=CHINA_TIME_SCRIPT + r'''
            const byId=id=>document.getElementById(id);
            let currentAccessToken='test', selectedConversationId='c1', selectedPersonId='p1';
            let currentMessageWindow=50;
            async function loadMessages() {}
            function clearSession() { currentAccessToken=null; }
            async function clientSubmitUnifiedConversationImport() { window.legacyCalled=true; }
            async function api(url, options) {
              const response=await fetch(url, options); const result=await response.json();
              if(!response.ok) throw new Error(result.detail); return result;
            }
        ''' + NAMED_CHAT_SCRIPT + r'''
            byId('submit').onclick=async()=>{
              try { await clientSubmitUnifiedConversationImport(); }
              catch(e) { byId('client-unified-import-status').textContent=e.message; }
            };
        ''')
        page.locator('#text-import-body').fill(SAMPLE)
        page.locator('#submit').click()
        page.wait_for_function("document.querySelectorAll('#named-chat-self option').length===3")
        assert not imports
        assert page.locator('#named-chat-self').input_value() == ''
        assert page.locator('#named-chat-other').input_value() == ''
        assert '第二行 <script>' in page.locator('#named-chat-preview').inner_text()
        assert page.evaluate('window.injected') is None
        assert '10:40:00' not in page.locator('#named-chat-preview strong').first.inner_text()
        page.locator('#named-chat-self').select_option('ID2')
        page.locator('#named-chat-other').select_option('ID2')
        page.locator('#submit').click()
        assert not imports
        page.locator('#named-chat-other').select_option('ID1')
        page.once('dialog', lambda dialog: dialog.dismiss())
        page.locator('#submit').click()
        assert not imports
        page.screenshot(path=str(OUT / f'test203-preview-{width}.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#submit').click()
        page.wait_for_function("document.querySelector('#client-unified-import-status').textContent.includes('已导入 2')")
        assert imports[0]['self_name'] == 'ID2' and imports[0]['other_name'] == 'ID1'
        assert imports[0]['text'] == SAMPLE and imports[0]['source_format'] == 'named_chat'
        assert page.locator('#text-import-body').input_value() == ''
        # Upload automatically previews; editing invalidates identity mapping.
        page.locator('#named-chat-file').set_input_files({'name':'chat.txt','mimeType':'text/plain','buffer':SAMPLE.encode()})
        page.wait_for_function("document.querySelectorAll('#named-chat-self option').length===3")
        page.locator('#text-import-body').fill(SAMPLE + '\n改动')
        assert page.locator('#named-chat-preview').inner_text() == ''
        page.locator('#named-chat-recognize').click()
        page.wait_for_function("document.querySelectorAll('#named-chat-self option').length===3")
        page.locator('#conversation-select').select_option('c2')
        assert page.locator('#named-chat-preview').inner_text() == ''
        page.locator('#text-import-body').fill('普通消息')
        page.locator('#submit').click()
        assert page.evaluate('window.legacyCalled') is True
        page.close()
    browser.close()
print('TEST-203 named chat preview, mapping, upload, escaping, stale-state and mobile browser: PASS')
