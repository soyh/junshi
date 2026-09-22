CONVERSATION_CONTROLS_STYLE = r'''
#client-conversation-controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(160px, 1fr));
  gap: 8px 12px;
  margin: 10px 0 6px;
}
#client-conversation-controls .client-controls-actions,
#client-media-actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
#client-conversation-controls button,
#client-media-actions button { margin: 0 !important; }
#client-conversation-editor-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
#client-conversation-editor-actions button { margin-right: 0 !important; }
#client-media-card {
  grid-column: 1 / -1;
  padding: 14px;
  border: 1px solid rgba(78,105,150,.14);
  border-radius: 16px;
  background: rgba(255,255,255,.72);
}
#client-media-card h3 { margin: 0 0 5px; }
#client-media-controls {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(190px, .55fr);
  gap: 10px 12px;
  align-items: end;
}
#client-media-list { margin-top: 10px; }
.client-media-row {
  padding: 10px 0;
  border-top: 1px solid rgba(127,127,127,.18);
}
.client-media-row:first-child { border-top: 0; }
.client-media-row .client-media-meta { font-size: .82rem; opacity: .78; }
.client-media-row .client-media-analysis { margin-top: 5px; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 680px) {
  #client-conversation-controls,
  #client-media-controls { grid-template-columns: 1fr; }
  #client-conversation-controls .client-controls-actions,
  #client-media-actions { grid-column: auto; }
}
'''


CONVERSATION_CONTROLS_SCRIPT = r'''
  // TEST-177: display-window controls stay presentation-only; analysis continues
  // to call the canonical conversation analysis endpoint with the full history.
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

  async function clientMediaApi(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${requireToken()}`);
    const response = await fetch(path, {...options, headers});
    if (response.status === 204) return null;
    const text = await response.text();
    let data = null;
    if (text) {
      try { data = JSON.parse(text); } catch (_) { data = text; }
    }
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : data;
      throw new Error(typeof detail === 'string' ? detail : `HTTP ${response.status}`);
    }
    return data;
  }

  function clientRenderMedia(items) {
    const list = byId('client-media-list');
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      list.textContent = '当前会话还没有图片或视频。';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'client-media-row';
      const meta = document.createElement('div');
      meta.className = 'client-media-meta';
      meta.textContent = `${item.media_type === 'image' ? '图片' : '视频'} · ${item.original_filename} · ${item.analysis_status}`;
      const analysis = document.createElement('div');
      analysis.className = 'client-media-analysis';
      analysis.textContent = item.analysis_text || '尚未完成内容识别。';
      const actions = document.createElement('div');
      actions.className = 'client-controls-actions';
      const analyze = document.createElement('button');
      analyze.type = 'button';
      analyze.textContent = item.analysis_status === 'completed' ? '重新识别' : '识别内容';
      analyze.disabled = !currentAccessToken;
      analyze.addEventListener('click', async () => {
        const status = byId('client-media-status');
        analyze.disabled = true;
        try {
          status.textContent = '正在让当前 LLM 模型识别媒体内容…';
          await clientMediaApi(`/api/v1/media/${encodeURIComponent(item.id)}/analyze`, {method: 'POST'});
          await clientLoadMediaAttachments();
          await loadMessages();
          status.textContent = '媒体识别完成，结果已作为系统证据写入完整会话链路。';
          window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
            detail: {source: '媒体识别', conversation_id: selectedConversationId},
          }));
        } catch (error) {
          status.textContent = error instanceof Error ? error.message : String(error);
        } finally {
          analyze.disabled = !currentAccessToken;
        }
      });
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = '删除附件';
      remove.disabled = !currentAccessToken;
      remove.addEventListener('click', async () => {
        if (!window.confirm('确定删除这个附件吗？已经生成的系统证据消息不会自动删除。')) return;
        await clientMediaApi(`/api/v1/media/${encodeURIComponent(item.id)}`, {method: 'DELETE'});
        await clientLoadMediaAttachments();
      });
      actions.append(analyze, remove);
      row.append(meta, analysis, actions);
      list.appendChild(row);
    });
  }

  async function clientLoadMediaAttachments() {
    if (!selectedConversationId) {
      clientRenderMedia([]);
      return;
    }
    const items = await clientMediaApi(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/media`);
    clientRenderMedia(items);
  }

  async function clientUploadAndAnalyzeMedia() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    const input = byId('client-media-file');
    const file = input?.files?.[0];
    if (!file) throw new Error('请选择图片或视频');
    const form = new FormData();
    form.append('file', file);
    const sentAt = byId('client-media-sent-at')?.value || '';
    if (sentAt) form.append('sent_at', new Date(sentAt).toISOString());
    const status = byId('client-media-status');
    status.textContent = '正在上传媒体…';
    const created = await clientMediaApi(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/media`,
      {method: 'POST', body: form},
    );
    input.value = '';
    status.textContent = '上传完成，正在识别图片/视频内容…';
    try {
      await clientMediaApi(`/api/v1/media/${encodeURIComponent(created.id)}/analyze`, {method: 'POST'});
      status.textContent = '识别完成，结果已写入完整会话证据链。';
      await loadMessages();
      window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
        detail: {source: '媒体识别', conversation_id: selectedConversationId},
      }));
    } catch (error) {
      status.textContent = `附件已保存，但当前模型识别失败：${error instanceof Error ? error.message : String(error)}`;
    }
    await clientLoadMediaAttachments();
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

    const contentWorkspace = byId('conversation-content')?.querySelector(':scope > .workspace-grid');
    if (contentWorkspace && !byId('client-media-card')) {
      const card = document.createElement('section');
      card.id = 'client-media-card';
      card.className = 'workspace-card';
      card.innerHTML = `
        <h3>图片 / 视频</h3>
        <p class="note">上传聊天截图、照片、表情包或视频。系统会使用当前配置的多模态 LLM 识别内容；识别结果作为系统证据加入完整会话链路。</p>
        <div id="client-media-controls">
          <div>
            <label for="client-media-file">媒体文件</label>
            <input id="client-media-file" class="requires-auth" type="file" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime" disabled>
          </div>
          <div>
            <label for="client-media-sent-at">发送时间（可选）</label>
            <input id="client-media-sent-at" class="requires-auth" type="datetime-local" disabled>
          </div>
        </div>
        <div id="client-media-actions">
          <button id="client-upload-media" class="requires-auth client-primary-button" type="button" disabled>上传并识别</button>
          <button id="client-refresh-media" class="requires-auth" type="button" disabled>刷新附件</button>
        </div>
        <div id="client-media-status" class="status">选择会话后可上传图片或视频。</div>
        <div id="client-media-list" class="status">当前会话还没有图片或视频。</div>
      `;
      contentWorkspace.appendChild(card);
      bind('client-upload-media', clientUploadAndAnalyzeMedia, byId('client-media-status'));
      bind('client-refresh-media', clientLoadMediaAttachments, byId('client-media-status'));
    }
  }

  byId('conversation-select')?.addEventListener('change', async () => {
    try { await clientLoadMediaAttachments(); }
    catch (error) {
      const status = byId('client-media-status');
      if (status) status.textContent = error instanceof Error ? error.message : String(error);
    }
  });

  clientInstallConversationControls();
'''
