MODEL_REFERENCE_WORKSPACE_STYLE = r'''
    #model-reference-library {
      width: 100%;
      min-width: 0;
    }

    #model-reference-library .reference-library-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 14px;
    }

    #model-reference-library .reference-library-head h2 {
      margin: 0 0 5px;
      color: var(--sky-900, #0b2f50);
      font-size: 1.08rem;
    }

    #model-reference-library .reference-library-note {
      margin: 0;
      max-width: 860px;
      color: #61758a;
      font-size: .83rem;
      line-height: 1.6;
    }

    #model-reference-upload {
      display: grid;
      grid-template-columns: minmax(260px, 1fr) minmax(180px, .38fr) auto;
      gap: 10px;
      align-items: end;
      padding: 13px;
      border: 1px solid rgba(25, 167, 232, .16);
      border-radius: 14px;
      background: rgba(236, 248, 255, .58);
    }

    #model-reference-upload button {
      margin: 0 !important;
      min-height: 42px;
    }

    #model-reference-summary {
      margin: 12px 0 8px;
      color: var(--sky-800, #075985);
      font-size: .82rem;
      font-weight: 700;
    }

    #model-reference-list {
      display: grid;
      gap: 8px;
    }

    #model-reference-list .reference-item {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) minmax(126px, .25fr) auto;
      gap: 10px;
      align-items: center;
      padding: 11px 12px;
      border: 1px solid rgba(25, 167, 232, .14);
      border-radius: 13px;
      background: rgba(255, 255, 255, .82);
    }

    #model-reference-list .reference-item-main {
      min-width: 0;
    }

    #model-reference-list .reference-item-title {
      overflow: hidden;
      color: #26344d;
      font-weight: 800;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    #model-reference-list .reference-item-meta,
    #model-reference-list .reference-item-preview {
      margin-top: 3px;
      color: #718096;
      font-size: .76rem;
      line-height: 1.45;
    }

    #model-reference-list .reference-item-preview {
      display: -webkit-box;
      overflow: hidden;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    #model-reference-list .reference-kind {
      min-width: 0;
      margin: 0;
    }

    #model-reference-list button {
      margin: 0 !important;
    }

    #model-reference-status {
      margin-top: 10px;
    }

    @media (max-width: 760px) {
      #model-reference-upload {
        grid-template-columns: 1fr;
      }

      #model-reference-list .reference-item {
        grid-template-columns: auto minmax(0, 1fr);
      }

      #model-reference-list .reference-kind,
      #model-reference-list .reference-delete {
        grid-column: 2;
      }
    }
'''


MODEL_REFERENCE_WORKSPACE_SCRIPT = r'''
  async function clientReferenceFetch(path, options = {}) {
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

  function clientReferenceTypeLabel(value) {
    return value === 'skill' ? 'Skill · 方法约束' : '文档 · 参考知识';
  }

  function clientRenderModelReferences(items) {
    const list = byId('model-reference-list');
    const summary = byId('model-reference-summary');
    if (!list || !summary) return;
    list.replaceChildren();

    const enabled = (items || []).filter((item) => item.enabled);
    const skills = enabled.filter((item) => item.asset_type === 'skill').length;
    const documents = enabled.filter((item) => item.asset_type === 'document').length;
    summary.textContent = `资料库 ${items.length} 项 · 当前启用 ${enabled.length} 项（Skill ${skills} / 文档 ${documents}）`;

    if (!items.length) {
      const empty = document.createElement('div');
      empty.className = 'status';
      empty.textContent = '尚未上传参考资料。可以一次选择多个文档、多个 Skill，或混合上传。';
      list.appendChild(empty);
      return;
    }

    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'reference-item';
      row.dataset.referenceId = item.id;

      const enabledToggle = document.createElement('input');
      enabledToggle.type = 'checkbox';
      enabledToggle.checked = Boolean(item.enabled);
      enabledToggle.className = 'requires-auth';
      enabledToggle.disabled = !currentAccessToken;
      enabledToggle.title = '启用后，该项会加入模型参考上下文';

      const main = document.createElement('div');
      main.className = 'reference-item-main';
      const title = document.createElement('div');
      title.className = 'reference-item-title';
      title.textContent = item.title || item.original_filename;
      title.title = item.title || item.original_filename;
      const meta = document.createElement('div');
      meta.className = 'reference-item-meta';
      meta.textContent = `${item.original_filename} · ${Number(item.char_count || 0).toLocaleString()} 字符 · ${clientReferenceTypeLabel(item.asset_type)}`;
      const preview = document.createElement('div');
      preview.className = 'reference-item-preview';
      preview.textContent = item.content_preview || '无预览文本';
      main.append(title, meta, preview);

      const kind = document.createElement('select');
      kind.className = 'reference-kind requires-auth';
      kind.disabled = !currentAccessToken;
      [['document', '作为文档参考'], ['skill', '作为 Skill 约束']].forEach(([value, label]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        kind.appendChild(option);
      });
      kind.value = item.asset_type;

      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'reference-delete requires-auth';
      remove.disabled = !currentAccessToken;
      remove.textContent = '删除';

      enabledToggle.addEventListener('change', async () => {
        const status = byId('model-reference-status');
        try {
          await api(`/api/v1/model-references/${encodeURIComponent(item.id)}`, {
            method: 'PATCH',
            body: JSON.stringify({enabled: enabledToggle.checked}),
          });
          await clientLoadModelReferences();
        } catch (error) {
          enabledToggle.checked = !enabledToggle.checked;
          status.textContent = error instanceof Error ? error.message : String(error);
        }
      });

      kind.addEventListener('change', async () => {
        const status = byId('model-reference-status');
        try {
          await api(`/api/v1/model-references/${encodeURIComponent(item.id)}`, {
            method: 'PATCH',
            body: JSON.stringify({asset_type: kind.value}),
          });
          await clientLoadModelReferences();
        } catch (error) {
          kind.value = item.asset_type;
          status.textContent = error instanceof Error ? error.message : String(error);
        }
      });

      remove.addEventListener('click', async () => {
        if (!window.confirm(`确定删除参考项“${item.title || item.original_filename}”吗？`)) return;
        const status = byId('model-reference-status');
        try {
          await api(`/api/v1/model-references/${encodeURIComponent(item.id)}`, {method: 'DELETE'});
          await clientLoadModelReferences();
        } catch (error) {
          status.textContent = error instanceof Error ? error.message : String(error);
        }
      });

      row.append(enabledToggle, main, kind, remove);
      list.appendChild(row);
    });
  }

  async function clientLoadModelReferences() {
    const status = byId('model-reference-status');
    if (!currentAccessToken) {
      clientRenderModelReferences([]);
      if (status) status.textContent = '登录后可管理参考文档与 Skills。';
      return [];
    }
    const items = await api('/api/v1/model-references');
    clientRenderModelReferences(Array.isArray(items) ? items : []);
    if (status) status.textContent = '所有已启用项会组合进入分析与回复模型上下文。';
    return items;
  }

  async function clientUploadModelReferences() {
    const input = byId('model-reference-files');
    const type = byId('model-reference-upload-type');
    const status = byId('model-reference-status');
    const files = Array.from(input?.files || []);
    if (!files.length) throw new Error('请选择至少一个文档或 Skill 文件');

    for (let index = 0; index < files.length; index += 1) {
      const file = files[index];
      status.textContent = `正在上传并提取 ${index + 1}/${files.length}：${file.name}`;
      const form = new FormData();
      form.append('file', file, file.name);
      form.append('asset_type', type?.value || 'auto');
      await clientReferenceFetch('/api/v1/model-references', {method: 'POST', body: form});
    }

    input.value = '';
    await clientLoadModelReferences();
    status.textContent = `已完成 ${files.length} 个参考项上传；默认启用，可逐项关闭或调整为文档 / Skill。`;
  }

  function clientActivateReferenceSettingsTab() {
    const tabs = byId('guided-settings-tabs');
    const panelHost = byId('guided-settings-panel-host');
    const referenceTab = byId('guided-settings-reference-tab');
    const referencePanel = byId('model-reference-library');
    if (!tabs || !panelHost || !referenceTab || !referencePanel) return;

    Array.from(tabs.querySelectorAll('.settings-tab-button')).forEach((tab) => {
      const active = tab === referenceTab;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.tabIndex = active ? 0 : -1;
    });
    Array.from(panelHost.children).forEach((panel) => {
      if (panel.tagName === 'FIELDSET') panel.hidden = panel !== referencePanel;
    });
    clientLoadModelReferences().catch((error) => {
      byId('model-reference-status').textContent = error instanceof Error ? error.message : String(error);
    });
  }

  function clientInstallModelReferenceLibrary() {
    const tabs = byId('guided-settings-tabs');
    const panelHost = byId('guided-settings-panel-host');
    if (!tabs || !panelHost || byId('model-reference-library')) return;

    const existingTabs = Array.from(tabs.querySelectorAll('.settings-tab-button'));
    const tab = document.createElement('button');
    tab.id = 'guided-settings-reference-tab';
    tab.type = 'button';
    tab.className = 'settings-tab-button';
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-selected', 'false');
    tab.setAttribute('aria-controls', 'model-reference-library');
    tab.tabIndex = -1;
    tab.textContent = '参考资料 / Skills';
    tab.title = '参考资料 / Skills';

    const panel = document.createElement('fieldset');
    panel.id = 'model-reference-library';
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', tab.id);
    panel.hidden = true;

    const head = document.createElement('div');
    head.className = 'reference-library-head';
    const headText = document.createElement('div');
    const heading = document.createElement('h2');
    heading.textContent = '模型参考资料与 Skills';
    const note = document.createElement('p');
    note.className = 'reference-library-note';
    note.textContent = '可同时启用多个文档、多个 Skill，或混合参考。Skill 用于约束分析方法、关注点和表达方式；文档作为参考知识。系统安全规则、当前真实会话与 canonical evidence 始终优先。上传的 Skill 仅作为文本指令读取，不会执行其中代码、脚本、工具或网络操作。';
    headText.append(heading, note);
    head.appendChild(headText);

    const uploadBox = document.createElement('div');
    uploadBox.id = 'model-reference-upload';
    const fileWrap = document.createElement('div');
    const fileLabel = document.createElement('label');
    fileLabel.htmlFor = 'model-reference-files';
    fileLabel.textContent = '文档 / Skill 文件（支持多选）';
    const files = document.createElement('input');
    files.id = 'model-reference-files';
    files.type = 'file';
    files.multiple = true;
    files.accept = '.pdf,.docx,.txt,.md,.markdown,.csv,.json,.yaml,.yml,.xml,.html,.htm,.skill,.prompt,.zip';
    files.className = 'requires-auth';
    files.disabled = !currentAccessToken;
    fileWrap.append(fileLabel, files);

    const typeWrap = document.createElement('div');
    const typeLabel = document.createElement('label');
    typeLabel.htmlFor = 'model-reference-upload-type';
    typeLabel.textContent = '上传类型';
    const type = document.createElement('select');
    type.id = 'model-reference-upload-type';
    type.className = 'requires-auth';
    type.disabled = !currentAccessToken;
    [['auto', '自动识别'], ['document', '全部作为文档'], ['skill', '全部作为 Skill']].forEach(([value, label]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      type.appendChild(option);
    });
    typeWrap.append(typeLabel, type);

    const upload = document.createElement('button');
    upload.id = 'model-reference-upload-button';
    upload.type = 'button';
    upload.className = 'requires-auth client-primary-button';
    upload.disabled = !currentAccessToken;
    upload.textContent = '上传并启用';
    uploadBox.append(fileWrap, typeWrap, upload);

    const summary = document.createElement('div');
    summary.id = 'model-reference-summary';
    summary.textContent = '资料库 0 项 · 当前启用 0 项';
    const list = document.createElement('div');
    list.id = 'model-reference-list';
    const status = document.createElement('div');
    status.id = 'model-reference-status';
    status.className = 'status';
    status.textContent = '登录后可上传参考资料。';

    panel.append(head, uploadBox, summary, list, status);
    tabs.appendChild(tab);
    panelHost.appendChild(panel);

    existingTabs.forEach((existingTab) => {
      existingTab.addEventListener('click', () => {
        panel.hidden = true;
        tab.setAttribute('aria-selected', 'false');
        tab.tabIndex = -1;
      });
    });

    tab.addEventListener('click', clientActivateReferenceSettingsTab);
    tab.addEventListener('keydown', (event) => {
      if (event.key === 'Home' && existingTabs.length) {
        event.preventDefault();
        existingTabs[0].click();
        existingTabs[0].focus();
      } else if (event.key === 'ArrowLeft' && existingTabs.length) {
        event.preventDefault();
        const previous = existingTabs[existingTabs.length - 1];
        previous.click();
        previous.focus();
      }
    });

    upload.addEventListener('click', async () => {
      upload.disabled = true;
      try { await clientUploadModelReferences(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
      finally { upload.disabled = !currentAccessToken; }
    });
  }

  clientInstallModelReferenceLibrary();
'''
