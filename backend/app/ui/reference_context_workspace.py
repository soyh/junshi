REFERENCE_CONTEXT_STYLE = r'''
    #reference-context-settings {
      margin-top: 18px;
      padding: 16px;
      border: 1px solid rgba(25, 167, 232, .20);
      border-radius: 16px;
      background:
        radial-gradient(circle at 92% 0%, rgba(88, 200, 245, .12), transparent 18rem),
        rgba(247, 252, 255, .82);
    }

    #reference-context-settings h3 {
      margin: 0 0 6px;
      color: var(--sky-900, #0b2f50);
      font-size: 1rem;
    }

    #reference-context-settings .reference-note {
      margin: 0 0 12px;
      color: #64748b;
      font-size: .82rem;
      line-height: 1.55;
    }

    #reference-upload-grid {
      display: grid;
      grid-template-columns: minmax(180px, .7fr) minmax(240px, 1.4fr) minmax(110px, .45fr);
      gap: 10px 12px;
      align-items: end;
    }

    #reference-upload-grid .reference-wide { grid-column: 1 / -1; }

    #reference-upload-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    #reference-upload-actions button { margin: 0 !important; }

    #reference-list {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    #reference-list .reference-row {
      padding: 12px;
      border: 1px solid rgba(25, 167, 232, .14);
      border-radius: 13px;
      background: rgba(255, 255, 255, .82);
    }

    #reference-list .reference-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 7px;
    }

    #reference-list .reference-title {
      min-width: 0;
      font-weight: 800;
      color: var(--sky-900, #0b2f50);
      overflow-wrap: anywhere;
    }

    #reference-list .reference-badge {
      display: inline-flex;
      align-items: center;
      flex: 0 0 auto;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: .72rem;
      font-weight: 800;
      color: var(--sky-800, #075985);
      background: rgba(25, 167, 232, .10);
      border: 1px solid rgba(25, 167, 232, .16);
    }

    #reference-list .reference-preview {
      max-height: 4.8em;
      overflow: hidden;
      color: #64748b;
      font-size: .78rem;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    #reference-list .reference-meta-grid {
      display: grid;
      grid-template-columns: minmax(150px, .7fr) minmax(140px, .55fr) minmax(190px, .8fr) auto;
      gap: 8px 10px;
      align-items: end;
      margin-top: 10px;
    }

    #reference-list .reference-inline-check {
      display: flex;
      align-items: center;
      gap: 7px;
      min-height: 42px;
    }

    #reference-list .reference-inline-check input { width: auto; }
    #reference-list button { margin: 0 !important; }

    @media (max-width: 820px) {
      #reference-upload-grid,
      #reference-list .reference-meta-grid {
        grid-template-columns: 1fr;
      }
      #reference-upload-grid .reference-wide { grid-column: auto; }
    }
'''


REFERENCE_CONTEXT_SCRIPT = r'''
  async function clientReferenceApi(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${requireToken()}`);
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
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

  function clientReferenceConversationQuery() {
    return selectedConversationId
      ? `?conversation_id=${encodeURIComponent(selectedConversationId)}`
      : '';
  }

  function clientReferenceEffectiveText(item) {
    if (item.override_enabled === true) return '当前会话：强制启用';
    if (item.override_enabled === false) return '当前会话：强制禁用';
    return item.enabled_by_default ? '继承全局：启用' : '继承全局：禁用';
  }

  function clientRenderReferences(items) {
    const list = byId('reference-list');
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(items) || !items.length) {
      list.textContent = '还没有参考资料或 Skill。';
      return;
    }

    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'reference-row';
      row.dataset.referenceId = item.id;

      const head = document.createElement('div');
      head.className = 'reference-head';
      const title = document.createElement('div');
      title.className = 'reference-title';
      title.textContent = item.name;
      const badge = document.createElement('span');
      badge.className = 'reference-badge';
      badge.textContent = item.reference_type === 'skill' ? 'SKILL · 方法约束' : 'DOCUMENT · 参考资料';
      head.append(title, badge);

      const preview = document.createElement('div');
      preview.className = 'reference-preview';
      preview.textContent = item.content_preview || '(无预览)';

      const meta = document.createElement('div');
      meta.className = 'reference-meta-grid';

      const globalWrap = document.createElement('label');
      globalWrap.className = 'reference-inline-check';
      const globalEnabled = document.createElement('input');
      globalEnabled.type = 'checkbox';
      globalEnabled.checked = Boolean(item.enabled_by_default);
      globalEnabled.className = 'requires-auth';
      globalEnabled.disabled = !currentAccessToken;
      globalWrap.append(globalEnabled, document.createTextNode('全局默认启用'));

      const priorityWrap = document.createElement('div');
      const priorityLabel = document.createElement('label');
      priorityLabel.textContent = '全局优先级';
      const priority = document.createElement('input');
      priority.type = 'number';
      priority.min = '0';
      priority.max = '10000';
      priority.value = String(item.priority ?? 100);
      priority.className = 'requires-auth';
      priority.disabled = !currentAccessToken;
      priorityWrap.append(priorityLabel, priority);

      const overrideWrap = document.createElement('div');
      const overrideLabel = document.createElement('label');
      overrideLabel.textContent = selectedConversationId ? '当前会话' : '当前会话';
      const override = document.createElement('select');
      override.className = 'requires-auth';
      override.disabled = !currentAccessToken || !selectedConversationId;
      [
        ['inherit', '跟随全局'],
        ['enable', '当前会话启用'],
        ['disable', '当前会话禁用'],
      ].forEach(([value, label]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        override.appendChild(option);
      });
      override.value = item.override_enabled === true
        ? 'enable'
        : item.override_enabled === false
          ? 'disable'
          : 'inherit';
      override.title = selectedConversationId
        ? clientReferenceEffectiveText(item)
        : '选择会话后可覆盖全局启用状态';
      overrideWrap.append(overrideLabel, override);

      const actions = document.createElement('div');
      actions.style.display = 'flex';
      actions.style.gap = '7px';
      actions.style.flexWrap = 'wrap';
      const save = document.createElement('button');
      save.type = 'button';
      save.className = 'requires-auth';
      save.disabled = !currentAccessToken;
      save.textContent = '保存';
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'requires-auth';
      remove.disabled = !currentAccessToken;
      remove.textContent = '删除';
      actions.append(save, remove);
      meta.append(globalWrap, priorityWrap, overrideWrap, actions);

      const detail = document.createElement('div');
      detail.className = 'reference-note';
      detail.style.marginTop = '8px';
      detail.textContent = `${clientReferenceEffectiveText(item)} · ${item.content_chars || 0} 字符 · effective priority ${item.effective_priority}`;

      save.addEventListener('click', async () => {
        const status = byId('reference-status');
        try {
          save.disabled = true;
          await clientReferenceApi(`/api/v1/references/${encodeURIComponent(item.id)}`, {
            method: 'PATCH',
            body: JSON.stringify({
              enabled_by_default: globalEnabled.checked,
              priority: Number(priority.value || 100),
            }),
          });

          if (selectedConversationId) {
            if (override.value === 'inherit') {
              await clientReferenceApi(
                `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/references/${encodeURIComponent(item.id)}/override`,
                {method: 'DELETE'},
              );
            } else {
              await clientReferenceApi(
                `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/references/${encodeURIComponent(item.id)}`,
                {
                  method: 'PUT',
                  body: JSON.stringify({enabled: override.value === 'enable'}),
                },
              );
            }
          }
          await clientLoadReferences();
          status.textContent = '参考项设置已保存。下一次分析/回复会使用新的有效集合。';
        } catch (error) {
          status.textContent = error instanceof Error ? error.message : String(error);
        } finally {
          save.disabled = !currentAccessToken;
        }
      });

      remove.addEventListener('click', async () => {
        if (!window.confirm(`确定删除参考项“${item.name}”吗？`)) return;
        const status = byId('reference-status');
        try {
          remove.disabled = true;
          await clientReferenceApi(`/api/v1/references/${encodeURIComponent(item.id)}`, {method: 'DELETE'});
          await clientLoadReferences();
          status.textContent = '参考项已删除。';
        } catch (error) {
          status.textContent = error instanceof Error ? error.message : String(error);
        } finally {
          remove.disabled = !currentAccessToken;
        }
      });

      row.append(head, preview, meta, detail);
      list.appendChild(row);
    });
  }

  async function clientLoadReferences() {
    const status = byId('reference-status');
    if (!currentAccessToken) {
      clientRenderReferences([]);
      if (status) status.textContent = '登录后可以管理参考资料与 Skills。';
      return [];
    }
    const items = await clientReferenceApi(`/api/v1/references${clientReferenceConversationQuery()}`);
    clientRenderReferences(items);
    const enabled = items.filter((item) => item.effective_enabled).length;
    if (status) {
      status.textContent = selectedConversationId
        ? `当前会话有效 ${enabled} / ${items.length} 项参考。Skill 约束方法，Document 提供二级参考。`
        : `全局共有 ${items.length} 项参考；选择会话后可设置会话级覆盖。`;
    }
    return items;
  }

  async function clientUploadReferences() {
    const input = byId('reference-files');
    const files = Array.from(input?.files || []);
    if (!files.length) throw new Error('请选择一个或多个文档 / Skill 文件');
    const type = byId('reference-upload-type')?.value || 'auto';
    const priority = Number(byId('reference-upload-priority')?.value || 100);
    const description = byId('reference-upload-description')?.value?.trim() || '';
    const enabled = Boolean(byId('reference-upload-enabled')?.checked);
    const status = byId('reference-status');

    let completed = 0;
    for (let index = 0; index < files.length; index += 1) {
      const file = files[index];
      status.textContent = `正在上传 ${index + 1}/${files.length}：${file.name}`;
      const form = new FormData();
      form.append('file', file, file.name);
      form.append('reference_type', type);
      form.append('priority', String(priority));
      form.append('enabled_by_default', enabled ? 'true' : 'false');
      if (description) form.append('description', description);
      await clientReferenceApi('/api/v1/references', {method: 'POST', body: form});
      completed += 1;
    }
    input.value = '';
    await clientLoadReferences();
    status.textContent = `已上传 ${completed} 个参考项；可同时启用多文档、多 Skill 或混合参考。`;
  }

  function installReferenceContextSettings() {
    const provider = byId('provider');
    if (!provider || byId('reference-context-settings')) return;

    const section = document.createElement('section');
    section.id = 'reference-context-settings';

    const heading = document.createElement('h3');
    heading.textContent = '参考资料 / Skills';
    const note = document.createElement('p');
    note.className = 'reference-note';
    note.textContent = '可同时启用多个文档、多个 Skill，或混合参考。Skill 只约束分析方法、优先级和表达方向；Document 作为二级参考背景。它们都不能覆盖系统安全、用户隔离、canonical evidence、用户确认或执行边界。原始图片/视频取证保持中立，参考项进入后续分析与回复推理。';

    const grid = document.createElement('div');
    grid.id = 'reference-upload-grid';

    const typeWrap = document.createElement('div');
    const typeLabel = document.createElement('label');
    typeLabel.htmlFor = 'reference-upload-type';
    typeLabel.textContent = '上传类型';
    const type = document.createElement('select');
    type.id = 'reference-upload-type';
    [
      ['auto', '自动判断（推荐）'],
      ['document', 'Document'],
      ['skill', 'Skill'],
    ].forEach(([value, label]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      type.appendChild(option);
    });
    typeWrap.append(typeLabel, type);

    const fileWrap = document.createElement('div');
    const fileLabel = document.createElement('label');
    fileLabel.htmlFor = 'reference-files';
    fileLabel.textContent = '选择文档 / Skill（可多选）';
    const files = document.createElement('input');
    files.id = 'reference-files';
    files.type = 'file';
    files.multiple = true;
    files.accept = '.txt,.md,.markdown,.json,.csv,.yaml,.yml,.docx,.skill,.zip,text/plain,text/markdown,application/json,text/csv,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/zip';
    files.className = 'requires-auth';
    files.disabled = !currentAccessToken;
    fileWrap.append(fileLabel, files);

    const priorityWrap = document.createElement('div');
    const priorityLabel = document.createElement('label');
    priorityLabel.htmlFor = 'reference-upload-priority';
    priorityLabel.textContent = '优先级（小值先）';
    const priority = document.createElement('input');
    priority.id = 'reference-upload-priority';
    priority.type = 'number';
    priority.min = '0';
    priority.max = '10000';
    priority.value = '100';
    priorityWrap.append(priorityLabel, priority);

    const descriptionWrap = document.createElement('div');
    descriptionWrap.className = 'reference-wide';
    const descriptionLabel = document.createElement('label');
    descriptionLabel.htmlFor = 'reference-upload-description';
    descriptionLabel.textContent = '说明（可选，同一批文件共用）';
    const description = document.createElement('input');
    description.id = 'reference-upload-description';
    description.type = 'text';
    description.placeholder = '例如：依恋理论分析框架 / 我的沟通原则 / 项目背景资料';
    descriptionWrap.append(descriptionLabel, description);

    const enabledWrap = document.createElement('label');
    enabledWrap.className = 'reference-wide';
    enabledWrap.style.display = 'flex';
    enabledWrap.style.alignItems = 'center';
    enabledWrap.style.gap = '7px';
    const enabled = document.createElement('input');
    enabled.id = 'reference-upload-enabled';
    enabled.type = 'checkbox';
    enabled.checked = true;
    enabled.style.width = 'auto';
    enabledWrap.append(enabled, document.createTextNode('上传后全局默认启用'));

    grid.append(typeWrap, fileWrap, priorityWrap, descriptionWrap, enabledWrap);

    const actions = document.createElement('div');
    actions.id = 'reference-upload-actions';
    const upload = document.createElement('button');
    upload.id = 'reference-upload';
    upload.type = 'button';
    upload.className = 'requires-auth client-primary-button';
    upload.disabled = !currentAccessToken;
    upload.textContent = '上传参考项';
    const refresh = document.createElement('button');
    refresh.id = 'reference-refresh';
    refresh.type = 'button';
    refresh.className = 'requires-auth';
    refresh.disabled = !currentAccessToken;
    refresh.textContent = '刷新';
    actions.append(upload, refresh);

    const status = document.createElement('div');
    status.id = 'reference-status';
    status.className = 'status';
    status.textContent = '支持 UTF-8 文本、Markdown、JSON、CSV、YAML、DOCX、.skill，以及包含 SKILL.md 的 Skill ZIP。';

    const list = document.createElement('div');
    list.id = 'reference-list';
    list.className = 'status';
    list.textContent = '还没有参考资料或 Skill。';

    section.append(heading, note, grid, actions, status, list);
    provider.appendChild(section);

    upload.addEventListener('click', async () => {
      upload.disabled = true;
      try { await clientUploadReferences(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
      finally { upload.disabled = !currentAccessToken; }
    });
    refresh.addEventListener('click', async () => {
      try { await clientLoadReferences(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
    byId('conversation-select')?.addEventListener('change', async () => {
      try { await clientLoadReferences(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });

    if (currentAccessToken) {
      clientLoadReferences().catch((error) => {
        status.textContent = error instanceof Error ? error.message : String(error);
      });
    }
  }

  installReferenceContextSettings();
'''
