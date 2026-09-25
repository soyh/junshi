CONVERSATION_CONTROLS_STYLE = r'''
#client-conversation-controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(160px, 1fr));
  gap: 8px 12px;
  margin: 10px 0 6px;
}
#client-conversation-controls .client-controls-actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
#client-conversation-controls button { margin: 0 !important; }
#client-conversation-editor-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
#client-conversation-editor-actions button { margin-right: 0 !important; }
@media (max-width: 680px) {
  #client-conversation-controls { grid-template-columns: 1fr; }
  #client-conversation-controls .client-controls-actions { grid-column: auto; }
}
'''


CONVERSATION_CONTROLS_SCRIPT = r'''
  // TEST-177: display-window controls stay presentation-only; analysis continues
  // to call the canonical conversation analysis endpoint with the full history.
  // TEST-196: legacy media upload controls were removed. The single canonical
  // media entrypoint is installed by media_upload_workspace.py.
  let clientAllConversationMessages = [];

  function clientMessageFilterDate(value, endOfDay = false) {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    if (endOfDay && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      parsed.setHours(23, 59, 59, 999);
    }
    return parsed;
  }

  function clientFilteredMessages(items) {
    const fromInput = byId('client-message-from');
    const toInput = byId('client-message-to');
    if (!fromInput || !toInput) return items;
    const from = clientMessageFilterDate(fromInput.value);
    const to = clientMessageFilterDate(toInput.value, true);
    return items.filter((item) => {
      const sent = new Date(item.sent_at);
      if (Number.isNaN(sent.getTime())) return true;
      if (from && sent < from) return false;
      if (to && sent > to) return false;
      return true;
    });
  }

  const baseRenderMessagesForClientWindow = renderMessages;
  renderMessages = function(items) {
    clientAllConversationMessages = Array.isArray(items) ? items.slice() : [];
    const visible = clientFilteredMessages(clientAllConversationMessages);
    baseRenderMessagesForClientWindow(visible);
    const info = byId('client-message-window-status');
    if (info) {
      info.textContent = `当前显示 ${visible.length} / ${clientAllConversationMessages.length} 条；AI 分析仍使用该会话完整历史。`;
    }
  };

  function clientApplyMessageWindow() {
    renderMessages(clientAllConversationMessages);
  }

  function clientClearMessageWindow() {
    const from = byId('client-message-from');
    const to = byId('client-message-to');
    if (from) from.value = '';
    if (to) to.value = '';
    renderMessages(clientAllConversationMessages);
  }

  async function clientLoadSelectedConversationForEdit() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    const item = await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}`);
    byId('conversation-title').value = item.title || '';
    byId('conversation-state').value = item.status;
    selectedRelationshipId = item.relationship_id || null;
    if (byId('relationship-select')) byId('relationship-select').value = selectedRelationshipId || '';
    conversationStatus.textContent = '已载入当前会话，可修改标题、状态或关系后保存。';
  }

  async function clientSaveSelectedConversation() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    const updated = await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        relationship_id: selectedRelationshipId || null,
        title: nullableText('conversation-title'),
        status: byId('conversation-state').value,
      }),
    });
    await loadConversations();
    selectedConversationId = updated.id;
    byId('conversation-select').value = updated.id;
    byId('conversation-id').value = updated.id;
    conversationStatus.textContent = `已保存会话：${updated.title || '(untitled)'}`;
  }

  async function clientDeleteSelectedConversation() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    const deletingId = selectedConversationId;
    if (!window.confirm('确定删除当前会话及其关联记录吗？此操作不可撤销。')) return;
    await api(`/api/v1/conversations/${encodeURIComponent(deletingId)}`, { method: 'DELETE' });
    selectedConversationId = null;
    byId('conversation-id').value = '';
    byId('conversation-title').value = '';
    clientAllConversationMessages = [];
    await loadConversations();
    resetConversationContent('会话已删除，请选择其它会话。');
    conversationStatus.textContent = '会话已删除。';
    const mediaList = byId('client-media-list');
    if (mediaList) mediaList.textContent = '请先选择会话。';
  }

  function clientInstallConversationControls() {
    const createButton = byId('create-conversation');
    if (createButton && !byId('client-edit-conversation')) {
      const actions = document.createElement('div');
      actions.id = 'client-conversation-editor-actions';

      const edit = document.createElement('button');
      edit.id = 'client-edit-conversation';
      edit.type = 'button';
      edit.className = 'requires-auth';
      edit.disabled = !currentAccessToken;
      edit.textContent = '读取并修改';

      const save = document.createElement('button');
      save.id = 'client-save-conversation';
      save.type = 'button';
      save.className = 'requires-auth';
      save.disabled = !currentAccessToken;
      save.textContent = '保存修改';

      const remove = document.createElement('button');
      remove.id = 'client-delete-conversation';
      remove.type = 'button';
      remove.className = 'requires-auth';
      remove.disabled = !currentAccessToken;
      remove.textContent = '删除会话';

      createButton.insertAdjacentElement('afterend', actions);
      actions.append(edit, save, remove);

      bind('client-edit-conversation', clientLoadSelectedConversationForEdit, conversationStatus);
      bind('client-save-conversation', clientSaveSelectedConversation, conversationStatus);
      bind('client-delete-conversation', clientDeleteSelectedConversation, conversationStatus);
    }

    const history = byId('client-unified-message-history');
    const messageListNode = byId('message-list');
    const host = history || messageListNode?.parentElement;
    if (host && !byId('client-conversation-controls')) {
      const controls = document.createElement('div');
      controls.id = 'client-conversation-controls';

      const fromWrap = document.createElement('div');
      const fromLabel = document.createElement('label');
      fromLabel.htmlFor = 'client-message-from';
      fromLabel.textContent = '显示起始时间';
      const from = document.createElement('input');
      from.id = 'client-message-from';
      from.type = 'datetime-local';
      fromWrap.append(fromLabel, from);

      const toWrap = document.createElement('div');
      const toLabel = document.createElement('label');
      toLabel.htmlFor = 'client-message-to';
      toLabel.textContent = '显示结束时间';
      const to = document.createElement('input');
      to.id = 'client-message-to';
      to.type = 'datetime-local';
      toWrap.append(toLabel, to);

      const actions = document.createElement('div');
      actions.className = 'client-controls-actions';
      const apply = document.createElement('button');
      apply.id = 'client-apply-message-window';
      apply.type = 'button';
      apply.textContent = '按时间显示';
      const clear = document.createElement('button');
      clear.id = 'client-clear-message-window';
      clear.type = 'button';
      clear.textContent = '显示全部';
      actions.append(apply, clear);

      const status = document.createElement('div');
      status.id = 'client-message-window-status';
      status.className = 'client-controls-actions note';
      status.textContent = '仅过滤页面显示；AI 分析始终参考该会话完整历史。';

      controls.append(fromWrap, toWrap, actions, status);
      if (history) history.insertAdjacentElement('beforebegin', controls);
      else host.insertBefore(controls, messageListNode || null);

      apply.addEventListener('click', clientApplyMessageWindow);
      clear.addEventListener('click', clientClearMessageWindow);
    }
  }

  clientInstallConversationControls();
'''