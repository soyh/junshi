SETTINGS_TAB_WORKSPACE_STYLE = r'''
    #guided-settings[open] {
      grid-column: 1 / -1;
      width: 100%;
      box-sizing: border-box;
      padding: 14px 16px 16px;
      background:
        radial-gradient(circle at 92% 4%, rgba(88, 200, 245, .16), transparent 20rem),
        rgba(255, 255, 255, .82);
    }

    #guided-settings[open] > summary {
      margin-bottom: 12px;
      color: var(--sky-900, #0b2f50);
      font-size: .95rem;
    }

    /* TEST-190: the customer shell keeps the settings trigger in the top-right,
       but the opened workspace must no longer inherit that narrow host width. */
    #client-settings-host #guided-settings[open] {
      position: relative;
      z-index: 80;
      width: auto !important;
      padding: 0 !important;
      background: transparent !important;
    }

    #client-settings-host #guided-settings[open]::before {
      content: "";
      position: fixed;
      inset: 0;
      z-index: 79;
      pointer-events: none;
      background: rgba(228, 242, 252, .28);
      backdrop-filter: blur(2px);
    }

    #client-settings-host #guided-settings[open] > summary {
      position: relative;
      z-index: 82;
      margin-bottom: 0;
      border-color: rgba(25, 167, 232, .34) !important;
      color: var(--sky-800, #075985) !important;
      background: rgba(246, 252, 255, .96) !important;
      box-shadow: 0 10px 28px rgba(28, 124, 176, .14) !important;
    }

    #guided-settings-content.settings-tab-workspace {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      max-height: none !important;
      overflow: visible !important;
      padding: 0 !important;
    }

    #client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace {
      position: fixed !important;
      top: clamp(82px, 10vh, 112px) !important;
      left: 50% !important;
      right: auto !important;
      z-index: 81;
      width: min(1180px, calc(100vw - 48px)) !important;
      max-width: calc(100vw - 48px) !important;
      max-height: calc(100vh - 132px) !important;
      margin: 0 !important;
      padding: 14px !important;
      box-sizing: border-box;
      overflow: hidden !important;
      transform: translateX(-50%) !important;
      border: 1px solid rgba(25, 167, 232, .22) !important;
      border-radius: 22px !important;
      background:
        radial-gradient(circle at 88% 0%, rgba(88, 200, 245, .18), transparent 22rem),
        rgba(247, 252, 255, .985) !important;
      box-shadow:
        0 30px 90px rgba(31, 91, 132, .24),
        inset 0 1px 0 rgba(255, 255, 255, .96) !important;
      backdrop-filter: blur(24px);
    }

    #guided-settings-tabs {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px 10px;
      align-items: stretch;
      width: 100%;
      margin-bottom: 12px;
      padding: 5px;
      box-sizing: border-box;
      border: 1px solid rgba(25, 167, 232, .12);
      border-radius: 15px;
      background: rgba(235, 248, 255, .66);
    }

    #guided-settings-tabs .settings-tab-button {
      min-width: 0;
      width: 100%;
      margin: 0 !important;
      padding: 10px 12px;
      border: 1px solid rgba(25, 167, 232, .18);
      border-radius: 11px;
      font-weight: 800;
      color: var(--sky-800, #075985);
      background: rgba(255, 255, 255, .70);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      box-shadow: none;
    }

    #guided-settings-tabs .settings-tab-button:hover:not(:disabled) {
      background: rgba(255, 255, 255, .96);
    }

    #guided-settings-tabs .settings-tab-button[aria-selected="true"] {
      color: #fff;
      background: linear-gradient(135deg, var(--sky-500, #19a7e8), var(--sky-700, #0877b9));
      border-color: transparent;
      box-shadow: 0 8px 22px rgba(25, 167, 232, .18);
    }

    #guided-settings-panel-host {
      width: 100%;
      min-width: 0;
      box-sizing: border-box;
      max-height: min(70vh, 760px);
      overflow-y: auto;
      overflow-x: hidden;
      scrollbar-gutter: stable;
      border: 1px solid rgba(25, 167, 232, .16);
      border-radius: 16px;
      padding: 16px 18px 18px;
      background:
        linear-gradient(145deg, rgba(255,255,255,.90), rgba(241,250,255,.82));
      box-shadow: inset 0 1px 0 rgba(255,255,255,.92);
    }

    #client-settings-host #guided-settings-panel-host {
      max-height: calc(100vh - 236px);
    }

    #guided-settings-panel-host > fieldset {
      width: 100% !important;
      max-width: none !important;
      box-sizing: border-box;
      margin: 0 !important;
      padding: 0 !important;
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
    }

    #guided-settings-panel-host > fieldset > legend {
      display: none !important;
    }

    #guided-settings-panel-host > fieldset[hidden] {
      display: none !important;
    }

    @media (max-width: 900px) {
      #guided-settings-tabs {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 620px) {
      #guided-settings[open] {
        padding: 12px;
      }

      #client-settings-host #guided-settings[open] {
        padding: 0 !important;
      }

      #client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace {
        top: 68px !important;
        width: calc(100vw - 18px) !important;
        max-width: calc(100vw - 18px) !important;
        max-height: calc(100vh - 78px) !important;
        padding: 10px !important;
        border-radius: 17px !important;
      }

      #guided-settings-tabs {
        display: flex;
        overflow-x: auto;
        scrollbar-gutter: stable;
      }

      #guided-settings-tabs .settings-tab-button {
        flex: 0 0 132px;
      }

      #guided-settings-panel-host {
        padding: 12px;
        max-height: none;
      }

      #client-settings-host #guided-settings-panel-host {
        max-height: calc(100vh - 172px);
      }
    }
'''


SETTINGS_TAB_WORKSPACE_SCRIPT = r'''
  function installSharedSettingsTabs() {
    const settings = byId('guided-settings-content');
    if (!settings || settings.dataset.sharedTabsInstalled === 'true') return;

    const legacyPanels = Array.from(
      settings.querySelectorAll(':scope > .lifecycle-settings-panel')
    );
    if (!legacyPanels.length) return;

    settings.dataset.sharedTabsInstalled = 'true';
    settings.classList.add('settings-tab-workspace');

    const tabs = document.createElement('div');
    tabs.id = 'guided-settings-tabs';
    tabs.setAttribute('role', 'tablist');
    tabs.setAttribute('aria-label', '账号、安全与模型设置');

    const panelHost = document.createElement('div');
    panelHost.id = 'guided-settings-panel-host';

    const tabLabels = {
      '账号登录': '账号登录',
      'Session management': '登录会话',
      'Account Security': '账号安全',
      'LLM 模型设置': '模型设置',
    };

    const entries = legacyPanels.map((details, index) => {
      const summary = details.querySelector(':scope > summary');
      const fieldset = details.querySelector(':scope > fieldset');
      if (!summary || !fieldset) return null;

      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'settings-tab-button';
      tab.id = `guided-settings-tab-${index}`;
      tab.setAttribute('role', 'tab');
      const existingPanelId = fieldset.id.trim();
      const panelId = existingPanelId || `guided-settings-panel-${index}`;
      tab.setAttribute('aria-controls', panelId);
      const sourceLabel = summary.textContent.trim() || '设置';
      tab.dataset.sourceLabel = sourceLabel;
      tab.textContent = tabLabels[sourceLabel] || sourceLabel;
      tab.title = tab.textContent;

      // Preserve stable fieldset IDs such as "provider". Later workspace
      // installers use those IDs as integration mount points after the tab
      // layout has moved the fieldsets into the shared panel host.
      fieldset.id = panelId;
      fieldset.setAttribute('role', 'tabpanel');
      fieldset.setAttribute('aria-labelledby', tab.id);

      tabs.appendChild(tab);
      panelHost.appendChild(fieldset);
      details.remove();
      return { tab, fieldset };
    }).filter(Boolean);

    function activate(index) {
      entries.forEach((entry, entryIndex) => {
        const active = entryIndex === index;
        entry.tab.setAttribute('aria-selected', active ? 'true' : 'false');
        entry.tab.tabIndex = active ? 0 : -1;
        entry.fieldset.hidden = !active;
      });
    }

    entries.forEach((entry, index) => {
      entry.tab.addEventListener('click', () => activate(index));
      entry.tab.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        let next = index;
        if (event.key === 'ArrowLeft') next = (index - 1 + entries.length) % entries.length;
        if (event.key === 'ArrowRight') next = (index + 1) % entries.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = entries.length - 1;
        activate(next);
        entries[next].tab.focus();
      });
    });

    settings.replaceChildren(tabs, panelHost);
    activate(0);

    const details = byId('guided-settings');
    if (details && details.dataset.escapeCloseBound !== 'true') {
      details.dataset.escapeCloseBound = 'true';
      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && details.open) {
          details.open = false;
          details.querySelector(':scope > summary')?.focus();
        }
      });
    }
  }

  installSharedSettingsTabs();
'''
