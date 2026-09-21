USER_PRESENTATION_STYLE = r'''
    /* TEST-160: presentation-only compact layout. No canonical/API behavior changes. */
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
      max-height: 7.8em;
      padding-bottom: 24px;
      mask-image: linear-gradient(to bottom, #000 0%, #000 70%, transparent 100%);
    }

    .user-long-content.is-expanded {
      max-height: none;
      mask-image: none;
    }

    .user-long-content::after {
      content: attr(data-drawer-label);
      position: absolute;
      right: 0;
      bottom: 0;
      padding: 3px 8px;
      border: 1px solid rgba(25, 167, 232, .20);
      border-radius: 999px;
      color: var(--sky-700, #0969a8);
      background: rgba(245, 252, 255, .96);
      box-shadow: 0 4px 10px rgba(16, 111, 165, .08);
      font-size: .72rem;
      font-weight: 700;
      pointer-events: none;
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
    }
'''


USER_PRESENTATION_SCRIPT = r'''
  const userUuidPattern = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/gi;
  const userLongContentThreshold = 260;

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
      .replace(/\b(source|evidence|relationship|conversation|message|interaction)_id\b\s*[:=]?/gi, '')
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

  function userPrepareDrawer(node) {
    if (!node || !(node instanceof Element)) return;
    if (node.classList.contains('user-long-content')) return;
    if (node.querySelector('button, input, select, textarea, a')) return;
    const text = (node.textContent || '').trim();
    const lineCount = text ? text.split(/\r?\n/).length : 0;
    if (text.length <= userLongContentThreshold && lineCount <= 6) return;

    node.classList.add('user-long-content');
    node.classList.remove('is-expanded');
    node.dataset.drawerLabel = '点击展开';
    node.setAttribute('role', 'button');
    node.setAttribute('tabindex', '0');
    node.setAttribute('aria-expanded', 'false');

    node.addEventListener('click', () => {
      if (node.classList.contains('is-expanded')) return;
      node.classList.add('is-expanded');
      node.dataset.drawerLabel = '双击收起';
      node.setAttribute('aria-expanded', 'true');
    });

    node.addEventListener('dblclick', (event) => {
      event.preventDefault();
      node.classList.remove('is-expanded');
      node.dataset.drawerLabel = '点击展开';
      node.setAttribute('aria-expanded', 'false');
    });

    node.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      const expanded = node.classList.toggle('is-expanded');
      node.dataset.drawerLabel = expanded ? '双击收起' : '点击展开';
      node.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });
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
    userPrepareDrawer(body);
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
    if (parts.length > 1) userPrepareDrawer(parts[parts.length - 1]);
  }

  function userEnhanceVisibleContent(root = document.body) {
    userHideTechnicalCopy();
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
    scope.querySelectorAll?.('.status').forEach((node) => {
      userCleanSystemMetadata(node);
      if (node.childElementCount === 0) userPrepareDrawer(node);
    });
  }

  const userPresentationObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'characterData') {
        const parent = mutation.target.parentElement;
        if (parent) userEnhanceVisibleContent(parent);
        return;
      }
      mutation.addedNodes.forEach((node) => {
        if (node instanceof Element) userEnhanceVisibleContent(node);
      });
    });
  });

  userEnhanceVisibleContent();
  userPresentationObserver.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
'''
