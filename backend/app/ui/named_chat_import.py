NAMED_CHAT_STYLE = r'''
    #named-chat-tools { margin: 12px 0; min-width: 0; }
    #named-chat-tools .named-chat-mapping {
      display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px;
    }
    #named-chat-tools :is(input, select, button) { max-width: 100%; box-sizing: border-box; min-height: 44px; }
    #named-chat-preview { max-height: 360px; overflow: auto; overflow-wrap: anywhere; }
    #named-chat-preview article { border-bottom: 1px solid #cbe4f1; padding: 10px 0; }
    #named-chat-preview pre { white-space: pre-wrap; font: inherit; margin: 5px 0; }
    @media (max-width: 620px) {
      #named-chat-tools .named-chat-mapping { grid-template-columns: minmax(0, 1fr); }
      #named-chat-tools :is(input, select, button) { width: 100%; font-size: 16px; }
    }
'''

NAMED_CHAT_SCRIPT = r'''
  // TEST-203: parsed transcript is previewed before any writes or model calls.
  let namedChatPreview = null;
  let namedChatRevision = 0;
  const namedText = byId('text-import-body');
  const namedCard = byId('client-unified-import-card');
  function namedChatDetected(text) {
    return /^\s*\d{4}年/m.test(text);
  }
  function clearNamedChatPreview() {
    namedChatRevision += 1;
    namedChatPreview = null;
    byId('named-chat-preview')?.replaceChildren();
    for (const id of ['named-chat-self', 'named-chat-other']) {
      const select = byId(id);
      if (select) select.replaceChildren(new Option('请先识别记录', ''));
    }
  }
  function renderNamedChatPreview() {
    const host = byId('named-chat-preview');
    host.replaceChildren();
    if (!namedChatPreview) return;
    const me = byId('named-chat-self').value;
    const other = byId('named-chat-other').value;
    const heading = document.createElement('p');
    const count = namedChatPreview.messages.length;
    heading.textContent = `识别到 ${count} 条消息、${namedChatPreview.senders.length} 个用户名。预览按原文顺序；确认后按时间整理，同一时间保持原顺序。`;
    host.appendChild(heading);
    if (namedChatPreview.senders.length !== 2) {
      const warning = document.createElement('p');
      warning.textContent = '当前仅支持双方聊天，请先处理多余用户名；不会自动忽略任何人的消息。';
      host.appendChild(warning);
    }
    // Paginate DOM rendering without silently limiting the actual import.
    for (const message of namedChatPreview.messages.slice(0, namedChatPreview.visibleCount)) {
      const row = document.createElement('article');
      const title = document.createElement('strong');
      const role = message.sender_name === me ? '我' : message.sender_name === other ? '对方' : '未分配';
      const time = message.time_precision === 'minute'
        ? message.sent_at.slice(0, 16).replace('T', ' ')
        : message.sent_at.slice(0, 19).replace('T', ' ');
      title.textContent = `${message.sender_name}（${role}） · ${time} UTC${namedChatPreview.utc_offset}`;
      const content = document.createElement('pre');
      content.textContent = message.content;
      row.append(title, content);
      host.appendChild(row);
    }
    if (count > namedChatPreview.visibleCount) {
      const more = document.createElement('button');
      more.type = 'button';
      more.textContent = `继续预览（已显示 ${namedChatPreview.visibleCount}/${count}）`;
      more.addEventListener('click', () => {
        namedChatPreview.visibleCount += 100;
        renderNamedChatPreview();
      });
      host.appendChild(more);
    }
  }
  async function previewNamedChat() {
    if (!currentAccessToken) throw new Error('请先登录');
    if (!selectedConversationId) throw new Error('请先选择会话');
    clearNamedChatPreview();
    const revision = namedChatRevision;
    const text = namedText.value;
    const conversation = selectedConversationId;
    const person = selectedPersonId;
    const token = currentAccessToken;
    const offset = byId('named-chat-offset').value.trim();
    const result = await api('/api/v1/text-imports/preview', {
      method: 'POST', body: JSON.stringify({text, utc_offset: offset}),
    });
    if (revision !== namedChatRevision || text !== namedText.value ||
        conversation !== selectedConversationId || person !== selectedPersonId ||
        token !== currentAccessToken) return;
    namedChatPreview = {...result, text, conversation, person, token, visibleCount: 100};
    for (const id of ['named-chat-self', 'named-chat-other']) {
      byId(id).replaceChildren(new Option('请选择用户名', ''));
      for (const name of result.senders) byId(id).add(new Option(name, name));
    }
    renderNamedChatPreview();
    byId('client-unified-import-status').textContent = '请选择哪个用户名是我、哪个是对方，检查预览后点击“添加到当前会话”。';
  }
  if (namedCard && namedText) {
    const tools = document.createElement('section');
    tools.id = 'named-chat-tools';
    function element(tag, attrs = {}, text = '') {
      const node = document.createElement(tag);
      for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
      node.textContent = text;
      return node;
    }
    tools.append(
      element('p', {}, '聊天导出格式：用户名、日期时间、正文分行，例如 ID1 / 2026年09月26日 10:40 / 早早早。先识别，再选择双方身份。'),
      element('label', {for: 'named-chat-file'}, '上传聊天记录（UTF-8 .txt / .md）'),
      element('input', {id: 'named-chat-file', type: 'file', accept: '.txt,.md,text/plain,text/markdown'}),
      element('label', {for: 'named-chat-offset'}, '原记录所在时区（默认北京时间 UTC+08:00）'),
      element('input', {id: 'named-chat-offset', value: '+08:00', 'aria-describedby': 'named-chat-time-note'}),
      element('p', {id: 'named-chat-time-note'}, '没有秒数的记录按分钟显示；存储秒数为 00，不推测实际秒数。'),
      element('button', {id: 'named-chat-recognize', type: 'button', class: 'requires-auth'}, '识别并预览聊天记录'),
    );
    const mapping = element('div', {class: 'named-chat-mapping'});
    for (const [id, label] of [['named-chat-self', '哪个用户名是我'], ['named-chat-other', '哪个用户名是对方']]) {
      const field = element('div');
      field.append(element('label', {for: id}, label), element('select', {id}));
      mapping.appendChild(field);
    }
    tools.append(mapping, element('div', {id: 'named-chat-preview', 'aria-live': 'polite'}));
    namedCard.insertBefore(tools, byId('client-unified-import-actions'));
    clearNamedChatPreview();
    byId('named-chat-recognize').disabled = !currentAccessToken;
    const showError = error => { byId('client-unified-import-status').textContent = error instanceof Error ? error.message : String(error); };
    namedText.addEventListener('input', clearNamedChatPreview);
    byId('named-chat-offset').addEventListener('input', clearNamedChatPreview);
    byId('conversation-select')?.addEventListener('change', clearNamedChatPreview);
    byId('person-select')?.addEventListener('change', clearNamedChatPreview);
    for (const id of ['named-chat-self', 'named-chat-other']) byId(id).addEventListener('change', renderNamedChatPreview);
    byId('named-chat-recognize').addEventListener('click', async () => {
      const button = byId('named-chat-recognize');
      button.disabled = true;
      try { await previewNamedChat(); } catch (error) { showError(error); }
      finally { button.disabled = !currentAccessToken; }
    });
    byId('named-chat-file').addEventListener('change', async event => {
      const file = event.target.files[0];
      if (!file) return;
      clearNamedChatPreview();
      const revision = namedChatRevision;
      try {
        if (!/\.(txt|md)$/i.test(file.name)) throw new Error('请选择 .txt 或 .md 文件');
        if (file.size > 1_000_000) throw new Error('文件不能超过 1 MB');
        const text = new TextDecoder('utf-8', {fatal: true}).decode(await file.arrayBuffer());
        if (revision !== namedChatRevision) return;
        namedText.value = text;
        await previewNamedChat();
      } catch (error) { showError(error); }
      finally { event.target.value = ''; }
    });
  }
  const submitBeforeNamedChat = clientSubmitUnifiedConversationImport;
  clientSubmitUnifiedConversationImport = async function() {
    if (!namedChatDetected(namedText.value)) return submitBeforeNamedChat();
    const state = namedChatPreview;
    if (!state || state.text !== namedText.value || state.conversation !== selectedConversationId ||
        state.person !== selectedPersonId || state.token !== currentAccessToken ||
        state.utc_offset !== byId('named-chat-offset').value.trim()) {
      await previewNamedChat();
      return;
    }
    const me = byId('named-chat-self').value;
    const other = byId('named-chat-other').value;
    if (!me || !other || me === other) throw new Error('请选择两个不同的用户名，分别作为我和对方');
    if (state.senders.length !== 2) throw new Error('请先处理第三个用户名或不完整的双方记录');
    if (!window.confirm(`确认将 ${state.messages.length} 条消息导入当前会话？我：${me}；对方：${other}`)) return;
    const result = await api('/api/v1/text-imports', {
      method: 'POST', body: JSON.stringify({person_id: state.person,
        conversation_id: state.conversation, text: state.text, source_format: 'named_chat',
        self_name: me, other_name: other, utc_offset: state.utc_offset, auto_sort_by_sent_at: true}),
    });
    if (result.conversation_id !== state.conversation) throw new Error('导入返回了非预期会话');
    if (state.conversation === selectedConversationId && state.person === selectedPersonId) {
      if (namedText.value === state.text) namedText.value = '';
      clearNamedChatPreview();
      byId('client-unified-import-status').textContent = `已导入 ${result.imported_count} 条消息。`;
      try { await loadMessages(currentMessageWindow); }
      catch (error) { byId('client-unified-import-status').textContent += '列表刷新失败，请刷新记录；不要重复导入。'; }
    }
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: {source: '批量导入', conversation_id: state.conversation},
    }));
  };
  const clearSessionBeforeNamedChat = clearSession;
  clearSession = function(message) {
    clearNamedChatPreview();
    clearSessionBeforeNamedChat(message);
  };
'''
