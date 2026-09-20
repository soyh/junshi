VISUAL_THEME_STYLE = r'''
    :root {
      color-scheme: light !important;
      --sky-950: #08233d;
      --sky-900: #0b2f50;
      --sky-800: #0d4673;
      --sky-700: #0969a8;
      --sky-600: #0787cf;
      --sky-500: #19a7e8;
      --sky-400: #58c8f5;
      --sky-300: #8fddfb;
      --sky-200: #c4eeff;
      --sky-100: #e2f6ff;
      --sky-50: #f4fbff;
      --ink: #102a43;
      --muted: #5d7790;
      --line: rgba(26, 154, 221, .22);
      --panel: rgba(255, 255, 255, .78);
      --panel-strong: rgba(255, 255, 255, .94);
      --shadow: 0 18px 50px rgba(16, 100, 150, .13);
      --glow: 0 0 0 1px rgba(101, 208, 255, .20), 0 20px 70px rgba(25, 167, 232, .12);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    }

    html {
      min-height: 100%;
      background:
        radial-gradient(circle at 14% 8%, rgba(76, 201, 255, .26), transparent 30rem),
        radial-gradient(circle at 84% 18%, rgba(35, 116, 255, .14), transparent 28rem),
        linear-gradient(180deg, #edf9ff 0%, #f7fcff 42%, #eef8ff 100%);
      background-attachment: fixed;
    }

    body {
      position: relative;
      max-width: 1440px;
      margin: 0 auto;
      padding: 30px 26px 70px;
      color: var(--ink);
      background: transparent;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: -1;
      opacity: .36;
      background-image:
        linear-gradient(rgba(43, 155, 214, .06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(43, 155, 214, .06) 1px, transparent 1px);
      background-size: 34px 34px;
      mask-image: linear-gradient(to bottom, #000 0%, rgba(0,0,0,.38) 58%, transparent 100%);
    }

    body > header {
      position: relative;
      overflow: hidden;
      padding: 24px 26px 20px;
      margin-bottom: 22px;
      border: 1px solid rgba(81, 193, 241, .30);
      border-radius: 24px;
      background:
        linear-gradient(135deg, rgba(255,255,255,.96), rgba(228,247,255,.80)),
        linear-gradient(90deg, rgba(18,162,229,.08), rgba(53,115,255,.04));
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    body > header::after {
      content: "";
      position: absolute;
      right: -80px;
      top: -120px;
      width: 330px;
      height: 330px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(80, 210, 255, .32), rgba(80, 210, 255, 0) 68%);
      pointer-events: none;
    }

    body > header h1 {
      margin: 0;
      font-size: clamp(1.9rem, 4vw, 3rem);
      letter-spacing: -.035em;
      color: var(--sky-950);
    }

    .visual-system-kicker {
      margin: 7px 0 0;
      color: var(--sky-700);
      font-size: .78rem;
      font-weight: 800;
      letter-spacing: .18em;
      text-transform: uppercase;
    }

    nav:not([hidden]) {
      gap: 8px;
    }

    nav:not([hidden]) a {
      border-color: rgba(38, 161, 220, .22);
      background: rgba(255, 255, 255, .68);
      color: var(--sky-800);
      box-shadow: 0 6px 18px rgba(16, 111, 165, .06);
      transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease, background .16s ease;
    }

    nav:not([hidden]) a:hover {
      transform: translateY(-2px);
      border-color: rgba(25, 167, 232, .48);
      background: rgba(245, 252, 255, .98);
      box-shadow: 0 10px 24px rgba(16, 111, 165, .12);
    }

    fieldset,
    .guided-step,
    .guided-hero,
    .workspace-card,
    .guided-settings,
    .guided-advanced {
      border-color: var(--line) !important;
      background: var(--panel);
      box-shadow: 0 10px 34px rgba(32, 115, 160, .07);
      backdrop-filter: blur(14px);
    }

    fieldset,
    .guided-step,
    .guided-hero {
      border-radius: 20px !important;
    }

    .workspace-card,
    .guided-settings,
    .guided-advanced {
      border-radius: 15px !important;
    }

    legend {
      padding: 0 10px;
      color: var(--sky-800);
      font-weight: 800;
      letter-spacing: .015em;
    }

    .guided-workflow {
      gap: 22px !important;
    }

    .guided-hero {
      position: relative;
      overflow: hidden;
      background:
        radial-gradient(circle at 90% 18%, rgba(77, 210, 255, .22), transparent 18rem),
        linear-gradient(125deg, rgba(255,255,255,.95), rgba(220,246,255,.78));
      box-shadow: var(--glow);
    }

    .guided-eyebrow {
      color: var(--sky-600);
      opacity: 1 !important;
    }

    .guided-hero h2,
    .guided-step-header h2,
    .workspace-card h2,
    .workspace-card h3 {
      color: var(--sky-950);
    }

    .guided-step-nav {
      top: 8px !important;
      padding: 9px !important;
      border: 1px solid rgba(74, 186, 238, .22);
      border-radius: 16px;
      background: rgba(242, 251, 255, .82) !important;
      box-shadow: 0 10px 30px rgba(29, 115, 164, .10);
      backdrop-filter: blur(20px);
    }

    .guided-step-nav a {
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
      font-weight: 700;
    }

    .guided-step {
      position: relative;
      overflow: hidden;
    }

    .guided-step::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 3px;
      background: linear-gradient(180deg, var(--sky-400), rgba(30, 115, 255, .28));
    }

    .guided-step-number {
      color: white;
      border: 0 !important;
      background: linear-gradient(135deg, var(--sky-500), #4f8eff);
      box-shadow: 0 8px 22px rgba(25, 167, 232, .28);
    }

    input,
    select,
    textarea {
      color: var(--ink);
      border: 1px solid rgba(64, 168, 220, .26);
      border-radius: 11px;
      background: rgba(255,255,255,.88);
      outline: none;
      transition: border-color .16s ease, box-shadow .16s ease, background .16s ease;
    }

    input:focus,
    select:focus,
    textarea:focus {
      border-color: var(--sky-500);
      background: #fff;
      box-shadow: 0 0 0 4px rgba(25, 167, 232, .13);
    }

    button {
      border: 1px solid rgba(24, 147, 211, .22);
      border-radius: 10px;
      color: var(--sky-900);
      background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(225,246,255,.92));
      box-shadow: 0 5px 14px rgba(28, 124, 176, .08);
      transition: transform .14s ease, box-shadow .14s ease, border-color .14s ease;
    }

    button:hover:not(:disabled) {
      transform: translateY(-1px);
      border-color: rgba(25, 167, 232, .52);
      box-shadow: 0 9px 20px rgba(28, 124, 176, .14);
    }

    .guided-primary-action,
    #login,
    #create-person,
    #create-relationship,
    #create-conversation,
    #load-strategic-reply {
      color: white !important;
      border-color: transparent !important;
      background: linear-gradient(135deg, #19a7e8, #3d82ef) !important;
      box-shadow: 0 10px 24px rgba(29, 145, 218, .24) !important;
    }

    .status {
      color: #284b67;
      border: 1px solid rgba(78, 175, 224, .14);
      background: rgba(227, 247, 255, .56) !important;
    }

    .note,
    .guided-step-header p {
      color: var(--muted);
      opacity: 1 !important;
    }

    .guided-action-bar {
      border: 1px solid rgba(66, 176, 230, .18);
      background: linear-gradient(135deg, rgba(229,247,255,.82), rgba(242,250,255,.90)) !important;
    }

    .person-deck-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin: 2px 0 12px;
    }

    .person-deck-heading {
      display: flex;
      align-items: baseline;
      gap: 9px;
      min-width: 0;
    }

    .person-deck-heading strong {
      font-size: 1rem;
      color: var(--sky-900);
    }

    .person-deck-count {
      padding: 3px 8px;
      border: 1px solid rgba(30, 158, 220, .22);
      border-radius: 999px;
      color: var(--sky-700);
      background: rgba(225, 247, 255, .76);
      font-size: .76rem;
      font-weight: 800;
      letter-spacing: .06em;
    }

    #person-card-deck {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(215px, 1fr));
      gap: 14px;
      margin: 0 0 14px;
    }

    .person-card {
      position: relative;
      isolation: isolate;
      overflow: hidden;
      min-height: 210px;
      width: 100%;
      margin: 0;
      padding: 17px;
      text-align: left;
      border: 1px solid rgba(53, 178, 234, .24);
      border-radius: 20px;
      color: var(--ink);
      background:
        radial-gradient(circle at 90% 8%, rgba(92, 213, 255, .32), transparent 8rem),
        linear-gradient(145deg, rgba(255,255,255,.98), rgba(220,246,255,.88));
      box-shadow: 0 14px 34px rgba(20, 115, 170, .10);
      cursor: pointer;
      transform: translateZ(0);
      transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    }

    .person-card::before {
      content: "";
      position: absolute;
      inset: -60% -35%;
      z-index: -1;
      opacity: 0;
      transform: rotate(18deg) translateX(-30%);
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.72), rgba(83,203,255,.22), transparent);
      transition: opacity .2s ease, transform .55s ease;
    }

    .person-card:hover:not(:disabled) {
      transform: translateY(-5px) scale(1.012);
      border-color: rgba(24, 161, 226, .55);
      box-shadow: 0 20px 46px rgba(16, 118, 178, .17), 0 0 0 1px rgba(85, 210, 255, .13);
    }

    .person-card:hover::before {
      opacity: 1;
      transform: rotate(18deg) translateX(35%);
    }

    .person-card.is-selected {
      border-color: rgba(18, 151, 220, .78);
      box-shadow: 0 20px 50px rgba(16, 118, 178, .21), inset 0 0 0 1px rgba(52, 181, 238, .24);
      background:
        radial-gradient(circle at 88% 10%, rgba(94, 217, 255, .46), transparent 9rem),
        linear-gradient(145deg, #ffffff, #dff6ff);
    }

    .person-card.is-selected::after {
      content: "当前";
      position: absolute;
      top: 13px;
      right: 13px;
      padding: 4px 8px;
      border-radius: 999px;
      color: white;
      background: linear-gradient(135deg, var(--sky-500), #4c86ef);
      font-size: .7rem;
      font-weight: 800;
      letter-spacing: .08em;
      box-shadow: 0 5px 14px rgba(25, 153, 220, .24);
    }

    .person-card-topline {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
      color: var(--sky-600);
      font-size: .67rem;
      font-weight: 800;
      letter-spacing: .16em;
      text-transform: uppercase;
    }

    .person-card-avatar {
      display: grid;
      place-items: center;
      width: 62px;
      height: 62px;
      margin-bottom: 16px;
      border: 1px solid rgba(255,255,255,.9);
      border-radius: 18px;
      color: white;
      background: linear-gradient(145deg, #25bdf2, #497cf0);
      box-shadow: 0 12px 28px rgba(22, 143, 215, .25), inset 0 1px 0 rgba(255,255,255,.34);
      font-size: 1.55rem;
      font-weight: 800;
    }

    .person-card-name {
      display: block;
      overflow: hidden;
      margin: 0 0 4px;
      color: var(--sky-950);
      font-size: 1.08rem;
      font-weight: 850;
      line-height: 1.25;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .person-card-nickname {
      display: block;
      min-height: 1.3em;
      overflow: hidden;
      color: var(--sky-700);
      font-size: .84rem;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .person-card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-top: 18px;
      padding-top: 12px;
      border-top: 1px solid rgba(45, 161, 217, .13);
      color: var(--muted);
      font-size: .76rem;
    }

    .person-card-signal {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--sky-700);
      font-weight: 700;
    }

    .person-card-signal::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #3cc8f1;
      box-shadow: 0 0 0 4px rgba(60,200,241,.13), 0 0 13px rgba(60,200,241,.52);
    }

    .person-create-drawer,
    .person-list-fallback {
      margin-top: 12px;
      border: 1px solid rgba(53, 168, 220, .18);
      border-radius: 13px;
      background: rgba(245,252,255,.64);
    }

    .person-create-drawer > summary,
    .person-list-fallback > summary {
      padding: 11px 13px;
      color: var(--sky-800);
      cursor: pointer;
      font-weight: 750;
    }

    .person-create-fields,
    .person-list-fallback-content {
      padding: 0 13px 13px;
    }

    .person-deck-empty {
      grid-column: 1 / -1;
      padding: 26px;
      border: 1px dashed rgba(35, 160, 220, .28);
      border-radius: 17px;
      color: var(--muted);
      text-align: center;
      background: rgba(236,249,255,.58);
    }

    @media (max-width: 760px) {
      body { padding: 16px 12px 42px; }
      body > header { padding: 20px 17px; border-radius: 18px; }
      #person-card-deck { grid-template-columns: 1fr 1fr; }
    }

    @media (max-width: 520px) {
      #person-card-deck { grid-template-columns: 1fr; }
      .person-deck-toolbar { align-items: flex-start; flex-direction: column; }
    }
'''


VISUAL_THEME_SCRIPT = r'''
  function visualElement(tag, className = '', text = '') {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function visualPersonParts(label) {
    const text = String(label || '').trim();
    const match = text.match(/^(.*) \((.*)\)$/);
    if (!match) return {name: text || '未命名人物', nickname: ''};
    return {name: match[1].trim() || '未命名人物', nickname: match[2].trim()};
  }

  function visualInitial(text) {
    const chars = Array.from(String(text || '').trim());
    return chars.length ? chars[0].toUpperCase() : '?';
  }

  function visualEnsurePersonDeck() {
    const select = byId('person-select');
    const heading = byId('person-heading');
    const card = heading ? heading.closest('.workspace-card') : null;
    if (!select || !card) return;
    card.classList.add('person-hub-card');

    let deck = byId('person-card-deck');
    if (!deck) {
      const toolbar = visualElement('div', 'person-deck-toolbar');
      const headingWrap = visualElement('div', 'person-deck-heading');
      const title = visualElement('strong', '', '人物卡组');
      const count = visualElement('span', 'person-deck-count', '0 PERSON');
      count.id = 'person-deck-count';
      headingWrap.append(title, count);

      const refresh = byId('load-persons');
      if (refresh) {
        refresh.textContent = '刷新人物';
        toolbar.append(headingWrap, refresh);
      } else {
        toolbar.append(headingWrap);
      }

      deck = visualElement('div');
      deck.id = 'person-card-deck';
      deck.setAttribute('role', 'list');
      deck.setAttribute('aria-label', '人物卡组');

      heading.insertAdjacentElement('afterend', toolbar);
      toolbar.insertAdjacentElement('afterend', deck);

      const createDetails = visualElement('details', 'person-create-drawer');
      const createSummary = visualElement('summary', '', '＋ 新建人物');
      const createFields = visualElement('div', 'person-create-fields');
      createDetails.append(createSummary, createFields);

      ['person-name', 'person-nickname', 'person-notes'].forEach((id) => {
        const label = document.querySelector(`label[for="${id}"]`);
        const field = byId(id);
        if (label) createFields.appendChild(label);
        if (field) createFields.appendChild(field);
      });
      const createButton = byId('create-person');
      if (createButton) createFields.appendChild(createButton);
      deck.insertAdjacentElement('afterend', createDetails);

      const fallback = visualElement('details', 'person-list-fallback');
      const fallbackSummary = visualElement('summary', '', '列表模式 / 键盘选择');
      const fallbackContent = visualElement('div', 'person-list-fallback-content');
      fallback.append(fallbackSummary, fallbackContent);
      const selectLabel = document.querySelector('label[for="person-select"]');
      if (selectLabel) fallbackContent.appendChild(selectLabel);
      fallbackContent.appendChild(select);
      createDetails.insertAdjacentElement('afterend', fallback);
    }
  }

  function visualSyncPersonCardSelection() {
    const select = byId('person-select');
    if (!select) return;
    document.querySelectorAll('#person-card-deck .person-card').forEach((card) => {
      const selected = card.dataset.personId === select.value;
      card.classList.toggle('is-selected', selected);
      card.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });
  }

  function visualRenderPersonDeck() {
    const select = byId('person-select');
    const deck = byId('person-card-deck');
    const count = byId('person-deck-count');
    if (!select || !deck) return;

    const options = Array.from(select.options).filter((option) => option.value);
    deck.replaceChildren();
    if (count) count.textContent = `${options.length} PERSON${options.length === 1 ? '' : 'S'}`;

    if (options.length === 0) {
      const empty = visualElement('div', 'person-deck-empty', currentAccessToken ? '还没有人物档案。点击“＋ 新建人物”创建第一张人物卡。' : '登录后会在这里显示人物卡片。');
      deck.appendChild(empty);
      return;
    }

    options.forEach((option, index) => {
      const parts = visualPersonParts(option.textContent);
      const card = visualElement('button', 'person-card');
      card.type = 'button';
      card.dataset.personId = option.value;
      card.disabled = select.disabled;
      card.setAttribute('role', 'listitem');
      card.setAttribute('aria-label', `选择人物 ${parts.name}${parts.nickname ? `，昵称 ${parts.nickname}` : ''}`);
      card.setAttribute('aria-pressed', option.value === select.value ? 'true' : 'false');
      if (option.value === select.value) card.classList.add('is-selected');

      const top = visualElement('div', 'person-card-topline');
      top.append(
        visualElement('span', '', `PERSON // ${String(index + 1).padStart(2, '0')}`),
        visualElement('span', '', 'PROFILE')
      );

      const avatar = visualElement('div', 'person-card-avatar', visualInitial(parts.nickname || parts.name));
      const name = visualElement('span', 'person-card-name', parts.name);
      const nickname = visualElement('span', 'person-card-nickname', parts.nickname ? `@ ${parts.nickname}` : '未设置昵称');
      const footer = visualElement('div', 'person-card-footer');
      footer.append(
        visualElement('span', 'person-card-signal', '档案在线'),
        visualElement('span', '', '点击进入 →')
      );

      card.append(top, avatar, name, nickname, footer);
      card.addEventListener('click', () => {
        select.value = option.value;
        visualSyncPersonCardSelection();
        select.dispatchEvent(new Event('change', {bubbles: true}));
      });
      deck.appendChild(card);
    });
  }

  function visualApplyShellPolish() {
    const header = document.querySelector('body > header');
    if (header && !header.querySelector('.visual-system-kicker')) {
      const title = header.querySelector('h1');
      const kicker = visualElement('p', 'visual-system-kicker', 'RELATIONSHIP INTELLIGENCE SYSTEM');
      if (title) title.insertAdjacentElement('afterend', kicker);
    }
    visualEnsurePersonDeck();
    visualRenderPersonDeck();
  }

  visualApplyShellPolish();

  const visualPersonSelect = byId('person-select');
  if (visualPersonSelect) {
    visualPersonSelect.addEventListener('change', visualSyncPersonCardSelection);
    const visualPersonObserver = new MutationObserver(() => {
      visualEnsurePersonDeck();
      visualRenderPersonDeck();
    });
    visualPersonObserver.observe(visualPersonSelect, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['disabled'],
    });
  }
'''
