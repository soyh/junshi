CARD_CLIENT_COMPACT_SURFACE_STYLE = r'''
    /* TEST-169: keep the customer surface to conversation choice, import, and usable results. */
    #client-conversation-host .client-legacy-conversation-card {
      display: none !important;
    }

    #client-conversation-bar {
      grid-column: 1 / -1;
      display: grid;
      gap: 10px;
      min-width: 0;
      padding: 13px 14px;
      border: 1px solid rgba(78, 105, 150, .14);
      border-radius: 18px;
      background: rgba(255, 255, 255, .78);
      box-shadow: 0 12px 34px rgba(47, 76, 118, .07);
    }

    #client-conversation-bar-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    #client-conversation-bar-title {
      color: #26344d;
      font-weight: 900;
      font-size: .92rem;
    }

    #client-conversation-new {
      margin: 0 !important;
      flex: 0 0 auto;
      border-radius: 999px !important;
      padding: 7px 12px !important;
    }

    #client-conversation-tabs {
      display: flex;
      gap: 9px;
      min-width: 0;
      overflow-x: auto;
      padding: 2px 1px 7px;
      scrollbar-gutter: stable;
    }

    .client-conversation-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex: 0 0 auto;
      max-width: 300px;
      min-width: 0;
      margin: 0 !important;
      padding: 8px 10px !important;
      border-radius: 13px !important;
      color: #425b72 !important;
      border: 1px solid rgba(25, 167, 232, .18) !important;
      background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(238,249,255,.94)) !important;
      box-shadow: 0 5px 16px rgba(25, 117, 170, .07) !important;
      white-space: nowrap;
    }

    .client-conversation-chip::before {
      content: "";
      flex: 0 0 auto;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #a8c6d7;
      box-shadow: 0 0 0 3px rgba(168, 198, 215, .18);
    }

    .client-conversation-chip:hover:not(:disabled) {
      border-color: rgba(25, 167, 232, .38) !important;
      background: linear-gradient(180deg, #fff, rgba(231,247,255,.98)) !important;
      box-shadow: 0 8px 20px rgba(25, 117, 170, .11) !important;
    }

    .client-conversation-chip.is-current {
      color: var(--sky-900, #0b2f50) !important;
      border-color: rgba(25, 167, 232, .42) !important;
      background:
        linear-gradient(135deg, rgba(228,248,255,.98), rgba(241,247,255,.98)) !important;
      box-shadow:
        0 8px 22px rgba(25, 139, 197, .12),
        inset 0 0 0 1px rgba(255,255,255,.78) !important;
    }

    .client-conversation-chip.is-current::before {
      background: var(--sky-500, #19a7e8);
      box-shadow: 0 0 0 3px rgba(25, 167, 232, .16);
    }

    .client-conversation-chip-label {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      font-weight: 760;
    }

    .client-conversation-chip-state {
      flex: 0 0 auto;
      padding: 2px 6px;
      border: 1px solid rgba(25, 167, 232, .18);
      border-radius: 999px;
      color: var(--sky-700, #0969a8);
      background: rgba(224, 246, 255, .82);
      font-size: .67rem;
      font-weight: 850;
      letter-spacing: .04em;
    }

    #client-conversation-empty {
      color: #718096;
      font-size: .82rem;
      padding: 4px 2px;
    }

    #client-conversation-compact-status {
      min-height: 1.2em;
      color: #718096;
      font-size: .76rem;
    }

    /* Import already refreshes history, so a second refresh button is customer noise. */
    #client-unified-import-actions #load-messages {
      display: none !important;
    }

    /* Successful orchestration status is implementation detail. Errors are mirrored below. */
    #client-automation-status,
    #client-reply-host #strategic-reply-status,
    #client-action-result #action-plan-generate-status {
      display: none !important;
    }

    #client-runtime-alert {
      display: none;
      grid-column: 1 / -1;
      margin: 0 !important;
      padding: 10px 12px !important;
      border: 1px solid rgba(220, 70, 70, .20);
      border-radius: 14px;
      color: #8f2d2d;
      background: rgba(255, 243, 243, .92);
      font-size: .82rem;
    }

    #client-runtime-alert.is-visible {
      display: block;
    }

    @media (max-width: 760px) {
      #client-conversation-bar-head {
        align-items: flex-start;
      }
      .client-conversation-chip {
        max-width: 240px;
      }
    }
'''


CARD_CLIENT_COMPACT_SURFACE_SCRIPT = r'''
  function clientConversationChipLabel(option) {
    const raw = String(option?.dataset?.test166BaseLabel || option?.textContent || '').trim();
    const withoutIndex = raw.replace(/^\d+\s*·\s*/, '');
    return withoutIndex.replace(/\s*·\s*(active|archived)\s*$/i, '').trim() || '未命名会话';
  }

  function clientEnsureRuntimeAlert() {
    let alert = byId('client-runtime-alert');
    if (alert) return alert;
    const grid = byId('client-results-grid');
    if (!grid) return null;
    alert = document.createElement('div');
    alert.id = 'client-runtime-alert';
    alert.className = 'status';
    grid.prepend(alert);
    return alert;
  }

  function clientMirrorRuntimeStatus(node) {
    const alert = clientEnsureRuntimeAlert();
    if (!node || !alert) return;
    const text = String(node.textContent || '').trim();
    const failed = /(failed|failure|error|timeout|失败|错误|异常|超时|未完全完成)/i.test(text);
    if (failed) {
      alert.textContent = text;
      alert.classList.add('is-visible');
    } else if (alert.textContent === text || !alert.textContent) {
      alert.textContent = '';
      alert.classList.remove('is-visible');
    }
  }

  function clientInstallRuntimeStatusMirrors() {
    [
      byId('client-automation-status'),
      byId('strategic-reply-status'),
      byId('action-plan-generate-status'),
    ].filter(Boolean).forEach((node) => {
      clientMirrorRuntimeStatus(node);
      const observer = new MutationObserver(() => clientMirrorRuntimeStatus(node));
      observer.observe(node, { childList: true, characterData: true, subtree: true });
    });
  }

  function clientEnsureConversationBar() {
    const host = byId('client-conversation-host');
    const legacyCard = byId('conversation-heading')?.closest('.workspace-card');
    const content = byId('conversation-content');
    if (!host || !content) return null;
    if (legacyCard) legacyCard.classList.add('client-legacy-conversation-card');

    let bar = byId('client-conversation-bar');
    if (bar) return bar;

    bar = document.createElement('section');
    bar.id = 'client-conversation-bar';

    const head = document.createElement('div');
    head.id = 'client-conversation-bar-head';
    const title = document.createElement('div');
    title.id = 'client-conversation-bar-title';
    title.textContent = '会话';
    const create = document.createElement('button');
    create.id = 'client-conversation-new';
    create.type = 'button';
    create.className = 'requires-auth';
    create.disabled = !currentAccessToken;
    create.textContent = '＋ 新会话';
    head.append(title, create);

    const tabs = document.createElement('div');
    tabs.id = 'client-conversation-tabs';
    tabs.setAttribute('role', 'tablist');
    tabs.setAttribute('aria-label', '当前人物的会话');

    const status = document.createElement('div');
    status.id = 'client-conversation-compact-status';
    status.textContent = '选择人物后显示会话。';

    bar.append(head, tabs, status);
    host.insertBefore(bar, content);

    create.addEventListener('click', async () => {
      if (!selectedPersonId) {
        status.textContent = '请先选择人物。';
        return;
      }
      create.disabled = true;
      try {
        const select = byId('conversation-select');
        const count = select
          ? Array.from(select.options).filter((option) => option.value).length
          : 0;
        byId('conversation-title').value = `会话 ${count + 1}`;
        byId('conversation-state').value = 'active';
        await createConversation();
        await loadMessages();
        status.textContent = '新会话已创建并选中。';
        clientRenderConversationBar();
      } catch (error) {
        status.textContent = error instanceof Error ? error.message : String(error);
      } finally {
        create.disabled = !currentAccessToken;
      }
    });

    return bar;
  }

  function clientRenderConversationBar() {
    const bar = clientEnsureConversationBar();
    const select = byId('conversation-select');
    const tabs = byId('client-conversation-tabs');
    const status = byId('client-conversation-compact-status');
    const create = byId('client-conversation-new');
    if (!bar || !select || !tabs || !status) return;

    if (create) create.disabled = !currentAccessToken;
    tabs.replaceChildren();
    const options = Array.from(select.options).filter((option) => option.value);
    if (options.length === 0) {
      const empty = document.createElement('div');
      empty.id = 'client-conversation-empty';
      empty.textContent = selectedPersonId
        ? '还没有会话，点击“＋ 新会话”开始。'
        : '选择人物后显示会话。';
      tabs.appendChild(empty);
      status.textContent = selectedPersonId ? '当前人物暂无会话。' : '尚未选择人物。';
      return;
    }

    options.forEach((option) => {
      const button = document.createElement('button');
      const isCurrent = option.value === selectedConversationId;
      const labelText = clientConversationChipLabel(option);
      button.type = 'button';
      button.className = 'client-conversation-chip requires-auth';
      button.disabled = !currentAccessToken;
      button.dataset.conversationId = option.value;
      button.classList.toggle('is-current', isCurrent);
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
      button.title = isCurrent ? `当前会话：${labelText}` : `切换到会话：${labelText}`;

      const label = document.createElement('span');
      label.className = 'client-conversation-chip-label';
      label.textContent = labelText;
      button.appendChild(label);

      if (isCurrent) {
        const state = document.createElement('span');
        state.className = 'client-conversation-chip-state';
        state.textContent = '当前';
        button.appendChild(state);
      }

      button.addEventListener('click', () => {
        select.value = option.value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        clientRenderConversationBar();
      });
      tabs.appendChild(button);
    });
    status.textContent = `共 ${options.length} 个会话；当前会话中的新增内容会自动进入分析链。`;
  }

  const clientCompactBaseLoadConversations = loadConversations;
  loadConversations = async function() {
    await clientCompactBaseLoadConversations();
    clientRenderConversationBar();
  };

  byId('conversation-select')?.addEventListener('change', clientRenderConversationBar);
  byId('person-select')?.addEventListener('change', () => {
    queueMicrotask(clientRenderConversationBar);
  });

  clientEnsureConversationBar();
  clientRenderConversationBar();
  clientInstallRuntimeStatusMirrors();
'''
