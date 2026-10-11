CARD_CLIENT_EXPERIENCE_STYLE = r'''
    /* TEST-167: customer-facing card-game shell over the verified lifecycle. */
    body {
      max-width: 1680px !important;
      min-height: 100vh;
      padding: 18px 22px 54px !important;
      background:
        radial-gradient(circle at 12% 14%, rgba(99, 102, 241, .18), transparent 30rem),
        radial-gradient(circle at 86% 10%, rgba(34, 211, 238, .16), transparent 26rem),
        radial-gradient(circle at 52% 92%, rgba(168, 85, 247, .10), transparent 34rem),
        linear-gradient(180deg, #f7fbff 0%, #eef6ff 48%, #f8fbff 100%) !important;
    }

    body > header,
    body > nav:not([hidden]),
    #guided-workflow > .guided-hero,
    #guided-workflow > .guided-step-nav,
    #guided-step-1,
    #guided-step-2,
    #guided-step-3,
    #guided-step-4,
    #guided-step-5,
    #guided-step-6 {
      display: none !important;
    }

    #guided-workflow {
      display: block !important;
      margin: 0 !important;
      padding: 0 !important;
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
    }

    #client-experience-shell {
      display: grid;
      gap: 22px;
      width: 100%;
    }

    .client-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding: 8px 4px 0;
    }

    .client-brand h1 {
      margin: 0;
      color: #14213d;
      font-size: clamp(1.55rem, 3.5vw, 2.4rem);
      letter-spacing: -.035em;
    }

    .client-brand p {
      margin: 5px 0 0;
      color: #65758b;
      font-size: .9rem;
    }

    #client-settings-host > #guided-settings {
      width: auto !important;
      min-width: 0;
      margin: 0 !important;
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
    }

    #client-settings-host > #guided-settings > summary {
      list-style: none;
      cursor: pointer;
      padding: 9px 13px;
      border: 1px solid rgba(90, 110, 150, .20);
      border-radius: 999px;
      color: #46566e;
      background: rgba(255,255,255,.74);
      box-shadow: 0 8px 22px rgba(64, 89, 122, .08);
      font-weight: 700;
    }

    #client-settings-host > #guided-settings > summary::-webkit-details-marker { display: none; }

    #client-settings-host > #guided-settings[open] {
      position: relative;
      z-index: 60;
    }

    #client-settings-host #guided-settings-content {
      position: absolute;
      right: 0;
      top: 48px;
      width: min(920px, calc(100vw - 44px));
      max-height: min(76vh, 760px);
      padding: 12px !important;
      border: 1px solid rgba(75, 101, 145, .18);
      border-radius: 18px;
      background: rgba(248, 252, 255, .97);
      box-shadow: 0 26px 70px rgba(42, 62, 98, .20);
      backdrop-filter: blur(24px);
    }

    .client-stage {
      position: relative;
      padding: 22px;
      border: 1px solid rgba(78, 105, 150, .15);
      border-radius: 26px;
      background: rgba(255,255,255,.66);
      box-shadow: 0 22px 64px rgba(42, 75, 120, .10);
      backdrop-filter: blur(18px);
    }

    .client-stage::before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      border-radius: inherit;
      background: linear-gradient(135deg, rgba(255,255,255,.66), transparent 42%, rgba(99,102,241,.035));
    }

    .client-stage-header {
      position: relative;
      z-index: 1;
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .client-stage-header h2 {
      margin: 0;
      color: #18233b;
      font-size: clamp(1.15rem, 2vw, 1.55rem);
    }

    .client-stage-header p {
      margin: 4px 0 0;
      color: #718096;
      font-size: .88rem;
    }

    #client-person-deck {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
      gap: 20px;
      perspective: 1400px;
    }

    .client-person-card {
      position: relative;
      min-height: 330px;
      perspective: 1200px;
      animation: clientCardFloat 6s ease-in-out infinite;
      animation-delay: var(--client-float-delay, 0s);
      transition: grid-column .25s ease, min-height .25s ease;
    }

    .client-person-card.is-flipped {
      grid-column: span 2;
      min-height: 610px;
      animation-play-state: paused;
    }

    .client-card-inner {
      position: absolute;
      inset: 0;
      transform-style: preserve-3d;
      transition: transform .62s cubic-bezier(.2,.78,.2,1);
    }

    .client-person-card.is-flipped .client-card-inner {
      transform: rotateY(180deg);
    }

    .client-card-face {
      position: absolute;
      inset: 0;
      overflow: auto;
      box-sizing: border-box;
      border: 1px solid rgba(76, 101, 150, .18);
      border-radius: 26px;
      backface-visibility: hidden;
      -webkit-backface-visibility: hidden;
      background:
        radial-gradient(circle at 82% 10%, rgba(70, 195, 255, .22), transparent 10rem),
        linear-gradient(145deg, rgba(255,255,255,.98), rgba(234,244,255,.93));
      box-shadow: 0 22px 48px rgba(42, 72, 118, .16), inset 0 1px 0 rgba(255,255,255,.90);
    }

    .client-card-front {
      display: flex;
      flex-direction: column;
      width: 100%;
      margin: 0 !important;
      padding: 22px !important;
      text-align: left;
      cursor: pointer;
      color: #17233b !important;
      border-color: rgba(83, 112, 166, .22) !important;
    }

    .client-card-front:hover:not(:disabled) {
      transform: translateY(-7px) rotateX(1.5deg) rotateY(-1.5deg) !important;
      box-shadow: 0 30px 62px rgba(45, 77, 128, .22), 0 0 0 1px rgba(99,102,241,.09) !important;
    }

    .client-card-back {
      transform: rotateY(180deg);
      padding: 20px;
      scrollbar-gutter: stable;
    }

    .client-person-card.is-selected .client-card-face {
      border-color: rgba(79, 70, 229, .44);
      box-shadow: 0 26px 58px rgba(72, 83, 176, .20), inset 0 0 0 1px rgba(79,70,229,.08);
    }

    .client-card-rarity {
      display: inline-flex;
      align-self: flex-start;
      padding: 4px 9px;
      border-radius: 999px;
      color: #53627a;
      background: rgba(255,255,255,.72);
      border: 1px solid rgba(75, 99, 143, .12);
      font-size: .68rem;
      font-weight: 800;
      letter-spacing: .11em;
      text-transform: uppercase;
    }

    .client-card-avatar {
      display: grid;
      place-items: center;
      width: 82px;
      height: 82px;
      margin: 28px 0 22px;
      border-radius: 24px;
      color: white;
      background: linear-gradient(145deg, #4f46e5, #22b8cf);
      box-shadow: 0 18px 34px rgba(73, 86, 181, .27), inset 0 1px 0 rgba(255,255,255,.35);
      font-size: 2rem;
      font-weight: 900;
    }

    .client-card-name {
      margin-top: auto;
      color: #14213d;
      font-size: 1.28rem;
      font-weight: 900;
      letter-spacing: -.02em;
    }

    .client-card-subtitle {
      margin-top: 5px;
      color: #6d7b90;
      font-size: .86rem;
      line-height: 1.45;
    }

    .client-new-card .client-card-face {
      background:
        radial-gradient(circle at 50% 16%, rgba(168, 85, 247, .13), transparent 11rem),
        linear-gradient(145deg, rgba(253,252,255,.98), rgba(242,238,255,.93));
      border-style: dashed;
    }

    .client-new-card .client-card-avatar {
      background: linear-gradient(145deg, #7c3aed, #4f46e5);
    }

    .client-card-section-title {
      margin: 14px 0 7px;
      color: #34445e;
      font-size: .78rem;
      font-weight: 900;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .client-card-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 9px 12px;
    }

    .client-card-grid .client-span-2 { grid-column: 1 / -1; }
    .client-card-back label { margin-top: 7px !important; color: #526279; font-size: .78rem; }
    .client-card-back input,
    .client-card-back select,
    .client-card-back textarea { padding: 8px 9px !important; }
    .client-card-back textarea { min-height: 62px !important; }

    .client-card-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 10px;
    }

    .client-card-actions button { margin: 0 !important; }

    .client-primary-button {
      color: white !important;
      border-color: transparent !important;
      background: linear-gradient(135deg, #4f46e5, #0891b2) !important;
      box-shadow: 0 10px 24px rgba(67, 73, 168, .22) !important;
    }

    .client-card-message {
      min-height: 1.3em;
      margin-top: 9px;
      color: #526279;
      font-size: .78rem;
    }

    #client-conversation-host,
    #client-results-grid {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
      gap: 14px;
    }

    #client-conversation-host > .workspace-card,
    #client-conversation-host > fieldset,
    #client-results-grid > .workspace-card,
    #client-results-grid > .client-result-card,
    #client-reality-checks {
      margin: 0 !important;
      border: 1px solid rgba(78, 105, 150, .14) !important;
      border-radius: 20px !important;
      background: rgba(255,255,255,.78) !important;
      box-shadow: 0 14px 38px rgba(47, 76, 118, .08) !important;
    }

    #client-conversation-host #conversation-select { min-height: 8rem; }
    #client-conversation-host #conversation-content { grid-column: 1 / -1; }
    #client-conversation-host #conversation-content > .note { display: none !important; }

    .client-result-card {
      padding: 15px;
      min-width: 0;
    }

    .client-result-card h3 {
      margin: 0 0 9px;
      color: #26344d;
      font-size: 1rem;
    }

    #client-reply-host #load-strategic-reply,
    #client-reply-host .note,
    #client-reply-host #strategic-reply-context-heading,
    #client-reply-host ~ .workspace-card,
    #client-reply-host #prepare-strategic-reply-message {
      display: none !important;
    }

    #client-reply-host #strategic-reply-status {
      font-size: .8rem;
      color: #68788f;
      background: transparent !important;
      border: 0 !important;
      padding: 0 0 7px !important;
    }

    #client-action-result #generated-action-plan-list .session-row > div:not(:first-child),
    #client-review-result #action-reanalysis-analysis > div:not(:first-child),
    #client-review-result #action-reanalysis-recommendations .session-row > div:not(:first-child) {
      display: none !important;
    }

    #client-action-result .session-row,
    #client-review-result .session-row {
      border: 0 !important;
      padding: 8px 0 !important;
    }

    #client-automation-status {
      grid-column: 1 / -1;
      margin: 0 !important;
      padding: 11px 13px !important;
      border-radius: 14px !important;
      color: #42536d;
      background: linear-gradient(135deg, rgba(238,244,255,.95), rgba(235,251,255,.92)) !important;
    }

    #client-reality-checks {
      position: relative;
      z-index: 1;
      padding: 12px 14px;
      grid-column: 1 / -1;
    }

    #client-reality-checks > summary {
      cursor: pointer;
      color: #394a64;
      font-weight: 850;
    }

    #client-reality-host {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }

    #client-reality-host .workspace-card {
      margin: 0 !important;
      padding: 12px !important;
      border-radius: 15px !important;
      background: rgba(250,252,255,.90) !important;
      box-shadow: none !important;
    }

    #client-reality-host .note,
    #client-reality-host #load-action-decision-context,
    #client-reality-host #load-action-execution-context,
    #client-reality-host #load-action-outcome-context,
    #client-reality-host #action-decision-status,
    #client-reality-host #action-execution-status,
    #client-reality-host #action-outcome-status {
      display: none !important;
    }

    .client-no-action {
      color: #718096;
      font-size: .84rem;
      padding: 7px 0;
    }

    @keyframes clientCardFloat {
      0%, 100% { transform: translateY(0) rotateZ(0deg); }
      50% { transform: translateY(-7px) rotateZ(.25deg); }
    }

    @media (prefers-reduced-motion: reduce) {
      .client-person-card { animation: none !important; }
      .client-card-inner { transition: none !important; }
      .client-card-front:hover:not(:disabled) { transform: none !important; }
    }

    @media (max-width: 820px) {
      body { padding: 12px 10px 36px !important; }
      .client-stage { padding: 15px; border-radius: 20px; }
      .client-topbar { align-items: flex-start; }
      #client-person-deck { grid-template-columns: 1fr; }
      .client-person-card.is-flipped { grid-column: span 1; min-height: 700px; }
      .client-card-grid { grid-template-columns: 1fr; }
      .client-card-grid .client-span-2 { grid-column: auto; }
      #client-settings-host #guided-settings-content { right: -4px; width: calc(100vw - 20px); }
    }
'''


CARD_CLIENT_EXPERIENCE_SCRIPT = r'''
  const clientCardState = {
    renderingDeck: false,
    refreshingReality: false,
  };

  function clientEl(tag, className = '', text = '') {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function clientSetLabel(forId, text) {
    const label = document.querySelector(`label[for="${forId}"]`);
    if (label) label.textContent = text;
  }

  function clientInput(labelText, value = '', type = 'text') {
    const wrap = clientEl('div');
    const label = clientEl('label', '', labelText);
    const input = document.createElement('input');
    input.type = type;
    input.value = value == null ? '' : String(value);
    wrap.append(label, input);
    return {wrap, input};
  }

  function clientTextarea(labelText, value = '') {
    const wrap = clientEl('div', 'client-span-2');
    const label = clientEl('label', '', labelText);
    const textarea = document.createElement('textarea');
    textarea.value = value == null ? '' : String(value);
    wrap.append(label, textarea);
    return {wrap, textarea};
  }

  function clientPersonInitial(label) {
    const chars = Array.from(String(label || '').trim());
    return chars.length ? chars[0].toUpperCase() : '?';
  }

  function clientMakeShell() {
    const guided = byId('guided-workflow');
    if (!guided || byId('client-experience-shell')) return;

    const shell = clientEl('div');
    shell.id = 'client-experience-shell';

    const topbar = clientEl('div', 'client-topbar');
    const brand = clientEl('div', 'client-brand');
    brand.append(
      clientEl('h1', '', 'AI 恋爱军师'),
      clientEl('p', '', '选择人物，导入真实对话，系统自动整理回复建议、下一步行动和复盘结果。'),
    );
    const settingsHost = clientEl('div');
    settingsHost.id = 'client-settings-host';
    topbar.append(brand, settingsHost);

    const personStage = clientEl('section', 'client-stage');
    personStage.id = 'client-person-stage';
    const personHeader = clientEl('div', 'client-stage-header');
    const personTitle = clientEl('div');
    personTitle.append(
      clientEl('h2', '', '人物卡组'),
      clientEl('p', '', '点击人物卡翻面查看人物关系与资料；修改后直接保存。'),
    );
    personHeader.append(personTitle);
    const deck = clientEl('div');
    deck.id = 'client-person-deck';
    deck.setAttribute('aria-label', '人物卡组');
    personStage.append(personHeader, deck);

    const conversationStage = clientEl('section', 'client-stage');
    conversationStage.id = 'client-conversation-stage';
    const conversationHeader = clientEl('div', 'client-stage-header');
    const conversationTitle = clientEl('div');
    conversationTitle.append(
      clientEl('h2', '', '当前会话'),
      clientEl('p', '', '选择会话后，可单条补充或批量导入对话；新增真实内容会自动触发系统更新。'),
    );
    conversationHeader.append(conversationTitle);
    const conversationHost = clientEl('div');
    conversationHost.id = 'client-conversation-host';
    conversationStage.append(conversationHeader, conversationHost);

    const resultsStage = clientEl('section', 'client-stage');
    resultsStage.id = 'client-results-stage';
    const resultsHeader = clientEl('div', 'client-stage-header');
    const resultsTitle = clientEl('div');
    resultsTitle.append(
      clientEl('h2', '', '军师结果'),
      clientEl('p', '', '系统只把可用结果留在这里；分析链、证据校验和复盘过程在后台完成。'),
    );
    resultsHeader.append(resultsTitle);
    const resultsGrid = clientEl('div');
    resultsGrid.id = 'client-results-grid';
    resultsStage.append(resultsHeader, resultsGrid);

    shell.append(topbar, personStage, conversationStage, resultsStage);
    guided.prepend(shell);

    const settings = byId('guided-settings');
    if (settings) settingsHost.appendChild(settings);

    const conversationCard = byId('conversation-heading')?.closest('.workspace-card');
    const conversationContent = byId('conversation-content');
    if (conversationCard) conversationHost.appendChild(conversationCard);
    if (conversationContent) conversationHost.appendChild(conversationContent);

    const automation = byId('lifecycle-automation-status');
    if (automation) {
      automation.id = 'client-automation-status';
      resultsGrid.appendChild(automation);
    }

    const replyCard = byId('strategic-reply-heading')?.closest('.workspace-card');
    if (replyCard) {
      const replyHost = clientEl('div');
      replyHost.id = 'client-reply-host';
      replyHost.appendChild(replyCard);
      resultsGrid.appendChild(replyHost);
    }

    const actionCard = clientEl('section', 'client-result-card');
    actionCard.id = 'client-action-result';
    actionCard.append(clientEl('h3', '', '下一步行动'));
    const generatedActions = byId('generated-action-plan-list');
    if (generatedActions) actionCard.appendChild(generatedActions);
    resultsGrid.appendChild(actionCard);

    const reviewCard = clientEl('section', 'client-result-card');
    reviewCard.id = 'client-review-result';
    reviewCard.append(clientEl('h3', '', '最新复盘'));
    const analysis = byId('action-reanalysis-analysis');
    const recommendations = byId('action-reanalysis-recommendations');
    if (analysis) reviewCard.appendChild(analysis);
    if (recommendations) reviewCard.appendChild(recommendations);
    resultsGrid.appendChild(reviewCard);

    const reality = document.createElement('details');
    reality.id = 'client-reality-checks';
    const realitySummary = clientEl('summary', '', '需要你确认 · 0');
    realitySummary.id = 'client-reality-summary';
    const realityHost = clientEl('div');
    realityHost.id = 'client-reality-host';
    reality.append(realitySummary, realityHost);
    resultsStage.appendChild(reality);

    [
      ['action-decision-heading', '需要你确认的下一步'],
      ['action-execution-heading', '现实执行确认'],
      ['action-outcome-heading', '实际结果'],
    ].forEach(([headingId, title]) => {
      const heading = byId(headingId);
      const card = heading?.closest('.workspace-card');
      if (heading) heading.textContent = title;
      if (card) realityHost.appendChild(card);
    });

    guidedSetText('confirm-action-decision', '确认采用');
    guidedSetText('reject-action-decision', '暂不采用');
    guidedSetText('record-action-execution', '我已执行');
    guidedSetText('record-action-outcome', '保存结果并自动复盘');
    guidedSetText('strategic-reply-heading', '回复建议');
    guidedSetText('copy-strategic-reply', '复制回复');
    guidedSetText('restore-strategic-reply', '恢复系统建议');
    guidedSetText('conversation-heading', '会话');
    guidedSetText('message-heading', '单条消息');
    guidedSetText('text-import-heading', '批量对话');
    clientSetLabel('conversation-select', '选择会话');
    clientSetLabel('strategic-reply-draft', '建议回复');
    clientSetLabel('action-decision-recommendation', '选择下一步');
    clientSetLabel('action-decision-note', '备注（可选）');
    clientSetLabel('action-execution-executed-at', '执行时间（可选）');
    clientSetLabel('action-execution-note', '备注（可选）');
    clientSetLabel('action-outcome-state', '实际结果');
    clientSetLabel('action-outcome-note', '结果备注（可选）');

    const outcomeSelect = byId('action-outcome-state');
    if (outcomeSelect) {
      const labels = {completed: '已完成', skipped: '未执行 / 跳过', failed: '未达到预期'};
      Array.from(outcomeSelect.options).forEach((option) => {
        if (labels[option.value]) option.textContent = labels[option.value];
      });
    }
  }

  function clientMarkSelectedCard() {
    document.querySelectorAll('#client-person-deck .client-person-card[data-person-id]').forEach((card) => {
      card.classList.toggle('is-selected', card.dataset.personId === selectedPersonId);
    });
  }

  function clientBuildFront(card, label, isNew = false) {
    const front = clientEl('button', 'client-card-face client-card-front');
    front.type = 'button';
    front.append(
      clientEl('span', 'client-card-rarity', isNew ? 'NEW CARD' : 'PERSON CARD'),
      clientEl('div', 'client-card-avatar', isNew ? '+' : clientPersonInitial(label)),
      clientEl('div', 'client-card-name', isNew ? '新建人物' : label),
      clientEl('div', 'client-card-subtitle', isNew ? '创建人物，并可同时补充关系资料。' : '点击翻面查看关系、资料并修改。'),
    );
    card.querySelector('.client-card-inner').appendChild(front);
    return front;
  }

  function clientBuildCardBase(personId = '') {
    const card = clientEl('article', 'client-person-card');
    if (personId) card.dataset.personId = personId;
    const inner = clientEl('div', 'client-card-inner');
    card.appendChild(inner);
    return card;
  }

  async function clientSelectPerson(personId) {
    const select = byId('person-select');
    if (!select) return;
    select.value = personId;
    select.dispatchEvent(new Event('change', {bubbles: true}));
    clientMarkSelectedCard();
  }

  function clientRelationshipPayload(personId, fields) {
    return {
      person_id: personId,
      status: fields.status.input.value.trim() || 'unknown',
      stage: fields.stage.input.value.trim() || 'unknown',
      long_term_goal: fields.longTerm.textarea.value.trim() || null,
      current_goal: fields.current.textarea.value.trim() || null,
      notes: fields.notes.textarea.value.trim() || null,
    };
  }

  function clientMakeRelationshipFields(initial = {}) {
    const status = clientInput('关系状态', initial.status || '');
    const stage = clientInput('关系阶段', initial.stage || '');
    const longTerm = clientTextarea('长期目标', initial.long_term_goal || '');
    const current = clientTextarea('当前目标', initial.current_goal || '');
    const notes = clientTextarea('关系备注', initial.notes || '');
    return {status, stage, longTerm, current, notes};
  }

  function clientAppendRelationshipFields(grid, fields) {
    grid.append(
      fields.status.wrap,
      fields.stage.wrap,
      fields.longTerm.wrap,
      fields.current.wrap,
      fields.notes.wrap,
    );
  }

  async function clientPopulatePersonBack(card, personId) {
    const back = card.querySelector('.client-card-back');
    back.replaceChildren(clientEl('div', 'client-card-message', '正在读取人物资料…'));
    try {
      const [person, relationships] = await Promise.all([
        api(`/api/v1/persons/${encodeURIComponent(personId)}`),
        api('/api/v1/relationships'),
      ]);
      const personRelationships = Array.isArray(relationships)
        ? relationships.filter((item) => item.person_id === personId)
        : [];

      back.replaceChildren();
      const title = clientEl('div', 'client-card-section-title', '人物资料');
      const personGrid = clientEl('div', 'client-card-grid');
      const name = clientInput('姓名 / 标识', person.name || '');
      const nickname = clientInput('昵称', person.nickname || '');
      const personNotes = clientTextarea('人物备注', person.notes || '');
      personGrid.append(name.wrap, nickname.wrap, personNotes.wrap);

      const relationTitle = clientEl('div', 'client-card-section-title', '人物关系');
      const relationGrid = clientEl('div', 'client-card-grid');
      const relationSelectWrap = clientEl('div', 'client-span-2');
      const relationLabel = clientEl('label', '', '关系记录');
      const relationSelect = document.createElement('select');
      const newOption = document.createElement('option');
      newOption.value = '';
      newOption.textContent = '＋ 新建关系';
      relationSelect.appendChild(newOption);
      personRelationships.forEach((item, index) => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = `${index + 1}. ${item.status || 'unknown'} · ${item.stage || 'unknown'}`;
        relationSelect.appendChild(option);
      });
      const preferred = personRelationships.find((item) => item.id === selectedRelationshipId) || personRelationships[0];
      if (preferred) relationSelect.value = preferred.id;
      relationSelectWrap.append(relationLabel, relationSelect);
      relationGrid.appendChild(relationSelectWrap);

      let relationFields = clientMakeRelationshipFields(preferred || {});
      clientAppendRelationshipFields(relationGrid, relationFields);

      function renderRelationshipFields(item) {
        relationGrid.querySelectorAll(':scope > :not(.client-span-2):not(:first-child)').forEach(() => {});
        while (relationGrid.children.length > 1) relationGrid.removeChild(relationGrid.lastChild);
        relationFields = clientMakeRelationshipFields(item || {});
        clientAppendRelationshipFields(relationGrid, relationFields);
      }

      relationSelect.addEventListener('change', async () => {
        const item = personRelationships.find((candidate) => candidate.id === relationSelect.value) || null;
        renderRelationshipFields(item);
        const underlying = byId('relationship-select');
        if (underlying) {
          underlying.value = item ? item.id : '';
          underlying.dispatchEvent(new Event('change', {bubbles: true}));
        }
      });

      const actions = clientEl('div', 'client-card-actions');
      const savePerson = clientEl('button', 'client-primary-button', '保存人物资料');
      savePerson.type = 'button';
      const saveRelation = clientEl('button', 'client-primary-button', '保存关系资料');
      saveRelation.type = 'button';
      const close = clientEl('button', '', '翻回卡面');
      close.type = 'button';
      const message = clientEl('div', 'client-card-message');
      actions.append(savePerson, saveRelation, close);

      savePerson.addEventListener('click', async () => {
        const nextName = name.input.value.trim();
        if (!nextName) {
          message.textContent = '姓名 / 标识不能为空。';
          return;
        }
        savePerson.disabled = true;
        message.textContent = '正在保存人物资料…';
        try {
          await api(`/api/v1/persons/${encodeURIComponent(personId)}`, {
            method: 'PATCH',
            body: JSON.stringify({
              name: nextName,
              nickname: nickname.input.value.trim() || null,
              notes: personNotes.textarea.value.trim() || null,
            }),
          });
          await loadPersons();
          await clientSelectPerson(personId);
          message.textContent = '人物资料已保存。';
        } catch (error) {
          message.textContent = error instanceof Error ? error.message : String(error);
        } finally {
          savePerson.disabled = false;
        }
      });

      saveRelation.addEventListener('click', async () => {
        saveRelation.disabled = true;
        message.textContent = '正在保存关系资料…';
        try {
          const payload = clientRelationshipPayload(personId, relationFields);
          let saved;
          if (relationSelect.value) {
            const {person_id, ...patchPayload} = payload;
            saved = await api(`/api/v1/relationships/${encodeURIComponent(relationSelect.value)}`, {
              method: 'PATCH',
              body: JSON.stringify(patchPayload),
            });
          } else {
            saved = await api('/api/v1/relationships', {
              method: 'POST',
              body: JSON.stringify(payload),
            });
          }
          await loadRelationships();
          const underlying = byId('relationship-select');
          if (underlying) {
            underlying.value = saved.id;
            underlying.dispatchEvent(new Event('change', {bubbles: true}));
          }
          await clientPopulatePersonBack(card, personId);
        } catch (error) {
          message.textContent = error instanceof Error ? error.message : String(error);
        } finally {
          saveRelation.disabled = false;
        }
      });

      close.addEventListener('click', () => card.classList.remove('is-flipped'));
      back.append(title, personGrid, relationTitle, relationGrid, actions, message);
    } catch (error) {
      back.replaceChildren(clientEl('div', 'client-card-message', error instanceof Error ? error.message : String(error)));
    }
  }

  function clientBuildPersonCard(personId, label, index) {
    const card = clientBuildCardBase(personId);
    card.style.setProperty('--client-float-delay', `${-(index % 5) * 0.7}s`);
    const front = clientBuildFront(card, label, false);
    const back = clientEl('section', 'client-card-face client-card-back');
    back.append(clientEl('div', 'client-card-message', '点击卡片读取人物资料。'));
    card.querySelector('.client-card-inner').appendChild(back);
    front.addEventListener('click', async () => {
      await clientSelectPerson(personId);
      await clientPopulatePersonBack(card, personId);
      card.classList.add('is-flipped');
    });
    return card;
  }

  function clientBuildNewPersonCard(index) {
    const card = clientBuildCardBase();
    card.classList.add('client-new-card');
    card.style.setProperty('--client-float-delay', `${-(index % 5) * 0.7}s`);
    const front = clientBuildFront(card, '新建人物', true);
    const back = clientEl('section', 'client-card-face client-card-back');
    card.querySelector('.client-card-inner').appendChild(back);

    const title = clientEl('div', 'client-card-section-title', '新建人物');
    const personGrid = clientEl('div', 'client-card-grid');
    const name = clientInput('姓名 / 标识');
    const nickname = clientInput('昵称');
    const notes = clientTextarea('人物备注');
    personGrid.append(name.wrap, nickname.wrap, notes.wrap);

    const relationTitle = clientEl('div', 'client-card-section-title', '关系资料（可选）');
    const relationGrid = clientEl('div', 'client-card-grid');
    const relationFields = clientMakeRelationshipFields({});
    clientAppendRelationshipFields(relationGrid, relationFields);

    const actions = clientEl('div', 'client-card-actions');
    const create = clientEl('button', 'client-primary-button', '创建人物卡');
    create.type = 'button';
    const close = clientEl('button', '', '翻回卡面');
    close.type = 'button';
    const message = clientEl('div', 'client-card-message');
    actions.append(create, close);
    back.append(title, personGrid, relationTitle, relationGrid, actions, message);

    front.addEventListener('click', () => card.classList.add('is-flipped'));
    close.addEventListener('click', () => card.classList.remove('is-flipped'));

    create.addEventListener('click', async () => {
      const personName = name.input.value.trim();
      if (!personName) {
        message.textContent = '姓名 / 标识不能为空。';
        return;
      }
      create.disabled = true;
      message.textContent = '正在创建人物卡…';
      try {
        const created = await api('/api/v1/persons', {
          method: 'POST',
          body: JSON.stringify({
            name: personName,
            nickname: nickname.input.value.trim() || null,
            notes: notes.textarea.value.trim() || null,
          }),
        });

        const relationshipPayload = clientRelationshipPayload(created.id, relationFields);
        const hasRelationshipData = [
          relationFields.status.input.value,
          relationFields.stage.input.value,
          relationFields.longTerm.textarea.value,
          relationFields.current.textarea.value,
          relationFields.notes.textarea.value,
        ].some((value) => String(value || '').trim());
        let createdRelationship = null;
        if (hasRelationshipData) {
          createdRelationship = await api('/api/v1/relationships', {
            method: 'POST',
            body: JSON.stringify(relationshipPayload),
          });
        }

        await loadPersons();
        await clientSelectPerson(created.id);
        if (createdRelationship) {
          await loadRelationships();
          const underlying = byId('relationship-select');
          if (underlying) {
            underlying.value = createdRelationship.id;
            underlying.dispatchEvent(new Event('change', {bubbles: true}));
          }
        }
        clientRenderPersonDeck();
        const createdCard = document.querySelector(`#client-person-deck .client-person-card[data-person-id="${CSS.escape(created.id)}"]`);
        if (createdCard) {
          await clientPopulatePersonBack(createdCard, created.id);
          createdCard.classList.add('is-flipped');
        }
      } catch (error) {
        message.textContent = error instanceof Error ? error.message : String(error);
      } finally {
        create.disabled = false;
      }
    });

    return card;
  }

  function clientRenderPersonDeck() {
    if (clientCardState.renderingDeck) return;
    const select = byId('person-select');
    const deck = byId('client-person-deck');
    if (!select || !deck) return;
    clientCardState.renderingDeck = true;
    try {
      const options = Array.from(select.options).filter((option) => option.value);
      deck.replaceChildren();
      options.forEach((option, index) => {
        deck.appendChild(clientBuildPersonCard(option.value, option.textContent || '未命名人物', index));
      });
      deck.appendChild(clientBuildNewPersonCard(options.length));
      clientMarkSelectedCard();
    } finally {
      clientCardState.renderingDeck = false;
    }
  }

  function clientNormalizeRealityOptions() {
    [
      ['action-execution-decision', '已确认行动'],
      ['action-outcome-decision', '已执行行动'],
    ].forEach(([id, prefix]) => {
      const select = byId(id);
      if (!select) return;
      let count = 0;
      Array.from(select.options).forEach((option) => {
        if (!option.value) return;
        count += 1;
        option.textContent = `${prefix} ${count}`;
      });
    });
  }

  function clientAutoSelectSingle(selectId) {
    const select = byId(selectId);
    if (!select || select.disabled) return 0;
    const options = Array.from(select.options).filter((option) => option.value);
    if (options.length === 1 && !select.value) {
      select.value = options[0].value;
      select.dispatchEvent(new Event('change', {bubbles: true}));
    }
    return options.length;
  }

  function clientRefreshRealityPrompt() {
    clientNormalizeRealityOptions();
    const counts = [
      clientAutoSelectSingle('action-decision-recommendation'),
      clientAutoSelectSingle('action-execution-decision'),
      clientAutoSelectSingle('action-outcome-decision'),
    ];
    const total = counts.reduce((sum, count) => sum + count, 0);
    const summary = byId('client-reality-summary');
    const details = byId('client-reality-checks');
    if (summary) summary.textContent = total ? `需要你确认 · ${total}` : '目前无需你确认';
    if (details && total > 0) details.open = true;
  }

  async function clientRefreshReadOnlyState() {
    if (clientCardState.refreshingReality || !selectedPersonId) return;
    clientCardState.refreshingReality = true;
    try {
      const tasks = [
        loadSavedActionPlan(),
        loadActionDecisionContext(),
        loadActionExecutionContext(),
        loadActionOutcomeContext(),
      ];
      await Promise.allSettled(tasks);
      clientRefreshRealityPrompt();
    } finally {
      clientCardState.refreshingReality = false;
    }
  }

  function clientInstallObservers() {
    const personSelect = byId('person-select');
    if (personSelect) {
      new MutationObserver(() => clientRenderPersonDeck()).observe(personSelect, {childList: true});
      personSelect.addEventListener('change', () => {
        clientMarkSelectedCard();
        setTimeout(() => { void clientRefreshReadOnlyState(); }, 0);
      });
    }

    ['action-decision-recommendation', 'action-execution-decision', 'action-outcome-decision'].forEach((id) => {
      const select = byId(id);
      if (!select) return;
      new MutationObserver(() => clientRefreshRealityPrompt()).observe(select, {childList: true, attributes: true});
      select.addEventListener('change', clientRefreshRealityPrompt);
    });

    window.addEventListener('junshi:evidence-changed', () => {
      const status = byId('client-automation-status');
      if (status) status.textContent = '新对话已记录，正在自动更新回复建议和下一步行动…';
    });
    window.addEventListener('junshi:decision-recorded', () => setTimeout(clientRefreshRealityPrompt, 0));
    window.addEventListener('junshi:execution-recorded', () => setTimeout(clientRefreshRealityPrompt, 0));
    window.addEventListener('junshi:outcome-recorded', () => setTimeout(clientRefreshRealityPrompt, 0));
  }

  clientMakeShell();
  clientInstallObservers();
  clientRenderPersonDeck();
  clientRefreshRealityPrompt();
'''
