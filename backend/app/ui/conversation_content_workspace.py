CONVERSATION_CONTENT_HTML = r'''
  <fieldset id="conversation-content" class="wide">
    <legend>Conversation Content</legend>
    <p class="note">TEST-137 只复用现有 Messages / Text Import canonical API。单条消息写入当前 Conversation；批量 Text Import 按现有 contract 创建新的 Conversation，成功后自动选中新会话。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="message-heading">
        <h2 id="message-heading">Messages</h2>
        <p class="note">先在上方选择 Conversation。列表继续由服务端按 sent_at / created_at 排序。</p>
        <label for="message-sender">Sender</label>
        <select id="message-sender" class="requires-auth" disabled>
          <option value="user">user</option>
          <option value="person">person</option>
          <option value="system">system</option>
          <option value="assistant">assistant</option>
        </select>
        <label for="message-sent-at">Sent at (optional ISO 8601)</label>
        <input id="message-sent-at" class="requires-auth" autocomplete="off" placeholder="2026-09-18T12:00:00+00:00" disabled>
        <label for="message-content">Content</label>
        <textarea id="message-content" class="requires-auth" disabled></textarea>
        <button id="load-messages" class="requires-auth" type="button" disabled>Refresh messages</button>
        <button id="create-message" class="requires-auth" type="button" disabled>Add message</button>
        <div id="messages-status" class="status">Select a conversation first.</div>
        <div id="message-list" class="status">No conversation selected.</div>
      </section>

      <section class="workspace-card" aria-labelledby="text-import-heading">
        <h2 id="text-import-heading">Text Import</h2>
        <p class="note">格式：ISO-8601 timestamp | sender_type | content。允许 sender_type：user / person / system / assistant。Import 会创建新 Conversation，不会向当前 Conversation 偷偷追加。粘贴内容可以是正序、倒序或局部乱序；页面导入会按 sent_at 自动整理，同一时间的消息保持原粘贴顺序。</p>
        <label for="text-import-title">New conversation title (optional)</label>
        <input id="text-import-title" class="requires-auth" autocomplete="off" disabled>
        <label for="text-import-body">Text</label>
        <textarea id="text-import-body" class="requires-auth" placeholder="2026-09-18T12:00:00+00:00 | user | 你好&#10;2026-09-18T12:01:00+00:00 | person | 你好呀" disabled></textarea>
        <button id="import-text" class="requires-auth" type="button" disabled>Import as new conversation</button>
        <div id="text-import-status" class="status">Select a person before importing.</div>
      </section>
    </div>
  </fieldset>
'''


CONVERSATION_CONTENT_SCRIPT = r'''
  const messagesStatus = byId('messages-status');
  const messageList = byId('message-list');
  const textImportStatus = byId('text-import-status');

  function resetConversationContent(message = 'Select a conversation first.') {
    messageList.replaceChildren();
    messageList.textContent = 'No conversation selected.';
    messagesStatus.textContent = message;
    textImportStatus.textContent = selectedPersonId
      ? 'Ready to import a new conversation for the selected person.'
      : 'Select a person before importing.';
    byId('message-content').value = '';
    byId('message-sent-at').value = '';
  }

  function renderMessages(items) {
    messageList.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      messageList.textContent = 'No messages in this conversation.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const meta = document.createElement('div');
      const body = document.createElement('div');
      meta.textContent = `${item.sent_at} · ${item.sender_type}`;
      body.textContent = item.content;
      row.append(meta, body);
      messageList.appendChild(row);
    });
  }

  async function loadMessages() {
    if (!selectedConversationId) {
      resetConversationContent();
      return;
    }
    messagesStatus.textContent = 'Loading messages...';
    const items = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/messages`
    );
    renderMessages(items);
    messagesStatus.textContent = `${items.length} message(s) loaded for the selected conversation.`;
  }

  async function createMessage() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    const content = byId('message-content').value.trim();
    if (!content) throw new Error('Message content is required');
    const sentAt = byId('message-sent-at').value.trim();
    const payload = {
      conversation_id: selectedConversationId,
      sender_type: byId('message-sender').value,
      content,
    };
    if (sentAt) payload.sent_at = sentAt;
    const created = await api('/api/v1/messages', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    byId('message-content').value = '';
    byId('message-sent-at').value = '';
    await loadMessages();
    messagesStatus.textContent = `Added ${created.sender_type} message at ${created.sent_at}.`;
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: { source: '新消息', conversation_id: selectedConversationId },
    }));
  }

  async function importTextConversation() {
    if (!selectedPersonId) throw new Error('Select a person before importing');
    const text = byId('text-import-body').value;
    if (!text.trim()) throw new Error('Import text is required');
    textImportStatus.textContent = '正在校验消息时间并按 sent_at 自动整理…';
    const data = await api('/api/v1/text-imports', {
      method: 'POST',
      body: JSON.stringify({
        person_id: selectedPersonId,
        title: nullableText('text-import-title'),
        text,
        auto_sort_by_sent_at: true,
      }),
    });
    selectedConversationId = data.conversation_id;
    byId('conversation-id').value = data.conversation_id;
    byId('text-import-title').value = '';
    byId('text-import-body').value = '';
    await loadConversations();
    byId('conversation-select').value = data.conversation_id;
    await loadMessages();
    conversationStatus.textContent = `Imported and selected conversation ${data.conversation_id}.`;
    textImportStatus.textContent = `已导入 ${data.imported_count} 条消息到新会话，并按 sent_at 自动整理为时间顺序。`;
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: { source: '批量导入', conversation_id: selectedConversationId },
    }));
  }

  const baseResetWorkspace = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspace(message);
    resetConversationContent();
  };

  bind('load-messages', loadMessages, messagesStatus);
  bind('create-message', createMessage, messagesStatus);
  bind('import-text', importTextConversation, textImportStatus);

  byId('conversation-select').addEventListener('change', async () => {
    try { await loadMessages(); }
    catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
  });

  byId('person-select').addEventListener('change', () => {
    resetConversationContent('Select a conversation first.');
  });

  byId('create-conversation').addEventListener('click', () => {
    resetConversationContent('Conversation may change; refresh messages after creation.');
  });
'''
