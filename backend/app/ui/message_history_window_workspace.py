MESSAGE_HISTORY_WINDOW_SCRIPT = r'''
  // TEST-178: override the TEST-177 client-only time filter at capture phase.
  // The visible window is fetched from the server; canonical analysis history
  // remains complete because analysis services still use MessageService.list().
  function historyWindowIso(value, endOfDay = false) {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) throw new Error('时间格式无效');
    if (endOfDay && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      parsed.setHours(23, 59, 59, 999);
    }
    return parsed.toISOString();
  }

  async function applyServerMessageWindow(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (!selectedConversationId) throw new Error('请先选择会话');
    const from = historyWindowIso(byId('client-message-from')?.value || '');
    const to = historyWindowIso(byId('client-message-to')?.value || '', true);
    await loadMessages({from, to, limit: 100});
    const info = byId('client-message-window-status');
    if (info) {
      info.textContent = `已从服务端按时间范围加载当前窗口，默认最多 100 条；AI 分析仍使用完整历史。`;
    }
  }

  async function clearServerMessageWindow(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    const from = byId('client-message-from');
    const to = byId('client-message-to');
    if (from) from.value = '';
    if (to) to.value = '';
    await loadMessages({limit: 100});
    const info = byId('client-message-window-status');
    if (info) {
      info.textContent = '默认显示最新 100 条；AI 分析仍使用该会话完整历史。';
    }
  }

  const applyWindowButton = byId('client-apply-message-window');
  const clearWindowButton = byId('client-clear-message-window');
  if (applyWindowButton) {
    applyWindowButton.addEventListener('click', async (event) => {
      try { await applyServerMessageWindow(event); }
      catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
    }, {capture: true});
  }
  if (clearWindowButton) {
    clearWindowButton.addEventListener('click', async (event) => {
      try { await clearServerMessageWindow(event); }
      catch (error) { messagesStatus.textContent = error instanceof Error ? error.message : String(error); }
    }, {capture: true});
  }
'''
