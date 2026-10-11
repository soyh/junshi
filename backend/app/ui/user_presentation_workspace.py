USER_PRESENTATION_STYLE = r'''
    /* TEST-161: presentation-only compact layout and comprehensive content drawers. */
    body {
      max-width: 1560px !important;
      padding: 16px 18px 36px !important;
    }

    body > header {
      padding: 14px 18px 12px !important;
      margin-bottom: 12px !important;
      border-radius: 18px !important;
    }

    body > header > .note,
    .visual-system-kicker,
    .user-system-copy,
    .user-system-message {
      display: none !important;
    }

    body > header nav:not([hidden]) {
      margin: 10px 0 0 !important;
    }

    .grid,
    .workspace-grid,
    .guided-primary,
    .guided-settings-content,
    .guided-advanced > div {
      align-items: start !important;
    }

    .grid { gap: 12px !important; }
    .workspace-grid { gap: 10px !important; }
    .guided-workflow { gap: 12px !important; }
    .guided-primary { gap: 10px !important; }

    .guided-hero {
      padding: 14px 16px !important;
      gap: 12px !important;
    }

    .guided-step {
      padding: 14px 16px !important;
    }

    .guided-step-header {
      margin-bottom: 10px !important;
    }

    .guided-step-header h2,
    .workspace-card h2,
    .workspace-card h3 {
      margin-top: 0;
      margin-bottom: 7px;
    }

    .guided-advanced {
      margin-top: 8px !important;
      padding: 9px 11px !important;
    }

    .guided-action-bar {
      margin-bottom: 9px !important;
      padding: 10px !important;
    }

    fieldset {
      padding: 13px !important;
    }

    .workspace-card {
      padding: 11px !important;
      align-self: start !important;
    }

    label {
      margin: 8px 0 3px !important;
    }

    input,
    select,
    textarea {
      padding: 8px !important;
    }

    textarea {
      min-height: 62px !important;
    }

    button {
      margin-top: 8px !important;
      padding: 8px 12px !important;
    }

    .status {
      min-height: 0 !important;
      padding: 8px 10px !important;
      margin-top: 7px;
    }

    .session-row {
      padding: 7px 0 !important;
    }

    #guided-person-primary .workspace-card,
    #guided-relationship-primary .workspace-card {
      max-width: none !important;
    }

    #conversation-id,
    label[for="conversation-id"] {
      display: none !important;
    }

    .user-long-content {
      position: relative;
      cursor: pointer;
      overflow: hidden;
      overflow-wrap: anywhere;
      transition: max-height .18s ease;
    }

    .user-long-content:not(.is-expanded) {
      max-height: 7.2em;
      padding-bottom: 25px !important;
      mask-image: linear-gradient(to bottom, #000 0%, #000 68%, transparent 100%);
    }

    .user-long-content.is-expanded {
      max-height: none;
      mask-image: none;
    }

    .user-long-content::after {
      content: attr(data-drawer-label);
      position: absolute;
      right: 5px;
      bottom: 4px;
      z-index: 3;
      padding: 3px 8px;
      border: 1px solid rgba(25, 167, 232, .20);
      border-radius: 999px;
      color: var(--sky-700, #0969a8);
      background: rgba(245, 252, 255, .97);
      box-shadow: 0 4px 10px rgba(16, 111, 165, .08);
      font-size: .72rem;
      font-weight: 700;
      pointer-events: none;
    }

    .user-drawer-window {
      border-color: rgba(25, 167, 232, .18) !important;
    }

    .user-drawer-window.user-long-content:not(.is-expanded) {
      max-height: 10.5rem;
    }

    .user-content-meta {
      color: var(--muted, #5d7790);
      font-size: .78rem;
      margin-bottom: 3px;
    }

    @media (min-width: 980px) {
      .guided-primary,
      .guided-advanced > div,
      .guided-settings-content {
        grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      }
    }

    @media (max-width: 760px) {
      body { padding: 10px 9px 28px !important; }
      body > header { padding: 12px !important; }
      .guided-step { padding: 11px !important; }
      .workspace-card, fieldset { padding: 10px !important; }
      .user-drawer-window.user-long-content:not(.is-expanded) { max-height: 9rem; }
    }
'''


USER_PRESENTATION_SCRIPT = r'''
  const userUuidPattern = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/gi;
  const userLongContentThreshold = 260;
  const userLongListRowThreshold = 4;

  const userDrawerSelectors = [
    '#person-profile-status',
    '#manage-message-detail',
    '#message-list',
    '#interaction-list',
    '#timeline-list',
    '#analysis-result',
    '#strategy-context-summary',
    '#strategy-candidate-list',
    '#strategy-constraint-list',
    '#recommendation-list',
    '#recommendation-constraint-list',
    '#strategic-reply-context',
    '#strategic-reply-recommendations',
    '#strategic-reply-constraints',
    '#strategic-reply-learning',
    '#generated-action-plan-summary',
    '#generated-action-plan-list',
    '#generated-action-plan-constraints',
    '#saved-action-plan-list',
    '#saved-action-plan-constraints',
    '#action-decision-candidate-detail',
    '#action-decision-constraints',
    '#action-decision-history',
    '#action-execution-candidate-detail',
    '#action-execution-constraints',
    '#action-execution-decisions',
    '#action-outcome-candidate-detail',
    '#action-outcome-history',
    '#action-feedback-items',
    '#action-feedback-summary',
    '#action-feedback-trend',
    '#action-feedback-signals',
    '#action-learning-candidate-detail',
    '#action-learning-history',
    '#action-learning-persisted',
    '#action-reanalysis-learning',
    '#action-reanalysis-constraints',
    '#action-reanalysis-analysis',
    '#action-reanalysis-recommendations',
    '#action-reanalysis-recommendation-constraints',
  ];

  function userHideTechnicalCopy() {
    const technicalNeedles = [
      'TEST-',
      'canonical API',
      'canonical service',
      'canonical consistency',
      'scope 一致性',
      'source metadata',
      'session token',
      'sent_at / created_at',
    ];
    document.querySelectorAll('.note').forEach((node) => {
      const text = node.textContent || '';
      if (technicalNeedles.some((needle) => text.includes(needle))) {
        node.classList.add('user-system-copy');
      }
    });
  }

  function userCleanTextNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE || !node.nodeValue) return;
    const cleaned = node.nodeValue
      .replace(userUuidPattern, '')
      .replace(/\b(source|evidence|relationship|conversation|message|interaction|decision|outcome|candidate|recommendation|person)_id\b\s*[:=]?/gi, '')
      .replace(/\s{2,}/g, ' ');
    if (cleaned !== node.nodeValue) node.nodeValue = cleaned;
  }

  function userCleanSystemMetadata(root) {
    if (!root || !(root instanceof Element)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(userCleanTextNode);
  }

  function userSetDrawerExpanded(node, expanded) {
    if (!node || !node.classList.contains('user-long-content')) return;
    if (expanded) {
      node.classList.add('is-expanded');
      node.dataset.drawerLabel = '双击收起';
      node.setAttribute('aria-expanded', 'true');
    } else {
      node.classList.remove('is-expanded');
      node.dataset.drawerLabel = '点击展开';
      node.setAttribute('aria-expanded', 'false');
    }
  }

  function userBindDrawerEvents(node) {
    if (node.dataset.userDrawerBound === '1') return;
    node.dataset.userDrawerBound = '1';

    node.addEventListener('click', (event) => {
      if (!node.classList.contains('user-long-content')) return;
      const ancestor = node.parentElement && node.parentElement.closest('.user-long-content');
      if (ancestor) userSetDrawerExpanded(ancestor, true);
      if (!node.classList.contains('is-expanded')) userSetDrawerExpanded(node, true);
      event.stopPropagation();
    });

    node.addEventListener('dblclick', (event) => {
      if (!node.classList.contains('user-long-content')) return;
      event.preventDefault();
      event.stopPropagation();
      userSetDrawerExpanded(node, false);
    });

    node.addEventListener('keydown', (event) => {
      if (!node.classList.contains('user-long-content')) return;
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      userSetDrawerExpanded(node, !node.classList.contains('is-expanded'));
    });
  }

  function userPrepareDrawer(node, forceWindow = false) {
    if (!node || !(node instanceof Element)) return;
    if (node.querySelector('button, input, select, textarea, a')) return;

    const text = (node.textContent || '').trim();
    const lineCount = text ? text.split(/\r?\n/).length : 0;
    const rowCount = node.querySelectorAll(':scope > .session-row').length;
    const shouldDrawer = (
      text.length > userLongContentThreshold ||
      lineCount > 6 ||
      (forceWindow && rowCount > userLongListRowThreshold)
    );

    const contentKey = `${text.length}:${lineCount}:${rowCount}:${text.slice(0, 64)}:${text.slice(-64)}`;
    const contentChanged = node.dataset.userDrawerContentKey !== contentKey;
    node.dataset.userDrawerContentKey = contentKey;

    userBindDrawerEvents(node);

    if (!shouldDrawer) {
      node.classList.remove('user-long-content', 'is-expanded');
      node.classList.toggle('user-drawer-window', forceWindow);
      node.removeAttribute('role');
      node.removeAttribute('tabindex');
      node.removeAttribute('aria-expanded');
      delete node.dataset.drawerLabel;
      return;
    }

    node.classList.add('user-long-content');
    node.classList.toggle('user-drawer-window', forceWindow);
    node.setAttribute('role', 'button');
    node.setAttribute('tabindex', '0');

    if (contentChanged || !node.hasAttribute('aria-expanded')) {
      userSetDrawerExpanded(node, false);
    }
  }

  function userNormalizeMessageRow(row) {
    if (!row || !(row instanceof Element) || !row.closest('#message-list')) return;
    const parts = row.querySelectorAll(':scope > div');
    if (parts.length < 2) return;
    const meta = parts[0];
    const body = parts[parts.length - 1];
    const metaText = meta.textContent || '';
    if (/\b(system|assistant)\b/i.test(metaText)) {
      row.classList.add('user-system-message');
      return;
    }
    meta.classList.add('user-content-meta');
    meta.textContent = metaText
      .replace(/\buser\b/gi, '我')
      .replace(/\bperson\b/gi, '对方');
    userPrepareDrawer(body, false);
  }

  function userNormalizeTimelineRow(row) {
    if (!row || !(row instanceof Element)) return;
    if (!row.closest('#timeline-list') && !row.closest('#interaction-list')) return;
    const parts = row.querySelectorAll(':scope > div');
    if (parts.length === 0) return;
    parts[0].classList.add('user-content-meta');
    parts[0].textContent = (parts[0].textContent || '')
      .replace(/\s*·\s*(message|interaction|conversation)\s*$/i, '')
      .replace(/\s*·\s*relationship\s+[0-9a-f-]+/gi, '');
    if (parts.length > 1) userPrepareDrawer(parts[parts.length - 1], false);
  }

  function userApplyExplicitDrawers(scope) {
    userDrawerSelectors.forEach((selector) => {
      if (scope.matches && scope.matches(selector)) userPrepareDrawer(scope, true);
      scope.querySelectorAll?.(selector).forEach((node) => userPrepareDrawer(node, true));
    });
  }

  function userEnhanceVisibleContent(root = document.body) {
    const scope = root instanceof Element ? root : document.body;

    if (scope.matches && scope.matches('.session-row')) {
      userNormalizeMessageRow(scope);
      userNormalizeTimelineRow(scope);
      userCleanSystemMetadata(scope);
    }

    scope.querySelectorAll?.('.session-row').forEach((row) => {
      userNormalizeMessageRow(row);
      userNormalizeTimelineRow(row);
      userCleanSystemMetadata(row);
    });

    if (scope.matches && scope.matches('.status')) userCleanSystemMetadata(scope);
    scope.querySelectorAll?.('.status').forEach((node) => userCleanSystemMetadata(node));

    userApplyExplicitDrawers(scope);
  }

  const userPresentationObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      const targetElement = mutation.target instanceof Element
        ? mutation.target
        : mutation.target.parentElement;

      if (targetElement) userEnhanceVisibleContent(targetElement);

      mutation.addedNodes.forEach((node) => {
        if (node instanceof Element) {
          userEnhanceVisibleContent(node);
        } else if (node.nodeType === Node.TEXT_NODE && node.parentElement) {
          userEnhanceVisibleContent(node.parentElement);
        }
      });
    });
  });

  userHideTechnicalCopy();
  userEnhanceVisibleContent();
  userPresentationObserver.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
'''
