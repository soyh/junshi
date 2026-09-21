LIFECYCLE_V2_STYLE = r'''
    /* TEST-164: vertical daily workflow + horizontal settings tabs. */
    body > header {
      display: none !important;
    }

    #guided-settings {
      grid-column: 1 / -1;
      width: 100%;
      box-sizing: border-box;
    }

    #guided-settings[open] { width: 100%; }

    #guided-settings-content {
      display: grid !important;
      grid-template-columns: repeat(4, minmax(150px, 1fr)) !important;
      grid-auto-rows: auto;
      gap: 8px 10px !important;
      align-items: start !important;
      max-height: min(72vh, 760px);
      overflow-y: auto;
      overflow-x: auto;
      padding: 10px 4px 6px 0;
      scrollbar-gutter: stable;
    }

    #guided-settings-content > .lifecycle-settings-panel {
      display: contents;
    }

    #guided-settings-content > .lifecycle-settings-panel > summary {
      grid-row: 1;
      min-width: 0;
      cursor: pointer;
      padding: 10px 12px;
      border: 1px solid rgba(25, 167, 232, .20);
      border-radius: 12px;
      font-weight: 700;
      color: var(--sky-800, #075985);
      background: rgba(226, 246, 255, .72);
      user-select: none;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    #guided-settings-content > .lifecycle-settings-panel[open] > summary {
      color: #fff;
      background: linear-gradient(135deg, var(--sky-500, #19a7e8), var(--sky-700, #0877b9));
      border-color: transparent;
      box-shadow: 0 8px 22px rgba(25, 167, 232, .18);
    }

    #guided-settings-content > .lifecycle-settings-panel > fieldset {
      grid-column: 1 / -1;
      grid-row: 2;
      min-width: 0;
      max-height: min(58vh, 620px);
      overflow-y: auto;
      overflow-x: hidden;
      scrollbar-gutter: stable;
      border: 1px solid rgba(25, 167, 232, .16) !important;
      border-radius: 12px !important;
      padding: 12px 14px 14px !important;
      margin: 0 !important;
      background: rgba(255,255,255,.72);
    }

    #guided-settings-content > .lifecycle-settings-panel > fieldset > legend { display: none; }
    #guided-settings-content textarea { min-height: 56px !important; max-height: 120px; }
    #guided-settings-content .status { max-height: 132px; overflow-y: auto; scrollbar-gutter: stable; }

    .user-long-content:not(.is-expanded),
    .user-long-list:not(.is-expanded) {
      max-height: 12rem !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      mask-image: none !important;
      scrollbar-gutter: stable;
      overscroll-behavior: contain;
    }

    .user-long-content.is-expanded,
    .user-long-list.is-expanded { overflow: visible !important; }

    .lifecycle-primary-conversation-only #conversation-select,
    .lifecycle-primary-conversation-only label[for="conversation-select"],
    .lifecycle-primary-conversation-only #create-conversation,
    .lifecycle-primary-conversation-only #load-conversations,
    .lifecycle-primary-conversation-only #conversation-title,
    .lifecycle-primary-conversation-only label[for="conversation-title"],
    .lifecycle-primary-conversation-only #conversation-state,
    .lifecycle-primary-conversation-only label[for="conversation-state"] {
      display: none !important;
    }

    #lifecycle-primary-conversation-banner {
      margin: 6px 0 10px;
      padding: 9px 11px;
      border-radius: 12px;
      background: rgba(224, 247, 255, .78);
      border: 1px solid rgba(25, 167, 232, .18);
      color: var(--sky-800, #075985);
      font-size: .9rem;
    }

    #lifecycle-automation-status {
      max-height: 8.5rem;
      overflow-y: auto;
      scrollbar-gutter: stable;
    }

    .lifecycle-inline-section { margin-top: 12px; }
    .lifecycle-hidden-step { display: none !important; }

    @media (max-width: 760px) {
      #guided-settings-content {
        min-width: 660px;
      }
    }
'''


LIFECYCLE_V2_SCRIPT = r'''
  const lifecycleAutomationStatus = (() => {
    let node = byId('lifecycle-automation-status');
    if (node) return node;
    node = document.createElement('div');
    node.id = 'lifecycle-automation-status';
    node.className = 'status';
    node.textContent = '自动跟进待命：新增真实消息后会刷新 AI 回复和行动计划；记录真实 Outcome 后会刷新反馈、学习与复盘。';
    const target = byId('guided-conversation-primary') || byId('guided-workflow');
    if (target) target.prepend(node);
    return node;
  })();

  let lifecycleAutomationBusy = false;
  let lifecyclePrimaryConversationId = null;

  function lifecycleCompactSettings() {
    const settings = byId('guided-settings-content');
    if (!settings) return;
    const account = byId('account');
    if (account && account.parentElement !== settings) settings.prepend(account);

    Array.from(settings.children).forEach((child) => {
      if (!(child instanceof HTMLFieldSetElement)) return;
      const legend = child.querySelector(':scope > legend');
      const title = legend ? legend.textContent.trim() : '设置';
      const details = document.createElement('details');
      details.className = 'lifecycle-settings-panel';
      const summary = document.createElement('summary');
      summary.textContent = title || '设置';
      details.appendChild(summary);
      child.parentNode.insertBefore(details, child);
      details.appendChild(child);
    });

    const panels = Array.from(settings.querySelectorAll(':scope > .lifecycle-settings-panel'));
    const initiallyOpen = panels.filter((panel) => panel.open);
    initiallyOpen.slice(1).forEach((panel) => { panel.open = false; });
    panels.forEach((panel) => {
      panel.addEventListener('toggle', () => {
        if (!panel.open) return;
        panels.forEach((other) => {
          if (other !== panel) other.open = false;
        });
      });
    });
  }

  function lifecycleRecomposeGuidedFlow() {
    const nav = document.querySelector('#guided-workflow > .guided-step-nav');
    if (nav) {
      nav.replaceChildren();
      [
        ['#guided-step-1', '1 选择人物'],
        ['#guided-step-2', '2 编辑关系'],
        ['#guided-step-3', '3 主会话与 AI'],
        ['#guided-step-5', '4 行动与复盘'],
      ].forEach(([href, text]) => {
        const a = document.createElement('a');
        a.href = href;
        a.textContent = text;
        nav.appendChild(a);
      });
    }

    const step3 = byId('guided-step-3');
    const step4 = byId('guided-step-4');
    const step5 = byId('guided-step-5');
    const step6 = byId('guided-step-6');

    if (step3 && step4) {
      const header = step3.querySelector('.guided-step-header h2');
      const copy = step3.querySelector('.guided-step-header p');
      if (header) header.textContent = '主会话、AI 分析与回复';
      if (copy) copy.textContent = '一个人物只展示一个主会话。新增真实消息后，系统自动刷新 AI 分析、回复建议和行动计划。';
      const primary = byId('guided-analysis-primary');
      const advanced = byId('guided-analysis-advanced')?.closest('details');
      if (primary) { primary.classList.add('lifecycle-inline-section'); step3.appendChild(primary); }
      if (advanced) step3.appendChild(advanced);
      step4.classList.add('lifecycle-hidden-step');
    }

    if (step5 && step6) {
      const header = step5.querySelector('.guided-step-header h2');
      const copy = step5.querySelector('.guided-step-header p');
      if (header) header.textContent = '行动更新与自动复盘';
      if (copy) copy.textContent = '你只需要确认真实行动、记录执行和 Outcome；系统随后自动刷新反馈、学习建议和最新复盘。';
      const actionBar = step6.querySelector('.guided-action-bar');
      const learning = byId('guided-learning-primary');
      if (actionBar) step5.appendChild(actionBar);
      if (learning) { learning.classList.add('lifecycle-inline-section'); step5.appendChild(learning); }
      step6.classList.add('lifecycle-hidden-step');
    }
  }

  function lifecycleInstallPrimaryConversationPresentation() {
    const card = byId('conversation-heading')?.closest('.workspace-card');
    if (!card) return;
    card.classList.add('lifecycle-primary-conversation-only');
    if (!byId('lifecycle-primary-conversation-banner')) {
      const banner = document.createElement('div');
      banner.id = 'lifecycle-primary-conversation-banner';
      banner.textContent = '当前人物只展示一个主会话。已有历史会话不会删除，仍保留在高级管理中。';
      byId('conversation-heading')?.insertAdjacentElement('afterend', banner);
    }
  }

  function lifecycleSelectPrimaryConversation() {
    const select = byId('conversation-select');
    if (!select || !selectedPersonId) return null;
    const options = Array.from(select.options).filter((option) => option.value);
    if (options.length === 0) {
      lifecyclePrimaryConversationId = null;
      return null;
    }
    const selected = options.find((option) => option.value === selectedConversationId) || options[options.length - 1];
    lifecyclePrimaryConversationId = selected.value;
    if (select.value !== selected.value) {
      select.value = selected.value;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    return selected.value;
  }

  async function lifecycleEnsurePrimaryConversation() {
    if (!selectedPersonId) return null;
    await loadConversations();
    const existing = lifecycleSelectPrimaryConversation();
    if (existing) return existing;
    const titleInput = byId('conversation-title');
    if (titleInput && !titleInput.value.trim()) titleInput.value = '主会话';
    await createConversation();
    await loadConversations();
    return lifecycleSelectPrimaryConversation();
  }

  async function lifecycleRefreshRelationshipEditor() {
    if (!selectedPersonId) return;
    await loadRelationships();
    const select = byId('relationship-select');
    const options = select ? Array.from(select.options).filter((option) => option.value) : [];
    if (!selectedRelationshipId && options.length > 0) {
      selectedRelationshipId = options[options.length - 1].value;
      select.value = selectedRelationshipId;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    if (selectedRelationshipId) await loadSelectedRelationshipManagement();
  }

  async function lifecycleAfterEvidenceChanged(source = '消息') {
    if (lifecycleAutomationBusy || !selectedConversationId) return;
    lifecycleAutomationBusy = true;
    lifecycleAutomationStatus.textContent = `${source}已保存。正在自动刷新 AI 回复与行动计划…`;
    try {
      await loadStrategicReply();
      lifecycleAutomationStatus.textContent = 'AI 回复已刷新，正在更新行动计划…';
      await generateActionPlan();
      await loadSavedActionPlan();
      await loadActionDecisionContext();
      lifecycleAutomationStatus.textContent = '自动跟进完成：AI 回复与行动计划已更新。发送回复、确认行动和现实执行仍由你决定。';
    } catch (error) {
      lifecycleAutomationStatus.textContent = `自动跟进未完全完成：${error instanceof Error ? error.message : String(error)}`;
    } finally {
      lifecycleAutomationBusy = false;
    }
  }

  async function lifecycleAfterDecisionRecorded(detail) {
    if (!detail || detail.decision !== 'confirmed') return;
    try {
      await loadActionExecutionContext();
      lifecycleAutomationStatus.textContent = '行动已确认，待执行状态已自动刷新。现实中执行后，请明确记录“已执行”。';
    } catch (error) {
      lifecycleAutomationStatus.textContent = `确认后刷新失败：${error instanceof Error ? error.message : String(error)}`;
    }
  }

  async function lifecycleAfterExecutionRecorded() {
    try {
      await loadActionOutcomeContext();
      lifecycleAutomationStatus.textContent = '执行记录已更新。请根据现实结果记录 Outcome；系统不会猜测现实结果。';
    } catch (error) {
      lifecycleAutomationStatus.textContent = `执行后刷新失败：${error instanceof Error ? error.message : String(error)}`;
    }
  }

  async function lifecycleAfterOutcomeRecorded() {
    if (lifecycleAutomationBusy) return;
    lifecycleAutomationBusy = true;
    lifecycleAutomationStatus.textContent = '真实 Outcome 已记录，正在自动刷新反馈、学习和复盘…';
    try {
      await loadActionFeedback();
      await loadActionLearning();
      await loadPersistedActionLearning();
      if (selectedConversationId) {
        await loadActionReanalysisInputs();
        await runActionReanalysis();
      }
      lifecycleAutomationStatus.textContent = '复盘完成：反馈、学习建议和最新分析已刷新。学习建议不会在未确认时自动改写长期记忆。';
    } catch (error) {
      lifecycleAutomationStatus.textContent = `自动复盘未完全完成：${error instanceof Error ? error.message : String(error)}`;
    } finally {
      lifecycleAutomationBusy = false;
    }
  }

  window.addEventListener('junshi:evidence-changed', (event) => lifecycleAfterEvidenceChanged(event.detail?.source || '证据'));
  window.addEventListener('junshi:decision-recorded', (event) => lifecycleAfterDecisionRecorded(event.detail));
  window.addEventListener('junshi:execution-recorded', () => lifecycleAfterExecutionRecorded());
  window.addEventListener('junshi:outcome-recorded', () => lifecycleAfterOutcomeRecorded());

  byId('person-select')?.addEventListener('change', async () => {
    if (!selectedPersonId) return;
    try {
      await lifecycleRefreshRelationshipEditor();
      await lifecycleEnsurePrimaryConversation();
      lifecycleAutomationStatus.textContent = '人物已切换：已恢复上次关系信息和主会话。';
    } catch (error) {
      lifecycleAutomationStatus.textContent = `人物初始化未完全完成：${error instanceof Error ? error.message : String(error)}`;
    }
  });

  lifecycleCompactSettings();
  lifecycleRecomposeGuidedFlow();
  lifecycleInstallPrimaryConversationPresentation();
'''
