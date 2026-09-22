MULTI_PROVIDER_SETTINGS_STYLE = r'''
#provider .provider-preset-note {
  margin: 6px 0 14px;
  font-size: .86rem;
  opacity: .76;
}
#provider .provider-preset-note strong {
  opacity: 1;
}
#provider-profile-controls {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(180px, .7fr);
  gap: 10px 12px;
  margin: 10px 0 14px;
}
#provider-profile-actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
#provider-profile-actions button { margin: 0; }
@media (max-width: 680px) {
  #provider-profile-controls { grid-template-columns: 1fr; }
  #provider-profile-actions { grid-column: auto; }
}
'''


MULTI_PROVIDER_SETTINGS_SCRIPT = r'''
  // TEST-178: multiple encrypted LLM profiles; the existing /settings/llm
  // contract continues to operate on the currently active profile.
  const multiProviderPresets = {
    qwen: {
      label: 'Qwen / 阿里云百炼',
      baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model: 'qwen3.7-flash',
    },
    deepseek: {
      label: 'DeepSeek',
      baseUrl: 'https://api.deepseek.com',
      model: 'deepseek-flash',
    },
    kimi: {
      label: 'Kimi / Moonshot',
      baseUrl: 'https://api.moonshot.ai/v1',
      model: 'kimi-k2.6',
    },
    openai: {
      label: 'OpenAI',
      baseUrl: 'https://api.openai.com/v1',
      model: 'gpt-5.6-luna',
    },
    gemini: {
      label: 'Gemini / Google',
      baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
      model: 'gemini-3.8-flash',
    },
    openai_compatible: {
      label: '其他 OpenAI-compatible',
      baseUrl: '',
      model: '',
    },
  };

  let llmProfiles = [];
  let selectedLlmProfileId = null;

  function fillProviderFields(profile) {
    if (!profile) return;
    byId('provider-name').value = profile.provider;
    byId('base-url').value = profile.base_url;
    byId('model').value = profile.model;
    byId('timeout').value = String(profile.timeout_seconds);
    byId('api-key').value = '';
    const nameInput = byId('provider-profile-name');
    if (nameInput) nameInput.value = profile.name || '';
  }

  function renderLlmProfiles(items) {
    llmProfiles = Array.isArray(items) ? items : [];
    const select = byId('provider-profile-select');
    if (!select) return;
    select.replaceChildren();
    const empty = document.createElement('option');
    empty.value = '';
    empty.textContent = llmProfiles.length ? '选择模型配置' : '暂无模型配置';
    select.appendChild(empty);
    llmProfiles.forEach((profile) => {
      const option = document.createElement('option');
      option.value = profile.id;
      option.textContent = `${profile.is_active ? '✓ ' : ''}${profile.name} · ${profile.provider} / ${profile.model}`;
      select.appendChild(option);
    });
    const active = llmProfiles.find((profile) => profile.is_active);
    if (selectedLlmProfileId && llmProfiles.some((profile) => profile.id === selectedLlmProfileId)) {
      select.value = selectedLlmProfileId;
    } else if (active) {
      selectedLlmProfileId = active.id;
      select.value = active.id;
      fillProviderFields(active);
    } else {
      selectedLlmProfileId = null;
      select.value = '';
    }
  }

  async function loadLlmProfiles() {
    if (!currentAccessToken) return;
    const items = await api('/api/v1/settings/llm/profiles');
    renderLlmProfiles(items);
    const active = llmProfiles.find((profile) => profile.is_active);
    providerStatus.textContent = active
      ? `当前模型：${active.name} · ${active.provider} / ${active.model}。API Key 仅服务端加密保存。`
      : '暂无多模型配置；可创建新的模型接口配置。';
  }

  function providerProfilePayload(requireKey = false) {
    const name = byId('provider-profile-name').value.trim();
    if (!name) throw new Error('配置名称不能为空');
    const key = byId('api-key').value;
    if (requireKey && !key) throw new Error('新建模型配置时必须填写 API Key');
    const payload = {
      name,
      provider: byId('provider-name').value,
      base_url: byId('base-url').value.trim(),
      model: byId('model').value.trim(),
      timeout_seconds: Number(byId('timeout').value),
    };
    if (key) payload.api_key = key;
    return payload;
  }

  async function createLlmProfile() {
    const payload = providerProfilePayload(true);
    payload.activate = llmProfiles.length === 0;
    const created = await api('/api/v1/settings/llm/profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    selectedLlmProfileId = created.id;
    byId('api-key').value = '';
    await loadLlmProfiles();
    providerStatus.textContent = `已创建模型配置：${created.name} · ${created.provider} / ${created.model}`;
  }

  async function updateLlmProfile() {
    if (!selectedLlmProfileId) throw new Error('请先选择要修改的模型配置');
    const updated = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selectedLlmProfileId)}`, {
      method: 'PUT',
      body: JSON.stringify(providerProfilePayload(false)),
    });
    byId('api-key').value = '';
    await loadLlmProfiles();
    providerStatus.textContent = `已更新模型配置：${updated.name} · ${updated.provider} / ${updated.model}`;
  }

  async function activateLlmProfile() {
    if (!selectedLlmProfileId) throw new Error('请先选择模型配置');
    const active = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selectedLlmProfileId)}/activate`, {
      method: 'POST',
    });
    await loadLlmProfiles();
    providerStatus.textContent = `已切换当前模型：${active.name} · ${active.provider} / ${active.model}`;
  }

  async function testSelectedLlmProfile() {
    if (!selectedLlmProfileId) throw new Error('请先选择模型配置');
    const result = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selectedLlmProfileId)}/test`, {
      method: 'POST',
    });
    const label = result && result.status === 'ok' ? 'PASS' : 'FAIL';
    providerStatus.textContent = `${label} [${result.code || 'unknown'}] ${result.provider || ''} / ${result.model || ''}: ${result.message || ''}`;
  }

  async function deleteSelectedLlmProfile() {
    if (!selectedLlmProfileId) throw new Error('请先选择模型配置');
    const profile = llmProfiles.find((item) => item.id === selectedLlmProfileId);
    if (!window.confirm(`确定删除模型配置“${profile?.name || selectedLlmProfileId}”吗？`)) return;
    await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selectedLlmProfileId)}`, {
      method: 'DELETE',
    });
    selectedLlmProfileId = null;
    byId('api-key').value = '';
    await loadLlmProfiles();
    providerStatus.textContent = '模型配置已删除；若删除的是当前配置，系统已自动选择剩余配置。';
  }

  function installMultiProviderSettings() {
    const providerSelect = byId('provider-name');
    const baseUrlInput = byId('base-url');
    const modelInput = byId('model');
    const providerFieldset = byId('provider');
    if (!providerSelect || !baseUrlInput || !modelInput || !providerFieldset) return;

    const previousProvider = providerSelect.value;
    providerSelect.replaceChildren();
    Object.entries(multiProviderPresets).forEach(([value, preset]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = preset.label;
      providerSelect.appendChild(option);
    });
    providerSelect.value = Object.prototype.hasOwnProperty.call(
      multiProviderPresets,
      previousProvider,
    ) ? previousProvider : 'qwen';

    const legend = providerFieldset.querySelector(':scope > legend');
    if (legend) legend.textContent = 'LLM 多模型设置';

    if (!byId('provider-profile-controls')) {
      const controls = document.createElement('div');
      controls.id = 'provider-profile-controls';

      const selectWrap = document.createElement('div');
      const selectLabel = document.createElement('label');
      selectLabel.htmlFor = 'provider-profile-select';
      selectLabel.textContent = '已保存模型配置';
      const profileSelect = document.createElement('select');
      profileSelect.id = 'provider-profile-select';
      profileSelect.className = 'requires-auth';
      profileSelect.disabled = !currentAccessToken;
      selectWrap.append(selectLabel, profileSelect);

      const nameWrap = document.createElement('div');
      const nameLabel = document.createElement('label');
      nameLabel.htmlFor = 'provider-profile-name';
      nameLabel.textContent = '配置名称';
      const nameInput = document.createElement('input');
      nameInput.id = 'provider-profile-name';
      nameInput.className = 'requires-auth';
      nameInput.placeholder = '例如：DeepSeek 主模型';
      nameInput.disabled = !currentAccessToken;
      nameWrap.append(nameLabel, nameInput);

      const actions = document.createElement('div');
      actions.id = 'provider-profile-actions';
      const specs = [
        ['provider-profile-refresh', '刷新配置列表', loadLlmProfiles],
        ['provider-profile-create', '新建配置', createLlmProfile],
        ['provider-profile-update', '保存修改', updateLlmProfile],
        ['provider-profile-activate', '设为当前模型', activateLlmProfile],
        ['provider-profile-test', '测试所选配置', testSelectedLlmProfile],
        ['provider-profile-delete', '删除所选配置', deleteSelectedLlmProfile],
      ];
      specs.forEach(([id, text, fn]) => {
        const button = document.createElement('button');
        button.id = id;
        button.type = 'button';
        button.className = 'requires-auth';
        button.disabled = !currentAccessToken;
        button.textContent = text;
        button.addEventListener('click', async () => {
          try { await fn(); }
          catch (error) { providerStatus.textContent = error instanceof Error ? error.message : String(error); }
        });
        actions.appendChild(button);
      });
      controls.append(selectWrap, nameWrap, actions);

      const providerLabel = providerFieldset.querySelector('label[for="provider-name"]');
      if (providerLabel) providerLabel.insertAdjacentElement('beforebegin', controls);
      else providerFieldset.appendChild(controls);

      profileSelect.addEventListener('change', () => {
        selectedLlmProfileId = profileSelect.value || null;
        const profile = llmProfiles.find((item) => item.id === selectedLlmProfileId);
        if (profile) fillProviderFields(profile);
      });
    }

    if (!providerFieldset.querySelector('.provider-preset-note')) {
      const note = document.createElement('p');
      note.className = 'provider-preset-note';
      note.textContent = '可以同时保存多套模型接口并切换当前模型。Base URL 与 Model 均可修改；API Key 仍只在服务端加密保存，不回传明文。';
      providerSelect.insertAdjacentElement('afterend', note);
    }

    const presetBaseUrls = new Set(
      Object.values(multiProviderPresets).map((preset) => preset.baseUrl).filter(Boolean),
    );
    const presetModels = new Set(
      Object.values(multiProviderPresets).map((preset) => preset.model).filter(Boolean),
    );

    function applySelectedProviderPreset() {
      const preset = multiProviderPresets[providerSelect.value];
      if (!preset) return;
      const currentBaseUrl = baseUrlInput.value.trim();
      const currentModel = modelInput.value.trim();
      if (!currentBaseUrl || presetBaseUrls.has(currentBaseUrl)) baseUrlInput.value = preset.baseUrl;
      if (!currentModel || presetModels.has(currentModel)) modelInput.value = preset.model;
      baseUrlInput.placeholder = preset.baseUrl || 'https://your-provider.example/v1';
      modelInput.placeholder = preset.model || 'model-name';
    }

    providerSelect.addEventListener('change', applySelectedProviderPreset);
    byId('load-provider')?.addEventListener('click', async () => {
      try { await loadLlmProfiles(); }
      catch (error) { providerStatus.textContent = error instanceof Error ? error.message : String(error); }
    });
    if (!baseUrlInput.value.trim() && !modelInput.value.trim()) applySelectedProviderPreset();
    renderLlmProfiles([]);
  }

  installMultiProviderSettings();
'''
