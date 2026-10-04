REFERENCE_CONTEXT_STYLE = r'''
    #reference-context-settings {
      grid-column: 1 / -1;
      min-width: 0;
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
      align-content: start;
      gap: 10px;
      margin-top: 12px;
      min-height: 360px;
      height: 60vh;
      max-height: 80vh;
      overflow: auto;
      resize: vertical;
      padding: 4px 8px 12px 0;
      white-space: normal;
    }

    #reference-batch-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 12px 0; }
    #reference-batch-toolbar button { margin: 0 !important; }
    #reference-batch-toolbar select { width: auto; max-width: 100%; }
    #reference-list .reference-select { flex: 0 0 auto; width: auto; margin: 0; }
    #reference-list .reference-title { flex: 1; }
    #reference-list .reference-head { justify-content: flex-start; }
    #reference-list .reference-item-settings summary { cursor: pointer; padding: 8px 0; }
    #reference-list .reference-item-settings[open] { padding-bottom: 8px; }
    #reference-selected-count { margin: 8px 0; }
    #reference-list .reference-row[hidden] { display: none !important; }
    #reference-list .reference-head { flex-wrap: wrap; }
    #reference-list .reference-row { min-width: 0; }
    #reference-list .reference-filename { overflow-wrap: anywhere; color: #475569; }
    #reference-list .reference-reader summary { cursor: pointer; padding: 10px 0; font-weight: 700; }
    #reference-list .reference-fulltext {
      box-sizing: border-box;
      width: 100%;
      height: 45vh;
      min-height: 200px;
      max-height: 70vh;
      overflow: auto;
      resize: vertical;
      padding: 16px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      background: #fff;
      color: #1e293b;
      font: 14px/1.8 system-ui, sans-serif;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    #reference-search { box-sizing: border-box; width: 100%; margin-top: 8px; }
    #reference-filter-count { margin: 8px 0; color: #475569; }
    @media (max-width: 600px) {
      #reference-context-settings { padding: 10px; }
      #reference-list { min-height: 260px; height: 55vh; }
      #reference-list .reference-fulltext { padding: 10px; }
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
      max-height: 10em;
      overflow: auto;
      color: #64748b;
      font-size: .9rem;
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
  let referenceBatchBusy = false;

  function clientFilterReferences() {
    const query = (byId('reference-search')?.value || '').trim().toLocaleLowerCase();
    const rows = Array.from(byId('reference-list')?.querySelectorAll('.reference-row') || []);
    let visible = 0;
    rows.forEach((row) => {
      const type = byId('reference-type-filter')?.value || 'all';
      row.hidden = !row.dataset.searchText.includes(query) || (type !== 'all' && row.dataset.referenceType !== type);
      if (!row.hidden) visible += 1;
    });
    const count = byId('reference-filter-count');
    if (count) count.textContent = rows.length
      ? `显示 ${visible} / ${rows.length} 个文件${visible ? '' : '，没有匹配的文件'}`
      : '暂无文件';
    clientReferenceSelectionChanged();
  }

  function clientReferenceSelectionChanged() {
    const selected = Array.from(document.querySelectorAll('#reference-list .reference-select:checked'));
    const hidden = selected.filter((input) => input.closest('.reference-row').hidden).length;
    const count = byId('reference-selected-count');
    if (count) count.textContent = `已选 ${selected.length} 项${hidden ? `（其中 ${hidden} 项不在当前筛选中）` : ''}`;
    document.querySelectorAll('[data-reference-batch]').forEach((button) => {
      button.disabled = referenceBatchBusy || !currentAccessToken || !selected.length;
    });
  }

  function clientReferenceSelectVisible(mode) {
    document.querySelectorAll('#reference-list .reference-row').forEach((row) => {
      const input = row.querySelector('.reference-select');
      if (mode === 'clear') input.checked = false;
      else if (!row.hidden) input.checked = mode === 'all' ? true : !input.checked;
    });
    clientReferenceSelectionChanged();
  }

  async function clientReferenceBatch(action) {
    if (referenceBatchBusy) return;
    const ids = Array.from(document.querySelectorAll('#reference-list .reference-select:checked'))
      .map((input) => input.closest('.reference-row').dataset.referenceId);
    if (!ids.length) return;
    const scope = action === 'delete' ? 'global' : byId('reference-batch-scope').value;
    const conversation = selectedConversationId;
    const token = currentAccessToken;
    const status = byId('reference-status');
    if (scope === 'conversation' && !conversation) {
      status.textContent = '请先选择会话。'; return;
    }
    if (action === 'inherit' && scope !== 'conversation') {
      status.textContent = '恢复跟随全局仅适用于当前会话。'; return;
    }
    if (ids.length > 500) { status.textContent = '每次最多操作 500 项，请缩小选择范围。'; return; }
    if (action === 'delete' && !window.confirm(`确定永久删除选中的 ${ids.length} 个文档 / Skill？包含当前筛选隐藏的选中项；删除后所有会话都无法再使用这些资料。`)) return;
    referenceBatchBusy = true;
    const controls = Array.from(document.querySelectorAll('#reference-context-settings input, #reference-context-settings select, #reference-context-settings button, #conversation-select'));
    const previous = controls.map((control) => control.disabled);
    controls.forEach((control) => { control.disabled = true; });
    status.textContent = `正在处理 ${ids.length} 项…`;
    try {
      const result = await clientReferenceApi('/api/v1/references/batch', {
        method: 'POST',
        body: JSON.stringify({reference_ids: ids, action, scope, conversation_id: scope === 'conversation' ? conversation : null}),
      });
      if (token !== currentAccessToken || conversation !== selectedConversationId) return;
      await clientLoadReferences();
      status.textContent = `已完成 ${result.updated_count} 项批量操作。下一次分析或回复使用更新后的设置。`;
    } catch (error) {
      if (token === currentAccessToken) status.textContent = `批量操作未确认成功：${error instanceof Error ? error.message : String(error)}。可刷新核对状态。`;
    } finally {
      referenceBatchBusy = false;
      controls.forEach((control, index) => { control.disabled = token === currentAccessToken ? previous[index] : true; });
      clientReferenceSelectionChanged();
    }
  }

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
      clientFilterReferences();
      return;
    }

    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'reference-row';
      row.dataset.referenceId = item.id;
      row.dataset.referenceType = item.reference_type;
      row.dataset.searchText = [item.name, item.original_filename, item.description].filter(Boolean).join(' ').toLocaleLowerCase();

      const head = document.createElement('div');
      head.className = 'reference-head';
      const title = document.createElement('div');
      title.className = 'reference-title';
      title.textContent = item.original_filename || item.name;
      title.title = item.name;
      const select = document.createElement('input');
      select.type = 'checkbox';
      select.className = 'reference-select requires-auth';
      select.disabled = !currentAccessToken;
      select.setAttribute('aria-label', `选择 ${item.original_filename || item.name}`);
      select.addEventListener('change', clientReferenceSelectionChanged);
      const badge = document.createElement('span');
      badge.className = 'reference-badge';
      badge.textContent = item.reference_type === 'skill' ? 'SKILL · 方法约束' : 'DOCUMENT · 参考资料';
      head.append(select, title);

      const filename = document.createElement('div');
      filename.className = 'reference-filename';
      filename.textContent = `${item.original_filename || item.name} · ${item.content_chars || 0} 字符`;
      const reader = document.createElement('details');
      reader.className = 'reference-reader';
      const summary = document.createElement('summary');
      summary.textContent = '展开全文';
      const fulltext = document.createElement('pre');
      fulltext.className = 'reference-fulltext';
      fulltext.tabIndex = 0;
      fulltext.setAttribute('aria-label', `${item.name} 全文`);
      let readSequence = 0;
      reader.append(summary, fulltext);
      reader.addEventListener('toggle', async () => {
        const sequence = ++readSequence;
        summary.textContent = reader.open ? '收起全文' : '展开全文';
        fulltext.textContent = '';
        if (!reader.open) return;
        const token = currentAccessToken;
        fulltext.textContent = '正在加载全文…';
        try {
          const data = await clientReferenceApi(`/api/v1/references/${encodeURIComponent(item.id)}/content`);
          if (sequence === readSequence && reader.open && row.isConnected && token === currentAccessToken) {
            fulltext.textContent = data.content || '(内容为空)';
          }
        } catch (error) {
          if (sequence === readSequence && reader.open && row.isConnected && token === currentAccessToken) {
            fulltext.textContent = `加载失败：${error instanceof Error ? error.message : String(error)}。请收起后重新展开。`;
          }
        }
      });

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

      const settings = document.createElement('details');
      settings.className = 'reference-item-settings';
      const settingsSummary = document.createElement('summary');
      settingsSummary.textContent = '设置';
      settings.append(settingsSummary, badge, filename, meta, detail);
      row.append(head, reader, settings);
      list.appendChild(row);
    });
    clientFilterReferences();
  }

  async function clientLoadReferences() {
    const status = byId('reference-status');
    if (!currentAccessToken) {
      clientRenderReferences([]);
      if (status) status.textContent = '登录后可以管理参考资料与 Skills。';
      return [];
    }
    const token = currentAccessToken;
    const conversation = selectedConversationId;
    const items = await clientReferenceApi(`/api/v1/references${clientReferenceConversationQuery()}`);
    if (token !== currentAccessToken || conversation !== selectedConversationId) return [];
    clientRenderReferences(items);
    const scope = byId('reference-batch-scope');
    if (scope) {
      scope.querySelector('option[value="conversation"]').disabled = !selectedConversationId;
      if (!selectedConversationId) scope.value = 'global';
    }
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
    list.setAttribute('role', 'region');
    list.setAttribute('aria-label', '已上传的参考资料');
    list.tabIndex = 0;
    list.textContent = '还没有参考资料或 Skill。';

    const searchLabel = document.createElement('label');
    searchLabel.htmlFor = 'reference-search';
    searchLabel.textContent = '查找已上传文件';
    const search = document.createElement('input');
    search.id = 'reference-search';
    search.type = 'search';
    search.placeholder = '输入文件名或说明';
    search.addEventListener('input', clientFilterReferences);
    const count = document.createElement('div');
    count.id = 'reference-filter-count';
    count.setAttribute('aria-live', 'polite');
    count.textContent = '暂无文件';
    const typeFilter = document.createElement('select');
    typeFilter.id = 'reference-type-filter';
    typeFilter.setAttribute('aria-label', '文件类型筛选');
    [['all', '全部类型'], ['document', '只看文档'], ['skill', '只看 Skill']].forEach(([value, label]) => {
      const option = document.createElement('option'); option.value = value; option.textContent = label; typeFilter.append(option);
    });
    typeFilter.addEventListener('change', clientFilterReferences);
    const toolbar = document.createElement('div');
    toolbar.id = 'reference-batch-toolbar';
    [['all', '全选当前结果'], ['invert', '反选当前结果'], ['clear', '清空全部选择']].forEach(([mode, label]) => {
      const button = document.createElement('button');
      button.type = 'button'; button.id = `reference-select-${mode}`; button.textContent = label;
      button.addEventListener('click', () => clientReferenceSelectVisible(mode));
      toolbar.append(button);
    });
    const scopeLabel = document.createElement('label');
    scopeLabel.htmlFor = 'reference-batch-scope'; scopeLabel.textContent = '启用 / 禁用作用范围';
    const scope = document.createElement('select');
    scope.id = 'reference-batch-scope';
    [['conversation', '当前会话'], ['global', '全局默认']].forEach(([value, label]) => {
      const option = document.createElement('option'); option.value = value; option.textContent = label;
      option.disabled = value === 'conversation' && !selectedConversationId; scope.append(option);
    });
    scope.value = selectedConversationId ? 'conversation' : 'global';
    toolbar.append(scopeLabel, scope);
    [['enable', '批量启用'], ['disable', '批量禁用'], ['inherit', '恢复跟随全局'], ['delete', '删除选中资料']].forEach(([action, label]) => {
      const button = document.createElement('button'); button.type = 'button';
      button.id = `reference-batch-${action}`; button.dataset.referenceBatch = action;
      button.textContent = label; button.disabled = true;
      button.addEventListener('click', () => clientReferenceBatch(action)); toolbar.append(button);
    });
    const selectedCount = document.createElement('div');
    selectedCount.id = 'reference-selected-count'; selectedCount.setAttribute('aria-live', 'polite');
    selectedCount.textContent = '已选 0 项';
    section.append(heading, note, grid, actions, status, searchLabel, search, typeFilter, count, toolbar, selectedCount, list);
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
