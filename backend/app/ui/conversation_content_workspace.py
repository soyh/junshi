CONVERSATION_CONTENT_HTML = r'''
  <fieldset id="conversation-content" class="wide">
    <legend>Conversation Content</legend>
    <p class="note">单条消息和批量文本都会写入当前选中的 Conversation。切换会话后，消息列表与后续分析作用域一起切换；不会因为批量导入而自动新建会话。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="message-heading">
        <h2 id="message-heading">Single Message</h2>
        <p class="note">用于逐条补充聊天内容。请先选择当前人物下的目标会话。</p>
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
        <h2 id="text-import-heading">Batch Text</h2>
        <p class="note">格式：ISO-8601 timestamp | sender_type | content。允许 sender_type：user / person / system / assistant。批量文本会追加到当前选中的 Conversation，并按 sent_at 自动整理；同一时间的消息保持原粘贴顺序。</p>
        <label for="text-import-body">Text</label>
        <textarea id="text-import-body" class="requires-auth" placeholder="2026-09-18T12:00:00+00:00 | user | 你好&#10;2026-09-18T12:01:00+00:00 | person | 你好呀" disabled></textarea>
        <button id="import-text" class="requires-auth" type="button" disabled>Import into current conversation</button>
        <div id="text-import-status" class="status">Select a conversation before importing.</div>
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
    textImportStatus.textContent = selectedConversationId
      ? 'Ready to import messages into the selected conversation.'
      : 'Select a conversation before importing.';
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
    textImportStatus.textContent = 'Ready to import messages into the selected conversation.';
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

  async function importTextBatch() {
    if (!selectedPersonId) throw new Error('Select a person before importing');
    if (!selectedConversationId) throw new Error('Select a conversation before importing');
    const targetConversationId = selectedConversationId;
    const text = byId('text-import-body').value;
    if (!text.trim()) throw new Error('Import text is required');
    textImportStatus.textContent = '正在校验消息时间并追加到当前会话…';
    const data = await api('/api/v1/text-imports', {
      method: 'POST',
      body: JSON.stringify({
        person_id: selectedPersonId,
        conversation_id: targetConversationId,
        text,
        auto_sort_by_sent_at: true,
      }),
    });
    if (data.conversation_id !== targetConversationId) {
      throw new Error('Import returned an unexpected conversation scope');
    }
    byId('text-import-body').value = '';
    await loadMessages();
    textImportStatus.textContent = `已向当前会话追加 ${data.imported_count} 条消息，并按 sent_at 自动整理。`;
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: { source: '批量导入', conversation_id: targetConversationId },
    }));
  }

  const baseResetWorkspace = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspace(message);
    resetConversationContent();
  };

  bind('load-messages', loadMessages, messagesStatus);
  bind('create-message', createMessage, messagesStatus);
  bind('import-text', importTextBatch, textImportStatus);

  byId('conversation-select').addEventListener('change', async () => {
    try { await loadMessages(); }
    catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
  });

  byId('person-select').addEventListener('change', () => {
    resetConversationContent('Select a conversation first.');
  });

  byId('create-conversation').addEventListener('click', () => {
    resetConversationContent('Conversation may change; loading the selected conversation after creation.');
  });
'''
