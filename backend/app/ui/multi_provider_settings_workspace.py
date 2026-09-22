MULTI_PROVIDER_SETTINGS_STYLE = r'''
#provider .provider-preset-note {
  margin: 6px 0 14px;
  font-size: .86rem;
  opacity: .76;
}
#provider .provider-preset-note strong {
  opacity: 1;
}
'''


MULTI_PROVIDER_SETTINGS_SCRIPT = r'''
  // TEST-175: user-selectable BYOK providers with editable presets.
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
      note.innerHTML = '<strong>厂商预设只负责填写推荐地址和模型。</strong> Base URL 与 Model 始终可由用户修改；API Key 仍只在服务端加密保存。';
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
  }

  installMultiProviderSettings();
'''
