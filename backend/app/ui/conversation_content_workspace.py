CONVERSATION_CONTENT_HTML = r'''
  <fieldset id="conversation-content" class="wide">
    <legend>Conversation Content</legend>
    <p class="note">单条消息和批量文本都会写入当前选中的 Conversation。切换会话后默认只显示最新 100 条；可以按时间范围查看更早历史。页面显示范围不会截断 AI 使用的完整会话历史。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="message-heading">
        <h2 id="message-heading">Single Message</h2>
        <p class="note">用于逐条补充聊天内容。历史消息支持修改和删除；这些操作会改变后续 AI 分析所读取的真实会话数据。</p>
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
        <button id="load-messages" class="requires-auth" type="button" disabled>Refresh latest 100</button>
        <button id="create-message" class="requires-auth" type="button" disabled>Add message</button>
        <div id="messages-status" class="status">Select a conversation first.</div>
        <div id="message-list" class="status">No conversation selected.</div>
      </section>

      <section class="workspace-card" aria-labelledby="text-import-heading">
        <h2 id="text-import-heading">Batch Text</h2>
        <p class="note">格式：ISO-8601 timestamp | sender_type | content。允许 sender_type：user / person / system / assistant。粘贴内容可以是正序、倒序或局部乱序；批量文本会追加到当前选中的 Conversation，并按 sent_at 自动整理；同一时间的消息保持原粘贴顺序。</p>
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
  let currentMessageDisplayWindow = { limit: 100 };

  function resetConversationContent(message = 'Select a conversation first.') {
    currentMessageDisplayWindow = { limit: 100 };
    messageList.replaceChildren();
    messageList.textContent = 'No conversation selected.';
    messagesStatus.textContent = message;
    textImportStatus.textContent = selectedConversationId
      ? 'Ready to import messages into the selected conversation.'
      : 'Select a conversation before importing.';
    byId('message-content').value = '';
    byId('message-sent-at').value = '';
  }

  async function editHistoryMessage(item) {
    const content = window.prompt('修改消息内容', item.content);
    if (content === null) return;
    if (!content.trim()) throw new Error('Message content is required');
    const sentAt = window.prompt('修改发送时间（ISO 8601）', item.sent_at);
    if (sentAt === null) return;
    if (!sentAt.trim()) throw new Error('Message sent_at is required');
    await api(`/api/v1/messages/${encodeURIComponent(item.id)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        content: content.trim(),
        sent_at: sentAt.trim(),
      }),
    });
    await loadMessages(currentMessageDisplayWindow);
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: { source: '历史消息修改', conversation_id: selectedConversationId },
    }));
  }

  async function deleteHistoryMessage(item) {
    if (!window.confirm('确定删除这条历史消息吗？此操作会改变后续 AI 分析使用的会话历史。')) return;
    await api(`/api/v1/messages/${encodeURIComponent(item.id)}`, { method: 'DELETE' });
    await loadMessages(currentMessageDisplayWindow);
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: { source: '历史消息删除', conversation_id: selectedConversationId },
    }));
  }

  function renderMessages(items) {
    messageList.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      messageList.textContent = 'No messages in this display window.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const meta = document.createElement('div');
      const body = document.createElement('div');
      meta.textContent = `${item.sent_at} · ${item.sender_type}`;
      body.textContent = item.content;

      const actions = document.createElement('div');
      actions.className = 'client-controls-actions';
      const edit = document.createElement('button');
      edit.type = 'button';
      edit.className = 'requires-auth';
      edit.disabled = !currentAccessToken;
      edit.textContent = '修改';
      edit.addEventListener('click', async () => {
        try { await editHistoryMessage(item); }
        catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
      });
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'requires-auth';
      remove.disabled = !currentAccessToken;
      remove.textContent = '删除';
      remove.addEventListener('click', async () => {
        try { await deleteHistoryMessage(item); }
        catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
      });
      actions.append(edit, remove);
      row.append(meta, body, actions);
      messageList.appendChild(row);
    });
  }

  async function loadMessages(options = { limit: 100 }) {
    if (!selectedConversationId) {
      resetConversationContent();
      return [];
    }
    currentMessageDisplayWindow = {
      limit: Number(options.limit || 100),
      ...(options.from ? { from: options.from } : {}),
      ...(options.to ? { to: options.to } : {}),
      ...(options.before ? { before: options.before } : {}),
    };
    messagesStatus.textContent = 'Loading messages...';
    textImportStatus.textContent = 'Ready to import messages into the selected conversation.';
    const params = new URLSearchParams();
    params.set('limit', String(currentMessageDisplayWindow.limit));
    if (currentMessageDisplayWindow.from) params.set('from', currentMessageDisplayWindow.from);
    if (currentMessageDisplayWindow.to) params.set('to', currentMessageDisplayWindow.to);
    if (currentMessageDisplayWindow.before) params.set('before', currentMessageDisplayWindow.before);
    const items = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/messages?${params.toString()}`
    );
    renderMessages(items);
    messagesStatus.textContent = `${items.length} message(s) displayed. Default window is latest 100; AI analysis still uses canonical full history.`;
    return items;
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
    await loadMessages({ limit: 100 });
    messagesStatus.textContent = `Added ${created.sender_type} message at ${created.sent_at}. Showing latest 100.`;
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
    await loadMessages({ limit: 100 });
    textImportStatus.textContent = `已向当前会话追加 ${data.imported_count} 条消息，并按 sent_at 自动整理。页面显示最新 100 条。`;
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: { source: '批量导入', conversation_id: targetConversationId },
    }));
  }

  const baseResetWorkspace = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspace(message);
    resetConversationContent();
  };

  bind('load-messages', () => loadMessages({ limit: 100 }), messagesStatus);
  bind('create-message', createMessage, messagesStatus);
  bind('import-text', importTextBatch, textImportStatus);

  byId('conversation-select').addEventListener('change', async () => {
    try { await loadMessages({ limit: 100 }); }
    catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
  });

  byId('person-select').addEventListener('change', () => {
    resetConversationContent('Select a conversation first.');
  });

  byId('create-conversation').addEventListener('click', () => {
    resetConversationContent('Conversation may change; loading the selected conversation after creation.');
  });
'''
