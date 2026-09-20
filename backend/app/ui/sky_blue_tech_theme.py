SKY_BLUE_TECH_THEME_STYLE = r'''
    :root {
      color-scheme: light;
      --tech-bg: #eef9ff;
      --tech-bg-deep: #dff3ff;
      --tech-panel: rgba(255, 255, 255, .88);
      --tech-panel-strong: rgba(255, 255, 255, .96);
      --tech-border: rgba(31, 151, 224, .24);
      --tech-border-strong: rgba(0, 136, 221, .46);
      --tech-primary: #168eea;
      --tech-primary-strong: #0878d1;
      --tech-primary-dark: #075ea5;
      --tech-cyan: #31c8f4;
      --tech-text: #12324a;
      --tech-muted: #557488;
      --tech-shadow: 0 14px 34px rgba(24, 116, 174, .12);
      --tech-shadow-soft: 0 7px 20px rgba(24, 116, 174, .09);
      --tech-radius: 18px;
      font-family: Inter, "SF Pro Display", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
    }

    html {
      min-height: 100%;
      scroll-behavior: smooth;
      background:
        radial-gradient(circle at 8% 10%, rgba(80, 202, 255, .26), transparent 28%),
        radial-gradient(circle at 92% 18%, rgba(40, 149, 242, .18), transparent 30%),
        linear-gradient(155deg, #f8fdff 0%, var(--tech-bg) 48%, #e8f7ff 100%);
    }

    body {
      position: relative;
      max-width: 1320px;
      margin: 24px auto;
      padding: 0 24px 64px;
      color: var(--tech-text);
      background: transparent;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      z-index: -1;
      pointer-events: none;
      opacity: .34;
      background-image:
        linear-gradient(rgba(37, 163, 230, .08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(37, 163, 230, .08) 1px, transparent 1px);
      background-size: 32px 32px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.8), transparent 82%);
    }

    body > header {
      position: relative;
      overflow: hidden;
      margin-bottom: 24px;
      padding: 26px 28px 22px;
      border: 1px solid var(--tech-border);
      border-radius: 22px;
      background:
        linear-gradient(130deg, rgba(255,255,255,.98), rgba(226,246,255,.92)),
        var(--tech-panel-strong);
      box-shadow: 0 18px 44px rgba(29, 126, 184, .14);
      backdrop-filter: blur(18px);
    }

    body > header::after {
      content: "";
      position: absolute;
      width: 300px;
      height: 300px;
      right: -110px;
      top: -160px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(49, 200, 244, .32), rgba(22, 142, 234, .08) 52%, transparent 72%);
      pointer-events: none;
    }

    body > header h1 {
      position: relative;
      z-index: 1;
      margin: 0 0 8px;
      font-size: clamp(1.8rem, 3vw, 2.65rem);
      letter-spacing: -.035em;
      color: #0878d1;
      background: linear-gradient(100deg, #067bd5, #1599ed 48%, #29bde9);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    body > header .note {
      position: relative;
      z-index: 1;
      max-width: 920px;
      color: var(--tech-muted);
    }

    body > header > nav[aria-label="主要功能"] {
      position: relative;
      z-index: 1;
      margin: 18px 0 0;
      padding: 8px;
      gap: 7px;
      width: fit-content;
      max-width: 100%;
      border: 1px solid rgba(63, 173, 230, .18);
      border-radius: 14px;
      background: rgba(236, 249, 255, .74);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
    }

    body > header > nav[aria-label="主要功能"] a {
      padding: 8px 11px;
      border: 1px solid transparent;
      border-radius: 10px;
      color: #176a9e;
      font-size: .89rem;
      font-weight: 700;
      transition: background .18s ease, border-color .18s ease, color .18s ease, transform .18s ease;
    }

    body > header > nav[aria-label="主要功能"] a:hover {
      color: #0569b7;
      border-color: rgba(25, 145, 218, .22);
      background: rgba(255,255,255,.94);
      transform: translateY(-1px);
    }

    fieldset,
    .workspace-card {
      border: 1px solid var(--tech-border);
      background: var(--tech-panel);
      box-shadow: var(--tech-shadow-soft);
      backdrop-filter: blur(14px);
    }

    fieldset {
      border-radius: var(--tech-radius);
    }

    .workspace-card {
      padding: 16px;
      border-radius: 15px;
      transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
    }

    .workspace-card:hover {
      border-color: rgba(25, 145, 218, .36);
      box-shadow: 0 12px 28px rgba(24, 116, 174, .11);
    }

    legend {
      padding: 0 8px;
      color: #0d78bc;
      font-weight: 800;
      letter-spacing: .01em;
    }

    h2, h3 {
      color: #17425d;
    }

    label {
      color: #315b73;
      font-weight: 700;
    }

    input,
    select,
    textarea {
      border: 1px solid rgba(38, 145, 205, .24);
      border-radius: 11px;
      color: var(--tech-text);
      background: rgba(248, 253, 255, .96);
      box-shadow: inset 0 1px 2px rgba(24, 91, 127, .035);
      transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
    }

    input:hover,
    select:hover,
    textarea:hover {
      border-color: rgba(20, 141, 216, .42);
    }

    input:focus,
    select:focus,
    textarea:focus {
      outline: none;
      border-color: rgba(12, 137, 220, .72);
      background: #fff;
      box-shadow: 0 0 0 4px rgba(36, 166, 232, .12);
    }

    button {
      min-height: 38px;
      padding: 9px 15px;
      border: 1px solid rgba(17, 133, 205, .24);
      border-radius: 11px;
      color: #0b629d;
      font-weight: 700;
      background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(231,247,255,.96));
      box-shadow: 0 5px 12px rgba(24, 116, 174, .08);
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease;
    }

    button:hover:not(:disabled) {
      transform: translateY(-1px);
      border-color: rgba(13, 133, 210, .48);
      background: linear-gradient(180deg, #fff, #dcf3ff);
      box-shadow: 0 8px 18px rgba(24, 116, 174, .14);
    }

    button:active:not(:disabled) {
      transform: translateY(0);
      box-shadow: 0 3px 8px rgba(24, 116, 174, .12);
    }

    button:disabled {
      opacity: .46;
      box-shadow: none;
    }

    #login,
    #create-person,
    #create-relationship,
    #create-conversation,
    #create-message,
    #create-interaction,
    #load-strategic-reply,
    #confirm-action-decision,
    #record-action-execution,
    #record-action-outcome,
    #persist-action-learning,
    .guided-primary-action {
      color: #fff;
      border-color: rgba(0, 112, 193, .58);
      background: linear-gradient(135deg, #0b82dc, #22a9ec 58%, #33c6ef);
      box-shadow: 0 9px 20px rgba(10, 132, 210, .22), inset 0 1px 0 rgba(255,255,255,.28);
    }

    #login:hover:not(:disabled),
    #create-person:hover:not(:disabled),
    #create-relationship:hover:not(:disabled),
    #create-conversation:hover:not(:disabled),
    #create-message:hover:not(:disabled),
    #create-interaction:hover:not(:disabled),
    #load-strategic-reply:hover:not(:disabled),
    #confirm-action-decision:hover:not(:disabled),
    #record-action-execution:hover:not(:disabled),
    #record-action-outcome:hover:not(:disabled),
    #persist-action-learning:hover:not(:disabled),
    .guided-primary-action:hover:not(:disabled) {
      border-color: rgba(0, 106, 184, .72);
      color: #fff;
      background: linear-gradient(135deg, #0874ca, #169fe6 58%, #2abce7);
      box-shadow: 0 12px 25px rgba(10, 132, 210, .28), inset 0 1px 0 rgba(255,255,255,.28);
    }

    #delete-selected-person,
    #delete-selected-relationship,
    #delete-selected-conversation,
    #delete-selected-interaction,
    #delete-selected-message,
    #delete-provider,
    #reject-action-decision {
      color: #a43d52;
      border-color: rgba(202, 83, 108, .24);
      background: linear-gradient(180deg, #fff, #fff2f5);
    }

    .note {
      color: var(--tech-muted);
      opacity: 1;
      line-height: 1.65;
    }

    .status {
      min-height: 2.5em;
      border: 1px solid rgba(48, 160, 218, .18);
      border-left: 3px solid rgba(22, 142, 234, .54);
      border-radius: 11px;
      color: #31566d;
      background: linear-gradient(135deg, rgba(240,250,255,.92), rgba(228,246,255,.82));
      box-shadow: inset 0 1px 0 rgba(255,255,255,.82);
    }

    .session-row {
      border-bottom-color: rgba(50, 150, 206, .16);
    }

    .guided-workflow {
      gap: 20px;
    }

    .guided-hero {
      position: relative;
      overflow: hidden;
      padding: 24px;
      border: 1px solid rgba(37, 158, 222, .28);
      border-radius: 21px;
      background:
        linear-gradient(120deg, rgba(255,255,255,.97), rgba(223,245,255,.9)),
        var(--tech-panel-strong);
      box-shadow: var(--tech-shadow);
    }

    .guided-hero::before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      opacity: .45;
      background-image:
        linear-gradient(rgba(43, 167, 229, .09) 1px, transparent 1px),
        linear-gradient(90deg, rgba(43, 167, 229, .09) 1px, transparent 1px);
      background-size: 26px 26px;
      mask-image: linear-gradient(90deg, transparent 28%, #000 72%, transparent 100%);
    }

    .guided-hero > * {
      position: relative;
      z-index: 1;
    }

    .guided-eyebrow {
      color: #0b8ed8;
      opacity: 1;
      font-size: .78rem;
      letter-spacing: .15em;
      text-transform: uppercase;
    }

    .guided-hero h2 {
      color: #0d4e75;
      font-size: clamp(1.4rem, 2.2vw, 2rem);
      letter-spacing: -.02em;
    }

    .guided-settings {
      border-color: rgba(30, 152, 216, .24);
      background: rgba(245, 252, 255, .82);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
    }

    .guided-settings > summary,
    .guided-advanced > summary {
      color: #1a6f9f;
    }

    .guided-step-nav {
      top: 8px;
      padding: 9px;
      border: 1px solid rgba(23, 145, 213, .2);
      border-radius: 16px;
      background: rgba(238, 250, 255, .88);
      box-shadow: 0 10px 30px rgba(24, 116, 174, .12), inset 0 1px 0 rgba(255,255,255,.9);
      backdrop-filter: blur(18px);
    }

    .guided-step-nav a {
      padding: 9px 12px;
      border: 1px solid transparent;
      border-radius: 11px;
      color: #28759e;
      font-weight: 800;
      text-decoration: none;
      transition: color .16s ease, background .16s ease, border-color .16s ease, transform .16s ease;
    }

    .guided-step-nav a:hover {
      color: #086fab;
      border-color: rgba(20, 146, 215, .24);
      background: rgba(255,255,255,.95);
      transform: translateY(-1px);
    }

    .guided-step {
      position: relative;
      overflow: hidden;
      padding: 22px;
      border: 1px solid rgba(24, 145, 211, .23);
      border-radius: 20px;
      background: rgba(255,255,255,.82);
      box-shadow: var(--tech-shadow-soft);
      backdrop-filter: blur(14px);
    }

    .guided-step::after {
      content: "";
      position: absolute;
      width: 170px;
      height: 170px;
      right: -100px;
      top: -105px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(45, 187, 239, .14), transparent 70%);
      pointer-events: none;
    }

    .guided-step-header {
      position: relative;
      z-index: 1;
      margin-bottom: 18px;
    }

    .guided-step-header h2 {
      color: #0d5078;
      font-size: 1.24rem;
    }

    .guided-step-header p {
      color: var(--tech-muted);
      opacity: 1;
      line-height: 1.55;
    }

    .guided-step-number {
      width: 38px;
      height: 38px;
      flex-basis: 38px;
      border: 1px solid rgba(255,255,255,.65);
      color: #fff;
      background: linear-gradient(145deg, #0b83db, #31c5ee);
      box-shadow: 0 7px 18px rgba(12, 137, 217, .24), inset 0 1px 0 rgba(255,255,255,.32);
    }

    .guided-advanced {
      padding: 13px 15px;
      border: 1px dashed rgba(26, 145, 208, .30);
      border-radius: 13px;
      background: rgba(242, 251, 255, .58);
    }

    .guided-advanced[open] {
      border-style: solid;
      background: rgba(246, 252, 255, .84);
    }

    .guided-action-bar {
      padding: 15px;
      border: 1px solid rgba(25, 149, 214, .18);
      border-radius: 14px;
      background: linear-gradient(135deg, rgba(238,249,255,.92), rgba(226,245,255,.8));
    }

    #guided-settings-content > fieldset,
    .guided-primary > fieldset {
      box-shadow: none;
    }

    ::selection {
      color: #073b5c;
      background: rgba(89, 203, 249, .34);
    }

    @media (max-width: 900px) {
      body {
        margin-top: 14px;
        padding: 0 14px 48px;
      }
      body > header {
        padding: 20px;
      }
      .guided-step {
        padding: 17px;
      }
      .guided-step-nav {
        top: 4px;
        overflow-x: auto;
        flex-wrap: nowrap;
        scrollbar-width: thin;
      }
      .guided-step-nav a {
        flex: 0 0 auto;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { transition: none !important; }
    }
'''
