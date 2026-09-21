SETTINGS_TAB_WORKSPACE_STYLE = r'''
    #guided-settings-content.settings-tab-workspace {
      display: block !important;
      min-width: 0 !important;
      max-height: none !important;
      overflow: visible !important;
      padding: 10px 4px 6px 0 !important;
    }

    #guided-settings-tabs {
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 8px 10px;
      align-items: stretch;
      width: 100%;
      margin-bottom: 10px;
    }

    #guided-settings-tabs .settings-tab-button {
      min-width: 0;
      width: 100%;
      padding: 10px 12px;
      border: 1px solid rgba(25, 167, 232, .20);
      border-radius: 12px;
      font-weight: 700;
      color: var(--sky-800, #075985);
      background: rgba(226, 246, 255, .72);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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
      max-height: min(58vh, 620px);
      overflow-y: auto;
      overflow-x: hidden;
      scrollbar-gutter: stable;
      border: 1px solid rgba(25, 167, 232, .16);
      border-radius: 12px;
      padding: 12px 14px 14px;
      background: rgba(255,255,255,.72);
    }

    #guided-settings-panel-host > fieldset {
      width: 100% !important;
      max-width: none !important;
      box-sizing: border-box;
      margin: 0 !important;
      padding: 0 !important;
      border: 0 !important;
      background: transparent !important;
    }

    #guided-settings-panel-host > fieldset > legend {
      display: none !important;
    }

    #guided-settings-panel-host > fieldset[hidden] {
      display: none !important;
    }

    @media (max-width: 760px) {
      #guided-settings-tabs {
        display: flex;
        overflow-x: auto;
        scrollbar-gutter: stable;
      }

      #guided-settings-tabs .settings-tab-button {
        flex: 0 0 160px;
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

    const entries = legacyPanels.map((details, index) => {
      const summary = details.querySelector(':scope > summary');
      const fieldset = details.querySelector(':scope > fieldset');
      if (!summary || !fieldset) return null;

      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'settings-tab-button';
      tab.id = `guided-settings-tab-${index}`;
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', `guided-settings-panel-${index}`);
      tab.textContent = summary.textContent.trim() || '设置';

      fieldset.id = `guided-settings-panel-${index}`;
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
  }

  installSharedSettingsTabs();
'''
