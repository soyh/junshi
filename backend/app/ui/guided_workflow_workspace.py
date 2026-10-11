GUIDED_WORKFLOW_HTML = r'''
  <section id="guided-workflow" class="wide guided-workflow" aria-labelledby="guided-workflow-title">
    <div class="guided-hero">
      <div>
        <p class="guided-eyebrow">日常使用流程</p>
        <h2 id="guided-workflow-title">按顺序完成，不需要在技术模块之间来回寻找</h2>
        <p class="note">页面保留原有 canonical API 与所有用户确认边界，只重新组织界面、汉化可见文案，并合并纯读取/纯下一步操作。</p>
      </div>
      <details id="guided-settings" class="guided-settings">
        <summary>账号、安全与模型设置</summary>
        <div id="guided-settings-content" class="guided-settings-content"></div>
      </details>
    </div>

    <nav class="guided-step-nav" aria-label="使用步骤">
      <a href="#guided-step-1">1 选择人物</a>
      <a href="#guided-step-2">2 维护关系</a>
      <a href="#guided-step-3">3 会话与证据</a>
      <a href="#guided-step-4">4 AI 分析与回复</a>
      <a href="#guided-step-5">5 行动计划与执行</a>
      <a href="#guided-step-6">6 结果、学习与复盘</a>
    </nav>

    <section id="guided-step-1" class="guided-step">
      <header class="guided-step-header">
        <span class="guided-step-number">1</span>
        <div><h2>选择对接人物</h2><p>先选择已有的人物；没有时再新建。后续关系、会话和分析都跟随当前人物。</p></div>
      </header>
      <div id="guided-person-primary" class="guided-primary"></div>
      <details class="guided-advanced"><summary>人物资料管理（修改 / 删除 / 档案）</summary><div id="guided-person-advanced"></div></details>
    </section>

    <section id="guided-step-2" class="guided-step">
      <header class="guided-step-header">
        <span class="guided-step-number">2</span>
        <div><h2>维护关系</h2><p>为当前人物选择或创建关系，并按需要维护关系状态、阶段和目标。</p></div>
      </header>
      <div id="guided-relationship-primary" class="guided-primary"></div>
      <details class="guided-advanced"><summary>关系资料管理（修改 / 删除）</summary><div id="guided-relationship-advanced"></div></details>
    </section>

    <section id="guided-step-3" class="guided-step">
      <header class="guided-step-header">
        <span class="guided-step-number">3</span>
        <div><h2>选择会话并录入真实信息</h2><p>选择会话后录入真实聊天或互动。消息与互动会成为后续分析使用的 canonical evidence。</p></div>
      </header>
      <div id="guided-conversation-primary" class="guided-primary"></div>
      <details class="guided-advanced"><summary>会话、消息与互动管理</summary><div id="guided-conversation-advanced"></div></details>
    </section>

    <section id="guided-step-4" class="guided-step">
      <header class="guided-step-header">
        <span class="guided-step-number">4</span>
        <div><h2>AI 分析并生成回复建议</h2><p>日常只需要一次显式生成。系统会使用当前会话的分析、证据与 recommendation 链生成可编辑回复，不会自动发送或保存成 Message。</p></div>
      </header>
      <div id="guided-analysis-primary" class="guided-primary"></div>
      <details class="guided-advanced"><summary>查看结构化分析 / 策略 / Recommendation 技术详情</summary><div id="guided-analysis-advanced"></div></details>
    </section>

    <section id="guided-step-5" class="guided-step">
      <header class="guided-step-header">
        <span class="guided-step-number">5</span>
        <div><h2>行动计划、用户决定与执行记录</h2><p>生成计划可以合并“生成 → 读取保存结果 → 载入待确认项”；但 Confirm / Reject 和 Execution 仍必须由用户明确操作。</p></div>
      </header>
      <div class="guided-action-bar">
        <button id="guided-generate-action-plan" class="requires-auth guided-primary-action" type="button" disabled>生成行动计划并准备确认</button>
        <div id="guided-action-plan-status" class="status">请选择会话后再生成行动计划。</div>
      </div>
      <div id="guided-action-primary" class="guided-primary"></div>
    </section>

    <section id="guided-step-6" class="guided-step">
      <header class="guided-step-header">
        <span class="guided-step-number">6</span>
        <div><h2>结果、反馈、学习与复盘</h2><p>Outcome 和 Learning memory 持久化仍需用户明确操作。只读 Feedback / Learning 查询可以合并；重新分析仍需显式触发。</p></div>
      </header>
      <div class="guided-action-bar">
        <button id="guided-load-feedback-learning" class="requires-auth" type="button" disabled>汇总反馈并加载学习建议</button>
        <button id="guided-run-reanalysis" class="requires-auth guided-primary-action" type="button" disabled>读取学习上下文并重新分析</button>
        <div id="guided-learning-status" class="status">完成真实 Outcome 后，可在这里继续反馈、学习和复盘。</div>
      </div>
      <div id="guided-learning-primary" class="guided-primary"></div>
    </section>
  </section>
'''


GUIDED_WORKFLOW_SCRIPT = r'''
  const guidedActionPlanStatus = byId('guided-action-plan-status');
  const guidedLearningStatus = byId('guided-learning-status');

  function guidedMoveNode(id, targetId) {
    const node = byId(id);
    const target = byId(targetId);
    if (node && target) target.appendChild(node);
    return node;
  }

  function guidedMoveCard(headingId, targetId) {
    const heading = byId(headingId);
    const target = byId(targetId);
    if (!heading || !target) return null;
    const card = heading.closest('.workspace-card');
    if (card) target.appendChild(card);
    return card;
  }

  function guidedSetText(id, text) {
    const node = byId(id);
    if (node) node.textContent = text;
  }

  function guidedSetLabel(forId, text) {
    const label = document.querySelector(`label[for="${forId}"]`);
    if (label) label.textContent = text;
  }

  function guidedSetLegend(fieldsetId, text) {
    const fieldset = byId(fieldsetId);
    const legend = fieldset ? fieldset.querySelector(':scope > legend') : null;
    if (legend) legend.textContent = text;
  }

  function guidedTranslateOptions(id, labels) {
    const select = byId(id);
    if (!select) return;
    Array.from(select.options).forEach((option) => {
      if (Object.prototype.hasOwnProperty.call(labels, option.value)) {
        option.textContent = labels[option.value];
      }
    });
  }

  function guidedReorganizeLayout() {
    guidedMoveCard('person-heading', 'guided-person-primary');
    guidedMoveCard('relationship-heading', 'guided-relationship-primary');
    guidedMoveCard('conversation-heading', 'guided-conversation-primary');

    guidedMoveCard('manage-person-heading', 'guided-person-advanced');
    guidedMoveCard('manage-relationship-heading', 'guided-relationship-advanced');
    guidedMoveCard('manage-conversation-heading', 'guided-conversation-advanced');
    guidedMoveCard('manage-interaction-heading', 'guided-conversation-advanced');
    guidedMoveCard('manage-message-heading', 'guided-conversation-advanced');

    guidedMoveNode('conversation-content', 'guided-conversation-primary');
    guidedMoveNode('relationship-evidence', 'guided-conversation-primary');

    guidedMoveNode('strategic-reply-workspace', 'guided-analysis-primary');
    guidedMoveNode('analysis', 'guided-analysis-advanced');
    guidedMoveNode('strategy-recommendation', 'guided-analysis-advanced');

    guidedMoveNode('action-plan-workspace', 'guided-action-primary');
    guidedMoveNode('action-decision-workspace', 'guided-action-primary');
    guidedMoveNode('action-execution-workspace', 'guided-action-primary');

    guidedMoveNode('action-outcome-workspace', 'guided-learning-primary');
    guidedMoveNode('action-feedback-workspace', 'guided-learning-primary');
    guidedMoveNode('action-learning-workspace', 'guided-learning-primary');
    guidedMoveNode('action-reanalysis-workspace', 'guided-learning-primary');

    const account = byId('account');
    const sessionFieldset = account && account.nextElementSibling && account.nextElementSibling.tagName === 'FIELDSET'
      ? account.nextElementSibling
      : null;
    if (sessionFieldset && !sessionFieldset.id) byId('guided-settings-content').appendChild(sessionFieldset);
    guidedMoveNode('account-security', 'guided-settings-content');
    guidedMoveNode('provider', 'guided-settings-content');

    const oldWorkspace = byId('workspace');
    const oldManagement = byId('product-management');
    if (oldWorkspace) oldWorkspace.classList.add('guided-source-empty');
    if (oldManagement) oldManagement.classList.add('guided-source-empty');

    ['generate-action-plan', 'load-action-feedback', 'load-action-learning', 'load-persisted-action-learning', 'load-action-reanalysis-inputs', 'run-action-reanalysis'].forEach((id) => {
      const node = byId(id);
      if (node) node.classList.add('guided-replaced-control');
    });
  }

  function guidedLocalizeStaticUI() {
    document.title = 'AI 恋爱军师';
    const pageTitle = document.querySelector('body > header h1');
    if (pageTitle) pageTitle.textContent = 'AI 恋爱军师';

    const buttons = {
      register: '注册', login: '登录', logout: '退出登录',
      'load-sessions': '手动刷新登录会话', 'rotate-session': '更新当前登录会话', 'revoke-others': '退出其他设备',
      'load-persons': '手动刷新人物列表', 'create-person': '新建人物',
      'load-relationships': '手动刷新关系列表', 'create-relationship': '新建关系',
      'load-conversations': '手动刷新会话列表', 'create-conversation': '新建会话',
      'load-provider': '读取配置', 'save-provider': '保存配置', 'test-provider': '测试连接', 'delete-provider': '删除配置',
      'run-analysis': '单独运行结构化分析（高级）',
      'load-selected-person': '读取当前人物', 'update-selected-person': '保存人物修改', 'delete-selected-person': '删除当前人物',
      'load-selected-relationship': '读取当前关系', 'update-selected-relationship': '保存关系修改', 'delete-selected-relationship': '删除当前关系',
      'load-selected-conversation': '读取当前会话', 'update-selected-conversation': '保存会话修改', 'archive-selected-conversation': '归档', 'activate-selected-conversation': '重新启用', 'delete-selected-conversation': '删除当前会话',
      'load-managed-interactions': '手动刷新互动记录', 'update-selected-interaction': '保存互动修改', 'delete-selected-interaction': '删除当前互动',
      'load-managed-messages': '手动刷新历史消息', 'delete-selected-message': '删除所选消息',
      'load-messages': '手动刷新消息', 'create-message': '添加消息', 'import-text': '导入为新会话',
      'load-interactions': '手动刷新互动', 'create-interaction': '添加互动', 'load-timeline': '手动刷新时间线',
      'load-strategy-context': '读取策略详情（高级）', 'load-recommendation-context': '读取 Recommendation 详情（高级）',
      'load-strategic-reply': '分析并生成回复建议', 'copy-strategic-reply': '复制编辑后的回复', 'restore-strategic-reply': '恢复 AI 原始草稿', 'prepare-strategic-reply-message': '准备“已发送消息”记录',
      'load-saved-action-plan': '手动刷新已保存计划', 'load-action-decision-context': '手动刷新待确认项',
      'confirm-action-decision': '确认所选行动', 'reject-action-decision': '拒绝所选行动',
      'load-action-execution-context': '手动刷新待执行项', 'record-action-execution': '记录所选行动已执行',
      'load-action-outcome-context': '手动刷新待记录结果', 'record-action-outcome': '记录所选行动结果',
      'persist-action-learning': '保存所选学习记忆'
    };
    Object.entries(buttons).forEach(([id, text]) => guidedSetText(id, text));

    const headings = {
      'person-heading': '选择或新建人物', 'relationship-heading': '选择或新建关系', 'conversation-heading': '选择或新建会话',
      'manage-person-heading': '人物管理', 'manage-relationship-heading': '关系管理', 'manage-conversation-heading': '会话管理',
      'manage-interaction-heading': '互动记录管理', 'manage-message-heading': '历史消息管理',
      'message-heading': '消息', 'text-import-heading': '批量文本导入', 'interaction-heading': '互动事件', 'timeline-heading': '人物时间线',
      'strategy-workspace-heading': '策略上下文', 'recommendation-workspace-heading': 'Recommendation 详情',
      'strategic-reply-heading': '回复草稿', 'strategic-reply-context-heading': '为什么这样回复',
      'action-plan-generate-heading': '行动计划生成结果', 'saved-action-plan-heading': '已保存行动计划',
      'action-decision-heading': '用户明确决定', 'action-decision-history-heading': '决定历史',
      'action-execution-heading': '执行记录', 'action-execution-history-heading': '执行状态',
      'action-outcome-heading': '结果记录', 'action-outcome-history-heading': '结果历史',
      'action-feedback-context-heading': '决定 / 结果反馈', 'action-feedback-summary-heading': '反馈汇总', 'action-feedback-trend-heading': '反馈趋势', 'action-feedback-signals-heading': 'Recommendation 信号',
      'action-learning-heading': '学习建议', 'action-learning-persisted-heading': '已保存学习记忆',
      'action-reanalysis-input-heading': '复盘输入', 'action-reanalysis-run-heading': '最新分析与 Recommendation'
    };
    Object.entries(headings).forEach(([id, text]) => guidedSetText(id, text));

    const labels = {
      username: '用户名', password: '密码',
      'person-name': '姓名 / 标识', 'person-nickname': '昵称', 'person-notes': '备注', 'person-select': '当前对接人物',
      'relationship-state': '关系状态', 'relationship-stage': '关系阶段', 'relationship-long-term-goal': '长期目标', 'relationship-current-goal': '当前目标', 'relationship-notes': '备注', 'relationship-select': '当前关系',
      'conversation-title': '会话标题', 'conversation-state': '会话状态', 'conversation-select': '当前会话',
      'provider-name': '模型接口类型', 'base-url': '接口地址（Base URL）', model: '模型名称', 'api-key': 'API Key', timeout: '超时时间（秒）',
      'conversation-id': '会话 ID（高级）',
      'message-sender': '发送方', 'message-sent-at': '发送时间（可选，ISO 8601）', 'message-content': '消息内容',
      'text-import-title': '新会话标题（可选）', 'text-import-body': '批量文本',
      'interaction-type': '互动类型', 'interaction-occurred-at': '发生时间（ISO 8601）', 'interaction-content': '内容（可选）',
      'strategic-reply-draft': '可编辑回复',
      'action-decision-recommendation': '待确认行动', 'action-decision-note': '决定备注（可选）',
      'action-execution-decision': '可执行的已确认决定', 'action-execution-executed-at': '执行时间（可选）', 'action-execution-note': '执行备注（可选）',
      'action-outcome-decision': '已执行但尚未记录结果的决定', 'action-outcome-state': '结果', 'action-outcome-note': '结果备注（可选）',
      'action-learning-candidate': '学习记忆建议'
    };
    Object.entries(labels).forEach(([id, text]) => guidedSetLabel(id, text));

    guidedSetLegend('conversation-content', '会话内容');
    guidedSetLegend('relationship-evidence', '关系证据与时间线');
    guidedSetLegend('strategy-recommendation', '策略与 Recommendation');
    guidedSetLegend('strategic-reply-workspace', 'AI 回复建议');
    guidedSetLegend('action-plan-workspace', '行动计划');
    guidedSetLegend('action-decision-workspace', '行动决定');
    guidedSetLegend('action-execution-workspace', '行动执行');
    guidedSetLegend('action-outcome-workspace', '行动结果');
    guidedSetLegend('action-feedback-workspace', '反馈');
    guidedSetLegend('action-learning-workspace', '学习');
    guidedSetLegend('action-reanalysis-workspace', '重新分析 / 复盘');
    guidedSetLegend('provider', 'LLM 模型设置');
    guidedSetLegend('analysis', '结构化分析（高级）');
    guidedSetLegend('account', '账号登录');

    guidedTranslateOptions('conversation-state', {active: '使用中', archived: '已归档'});
    guidedTranslateOptions('manage-conversation-status-value', {active: '使用中', archived: '已归档'});
    guidedTranslateOptions('message-sender', {user: '我（user）', person: '对方（person）', system: '系统', assistant: 'AI 助手'});
    guidedTranslateOptions('interaction-type', {message: '消息', call: '电话', meeting: '见面', date: '约会', gift: '礼物', other: '其他'});
    guidedTranslateOptions('manage-interaction-type', {message: '消息', call: '电话', meeting: '见面', date: '约会', gift: '礼物', other: '其他'});
    guidedTranslateOptions('action-outcome-state', {completed: '已完成', skipped: '跳过', failed: '失败'});
  }

  function guidedTranslateStatusText(text) {
    const exact = {
      'Not authenticated.': '未登录。',
      'Select a person first.': '请先选择人物。',
      'Select a relationship first.': '请先选择关系。',
      'Select a conversation first.': '请先选择会话。',
      'No person selected.': '尚未选择人物。',
      'No relationship selected.': '尚未选择关系。',
      'No conversation selected.': '尚未选择会话。',
      'No messages in this conversation.': '当前会话还没有消息。',
      'No timeline events for the selected person.': '当前人物还没有时间线事件。',
      'No evidence-backed recommendations returned.': '当前证据不足以形成可追溯的 Recommendation。',
      'No evidence-backed action was promoted to an Action Plan.': '当前证据不足以形成可进入行动计划的建议。',
      'No persisted Action Plan is currently supported by canonical evidence.': '当前没有仍被 canonical evidence 支持的已保存行动计划。',
      'No currently available proposed Action Plan item requires confirmation.': '当前没有需要你确认的行动计划。',
      'No confirmed Action Decision is currently execution_ready.': '当前没有已确认且可记录执行的行动。',
      'No executed confirmed Action Decision currently needs an Outcome.': '当前没有已执行且等待记录结果的行动。',
      'No observed Outcome currently produces a learning memory proposal.': '当前真实 Outcome 还没有形成可保存的学习记忆建议。'
    };
    if (Object.prototype.hasOwnProperty.call(exact, text)) return exact[text];
    let match = text.match(/^(\d+) person\(s\) available\.$/);
    if (match) return `${match[1]} 个对接人物可用。`;
    match = text.match(/^(\d+) relationship\(s\) for current person\.$/);
    if (match) return `当前人物有 ${match[1]} 条关系记录。`;
    match = text.match(/^(\d+) conversation\(s\) for current person\.$/);
    if (match) return `当前人物有 ${match[1]} 个会话。`;
    match = text.match(/^(\d+) message\(s\) loaded for the selected conversation\.$/);
    if (match) return `已载入当前会话的 ${match[1]} 条消息。`;
    match = text.match(/^(\d+) saved proposal\(s\) loaded\. This read did not create a user decision or execute an action\.$/);
    if (match) return `已读取 ${match[1]} 条已保存行动建议；本次读取没有创建用户决定，也没有执行行动。`;
    return text;
  }

  function guidedLocalizeStatusNode(node) {
    if (!node || !node.classList || !node.classList.contains('status')) return;
    if (node.children.length === 0 && node.textContent) {
      const translated = guidedTranslateStatusText(node.textContent.trim());
      if (translated !== node.textContent.trim()) node.textContent = translated;
    }
  }

  async function guidedGenerateActionPlan() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    guidedActionPlanStatus.textContent = '正在生成 evidence-backed 行动计划，并自动读取保存结果与待确认项…';
    await generateActionPlan();
    await loadSavedActionPlan();
    await loadActionDecisionContext();
    const count = Array.isArray(actionDecisionCandidates) ? actionDecisionCandidates.length : 0;
    guidedActionPlanStatus.textContent = count
      ? `已生成并载入 ${count} 条需要你确认的行动。系统没有自动确认或执行。`
      : '行动计划流程已完成；当前证据没有形成需要确认的行动。系统没有为了推进流程而编造计划。';
  }

  async function guidedLoadFeedbackLearning() {
    if (!selectedPersonId) throw new Error('请先选择人物');
    guidedLearningStatus.textContent = '正在读取 Feedback、学习建议和已保存学习记忆…';
    await loadActionFeedback();
    await loadActionLearning();
    await loadPersistedActionLearning();
    const count = Array.isArray(actionLearningCandidates) ? actionLearningCandidates.length : 0;
    guidedLearningStatus.textContent = `反馈与学习上下文已读取；当前有 ${count} 条学习记忆建议。没有自动保存学习记忆，也没有触发重新分析。`;
  }

  async function guidedRunReanalysis() {
    if (!selectedConversationId) throw new Error('请先选择会话');
    guidedLearningStatus.textContent = '正在读取学习上下文并执行一次显式重新分析…';
    await loadActionReanalysisInputs();
    await runActionReanalysis();
    guidedLearningStatus.textContent = '重新分析已完成。结果只用于决策支持，没有自动生成行动、执行、发送消息或修改关系。';
  }

  guidedReorganizeLayout();
  guidedLocalizeStaticUI();

  bind('guided-generate-action-plan', guidedGenerateActionPlan, guidedActionPlanStatus);
  bind('guided-load-feedback-learning', guidedLoadFeedbackLearning, guidedLearningStatus);
  bind('guided-run-reanalysis', guidedRunReanalysis, guidedLearningStatus);

  const guidedStatusObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      const target = mutation.target.nodeType === Node.TEXT_NODE ? mutation.target.parentElement : mutation.target;
      if (target && target.closest) guidedLocalizeStatusNode(target.closest('.status'));
    });
  });
  document.querySelectorAll('.status').forEach((node) => {
    guidedLocalizeStatusNode(node);
    guidedStatusObserver.observe(node, {childList: true, characterData: true, subtree: true});
  });
'''


GUIDED_WORKFLOW_STYLE = r'''
    .guided-workflow { display: grid; gap: 18px; }
    .guided-hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, .45fr); gap: 16px; align-items: start; padding: 18px; border: 1px solid rgba(127,127,127,.28); border-radius: 14px; }
    .guided-eyebrow { margin: 0 0 6px; font-size: .82rem; font-weight: 700; letter-spacing: .08em; opacity: .65; }
    .guided-hero h2 { margin: 0 0 8px; }
    .guided-settings { border: 1px solid rgba(127,127,127,.28); border-radius: 10px; padding: 10px 12px; }
    .guided-settings > summary, .guided-advanced > summary { cursor: pointer; font-weight: 700; }
    .guided-settings-content, .guided-advanced > div { margin-top: 12px; display: grid; gap: 12px; }
    .guided-step-nav { position: sticky; top: 0; z-index: 10; background: Canvas; padding: 10px 0; margin: 0; }
    .guided-step-nav a { font-size: .92rem; }
    .guided-step { border: 1px solid rgba(127,127,127,.3); border-radius: 14px; padding: 18px; scroll-margin-top: 68px; }
    .guided-step-header { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 14px; }
    .guided-step-header h2 { margin: 0 0 4px; }
    .guided-step-header p { margin: 0; opacity: .76; }
    .guided-step-number { display: inline-grid; place-items: center; width: 34px; height: 34px; flex: 0 0 34px; border-radius: 50%; border: 1px solid currentColor; font-weight: 700; }
    .guided-primary { display: grid; gap: 14px; }
    .guided-primary > fieldset { margin-top: 0; }
    .guided-advanced { margin-top: 14px; padding: 12px 14px; border: 1px dashed rgba(127,127,127,.35); border-radius: 10px; }
    .guided-action-bar { margin: 0 0 14px; padding: 14px; border-radius: 10px; background: rgba(127,127,127,.08); }
    .guided-primary-action { font-weight: 700; }
    .guided-source-empty, .guided-replaced-control { display: none !important; }
    #guided-settings-content > fieldset { margin: 0; }
    #guided-person-primary .workspace-card, #guided-relationship-primary .workspace-card { max-width: 760px; }
    @media (max-width: 760px) {
      .guided-hero { grid-template-columns: 1fr; }
      .guided-step-nav { position: static; }
    }
'''
