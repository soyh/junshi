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
  #my-profile-auto-send { border-top: 1px dashed #d6e2ec; padding-top: 10px; }
  .my-profile-check { display: flex; align-items: center; gap: 8px; font-size: .88rem; color: #23485f; cursor: pointer; }
  .my-profile-check input { width: 16px; height: 16px; margin: 0; }
  #my-profile-location-row > span { display: flex; gap: 6px; align-items: stretch; }
  #my-profile-location-row > span input { flex: 1 1 auto; min-width: 0; }
  #my-profile-location-row > span button { flex: 0 0 auto; padding: 8px 10px; white-space: nowrap; }
  #mp-location-note { display: block; font-style: normal; }

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
        <div><label for="mp-hometown">籍贯 / 老家</label><input id="mp-hometown" maxlength="40" placeholder="比如：台州"></div>
        <div id="my-profile-location-row"><label for="mp-current-location">当前所在地</label><span><input id="mp-current-location" maxlength="80" placeholder="点右侧按钮读取，或手动填写"><button id="mp-detect-location" type="button">读取当前位置</button></span><em id="mp-location-note" class="my-profile-hint"></em></div>
        <div><label for="mp-work-address">工作地址</label><input id="mp-work-address" maxlength="120" placeholder="比如：西湖区文三路 100 号"></div>
        <div><label for="mp-job">职业</label><input id="mp-job" maxlength="40" placeholder="比如：产品经理"></div>
        <div><label for="mp-hobbies">兴趣爱好</label><input id="mp-hobbies" maxlength="120" placeholder="比如：跑步、看展"></div>
        <div><label for="mp-relationship">感情状态</label><input id="mp-relationship" maxlength="40" placeholder="比如：单身"></div>
        <div><label for="mp-wechat-id">我的微信号</label><input id="mp-wechat-id" maxlength="60" placeholder="比如：lin_xiao96"></div>
        <div><label for="mp-wechat-aliases">微信的别称</label><input id="mp-wechat-aliases" maxlength="200" placeholder="比如：V、绿泡泡、地球号（逗号分隔）"></div>
        <div><label for="mp-wechat-word">提到微信时写</label><input id="mp-wechat-word" maxlength="20" placeholder="比如：V"><em class="my-profile-hint">有些平台屏蔽「微信/VX」，这里填你要用的说法；留空写「微信」。</em></div>
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
      <div id="my-profile-auto-send">
        <label class="my-profile-check" for="mp-auto-send"><input id="mp-auto-send" type="checkbox"> 我授权电脑客户端自动代发</label>
        <p class="my-profile-hint">勾选后，服务端把「必须由本人发送」这条约束降级为提示：通道插件生成的回复可以直接发出，统计里记为已授权。不勾选时保持原样。</p>
        <label class="my-profile-check" for="mp-strategic-plan"><input id="mp-strategic-plan" type="checkbox"> 先做「军师判断」再写回复（推荐）</label>
        <p class="my-profile-hint">开启后先生成判断卡片（局势、阶段、2–4 条战术，可含「这轮先不发」），再按选中的战术写一条消息；参考资料全文在这一步读到。关掉则回到原来的一次生成。</p>
        <label class="my-profile-check" for="mp-handoff"><input id="mp-handoff" type="checkbox"> 对方主动要联系方式时，可以把我的微信号发给他</label>
        <p class="my-profile-hint">只在对方明确开口、且聊得顺的时候给，不会主动塞；不勾选则一律不发号、也不问对方要号。对方给你的微信号会被记到人物资料里。对方用上面这些别称（V、绿泡泡…）开口也算数。</p>
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
      hometown: byId('mp-hometown'),
      current_location: byId('mp-current-location'),
      work_address: byId('mp-work-address'),
      job: byId('mp-job'),
      hobbies: byId('mp-hobbies'),
      relationship_status: byId('mp-relationship'),
      about: byId('mp-about'),
      wechat_id: byId('mp-wechat-id'),
      wechat_aliases: byId('mp-wechat-aliases'),
      wechat_display_alias: byId('mp-wechat-word'),
      reply_rules: byId('mp-rules'),
    };
    const autoSend = byId('mp-auto-send');
    const strategicPlan = byId('mp-strategic-plan');
    const handoff = byId('mp-handoff');
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
        if (autoSend) { autoSend.checked = !!(data && data.auto_send_authorized); }
        if (strategicPlan) { strategicPlan.checked = !(data && data.strategic_plan_enabled === false); }
        if (handoff) { handoff.checked = !!(data && data.contact_handoff_enabled); }
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
      payload.auto_send_authorized = !!(autoSend && autoSend.checked);
      payload.strategic_plan_enabled = !!(strategicPlan && strategicPlan.checked);
      payload.contact_handoff_enabled = !!(handoff && handoff.checked);
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

    function detectLocation() {
      const note = byId('mp-location-note');
      if (!navigator.geolocation) { note.textContent = '这台设备不支持定位，手动填写即可。'; return; }
      note.textContent = '正在读取定位…（手机第一次会弹权限）';
      navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        note.textContent = '正在换算成地址…';
        try {
          const data = await api(`/api/v1/settings/location?lat=${latitude}&lng=${longitude}`);
          profileFields.current_location.value = (data && data.label) || `纬度 ${latitude.toFixed(4)}，经度 ${longitude.toFixed(4)}`;
          note.textContent = data && data.fallback ? '只拿到坐标，可以自己改成常用叫法。' : '已填入，可手动调整。';
        } catch (error) {
          profileFields.current_location.value = `纬度 ${latitude.toFixed(4)}，经度 ${longitude.toFixed(4)}`;
          note.textContent = '地址换算没成功，已填坐标。';
        }
      }, (error) => {
        const reasons = {1: '你拒绝了定位权限', 2: '暂时定位不到', 3: '定位超时'};
        note.textContent = `${reasons[error.code] || '定位失败'}，手动填写也可以。`;
      }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
    }

    byId('my-profile-close').addEventListener('click', closeProfile);
    byId('mp-detect-location').addEventListener('click', detectLocation);
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
