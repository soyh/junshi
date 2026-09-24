MEDIA_UPLOAD_WORKSPACE_STYLE = r'''
    #client-media-import-card {
      grid-column: 1 / -1;
      padding: 16px !important;
    }

    #client-media-import-card h2 {
      margin: 0 0 6px;
      color: #26344d;
      font-size: 1.05rem;
    }

    #client-media-import-card .client-media-note {
      margin: 0 0 12px;
      color: #718096;
      font-size: .84rem;
      line-height: 1.55;
    }

    #client-media-controls {
      display: grid;
      grid-template-columns: minmax(260px, 1fr) minmax(220px, .65fr);
      gap: 10px 14px;
      align-items: end;
    }

    #client-media-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    #client-media-actions button { margin: 0 !important; }

    #client-media-list {
      margin-top: 10px;
      max-height: 260px;
      overflow-y: auto;
    }

    #client-media-list .client-media-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px 12px;
      align-items: center;
      padding: 9px 0;
      border-bottom: 1px solid rgba(127,127,127,.18);
    }

    #client-media-list .client-media-row:last-child { border-bottom: 0; }
    #client-media-list .client-media-meta { min-width: 0; }
    #client-media-list .client-media-title { font-weight: 800; overflow-wrap: anywhere; }
    #client-media-list .client-media-detail { margin-top: 3px; color: #718096; font-size: .78rem; }
    #client-media-list button { margin: 0 !important; }

    @media (max-width: 760px) {
      #client-media-controls { grid-template-columns: 1fr; }
    }
'''


MEDIA_UPLOAD_WORKSPACE_SCRIPT = r'''
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
      const error = new Error(typeof detail === 'string' ? detail : `HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function clientRenderMedia(items) {
    const list = byId('client-media-list');
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      list.textContent = '当前会话还没有图片或视频附件。';
      return;
    }

    items.slice().reverse().forEach((item) => {
      const row = document.createElement('div');
      row.className = 'client-media-row';

      const meta = document.createElement('div');
      meta.className = 'client-media-meta';
      const title = document.createElement('div');
      title.className = 'client-media-title';
      title.textContent = item.original_filename || `${item.media_type || 'media'} attachment`;
      const detail = document.createElement('div');
      detail.className = 'client-media-detail';
      const evidence = item.message_id ? '已写入会话证据' : '尚未生成会话证据';
      detail.textContent = `${item.media_type || 'media'} · ${item.analysis_status || 'unknown'} · ${evidence}`;
      meta.append(title, detail);

      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'requires-auth';
      remove.disabled = !currentAccessToken;
      remove.textContent = '删除附件';
      remove.addEventListener('click', async () => {
        if (!window.confirm(`确定删除附件“${item.original_filename || item.id}”及其媒体证据吗？`)) return;
        const conversationId = selectedConversationId;
        try {
          await api(`/api/v1/media/${encodeURIComponent(item.id)}`, {method: 'DELETE'});
          await clientLoadMedia();
          if (typeof loadMessages === 'function') await loadMessages(currentMessageWindow || {});
          const status = byId('client-media-status');
          if (status) status.textContent = '附件及其关联媒体证据已删除。';
          window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
            detail: {source: '媒体证据删除', conversation_id: conversationId},
          }));
        } catch (error) {
          const status = byId('client-media-status');
          status.textContent = error instanceof Error ? error.message : String(error);
        }
      });

      row.append(meta, remove);
      list.appendChild(row);
    });
  }

  async function clientLoadMedia() {
    const status = byId('client-media-status');
    if (!selectedConversationId) {
      if (status) status.textContent = '请先选择会话。';
      clientRenderMedia([]);
      return [];
    }
    const items = await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/media`);
    clientRenderMedia(items);
    if (status) status.textContent = `当前会话共有 ${items.length} 个图片/视频附件。`;
    return items;
  }

  async function clientUploadAndAnalyzeMedia() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    const input = byId('client-media-file');
    const sentAtInput = byId('client-media-sent-at');
    const status = byId('client-media-status');
    const files = Array.from(input?.files || []);
    if (files.length === 0) throw new Error('请选择聊天截图、图片或视频');

    const conversationId = selectedConversationId;
    let completed = 0;
    for (let index = 0; index < files.length; index += 1) {
      const file = files[index];
      status.textContent = `正在上传 ${index + 1}/${files.length}：${file.name}`;
      const form = new FormData();
      form.append('file', file, file.name);
      const sentAt = sentAtInput?.value?.trim();
      if (sentAt) form.append('sent_at', sentAt);

      const attachment = await clientMediaApi(
        `/api/v1/conversations/${encodeURIComponent(conversationId)}/media`,
        {method: 'POST', body: form},
      );

      status.textContent = `正在使用视觉模型识别 ${index + 1}/${files.length}：${file.name}`;
      await api(`/api/v1/media/${encodeURIComponent(attachment.id)}/analyze`, {method: 'POST'});
      completed += 1;
    }

    input.value = '';
    if (sentAtInput) sentAtInput.value = '';
    await clientLoadMedia();
    if (typeof loadMessages === 'function') await loadMessages(currentMessageWindow || {});
    status.textContent = `已完成 ${completed} 个附件的上传与视觉识别；识别结果已作为媒体证据加入当前会话。`;
    window.dispatchEvent(new CustomEvent('junshi:evidence-changed', {
      detail: {source: '媒体证据', conversation_id: conversationId},
    }));
  }

  function clientInstallMediaUpload() {
    const content = byId('conversation-content');
    const workspace = content ? content.querySelector(':scope > .workspace-grid') : null;
    if (!content || !workspace || byId('client-media-import-card')) return;

    const card = document.createElement('section');
    card.id = 'client-media-import-card';
    card.className = 'workspace-card';

    const heading = document.createElement('h2');
    heading.textContent = '聊天截图 / 图片 / 视频';

    const note = document.createElement('p');
    note.className = 'client-media-note';
    note.textContent = '可一次选择多张聊天截图、普通图片或视频。系统使用独立视觉模型识别可见文字、表情和互动线索；结果作为“媒体证据”写入当前会话。不会自动猜测截图中无法可靠确定的发言人或发送时间。视频当前按关键帧进行视觉分析。';

    const controls = document.createElement('div');
    controls.id = 'client-media-controls';

    const fileWrap = document.createElement('div');
    const fileLabel = document.createElement('label');
    fileLabel.htmlFor = 'client-media-file';
    fileLabel.textContent = '选择图片 / 视频';
    const fileInput = document.createElement('input');
    fileInput.id = 'client-media-file';
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.accept = 'image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime';
    fileInput.className = 'requires-auth';
    fileInput.disabled = !currentAccessToken;
    fileWrap.append(fileLabel, fileInput);

    const sentAtWrap = document.createElement('div');
    const sentAtLabel = document.createElement('label');
    sentAtLabel.htmlFor = 'client-media-sent-at';
    sentAtLabel.textContent = '证据时间（可选 ISO 8601）';
    const sentAtInput = document.createElement('input');
    sentAtInput.id = 'client-media-sent-at';
    sentAtInput.placeholder = '2026-09-24T00:00:00+08:00';
    sentAtInput.autocomplete = 'off';
    sentAtInput.className = 'requires-auth';
    sentAtInput.disabled = !currentAccessToken;
    sentAtWrap.append(sentAtLabel, sentAtInput);

    controls.append(fileWrap, sentAtWrap);

    const actions = document.createElement('div');
    actions.id = 'client-media-actions';
    const upload = document.createElement('button');
    upload.id = 'client-media-upload';
    upload.type = 'button';
    upload.className = 'requires-auth client-primary-button';
    upload.disabled = !currentAccessToken;
    upload.textContent = '上传并识别';
    const refresh = document.createElement('button');
    refresh.id = 'client-media-refresh';
    refresh.type = 'button';
    refresh.className = 'requires-auth';
    refresh.disabled = !currentAccessToken;
    refresh.textContent = '刷新附件';
    actions.append(upload, refresh);

    const status = document.createElement('div');
    status.id = 'client-media-status';
    status.className = 'status';
    status.textContent = '选择会话后，可以上传聊天截图、图片或视频。';

    const list = document.createElement('div');
    list.id = 'client-media-list';
    list.className = 'status';
    list.textContent = '当前会话还没有图片或视频附件。';

    card.append(heading, note, controls, actions, status, list);

    const unified = byId('client-unified-import-card');
    if (unified && unified.parentElement === workspace) unified.insertAdjacentElement('afterend', card);
    else workspace.prepend(card);

    upload.addEventListener('click', async () => {
      upload.disabled = true;
      try { await clientUploadAndAnalyzeMedia(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
      finally { upload.disabled = !currentAccessToken; }
    });
    refresh.addEventListener('click', async () => {
      try { await clientLoadMedia(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });

    byId('conversation-select')?.addEventListener('change', async () => {
      try { await clientLoadMedia(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
  }

  clientInstallMediaUpload();
'''