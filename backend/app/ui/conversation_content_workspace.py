CONVERSATION_CONTENT_HTML = r'''
  <fieldset id="conversation-content" class="wide">
    <legend>Conversation Content</legend>
    <p class="note">单条消息和批量文本都会写入当前选中的 Conversation。页面默认只加载最新 100 条；完整历史仍保存在服务端并继续用于 AI 分析。</p>

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
        <button id="load-messages" class="requires-auth" type="button" disabled>Refresh latest 100</button>
        <button id="load-earlier-messages" class="requires-auth" type="button" disabled>Load earlier 100</button>
        <button id="create-message" class="requires-auth" type="button" disabled>Add message</button>
        <div id="messages-status" class="status">Select a conversation first.</div>
        <div id="message-list" class="status">No conversation selected.</div>
      </section>

      <section class="workspace-card" aria-labelledby="text-import-heading">
        <h2 id="text-import-heading">Batch Text</h2>
        <p class="note">格式：ISO-8601 timestamp | sender_type | content。允许 sender_type：user / person / system / assistant。批量文本会追加到当前选中的 Conversation，并按 sent_at 自动整理。</p>
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
  let currentDisplayMessages = [];
  let currentMessageWindow = {from: null, to: null};

  function resetConversationContent(message = 'Select a conversation first.') {
    currentDisplayMessages = [];
    currentMessageWindow = {from: null, to: null};
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
    const nextContent = window.prompt('修改消息内容', item.content);
    if (nextContent === null) return;
    if (!nextContent.trim()) throw new Error('Message content cannot be empty');
    const nextSentAt = window.prompt('修改发送时间（ISO 8601）', item.sent_at);
    if (nextSentAt === null) return;
    const updated = await api(`/api/v1/messages/${encodeURIComponent(item.id)}`, {
      method: 'PATCH',
      body: JSON.stringify({content: nextContent, sent_at: nextSentAt}),
    });
    await loadMessages(currentMessageWindow);
    messagesStatus.textContent = `Updated message at ${updated.sent_at}.`;
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: {source: '历史消息修改', conversation_id: selectedConversationId},
    }));
  }

  async function deleteHistoryMessage(item) {
    if (!window.confirm('确定删除这条历史消息吗？')) return;
    await api(`/api/v1/messages/${encodeURIComponent(item.id)}`, {method: 'DELETE'});
    await loadMessages(currentMessageWindow);
    messagesStatus.textContent = 'Message deleted.';
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: {source: '历史消息删除', conversation_id: selectedConversationId},
    }));
  }

  function renderMessages(items) {
    currentDisplayMessages = Array.isArray(items) ? items.slice() : [];
    messageList.replaceChildren();
    if (currentDisplayMessages.length === 0) {
      messageList.textContent = 'No messages in this conversation window.';
      return;
    }
    currentDisplayMessages.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const meta = document.createElement('div');
      const body = document.createElement('div');
      const actions = document.createElement('div');
      actions.className = 'client-controls-actions';
      meta.textContent = `${item.sent_at} · ${item.sender_type}`;
      body.textContent = item.content;

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

  function messageHistoryUrl(options = {}) {
    const params = new URLSearchParams();
    params.set('limit', String(options.limit || 100));
    if (options.from) params.set('from', options.from);
    if (options.to) params.set('to', options.to);
    if (options.before) params.set('before', options.before);
    return `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/messages?${params.toString()}`;
  }

  async function loadMessages(options = {}) {
    if (!selectedConversationId) {
      resetConversationContent();
      return;
    }
    const normalized = {
      from: options.from || null,
      to: options.to || null,
      before: options.before || null,
      limit: options.limit || 100,
    };
    currentMessageWindow = {from: normalized.from, to: normalized.to};
    messagesStatus.textContent = 'Loading messages...';
    textImportStatus.textContent = 'Ready to import messages into the selected conversation.';
    const items = await api(messageHistoryUrl(normalized));
    renderMessages(items);
    const scope = normalized.from || normalized.to ? 'selected time window' : 'latest window';
    messagesStatus.textContent = `${items.length} message(s) loaded from the ${scope}; AI analysis still uses complete history.`;
    return items;
  }

  async function loadEarlierMessages() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    if (currentDisplayMessages.length === 0) return loadMessages(currentMessageWindow);
    const first = currentDisplayMessages[0];
    const earlier = await api(messageHistoryUrl({
      ...currentMessageWindow,
      before: first.sent_at,
      limit: 100,
    }));
    const merged = [...earlier, ...currentDisplayMessages];
    const seen = new Set();
    const deduped = merged.filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
    renderMessages(deduped);
    messagesStatus.textContent = `${deduped.length} message(s) displayed; loaded ${earlier.length} earlier message(s).`;
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
    await loadMessages(currentMessageWindow);
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
    await loadMessages(currentMessageWindow);
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
  bind('load-earlier-messages', loadEarlierMessages, messagesStatus);
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
