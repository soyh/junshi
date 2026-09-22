MULTI_PROVIDER_SETTINGS_STYLE = r'''
#provider .provider-preset-note {
  margin: 6px 0 14px;
  font-size: .86rem;
  opacity: .76;
}
#provider .provider-preset-note strong { opacity: 1; }
#client-llm-profile-box {
  margin: 0 0 16px;
  padding: 12px;
  border: 1px solid rgba(25, 167, 232, .18);
  border-radius: 12px;
  background: rgba(226, 246, 255, .30);
}
#client-llm-profile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
#client-llm-profile-actions button { margin: 8px 0 0 !important; }
'''


MULTI_PROVIDER_SETTINGS_SCRIPT = r'''
  // TEST-178: multiple saved LLM interfaces with one explicit active profile.
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

  let clientLLMProfiles = [];

  function clientSelectedLLMProfile() {
    const id = byId('client-llm-profile-select')?.value || '';
    return clientLLMProfiles.find((item) => item.id === id) || null;
  }

  function clientApplyLLMProfile(profile) {
    if (!profile) return;
    byId('client-llm-profile-name').value = profile.name || '';
    byId('provider-name').value = profile.provider;
    byId('base-url').value = profile.base_url;
    byId('model').value = profile.model;
    byId('timeout').value = String(profile.timeout_seconds);
    byId('api-key').value = '';
    providerStatus.textContent = `${profile.is_active ? '当前使用' : '已选择'}：${profile.name} · ${profile.provider} / ${profile.model}。API Key 已配置：${Boolean(profile.api_key_configured)}。`;
  }

  function clientRenderLLMProfiles(items) {
    clientLLMProfiles = Array.isArray(items) ? items : [];
    const select = byId('client-llm-profile-select');
    if (!select) return;
    const previous = select.value;
    select.replaceChildren();
    const empty = document.createElement('option');
    empty.value = '';
    empty.textContent = clientLLMProfiles.length ? '选择一个模型接口' : '还没有保存的模型接口';
    select.appendChild(empty);
    clientLLMProfiles.forEach((profile) => {
      const option = document.createElement('option');
      option.value = profile.id;
      option.textContent = `${profile.is_active ? '当前 · ' : ''}${profile.name} · ${profile.provider} / ${profile.model}`;
      select.appendChild(option);
    });
    const active = clientLLMProfiles.find((item) => item.is_active);
    const selected = clientLLMProfiles.find((item) => item.id === previous) || active || null;
    select.value = selected?.id || '';
    if (selected) clientApplyLLMProfile(selected);
  }

  async function clientLoadLLMProfiles() {
    if (!currentAccessToken) {
      clientRenderLLMProfiles([]);
      return [];
    }
    const items = await api('/api/v1/settings/llm/profiles');
    clientRenderLLMProfiles(items);
    return items;
  }

  function clientProfilePayload(includeKey) {
    const payload = {
      name: byId('client-llm-profile-name').value.trim(),
      provider: byId('provider-name').value,
      base_url: byId('base-url').value.trim(),
      model: byId('model').value.trim(),
      timeout_seconds: Number(byId('timeout').value),
    };
    if (!payload.name) throw new Error('请填写配置名称');
    if (!payload.base_url || !payload.model) throw new Error('Base URL 和 Model 必填');
    const key = byId('api-key').value;
    if (includeKey && !key) throw new Error('新建模型配置时必须填写 API Key');
    if (key) payload.api_key = key;
    return payload;
  }

  async function clientCreateLLMProfile() {
    const payload = clientProfilePayload(true);
    payload.activate = clientLLMProfiles.length === 0;
    const created = await api('/api/v1/settings/llm/profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    byId('api-key').value = '';
    await clientLoadLLMProfiles();
    byId('client-llm-profile-select').value = created.id;
    clientApplyLLMProfile(clientLLMProfiles.find((item) => item.id === created.id) || created);
    providerStatus.textContent = `已创建模型接口：${created.name}。${created.is_active ? '已设为当前使用。' : '可点击“设为当前”切换。'}`;
  }

  async function clientUpdateLLMProfile() {
    const selected = clientSelectedLLMProfile();
    if (!selected) throw new Error('请先选择一个已保存的模型接口');
    const payload = clientProfilePayload(false);
    const updated = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selected.id)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    byId('api-key').value = '';
    await clientLoadLLMProfiles();
    byId('client-llm-profile-select').value = updated.id;
    clientApplyLLMProfile(clientLLMProfiles.find((item) => item.id === updated.id) || updated);
    providerStatus.textContent = `已保存：${updated.name} · ${updated.provider} / ${updated.model}。`;
  }

  async function clientActivateLLMProfile() {
    const selected = clientSelectedLLMProfile();
    if (!selected) throw new Error('请先选择一个已保存的模型接口');
    const active = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selected.id)}/activate`, {
      method: 'POST',
    });
    await clientLoadLLMProfiles();
    byId('client-llm-profile-select').value = active.id;
    clientApplyLLMProfile(clientLLMProfiles.find((item) => item.id === active.id) || active);
    providerStatus.textContent = `当前 LLM 已切换为：${active.name} · ${active.provider} / ${active.model}。分析、回复和多模态识别将使用此配置。`;
  }

  async function clientTestLLMProfile() {
    const selected = clientSelectedLLMProfile();
    if (!selected) throw new Error('请先选择一个已保存的模型接口');
    const result = await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selected.id)}/test`, {
      method: 'POST',
    });
    if (result?.code) {
      providerStatus.textContent = `${result.status === 'ok' ? 'PASS' : 'FAIL'} [${result.code}] ${result.provider} / ${result.model}: ${result.message}`;
    } else {
      providerStatus.textContent = '模型接口连接测试完成。';
    }
  }

  async function clientDeleteLLMProfile() {
    const selected = clientSelectedLLMProfile();
    if (!selected) throw new Error('请先选择一个已保存的模型接口');
    if (!window.confirm(`确定删除模型配置“${selected.name}”吗？`)) return;
    await api(`/api/v1/settings/llm/profiles/${encodeURIComponent(selected.id)}`, {method: 'DELETE'});
    byId('api-key').value = '';
    byId('client-llm-profile-name').value = '';
    await clientLoadLLMProfiles();
    providerStatus.textContent = '模型配置已删除；如果删除的是当前配置，系统已自动切换到剩余配置。';
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
    if (legend) legend.textContent = 'LLM 模型设置';

    if (!providerFieldset.querySelector('.provider-preset-note')) {
      const note = document.createElement('p');
      note.className = 'provider-preset-note';
      note.textContent = '可保存多套模型接口并明确切换当前使用项。厂商预设只负责填写推荐地址和模型；Base URL 与 Model 始终可修改，API Key 仍只在服务端加密保存。';
      providerSelect.insertAdjacentElement('afterend', note);
    }

    if (!byId('client-llm-profile-box')) {
      const box = document.createElement('div');
      box.id = 'client-llm-profile-box';
      const title = document.createElement('strong');
      title.textContent = '已保存的模型接口';
      const selectLabel = document.createElement('label');
      selectLabel.htmlFor = 'client-llm-profile-select';
      selectLabel.textContent = '模型配置';
      const select = document.createElement('select');
      select.id = 'client-llm-profile-select';
      select.className = 'requires-auth';
      select.disabled = !currentAccessToken;
      const nameLabel = document.createElement('label');
      nameLabel.htmlFor = 'client-llm-profile-name';
      nameLabel.textContent = '配置名称';
      const name = document.createElement('input');
      name.id = 'client-llm-profile-name';
      name.className = 'requires-auth';
      name.placeholder = '例如：DeepSeek 主模型 / OpenAI 多模态';
      name.disabled = !currentAccessToken;
      const actions = document.createElement('div');
      actions.id = 'client-llm-profile-actions';
      [
        ['client-profile-refresh', '刷新列表'],
        ['client-profile-create', '新建配置'],
        ['client-profile-save', '保存修改'],
        ['client-profile-activate', '设为当前'],
        ['client-profile-test', '测试此配置'],
        ['client-profile-delete', '删除配置'],
      ].forEach(([id, label]) => {
        const button = document.createElement('button');
        button.id = id;
        button.type = 'button';
        button.className = 'requires-auth';
        button.disabled = !currentAccessToken;
        button.textContent = label;
        actions.appendChild(button);
      });
      box.append(title, selectLabel, select, nameLabel, name, actions);
      const firstLabel = providerFieldset.querySelector('label[for="provider-name"]');
      providerFieldset.insertBefore(box, firstLabel || providerFieldset.firstChild);

      select.addEventListener('change', () => clientApplyLLMProfile(clientSelectedLLMProfile()));
      const profileBindings = {
        'client-profile-refresh': clientLoadLLMProfiles,
        'client-profile-create': clientCreateLLMProfile,
        'client-profile-save': clientUpdateLLMProfile,
        'client-profile-activate': clientActivateLLMProfile,
        'client-profile-test': clientTestLLMProfile,
        'client-profile-delete': clientDeleteLLMProfile,
      };
      Object.entries(profileBindings).forEach(([id, fn]) => {
        byId(id).addEventListener('click', async () => {
          try { await fn(); }
          catch (error) { providerStatus.textContent = error instanceof Error ? error.message : String(error); }
        });
      });
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
      if (!currentBaseUrl || presetBaseUrls.has(currentBaseUrl)) {
        baseUrlInput.value = preset.baseUrl;
      }
      if (!currentModel || presetModels.has(currentModel)) {
        modelInput.value = preset.model;
      }
      baseUrlInput.placeholder = preset.baseUrl || 'https://your-provider.example/v1';
      modelInput.placeholder = preset.model || 'model-name';
    }

    providerSelect.addEventListener('change', applySelectedProviderPreset);
    if (!baseUrlInput.value.trim() && !modelInput.value.trim()) {
      applySelectedProviderPreset();
    }

    const baseLoadProvider = loadProvider;
    loadProvider = async function() {
      await baseLoadProvider();
      await clientLoadLLMProfiles();
    };
    byId('load-provider')?.addEventListener('click', async () => {
      try { await clientLoadLLMProfiles(); }
      catch (error) { providerStatus.textContent = error instanceof Error ? error.message : String(error); }
    });
  }

  installMultiProviderSettings();
'''
