CONVERSATION_SESSION_STYLE = r'''
    /* TEST-166: a person may have multiple visible conversations. */
    #conversation-select {
      min-height: 10.5rem;
    }

    #lifecycle-primary-conversation-banner {
      margin-bottom: 12px;
    }
'''


CONVERSATION_SESSION_SCRIPT = r'''
  function test166PresentConversationList() {
    const card = byId('conversation-heading')?.closest('.workspace-card');
    if (card) card.classList.remove('lifecycle-primary-conversation-only');

    const banner = byId('lifecycle-primary-conversation-banner');
    if (banner) {
      banner.textContent = '当前人物可以保留多个会话。下方会显示全部会话；选择任一会话后，单条消息、批量文本、时间线与 AI 分析都使用该会话作为当前作用域。';
    }

    const select = byId('conversation-select');
    if (select) {
      select.size = 8;
      const options = Array.from(select.options).filter((option) => option.value);
      options.forEach((option, index) => {
        const baseLabel = option.dataset.test166BaseLabel || option.textContent;
        option.dataset.test166BaseLabel = baseLabel;
        option.textContent = `${index + 1} · ${baseLabel}`;
      });
    }

    guidedSetLabel('conversation-select', '当前人物的会话（可切换）');
    guidedSetText('load-conversations', '刷新全部会话');
    guidedSetText('create-conversation', '新建会话');
    guidedSetText('import-text', '导入到当前会话');
    guidedSetText('message-heading', '单条消息');
    guidedSetText('text-import-heading', '批量文本');

    const stepHeader = byId('guided-step-3')?.querySelector('.guided-step-header h2');
    const stepCopy = byId('guided-step-3')?.querySelector('.guided-step-header p');
    if (stepHeader) stepHeader.textContent = '会话、AI 分析与回复';
    if (stepCopy) {
      stepCopy.textContent = '一个人物可以保留多个独立会话。先选择目标会话，再用单条消息或批量文本持续追加真实内容；AI 分析与回复始终跟随当前选中的会话。';
    }
  }

  const test166BaseLoadConversations = loadConversations;
  loadConversations = async function() {
    await test166BaseLoadConversations();
    test166PresentConversationList();

    const select = byId('conversation-select');
    if (
      select &&
      selectedConversationId &&
      Array.from(select.options).some((option) => option.value === selectedConversationId)
    ) {
      select.value = selectedConversationId;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
  };

  lifecycleSelectPrimaryConversation = function() {
    const select = byId('conversation-select');
    if (!select || !selectedPersonId) return null;
    const options = Array.from(select.options).filter((option) => option.value);
    if (options.length === 0) {
      lifecyclePrimaryConversationId = null;
      selectedConversationId = null;
      byId('conversation-id').value = '';
      test166PresentConversationList();
      return null;
    }

    const selected = (
      options.find((option) => option.value === selectedConversationId) ||
      options[0]
    );
    lifecyclePrimaryConversationId = selected.value;
    selectedConversationId = selected.value;
    byId('conversation-id').value = selected.value;
    select.value = selected.value;
    select.dispatchEvent(new Event('change', { bubbles: true }));
    test166PresentConversationList();
    return selected.value;
  };

  lifecycleEnsurePrimaryConversation = async function() {
    if (!selectedPersonId) return null;
    await loadConversations();
    if (selectedConversationId) {
      lifecyclePrimaryConversationId = selectedConversationId;
      return selectedConversationId;
    }
    return lifecycleSelectPrimaryConversation();
  };

  test166PresentConversationList();
'''
