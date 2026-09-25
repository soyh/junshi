VIEWPORT_SAFE_UI_POLISH_STYLE = r'''
    /* TEST-191: final viewport-safe customer presentation overrides. */
    body:has(#guided-settings[open]) {
      overflow: hidden !important;
    }

    #client-settings-host #guided-settings[open] {
      position: fixed !important;
      inset: 0 !important;
      z-index: 120 !important;
      width: auto !important;
      height: auto !important;
      max-width: none !important;
      max-height: none !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      background: transparent !important;
    }

    #client-settings-host #guided-settings[open]::before {
      position: absolute !important;
      inset: 0 !important;
      z-index: 0 !important;
      background: rgba(224, 240, 251, .48) !important;
      backdrop-filter: blur(5px) !important;
    }

    #client-settings-host #guided-settings[open] > summary {
      position: absolute !important;
      top: 16px !important;
      right: clamp(12px, 2vw, 28px) !important;
      z-index: 3 !important;
      width: auto !important;
      max-width: calc(100vw - 24px) !important;
      margin: 0 !important;
    }

    #client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace {
      position: absolute !important;
      top: 68px !important;
      left: clamp(10px, 2.2vw, 30px) !important;
      right: clamp(10px, 2.2vw, 30px) !important;
      bottom: clamp(10px, 2.2vh, 24px) !important;
      z-index: 2 !important;
      display: grid !important;
      grid-template-rows: auto minmax(0, 1fr) !important;
      width: auto !important;
      min-width: 0 !important;
      max-width: none !important;
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      margin: 0 !important;
      padding: 14px !important;
      box-sizing: border-box !important;
      overflow: hidden !important;
      transform: none !important;
    }

    #guided-settings-tabs {
      position: relative !important;
      z-index: 4 !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }

    #client-settings-host #guided-settings-panel-host {
      position: relative !important;
      z-index: 1 !important;
      isolation: isolate !important;
      min-width: 0 !important;
      min-height: 0 !important;
      max-width: 100% !important;
      max-height: none !important;
      overflow-x: hidden !important;
      overflow-y: auto !important;
    }

    /* TEST-192: every settings tab owns one normal-flow panel. Legacy workspace
       rules are not allowed to keep absolute/fixed coordinates after the
       fieldset has been moved into the shared panel host. */
    #client-settings-host #guided-settings-panel-host > fieldset {
      position: static !important;
      inset: auto !important;
      top: auto !important;
      right: auto !important;
      bottom: auto !important;
      left: auto !important;
      float: none !important;
      clear: both !important;
      grid-column: auto !important;
      grid-row: auto !important;
      grid-area: auto !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
      transform: none !important;
      translate: none !important;
      z-index: auto !important;
      box-sizing: border-box !important;
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
    }

    #client-settings-host #guided-settings-panel-host > fieldset[hidden] {
      display: none !important;
      visibility: hidden !important;
      pointer-events: none !important;
    }

    #client-settings-host #guided-settings-panel-host > fieldset:not([hidden]) {
      display: block !important;
      visibility: visible !important;
      pointer-events: auto !important;
    }

    #client-settings-host #guided-settings-panel-host > fieldset > legend {
      display: none !important;
    }

    #client-settings-host #guided-settings-panel-host .workspace-grid,
    #client-settings-host #guided-settings-panel-host .workspace-card,
    #client-settings-host #guided-settings-panel-host .status,
    #client-settings-host #guided-settings-panel-host input,
    #client-settings-host #guided-settings-panel-host select,
    #client-settings-host #guided-settings-panel-host textarea {
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }

    #client-settings-host #guided-settings-panel-host .workspace-grid {
      width: 100% !important;
    }

    #guided-settings-panel-host > fieldset,
    #provider,
    #dual-model-intro,
    #dual-model-settings,
    #provider-advanced-profiles {
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }

    #dual-model-settings {
      width: 100% !important;
    }

    #client-conversation-tabs {
      display: grid !important;
      grid-template-columns: repeat(auto-fill, minmax(190px, 240px)) !important;
      align-items: stretch !important;
      gap: 10px !important;
      overflow: visible !important;
      padding: 3px 1px 5px !important;
    }

    .client-conversation-chip {
      display: grid !important;
      grid-template-columns: auto minmax(0, 1fr) auto !important;
      align-items: center !important;
      gap: 9px !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: none !important;
      min-height: 58px !important;
      padding: 10px 12px !important;
      border-radius: 16px !important;
      white-space: normal !important;
      text-align: left !important;
      line-height: 1.35 !important;
    }

    .client-conversation-chip-label {
      display: block;
      line-height: 1.35;
    }

    #client-unified-message-history {
      margin-top: 14px !important;
      border: 0 !important;
      background: transparent !important;
    }

    #client-unified-message-history > summary {
      display: inline-flex !important;
      align-items: center !important;
      gap: 8px !important;
      width: auto !important;
      min-height: 42px !important;
      margin: 0 !important;
      padding: 9px 13px !important;
      box-sizing: border-box !important;
      list-style: none !important;
      cursor: pointer !important;
      border: 1px solid rgba(25, 167, 232, .24) !important;
      border-radius: 14px !important;
      color: var(--sky-800, #075985) !important;
      background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(235,248,255,.94)) !important;
      box-shadow: 0 7px 18px rgba(25, 117, 170, .08) !important;
      font-size: .82rem !important;
      font-weight: 850 !important;
    }

    #client-unified-message-history > summary::-webkit-details-marker {
      display: none !important;
    }

    #client-unified-message-history > summary::before {
      content: "▤";
      display: grid;
      place-items: center;
      width: 24px;
      height: 24px;
      flex: 0 0 24px;
      border-radius: 8px;
      color: #0877b9;
      background: rgba(210, 240, 255, .92);
      font-size: .78rem;
    }

    #client-unified-message-history > summary:hover {
      border-color: rgba(25, 167, 232, .42) !important;
      background: linear-gradient(180deg, #fff, rgba(226,245,255,.98)) !important;
      box-shadow: 0 10px 24px rgba(25, 117, 170, .12) !important;
    }

    #client-unified-message-history[open] > summary {
      border-color: rgba(25, 167, 232, .44) !important;
      background: rgba(226, 246, 255, .94) !important;
    }

    #client-media-controls > div {
      min-width: 0;
    }

    #client-media-file {
      width: 100% !important;
      min-width: 0 !important;
      min-height: 46px !important;
      margin: 0 !important;
      padding: 5px 7px !important;
      box-sizing: border-box !important;
      border: 1px solid rgba(25, 167, 232, .22) !important;
      border-radius: 13px !important;
      color: #425b72 !important;
      background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(239,249,255,.94)) !important;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.92) !important;
      font-size: .82rem !important;
    }

    #client-media-file::file-selector-button,
    #client-media-file::-webkit-file-upload-button {
      margin: 0 10px 0 0 !important;
      padding: 8px 12px !important;
      border: 1px solid rgba(25, 167, 232, .26) !important;
      border-radius: 10px !important;
      color: var(--sky-800, #075985) !important;
      background: linear-gradient(180deg, #ffffff, rgba(224,245,255,.98)) !important;
      box-shadow: 0 5px 14px rgba(25, 117, 170, .08) !important;
      font: inherit !important;
      font-weight: 800 !important;
      cursor: pointer !important;
    }

    #client-media-file::file-selector-button:hover,
    #client-media-file::-webkit-file-upload-button:hover {
      border-color: rgba(25, 167, 232, .46) !important;
      background: linear-gradient(180deg, #fff, rgba(210,240,255,.98)) !important;
    }

    #client-media-actions #client-media-upload {
      color: #fff !important;
      border-color: transparent !important;
      border-radius: 12px !important;
      background: linear-gradient(135deg, var(--sky-500, #19a7e8), var(--sky-700, #0877b9)) !important;
      box-shadow: 0 8px 20px rgba(25, 139, 197, .18) !important;
    }

    #client-media-actions #client-media-refresh {
      border: 1px solid rgba(25, 167, 232, .22) !important;
      border-radius: 12px !important;
      color: var(--sky-800, #075985) !important;
      background: rgba(248, 253, 255, .96) !important;
      box-shadow: 0 5px 14px rgba(25, 117, 170, .06) !important;
    }

    /* TEST-193: settings navigation and its active operation page must occupy
       two explicit, non-overlapping rows. Automatic grid placement is not
       allowed to place the panel host beside or on top of the navigation. */
    #client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace {
      grid-template-columns: minmax(0, 1fr) !important;
      grid-template-rows: max-content minmax(0, 1fr) !important;
      column-gap: 0 !important;
      row-gap: 14px !important;
      align-items: stretch !important;
      align-content: stretch !important;
    }

    #client-settings-host #guided-settings-tabs {
      grid-column: 1 / -1 !important;
      grid-row: 1 !important;
      align-self: start !important;
      justify-self: stretch !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: none !important;
      margin: 0 !important;
    }

    #client-settings-host #guided-settings-panel-host {
      grid-column: 1 / -1 !important;
      grid-row: 2 !important;
      align-self: stretch !important;
      justify-self: stretch !important;
      width: 100% !important;
      min-width: 0 !important;
      max-width: none !important;
      margin: 0 !important;
    }

    @media (max-width: 980px) {
      #client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace {
        left: 12px !important;
        right: 12px !important;
        bottom: 12px !important;
      }

      #client-settings-host #guided-settings-panel-host .workspace-grid {
        grid-template-columns: 1fr !important;
      }
    }

    @media (max-width: 620px) {
      #client-settings-host #guided-settings[open] > summary {
        top: 10px !important;
        right: 9px !important;
      }

      #client-settings-host #guided-settings[open] #guided-settings-content.settings-tab-workspace {
        top: 58px !important;
        left: 7px !important;
        right: 7px !important;
        bottom: 7px !important;
        padding: 9px !important;
        border-radius: 16px !important;
        row-gap: 10px !important;
      }

      #client-conversation-tabs {
        grid-template-columns: 1fr !important;
      }

      .client-conversation-chip {
        min-height: 54px !important;
      }

      #client-media-actions {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
      }

      #client-media-actions button {
        width: 100% !important;
      }
    }
'''
