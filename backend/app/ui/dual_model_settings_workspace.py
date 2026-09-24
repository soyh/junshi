DUAL_MODEL_SETTINGS_STYLE = r'''
    #dual-model-intro {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      margin: 0 0 12px;
      padding: 15px 17px;
      border: 1px solid rgba(25, 167, 232, .16);
      border-radius: 16px;
      background:
        radial-gradient(circle at 94% 4%, rgba(82, 205, 250, .22), transparent 14rem),
        linear-gradient(135deg, rgba(244,252,255,.96), rgba(232,247,255,.82));
    }

    #dual-model-intro .dual-model-eyebrow {
      margin: 0 0 4px;
      color: var(--sky-600, #0787cf);
      font-size: .69rem;
      font-weight: 900;
      letter-spacing: .14em;
      text-transform: uppercase;
    }

    #dual-model-intro h3 {
      margin: 0;
      color: var(--sky-950, #08233d);
      font-size: 1.08rem;
    }

    #dual-model-intro p {
      max-width: 780px;
      margin: 6px 0 0;
      color: var(--muted, #5d7790);
      font-size: .82rem;
      line-height: 1.55;
    }

    #dual-model-intro .dual-model-route-chip {
      flex: 0 0 auto;
      padding: 6px 10px;
      border: 1px solid rgba(25, 167, 232, .20);
      border-radius: 999px;
      color: var(--sky-800, #0d4673);
      background: rgba(255,255,255,.82);
      font-size: .72rem;
      font-weight: 900;
      white-space: nowrap;
    }

    #dual-model-status {
      margin: 0 0 14px !important;
      padding: 10px 12px !important;
      border-radius: 12px !important;
      line-height: 1.5;
    }

    #dual-model-settings {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }

    #dual-model-settings .dual-model-card {
      position: relative;
      overflow: hidden;
      min-width: 0;
      padding: 16px;
      border: 1px solid rgba(25, 167, 232, .19);
      border-radius: 18px;
      background:
        radial-gradient(circle at 96% 2%, rgba(88, 200, 245, .17), transparent 12rem),
        linear-gradient(145deg, rgba(255,255,255,.97), rgba(240,250,255,.90));
      box-shadow: 0 12px 32px rgba(23, 116, 169, .08);
    }

    #dual-model-settings .dual-model-card::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 3px;
      background: linear-gradient(180deg, var(--sky-400, #58c8f5), #4f8eff);
    }

    #dual-model-settings .dual-model-card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 4px;
    }

    #dual-model-settings .dual-model-title-wrap {
      min-width: 0;
    }

    #dual-model-settings .dual-model-role-label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
      padding: 4px 8px;
      border: 1px solid rgba(25, 167, 232, .18);
      border-radius: 999px;
      color: var(--sky-700, #0969a8);
      background: rgba(226,246,255,.74);
      font-size: .66rem;
      font-weight: 900;
      letter-spacing: .08em;
    }

    #dual-model-settings h3 {
      margin: 0;
      color: var(--sky-950, #08233d);
      font-size: 1.05rem;
    }

    #dual-model-settings .dual-model-role-state {
      flex: 0 0 auto;
      padding: 5px 8px;
      border: 1px solid rgba(127,127,127,.18);
      border-radius: 999px;
      color: #526279;
      background: rgba(255,255,255,.82);
      font-size: .69rem;
      font-weight: 900;
      white-space: nowrap;
    }

    #dual-model-settings .dual-model-role-state[data-state="active"] {
      color: #05603a;
      border-color: rgba(21, 164, 103, .22);
      background: rgba(224, 250, 239, .88);
    }

    #dual-model-settings .dual-model-role-state[data-state="linked"] {
      color: var(--sky-800, #0d4673);
      border-color: rgba(25, 167, 232, .22);
      background: rgba(226, 246, 255, .88);
    }

    #dual-model-settings .dual-model-role-state[data-state="empty"] {
      color: #805b16;
      border-color: rgba(207, 151, 45, .20);
      background: rgba(255, 247, 224, .88);
    }

    #dual-model-settings .dual-model-role-note {
      min-height: 2.6em;
      margin: 6px 0 13px;
      color: var(--muted, #5d7790);
      font-size: .79rem;
      line-height: 1.55;
    }

    #dual-model-settings .dual-model-fields {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 12px;
    }

    #dual-model-settings .dual-model-field {
      min-width: 0;
    }

    #dual-model-settings .dual-model-field-name,
    #dual-model-settings .dual-model-field-baseUrl,
    #dual-model-settings .dual-model-field-apiKey {
      grid-column: 1 / -1;
    }

    #dual-model-settings .dual-model-field label {
      display: block;
      margin-bottom: 5px;
      color: var(--sky-900, #0b2f50);
      font-size: .76rem;
      font-weight: 800;
    }

    #dual-model-settings .dual-model-field input,
    #dual-model-settings .dual-model-field select {
      width: 100%;
      min-width: 0;
      box-sizing: border-box;
      margin: 0;
    }

    #dual-model-settings .dual-model-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 13px;
      padding-top: 12px;
      border-top: 1px solid rgba(25, 167, 232, .11);
    }

    #dual-model-settings .dual-model-actions button {
      margin: 0 !important;
    }

    #dual-model-settings .dual-model-actions .client-primary-button {
      color: #fff !important;
      border-color: transparent !important;
      background: linear-gradient(135deg, var(--sky-500, #19a7e8), #4d86ef) !important;
      box-shadow: 0 8px 20px rgba(29, 145, 218, .18) !important;
    }

    #dual-model-settings .dual-model-key-state {
      margin-top: 5px;
      color: var(--muted, #5d7790);
      font-size: .72rem;
      line-height: 1.45;
    }

    #provider-advanced-profiles {
      margin-top: 4px;
      padding: 12px 14px;
      border: 1px dashed rgba(25, 167, 232, .22);
      border-radius: 14px;
      background: rgba(245, 252, 255, .62);
    }

    #provider-advanced-profiles > summary {
      cursor: pointer;
      color: var(--sky-800, #0d4673);
      font-weight: 900;
      font-size: .8rem;
    }

    #provider-advanced-profiles-content {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(25, 167, 232, .12);
    }

    @media (max-width: 980px) {
      #dual-model-settings {
        grid-template-columns: 1fr;
      }

      #dual-model-settings .dual-model-role-note {
        min-height: 0;
      }
    }

    @media (max-width: 620px) {
      #dual-model-intro {
        display: block;
      }

      #dual-model-intro .dual-model-route-chip {
        display: inline-block;
        margin-top: 10px;
      }

      #dual-model-settings .dual-model-card {
        padding: 14px 12px 14px 14px;
      }

      #dual-model-settings .dual-model-fields {
        grid-template-columns: 1fr;
      }

      #dual-model-settings .dual-model-field-name,
      #dual-model-settings .dual-model-field-baseUrl,
      #dual-model-settings .dual-model-field-apiKey {
        grid-column: auto;
      }
    }
'''


DUAL_MODEL_SETTINGS_SCRIPT = r'''
  let dualPrimaryProfileId = null;
  let dualVisionProfileId = null;

  function dualRoleIds(role) {
    return {
      name: `dual-${role}-name`,
      provider: `dual-${role}-provider`,
      baseUrl: `dual-${role}-base-url`,
      model: `dual-${role}-model`,
      apiKey: `dual-${role}-api-key`,
      timeout: `dual-${role}-timeout`,
      keyState: `dual-${role}-key-state`,
      state: `dual-${role}-state`,
    };
  }

  function dualSetRoleState(role, text, state = 'empty') {
    const node = byId(dualRoleIds(role).state);
    if (!node) return;
    node.textContent = text;
    node.dataset.state = state;
  }

  function dualFillProviderOptions(select) {
    select.replaceChildren();
    Object.entries(multiProviderPresets).forEach(([value, preset]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = preset.label;
      select.appendChild(option);
    });
  }

  function dualApplyPreset(role) {
    const ids = dualRoleIds(role);
    const provider = byId(ids.provider);
    const baseUrl = byId(ids.baseUrl);
    const model = byId(ids.model);
    const preset = provider ? multiProviderPresets[provider.value] : null;
    if (!preset || !baseUrl || !model) return;
    const knownBaseUrls = new Set(Object.values(multiProviderPresets).map((item) => item.baseUrl).filter(Boolean));
    const knownModels = new Set(Object.values(multiProviderPresets).map((item) => item.model).filter(Boolean));
    if (!baseUrl.value.trim() || knownBaseUrls.has(baseUrl.value.trim())) baseUrl.value = preset.baseUrl;
    if (!model.value.trim() || knownModels.has(model.value.trim())) model.value = preset.model;
    baseUrl.placeholder = preset.baseUrl || 'https://your-provider.example/v1';
    model.placeholder = preset.model || 'model-name';
  }

  function dualFillRole(role, profile) {
    const ids = dualRoleIds(role);
    if (!profile) {
      byId(ids.name).value = role === 'primary' ? '主文本模型' : '视觉模型';
      byId(ids.provider).value = 'qwen';
      byId(ids.baseUrl).value = multiProviderPresets.qwen.baseUrl;
      byId(ids.model).value = role === 'primary' ? 'qwen3.7-flash' : 'qwen3-vl-flash';
      byId(ids.apiKey).value = '';
      byId(ids.timeout).value = '60';
      byId(ids.keyState).textContent = 'API Key：未保存。首次创建必须填写。';
      return;
    }
    byId(ids.name).value = profile.name || '';
    byId(ids.provider).value = profile.provider;
    byId(ids.baseUrl).value = profile.base_url;
    byId(ids.model).value = profile.model;
    byId(ids.apiKey).value = '';
    byId(ids.timeout).value = String(profile.timeout_seconds);
    byId(ids.keyState).textContent = profile.api_key_configured
      ? 'API Key：已在服务端加密保存；留空表示保持原 Key。'
      : 'API Key：未保存。';
  }

  function dualRolePayload(role, requireKey) {
    const ids = dualRoleIds(role);
    const key = byId(ids.apiKey).value;
    const payload = {
      name: byId(ids.name).value.trim(),
      provider: byId(ids.provider).value,
      base_url: byId(ids.baseUrl).value.trim(),
      model: byId(ids.model).value.trim(),
      timeout_seconds: Number(byId(ids.timeout).value),
    };
    if (!payload.name) throw new Error('配置名称不能为空');
    if (!payload.base_url) throw new Error('Base URL 不能为空');
    if (!payload.model) throw new Error('Model 不能为空');
    if (requireKey && !key) throw new Error('首次创建该角色模型时必须填写 API Key');
    if (key) payload.api_key = key;
    return payload;
  }

  async function loadDualModelSettings() {
    if (!currentAccessToken) return;
    const [profiles, vision] = await Promise.all([
      api('/api/v1/settings/llm/profiles'),
      api('/api/v1/settings/llm/vision'),
    ]);
    const active = Array.isArray(profiles) ? profiles.find((item) => item.is_active) : null;
    dualPrimaryProfileId = active?.id || null;
    dualVisionProfileId = vision?.profile_id || null;
    dualFillRole('primary', active || null);
    dualFillRole('vision', vision || null);

    dualSetRoleState(
      'primary',
      active ? '当前生效' : '未配置',
      active ? 'active' : 'empty',
    );
    dualSetRoleState(
      'vision',
      vision ? '独立视觉' : active ? '跟随主模型' : '未配置',
      vision ? 'active' : active ? 'linked' : 'empty',
    );

    const status = byId('dual-model-status');
    const primaryText = active
      ? `主文本/分析：${active.provider} / ${active.model}`
      : '主文本/分析：未配置';
    const visionText = vision
      ? `视觉图片/视频：${vision.provider} / ${vision.model}`
      : active
        ? '视觉图片/视频：跟随主模型'
        : '视觉图片/视频：未配置';
    status.textContent = `${primaryText}；${visionText}。两套配置的 Provider、API Key、Base URL、Model、Timeout 可完全不同。`;
  }

  async function dualRefreshAdvancedProfiles() {
    if (typeof loadLlmProfiles === 'function') {
      await loadLlmProfiles();
    }
  }

  async function saveDualPrimary() {
    const requireKey = !dualPrimaryProfileId;
    const payload = dualRolePayload('primary', requireKey);
    let profile;
    if (dualPrimaryProfileId) {
      profile = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(dualPrimaryProfileId)}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    } else {
      payload.activate = true;
      profile = await api('/api/v1/settings/llm/profiles', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      dualPrimaryProfileId = profile.id;
    }
    await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(profile.id)}/activate`, {method: 'POST'});
    byId('dual-primary-api-key').value = '';
    await loadDualModelSettings();
    await dualRefreshAdvancedProfiles();
    byId('dual-model-status').textContent = `主文本/分析模型已保存：${profile.name} · ${profile.provider} / ${profile.model}`;
  }

  async function saveDualVision() {
    const sharesPrimary = Boolean(dualVisionProfileId && dualVisionProfileId === dualPrimaryProfileId);
    const requireKey = !dualVisionProfileId || sharesPrimary;
    const payload = dualRolePayload('vision', requireKey);
    let profile;
    if (dualVisionProfileId && !sharesPrimary) {
      profile = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(dualVisionProfileId)}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    } else {
      payload.activate = false;
      profile = await api('/api/v1/settings/llm/profiles', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      dualVisionProfileId = profile.id;
    }
    await api('/api/v1/settings/llm/vision', {
      method: 'PUT',
      body: JSON.stringify({profile_id: profile.id}),
    });
    byId('dual-vision-api-key').value = '';
    await loadDualModelSettings();
    await dualRefreshAdvancedProfiles();
    byId('dual-model-status').textContent = `视觉模型已保存：${profile.name} · ${profile.provider} / ${profile.model}`;
  }

  async function testDualPrimary() {
    if (!dualPrimaryProfileId) throw new Error('请先保存主文本模型');
    const result = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(dualPrimaryProfileId)}/test`, {method: 'POST'});
    const label = result?.status === 'ok' ? 'PASS' : 'FAIL';
    byId('dual-model-status').textContent = `${label} [主文本连接/${result?.code || 'unknown'}] ${result?.provider || ''} / ${result?.model || ''}: ${result?.message || ''}`;
  }

  async function testDualVision() {
    const result = await api('/api/v1/settings/llm/vision/test', {method: 'POST'});
    const label = result?.status === 'ok' ? 'PASS' : 'FAIL';
    byId('dual-model-status').textContent = `${label} [视觉图片测试/${result?.code || 'unknown'}] ${result?.provider || ''} / ${result?.model || ''}: ${result?.message || ''}`;
  }

  async function dualVisionFollowPrimary() {
    await api('/api/v1/settings/llm/vision', {method: 'DELETE'});
    dualVisionProfileId = null;
    await loadDualModelSettings();
    await dualRefreshAdvancedProfiles();
    byId('dual-model-status').textContent = '视觉模型已改为跟随主文本模型。独立视觉 Profile 仍保留在高级 Profile 管理中，不会删除。';
  }

  function dualMakeInput(role, field, labelText, type = 'text') {
    const ids = dualRoleIds(role);
    const wrap = document.createElement('div');
    wrap.className = `dual-model-field dual-model-field-${field}`;
    const label = document.createElement('label');
    const id = ids[field];
    label.htmlFor = id;
    label.textContent = labelText;
    let input;
    if (field === 'provider') {
      input = document.createElement('select');
      dualFillProviderOptions(input);
    } else {
      input = document.createElement('input');
      input.type = type;
    }
    input.id = id;
    input.className = 'requires-auth';
    input.disabled = !currentAccessToken;
    if (field === 'apiKey') {
      input.autocomplete = 'new-password';
      input.placeholder = '留空保持已有 Key；首次创建必须填写';
    }
    if (field === 'timeout') {
      input.type = 'number';
      input.min = '0.1';
      input.max = '300';
      input.step = '0.1';
    }
    wrap.append(label, input);
    if (field === 'apiKey') {
      const state = document.createElement('div');
      state.id = ids.keyState;
      state.className = 'dual-model-key-state';
      wrap.appendChild(state);
    }
    return wrap;
  }

  function dualBuildCard(role, roleLabel, titleText, noteText) {
    const card = document.createElement('section');
    card.className = 'dual-model-card';
    card.id = `dual-${role}-card`;

    const header = document.createElement('div');
    header.className = 'dual-model-card-header';
    const titleWrap = document.createElement('div');
    titleWrap.className = 'dual-model-title-wrap';
    const roleTag = document.createElement('span');
    roleTag.className = 'dual-model-role-label';
    roleTag.textContent = roleLabel;
    const title = document.createElement('h3');
    title.textContent = titleText;
    titleWrap.append(roleTag, title);

    const roleState = document.createElement('span');
    roleState.id = dualRoleIds(role).state;
    roleState.className = 'dual-model-role-state';
    roleState.dataset.state = 'empty';
    roleState.textContent = '等待登录';
    header.append(titleWrap, roleState);

    const note = document.createElement('p');
    note.className = 'dual-model-role-note';
    note.textContent = noteText;

    const fields = document.createElement('div');
    fields.className = 'dual-model-fields';
    fields.append(
      dualMakeInput(role, 'name', '配置名称'),
      dualMakeInput(role, 'provider', '模型服务'),
      dualMakeInput(role, 'model', '模型名称'),
      dualMakeInput(role, 'baseUrl', '接口地址（Base URL）'),
      dualMakeInput(role, 'apiKey', 'API Key', 'password'),
      dualMakeInput(role, 'timeout', '超时时间（秒）', 'number'),
    );

    card.append(header, note, fields);
    card.querySelector(`#${dualRoleIds(role).provider}`)?.addEventListener(
      'change',
      () => dualApplyPreset(role),
    );
    return card;
  }

  function installDualModelSettings() {
    const providerFieldset = byId('provider');
    if (!providerFieldset || byId('dual-model-settings')) return;

    const legend = providerFieldset.querySelector(':scope > legend');
    if (legend) legend.textContent = 'AI 模型设置';

    const intro = document.createElement('div');
    intro.id = 'dual-model-intro';
    const introCopy = document.createElement('div');
    const eyebrow = document.createElement('p');
    eyebrow.className = 'dual-model-eyebrow';
    eyebrow.textContent = 'DUAL MODEL ROUTING';
    const introTitle = document.createElement('h3');
    introTitle.textContent = '文本推理与视觉理解独立配置';
    const introNote = document.createElement('p');
    introNote.textContent = '主文本模型负责分析、策略与回复；视觉模型负责聊天截图、图片和视频关键帧。两者可以使用完全不同的服务商、接口地址、模型和 API Key。';
    introCopy.append(eyebrow, introTitle, introNote);
    const routeChip = document.createElement('span');
    routeChip.className = 'dual-model-route-chip';
    routeChip.textContent = '文本 / 视觉分流';
    intro.append(introCopy, routeChip);

    const status = document.createElement('div');
    status.id = 'dual-model-status';
    status.className = 'status dual-model-status';
    status.textContent = '登录后可分别配置主文本模型和视觉模型。';

    const grid = document.createElement('div');
    grid.id = 'dual-model-settings';
    const primary = dualBuildCard(
      'primary',
      'TEXT · 主路由',
      '主文本 / 分析模型',
      '用于结构化分析、策略生成、Recommendation、行动计划与回复建议等文本任务。',
    );
    const primaryActions = document.createElement('div');
    primaryActions.className = 'dual-model-actions';
    const savePrimary = document.createElement('button');
    savePrimary.id = 'dual-primary-save';
    savePrimary.type = 'button';
    savePrimary.className = 'requires-auth client-primary-button';
    savePrimary.disabled = !currentAccessToken;
    savePrimary.textContent = '保存主文本模型';
    const testPrimary = document.createElement('button');
    testPrimary.id = 'dual-primary-test';
    testPrimary.type = 'button';
    testPrimary.className = 'requires-auth';
    testPrimary.disabled = !currentAccessToken;
    testPrimary.textContent = '测试主模型连接';
    primaryActions.append(savePrimary, testPrimary);
    primary.appendChild(primaryActions);

    const vision = dualBuildCard(
      'vision',
      'VISION · 多模态',
      '视觉 / 图片视频模型',
      '用于聊天截图、图片与视频关键帧识别。未单独配置时可让视觉任务跟随主文本模型。',
    );
    const visionActions = document.createElement('div');
    visionActions.className = 'dual-model-actions';
    const saveVision = document.createElement('button');
    saveVision.id = 'dual-vision-save';
    saveVision.type = 'button';
    saveVision.className = 'requires-auth client-primary-button';
    saveVision.disabled = !currentAccessToken;
    saveVision.textContent = '保存视觉模型';
    const testVision = document.createElement('button');
    testVision.id = 'dual-vision-test';
    testVision.type = 'button';
    testVision.className = 'requires-auth';
    testVision.disabled = !currentAccessToken;
    testVision.textContent = '测试视觉能力';
    const follow = document.createElement('button');
    follow.id = 'dual-vision-follow-primary';
    follow.type = 'button';
    follow.className = 'requires-auth';
    follow.disabled = !currentAccessToken;
    follow.textContent = '视觉跟随主模型';
    visionActions.append(saveVision, testVision, follow);
    vision.appendChild(visionActions);

    grid.append(primary, vision);

    const advanced = document.createElement('details');
    advanced.id = 'provider-advanced-profiles';
    const summary = document.createElement('summary');
    summary.textContent = '高级：Profile 管理、角色切换与兼容设置';
    const advancedContent = document.createElement('div');
    advancedContent.id = 'provider-advanced-profiles-content';
    advanced.append(summary, advancedContent);

    const keep = new Set([legend, intro, status, grid, advanced]);
    Array.from(providerFieldset.children).forEach((child) => {
      if (!keep.has(child) && child !== legend) advancedContent.appendChild(child);
    });

    if (legend) legend.insertAdjacentElement('afterend', intro);
    else providerFieldset.prepend(intro);
    intro.insertAdjacentElement('afterend', status);
    status.insertAdjacentElement('afterend', grid);
    grid.insertAdjacentElement('afterend', advanced);

    savePrimary.addEventListener('click', async () => {
      try { await saveDualPrimary(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
    testPrimary.addEventListener('click', async () => {
      try { await testDualPrimary(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
    saveVision.addEventListener('click', async () => {
      try { await saveDualVision(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
    testVision.addEventListener('click', async () => {
      try { await testDualVision(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
    follow.addEventListener('click', async () => {
      try { await dualVisionFollowPrimary(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });

    const baseEstablishSession = establishSession;
    establishSession = function(data, message) {
      baseEstablishSession(data, message);
      loadDualModelSettings().catch((error) => {
        status.textContent = error instanceof Error ? error.message : String(error);
      });
    };

    loadDualModelSettings().catch(() => {});
  }

  installDualModelSettings();
'''
