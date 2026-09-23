DUAL_MODEL_SETTINGS_STYLE = r'''
    #dual-model-settings {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 14px;
    }

    #dual-model-settings .dual-model-card {
      min-width: 0;
      padding: 14px;
      border: 1px solid rgba(25, 167, 232, .18);
      border-radius: 14px;
      background: rgba(248,252,255,.92);
    }

    #dual-model-settings h3 {
      margin: 0;
      color: #26344d;
      font-size: 1rem;
    }

    #dual-model-settings .dual-model-role-note {
      margin: 5px 0 10px;
      color: #718096;
      font-size: .8rem;
      line-height: 1.5;
    }

    #dual-model-settings .dual-model-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 10px;
    }

    #dual-model-settings .dual-model-actions button { margin: 0 !important; }

    #dual-model-settings .dual-model-key-state {
      margin-top: 5px;
      color: #718096;
      font-size: .76rem;
    }

    #dual-model-status {
      margin: 0 0 12px !important;
    }

    #provider-advanced-profiles {
      margin-top: 10px;
      padding-top: 8px;
      border-top: 1px solid rgba(127,127,127,.16);
    }

    #provider-advanced-profiles > summary {
      cursor: pointer;
      color: #526279;
      font-weight: 800;
      font-size: .82rem;
    }

    #provider-advanced-profiles-content {
      margin-top: 10px;
    }

    @media (max-width: 820px) {
      #dual-model-settings { grid-template-columns: 1fr; }
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
    };
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
    if (!preset) return;
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
    byId('dual-model-status').textContent = `主文本/分析模型已保存：${profile.name} · ${profile.provider} / ${profile.model}`;
  }

  async function saveDualVision() {
    const requireKey = !dualVisionProfileId;
    const payload = dualRolePayload('vision', requireKey);
    let profile;
    if (dualVisionProfileId) {
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
    byId('dual-model-status').textContent = `视觉模型已保存：${profile.name} · ${profile.provider} / ${profile.model}`;
  }

  async function testDualPrimary() {
    if (!dualPrimaryProfileId) throw new Error('请先保存主文本模型');
    const result = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(dualPrimaryProfileId)}/test`, {method: 'POST'});
    const label = result?.status === 'ok' ? 'PASS' : 'FAIL';
    byId('dual-model-status').textContent = `${label} [主文本连接/${result?.code || 'unknown'}] ${result?.provider || ''} / ${result?.model || ''}: ${result?.message || ''}`;
  }

  async function testDualVision() {
    if (!dualVisionProfileId) throw new Error('请先保存视觉模型，或选择“视觉跟随主模型”');
    const result = await api('/api/v1/settings/llm/vision/test', {method: 'POST'});
    const label = result?.status === 'ok' ? 'PASS' : 'FAIL';
    byId('dual-model-status').textContent = `${label} [视觉图片测试/${result?.code || 'unknown'}] ${result?.provider || ''} / ${result?.model || ''}: ${result?.message || ''}`;
  }

  async function dualVisionFollowPrimary() {
    await api('/api/v1/settings/llm/vision', {method: 'DELETE'});
    dualVisionProfileId = null;
    await loadDualModelSettings();
    byId('dual-model-status').textContent = '视觉模型已改为跟随主文本模型。独立视觉 Profile 仍保留在高级 Profile 管理中，不会删除。';
  }

  function dualMakeInput(role, field, labelText, type = 'text') {
    const ids = dualRoleIds(role);
    const wrap = document.createElement('div');
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

  function dualBuildCard(role, titleText, noteText) {
    const card = document.createElement('section');
    card.className = 'dual-model-card';
    card.id = `dual-${role}-card`;
    const title = document.createElement('h3');
    title.textContent = titleText;
    const note = document.createElement('p');
    note.className = 'dual-model-role-note';
    note.textContent = noteText;
    card.append(
      title,
      note,
      dualMakeInput(role, 'name', '配置名称'),
      dualMakeInput(role, 'provider', 'Provider'),
      dualMakeInput(role, 'baseUrl', 'Base URL'),
      dualMakeInput(role, 'model', 'Model'),
      dualMakeInput(role, 'apiKey', 'API Key', 'password'),
      dualMakeInput(role, 'timeout', 'Timeout seconds', 'number'),
    );
    byId(dualRoleIds(role).provider)?.addEventListener('change', () => dualApplyPreset(role));
    return card;
  }

  function installDualModelSettings() {
    const providerFieldset = byId('provider');
    if (!providerFieldset || byId('dual-model-settings')) return;

    const legend = providerFieldset.querySelector(':scope > legend');
    if (legend) legend.textContent = 'AI 模型设置';

    const status = document.createElement('div');
    status.id = 'dual-model-status';
    status.className = 'status';
    status.textContent = '登录后分别配置主文本模型和视觉模型。';

    const grid = document.createElement('div');
    grid.id = 'dual-model-settings';
    const primary = dualBuildCard(
      'primary',
      '主文本 / 分析模型',
      '用于结构化分析、策略、回复生成等文本任务。可使用独立 Provider、API Key、Base URL 和 Model。',
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
      '视觉 / 图片视频模型',
      '用于聊天截图、图片和视频关键帧识别。可以与主模型使用完全不同的 Provider、API Key、Base URL 和 Model。',
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
    summary.textContent = '高级：Profile 管理与兼容设置';
    const advancedContent = document.createElement('div');
    advancedContent.id = 'provider-advanced-profiles-content';
    advanced.append(summary, advancedContent);

    const keep = new Set([legend, status, grid, advanced]);
    Array.from(providerFieldset.children).forEach((child) => {
      if (!keep.has(child) && child !== legend) advancedContent.appendChild(child);
    });

    if (legend) legend.insertAdjacentElement('afterend', status);
    else providerFieldset.prepend(status);
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
      loadDualModelSettings().catch((error) => { status.textContent = error instanceof Error ? error.message : String(error); });
    };

    loadDualModelSettings().catch(() => {});
  }

  installDualModelSettings();
'''
