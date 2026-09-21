CARD_CLIENT_GENERATION_RECOVERY_STYLE = r'''
    #client-reply-retry-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 10px;
      flex-wrap: wrap;
    }

    #client-reply-retry {
      margin: 0 !important;
      border-radius: 999px !important;
      padding: 8px 13px !important;
    }

    #client-reply-retry-status {
      color: #6b7a90;
      font-size: .78rem;
      min-height: 1.2em;
    }
'''


CARD_CLIENT_GENERATION_RECOVERY_SCRIPT = r'''
  let clientReplyRecoveryBusy = false;
  let clientAutoReplyRecoveryKey = '';

  async function clientRunReplyRecovery({ automatic = false } = {}) {
    if (clientReplyRecoveryBusy) return false;
    const status = byId('client-reply-retry-status');
    const button = byId('client-reply-retry');
    if (!selectedConversationId) {
      if (status) status.textContent = '请先选择会话。';
      return false;
    }

    clientReplyRecoveryBusy = true;
    if (button) button.disabled = true;
    if (status) {
      status.textContent = automatic
        ? '自动生成首次失败，正在重试一次…'
        : '正在重新分析并生成回复建议…';
    }

    try {
      await loadStrategicReply();
      if (button) button.textContent = '重新生成回复';
      if (status) status.textContent = '回复建议已生成，正在刷新下一步行动…';
      try {
        await generateActionPlan();
        await loadSavedActionPlan();
        await loadActionDecisionContext();
        if (status) status.textContent = '回复建议和下一步行动已刷新。';
      } catch (actionError) {
        if (status) {
          status.textContent = `回复建议已生成，但行动计划刷新失败：${actionError instanceof Error ? actionError.message : String(actionError)}`;
        }
      }
      const alert = byId('client-runtime-alert');
      if (alert) {
        alert.textContent = '';
        alert.classList.remove('is-visible');
      }
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (status) status.textContent = `生成失败：${message}`;
      const alert = clientEnsureRuntimeAlert();
      if (alert) {
        alert.textContent = `回复生成失败：${message}`;
        alert.classList.add('is-visible');
      }
      return false;
    } finally {
      clientReplyRecoveryBusy = false;
      if (button) button.disabled = !currentAccessToken || !selectedConversationId;
    }
  }

  function clientEnsureReplyRecoveryControl() {
    const host = byId('client-reply-host');
    if (!host) return null;
    let wrap = byId('client-reply-retry-wrap');
    if (wrap) return wrap;

    wrap = document.createElement('div');
    wrap.id = 'client-reply-retry-wrap';

    const button = document.createElement('button');
    button.id = 'client-reply-retry';
    button.type = 'button';
    button.className = 'requires-auth client-primary-button';
    button.disabled = !currentAccessToken;
    button.textContent = '生成回复建议';

    const status = document.createElement('span');
    status.id = 'client-reply-retry-status';
    status.textContent = '系统会自动生成；如果自动失败，可在这里手动重试。';

    wrap.append(button, status);
    const heading = host.querySelector('h3, h2');
    if (heading) heading.insertAdjacentElement('afterend', wrap);
    else host.prepend(wrap);

    button.addEventListener('click', () => clientRunReplyRecovery({ automatic: false }));
    return wrap;
  }

  function clientSyncReplyRecoveryControl() {
    const wrap = clientEnsureReplyRecoveryControl();
    if (!wrap) return;
    const button = byId('client-reply-retry');
    const status = byId('client-reply-retry-status');
    if (!button || !status) return;
    const draft = byId('strategic-reply-draft');
    const hasDraft = Boolean(draft && draft.value.trim());
    button.textContent = hasDraft ? '重新生成回复' : '生成回复建议';
    button.disabled = !currentAccessToken || !selectedConversationId || clientReplyRecoveryBusy;
    if (!selectedConversationId) status.textContent = '选择会话后可生成回复建议。';
  }

  function clientInstallAutomaticReplyRecovery() {
    const automation = byId('client-automation-status');
    if (!automation) return;
    const maybeRecover = () => {
      const text = String(automation.textContent || '').trim();
      if (!/自动跟进未完全完成/i.test(text)) return;
      if (!selectedConversationId || clientReplyRecoveryBusy) return;
      const key = `${selectedConversationId}:${text}`;
      if (key === clientAutoReplyRecoveryKey) return;
      clientAutoReplyRecoveryKey = key;
      window.setTimeout(() => {
        if (selectedConversationId) clientRunReplyRecovery({ automatic: true });
      }, 450);
    };
    maybeRecover();
    const observer = new MutationObserver(maybeRecover);
    observer.observe(automation, { childList: true, characterData: true, subtree: true });
  }

  byId('conversation-select')?.addEventListener('change', () => {
    clientAutoReplyRecoveryKey = '';
    clientSyncReplyRecoveryControl();
  });
  byId('person-select')?.addEventListener('change', () => {
    clientAutoReplyRecoveryKey = '';
    queueMicrotask(clientSyncReplyRecoveryControl);
  });

  const clientRecoveryBaseRenderStrategicReply = renderStrategicReply;
  renderStrategicReply = function(data) {
    clientRecoveryBaseRenderStrategicReply(data);
    clientSyncReplyRecoveryControl();
  };

  clientEnsureReplyRecoveryControl();
  clientSyncReplyRecoveryControl();
  clientInstallAutomaticReplyRecovery();
'''
