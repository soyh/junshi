CARD_CLIENT_UNIFIED_IMPORT_STYLE = r'''
    /* TEST-168: one customer-facing conversation importer for single or batch input. */
    #client-conversation-host .client-legacy-message-card,
    #client-conversation-host .client-legacy-batch-card {
      display: none !important;
    }

    #client-unified-import-card {
      grid-column: 1 / -1;
      padding: 16px !important;
    }

    #client-unified-import-card h2 {
      margin: 0 0 6px;
      color: #26344d;
      font-size: 1.05rem;
    }

    #client-unified-import-card .client-unified-import-note {
      margin: 0 0 12px;
      color: #718096;
      font-size: .84rem;
      line-height: 1.55;
    }

    #client-unified-import-controls {
      display: grid;
      grid-template-columns: minmax(150px, .45fr) minmax(220px, .8fr);
      gap: 10px 14px;
      align-items: end;
    }

    #client-unified-import-controls .client-unified-import-text {
      grid-column: 1 / -1;
    }

    #client-unified-import-controls textarea {
      min-height: 150px !important;
      max-height: 360px;
    }

    #client-unified-import-actions {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    #client-unified-import-actions button {
      margin: 0 !important;
    }

    #client-unified-import-status {
      margin-top: 10px !important;
      min-height: 1.6em;
      padding: 9px 11px !important;
      font-size: .8rem;
    }

    #client-unified-message-history {
      margin-top: 12px;
    }

    #client-unified-message-history > summary {
      cursor: pointer;
      color: #53627a;
      font-weight: 800;
      font-size: .84rem;
    }

    #client-unified-message-history #message-list {
      margin-top: 9px;
      max-height: 260px;
      overflow-y: auto;
      scrollbar-gutter: stable;
    }

    @media (max-width: 760px) {
      #client-unified-import-controls {
        grid-template-columns: 1fr;
      }
      #client-unified-import-controls .client-unified-import-text {
        grid-column: auto;
      }
    }
'''


CARD_CLIENT_UNIFIED_IMPORT_SCRIPT = r'''
  function clientUnifiedLooksLikeStructuredImport(text) {
    const allowedSenders = new Set(['user', 'person', 'system', 'assistant']);
    const lines = String(text || '')
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
    if (lines.length === 0) return false;
    return lines.every((line) => {
      const parts = line.split('|');
      if (parts.length < 3) return false;
      const sentAt = parts.shift().trim();
      const sender = parts.shift().trim();
      const content = parts.join('|').trim();
      return Boolean(sentAt && allowedSenders.has(sender) && content);
    });
  }

  async function clientSubmitUnifiedConversationImport() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    const input = byId('text-import-body');
    const text = input ? input.value : '';
    if (!text.trim()) throw new Error('请输入或粘贴会话内容');

    const status = byId('client-unified-import-status');
    if (clientUnifiedLooksLikeStructuredImport(text)) {
      status.textContent = '检测到结构化对话，正在批量导入并按时间整理…';
      await importTextBatch();
      status.textContent = textImportStatus.textContent || '对话已批量导入。';
      return;
    }

    status.textContent = '检测到单条内容，正在添加到当前会话…';
    byId('message-content').value = text.trim();
    await createMessage();
    input.value = '';
    status.textContent = '已添加 1 条消息。系统正在自动更新回复建议和下一步行动。';
  }

  function clientInstallUnifiedConversationImport() {
    const content = byId('conversation-content');
    const workspace = content ? content.querySelector(':scope > .workspace-grid') : null;
    if (!content || !workspace || byId('client-unified-import-card')) return;

    const messageCard = byId('message-heading')?.closest('.workspace-card');
    const batchCard = byId('text-import-heading')?.closest('.workspace-card');
    if (!messageCard || !batchCard) return;

    messageCard.classList.add('client-legacy-message-card');
    batchCard.classList.add('client-legacy-batch-card');

    const card = document.createElement('section');
    card.id = 'client-unified-import-card';
    card.className = 'workspace-card';

    const heading = document.createElement('h2');
    heading.id = 'client-unified-import-heading';
    heading.textContent = '导入会话内容';

    const note = document.createElement('p');
    note.className = 'client-unified-import-note';
    note.textContent = '直接粘贴一条或多条内容。普通文本会作为一条消息添加；“时间 | 发送者 | 内容”格式会自动识别为批量对话。无需选择单条或批量模式。';

    const controls = document.createElement('div');
    controls.id = 'client-unified-import-controls';

    const senderLabel = document.querySelector('label[for="message-sender"]');
    const sender = byId('message-sender');
    const sentAtLabel = document.querySelector('label[for="message-sent-at"]');
    const sentAt = byId('message-sent-at');
    const textLabel = document.querySelector('label[for="text-import-body"]');
    const text = byId('text-import-body');

    const senderWrap = document.createElement('div');
    if (senderLabel) senderLabel.textContent = '发送者（普通文本）';
    if (senderLabel) senderWrap.appendChild(senderLabel);
    if (sender) senderWrap.appendChild(sender);

    const sentAtWrap = document.createElement('div');
    if (sentAtLabel) sentAtLabel.textContent = '发送时间（可选，仅普通文本）';
    if (sentAtLabel) sentAtWrap.appendChild(sentAtLabel);
    if (sentAt) sentAtWrap.appendChild(sentAt);

    const textWrap = document.createElement('div');
    textWrap.className = 'client-unified-import-text';
    if (textLabel) textLabel.textContent = '会话内容';
    if (textLabel) textWrap.appendChild(textLabel);
    if (text) {
      text.placeholder = '直接粘贴一条消息，或粘贴多条：\n2026-09-21T12:00:00+00:00 | user | 第一条\n2026-09-21T12:01:00+00:00 | person | 第二条';
      textWrap.appendChild(text);
    }
    controls.append(senderWrap, sentAtWrap, textWrap);

    const actions = document.createElement('div');
    actions.id = 'client-unified-import-actions';
    const submit = document.createElement('button');
    submit.id = 'client-unified-import';
    submit.type = 'button';
    submit.className = 'requires-auth client-primary-button';
    submit.disabled = !currentAccessToken;
    submit.textContent = '添加到当前会话';

    const refresh = byId('load-messages');
    if (refresh) {
      refresh.textContent = '刷新会话记录';
      actions.append(submit, refresh);
    } else {
      actions.appendChild(submit);
    }

    const status = document.createElement('div');
    status.id = 'client-unified-import-status';
    status.className = 'status';
    status.textContent = '选择会话后，直接粘贴内容即可。';

    const history = document.createElement('details');
    history.id = 'client-unified-message-history';
    const historySummary = document.createElement('summary');
    historySummary.textContent = '查看当前会话记录';
    const messageListNode = byId('message-list');
    history.appendChild(historySummary);
    if (messageListNode) history.appendChild(messageListNode);

    card.append(heading, note, controls, actions, status, history);
    workspace.prepend(card);

    const stageCopy = document.querySelector('#client-conversation-stage .client-stage-header p');
    if (stageCopy) {
      stageCopy.textContent = '选择会话后直接粘贴内容；系统自动识别一条或多条，并在保存后自动更新回复建议和下一步行动。';
    }

    submit.addEventListener('click', async () => {
      submit.disabled = true;
      try {
        await clientSubmitUnifiedConversationImport();
      } catch (error) {
        status.textContent = error instanceof Error ? error.message : String(error);
      } finally {
        submit.disabled = !currentAccessToken;
      }
    });

    byId('conversation-select')?.addEventListener('change', () => {
      status.textContent = selectedConversationId
        ? '可以直接粘贴内容；系统会自动判断一条或多条。'
        : '请先选择会话。';
    });
  }

  clientInstallUnifiedConversationImport();
'''
