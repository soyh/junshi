MY_PROFILE_STYLE = r'''
  #my-profile-open-nav {
    font-size: 13px;
    background: transparent;
    border: 0;
    box-shadow: none;
    color: inherit;
    margin: 0;
    padding: 8px;
    cursor: pointer;
  }

  #my-profile-panel {
    position: fixed;
    inset: 0;
    z-index: 90;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px 16px;
    background: rgba(12, 40, 62, .38);
    backdrop-filter: blur(3px);
  }

  #my-profile-panel[hidden] { display: none; }

  #my-profile-card {
    width: min(760px, 100%);
    max-height: min(86vh, 900px);
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 18px 20px;
    border-radius: 18px;
    background: #fff;
    color: #183149;
    box-shadow: 0 24px 60px rgba(15, 60, 95, .28);
    overflow: hidden;
  }

  #my-profile-card > header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  #my-profile-card h2 { margin: 0; font-size: 1.05rem; }
  #my-profile-note { margin: 0; color: #5a7288; font-size: .86rem; line-height: 1.5; }
  #my-profile-body { overflow: auto; display: grid; gap: 14px; padding-right: 4px; }
  #my-profile-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; }
  #my-profile-fields label { display: block; font-size: .8rem; color: #5a7288; margin-bottom: 3px; }
  #my-profile-fields input { width: 100%; box-sizing: border-box; padding: 8px 10px; border: 1px solid #cddbe7; border-radius: 9px; font: inherit; }
  #my-profile-about { grid-column: 1 / -1; }
  #my-profile-rules-head { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  #my-profile-rules-head select { padding: 7px 9px; border-radius: 9px; border: 1px solid #cddbe7; font: inherit; }
  #my-profile-template-note { color: #6b8497; font-size: .78rem; }
  #my-profile-rules { width: 100%; box-sizing: border-box; min-height: 130px; padding: 10px; border: 1px solid #cddbe7; border-radius: 10px; font: inherit; line-height: 1.55; resize: vertical; }
  #my-profile-card > footer { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  #my-profile-status { color: #4b6b83; font-size: .85rem; flex: 1 1 220px; }
  #my-profile-card button { padding: 9px 16px; border-radius: 10px; border: 1px solid #9cc3de; background: #f4fbff; color: #12506f; font: inherit; cursor: pointer; }
  #my-profile-card button.primary { background: #1976a8; border-color: #1976a8; color: #fff; }
  .my-profile-hint { margin: 6px 0; color: #6b8497; font-size: .78rem; line-height: 1.5; }

  @media (max-width: 620px) {
    #my-profile-panel { padding: 0; align-items: stretch; }
    #my-profile-card { width: 100%; max-height: 100vh; border-radius: 0; padding: 14px 14px 18px; }
    #my-profile-fields { grid-template-columns: 1fr; }
    #my-profile-fields input, #my-profile-rules, #my-profile-rules-head select { font-size: 16px; }
    #my-profile-rules { min-height: 150px; }
  }
'''

MY_PROFILE_HTML = r'''
<div id="my-profile-panel" hidden>
  <section id="my-profile-card" role="dialog" aria-modal="true" aria-labelledby="my-profile-title">
    <header>
      <h2 id="my-profile-title">我的资料</h2>
      <button id="my-profile-close" type="button">关闭</button>
    </header>
    <p id="my-profile-note">这些是“你”的事实，自动回复会用第一人称使用；没填的项会保持模糊，不会替你想一个年龄或职业。内容跟随你的账号，在网页、电脑客户端和手机上看到的是同一份。</p>
    <div id="my-profile-body">
      <div id="my-profile-fields">
        <div><label for="mp-nickname">称呼 / 昵称</label><input id="mp-nickname" maxlength="40" autocomplete="nickname" placeholder="比如：小林"></div>
        <div><label for="mp-gender">性别</label><input id="mp-gender" maxlength="20" placeholder="比如：男"></div>
        <div><label for="mp-birth-year">出生年份</label><input id="mp-birth-year" maxlength="20" inputmode="numeric" placeholder="比如：1996"></div>
        <div><label for="mp-city">所在城市</label><input id="mp-city" maxlength="40" placeholder="比如：杭州"></div>
        <div><label for="mp-job">职业</label><input id="mp-job" maxlength="40" placeholder="比如：产品经理"></div>
        <div><label for="mp-hobbies">兴趣爱好</label><input id="mp-hobbies" maxlength="120" placeholder="比如：跑步、看展"></div>
        <div><label for="mp-relationship">感情状态</label><input id="mp-relationship" maxlength="40" placeholder="比如：单身"></div>
        <div id="my-profile-about"><label for="mp-about">其他想让它知道的</label><input id="mp-about" maxlength="400" placeholder="比如：不太爱打电话，晚上回消息慢"></div>
      </div>
      <div>
        <div id="my-profile-rules-head">
          <strong>默认回复规则</strong>
          <select id="mp-template"><option value="">选一个模板…</option></select>
          <button id="mp-fill-template" type="button">填入模板</button>
          <span id="my-profile-template-note"></span>
        </div>
        <p id="my-profile-note-rules" class="my-profile-hint">通道里没单独写规则时用这里；只影响语气、称呼、长度、用词、表情和节奏，不能覆盖证据与安全边界。留空即使用默认风格。</p>
        <textarea id="mp-rules" maxlength="1500" placeholder="例如：短句、口语、允许倒装；不要破折号，不要设问后自答。"></textarea>
      </div>
    </div>
    <footer>
      <span id="my-profile-status" role="status"></span>
      <button id="my-profile-save" class="primary" type="button">保存</button>
    </footer>
  </section>
</div>
'''

MY_PROFILE_SCRIPT = r'''
  (function installMyProfile(){
    const profilePanel = byId('my-profile-panel');
    if (!profilePanel || profilePanel.dataset.installed === 'true') return;
    profilePanel.dataset.installed = 'true';
    const profileStatus = byId('my-profile-status');
    const profileFields = {
      nickname: byId('mp-nickname'),
      gender: byId('mp-gender'),
      birth_year: byId('mp-birth-year'),
      city: byId('mp-city'),
      job: byId('mp-job'),
      hobbies: byId('mp-hobbies'),
      relationship_status: byId('mp-relationship'),
      about: byId('mp-about'),
      reply_rules: byId('mp-rules'),
    };
    const templateSelect = byId('mp-template');
    const templateNote = byId('my-profile-template-note');
    let templateCache = null;

    function profileSetStatus(text) { profileStatus.textContent = text || ''; }

    async function loadTemplates() {
      if (templateCache) return templateCache;
      try {
        const data = await api('/api/v1/settings/reply-templates');
        templateCache = Array.isArray(data && data.templates) ? data.templates : [];
      } catch (_) {
        templateCache = [];
      }
      templateSelect.replaceChildren(new Option('选一个模板…', ''));
      templateCache.forEach((item) => templateSelect.appendChild(new Option(item.name, item.name)));
      return templateCache;
    }

    async function openProfile() {
      if (!currentAccessToken) { profileSetStatus('请先登录。'); profilePanel.hidden = false; return; }
      profilePanel.hidden = false;
      profileSetStatus('正在读取…');
      try {
        const data = await api('/api/v1/settings/profile');
        Object.entries(profileFields).forEach(([key, node]) => {
          node.value = (data && data[key]) || '';
        });
        profileSetStatus(data && data.updated_at ? `上次保存：${data.updated_at}` : '还没有填写过。');
        await loadTemplates();
      } catch (error) {
        profileSetStatus(`读取失败：${error instanceof Error ? error.message : String(error)}`);
      }
    }

    function closeProfile() { profilePanel.hidden = true; }

    async function saveProfile() {
      const payload = {};
      Object.entries(profileFields).forEach(([key, node]) => { payload[key] = node.value; });
      profileSetStatus('正在保存…');
      try {
        const data = await api('/api/v1/settings/profile', {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        profileSetStatus(data && data.updated_at ? `已保存（${data.updated_at}）` : '已保存');
        if (typeof loadWorkspace === 'function') { try { await loadWorkspace(); } catch (_) {} }
      } catch (error) {
        profileSetStatus(`保存失败：${error instanceof Error ? error.message : String(error)}`);
      }
    }

    async function fillTemplate() {
      const name = templateSelect.value;
      if (!name) { templateNote.textContent = '先选一个模板。'; return; }
      const list = await loadTemplates();
      const found = list.find((item) => item.name === name);
      if (!found) { templateNote.textContent = '模板不可用。'; return; }
      profileFields.reply_rules.value = found.text;
      templateNote.textContent = found.note || '';
    }

    byId('my-profile-close').addEventListener('click', closeProfile);
    byId('my-profile-save').addEventListener('click', saveProfile);
    byId('mp-fill-template').addEventListener('click', fillTemplate);
    profilePanel.addEventListener('click', (event) => { if (event.target === profilePanel) closeProfile(); });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !profilePanel.hidden) closeProfile();
    });

    const profileFooter = byId('client-footer');
    if (profileFooter && !byId('my-profile-open-nav')) {
      const openButton = clientEl('button', '', '我的资料');
      openButton.type = 'button';
      openButton.id = 'my-profile-open-nav';
      profileFooter.insertBefore(openButton, byId('logout'));
      openButton.addEventListener('click', openProfile);
    }
  })();
'''
