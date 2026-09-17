PROVIDER_SETTINGS_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LLM Provider Settings</title>
  <style>
    :root { color-scheme: light dark; font-family: Arial, sans-serif; }
    body { max-width: 920px; margin: 32px auto; padding: 0 20px; }
    fieldset { margin: 20px 0; padding: 18px; border-radius: 8px; }
    label { display: block; margin: 12px 0 4px; font-weight: 600; }
    input, select, button, textarea { font: inherit; }
    input, select { width: 100%; box-sizing: border-box; padding: 9px; }
    button { margin: 12px 8px 0 0; padding: 9px 14px; cursor: pointer; }
    #status, #analysis-result { white-space: pre-wrap; overflow-wrap: anywhere; padding: 12px; border-radius: 6px; background: rgba(127,127,127,.12); }
    .note { opacity: .78; font-size: .92rem; }
  </style>
</head>
<body>
  <h1>LLM Provider Settings</h1>
  <p class="note">当前仍使用 X-User-ID 作为临时用户边界。API Key 不会从服务端读取回页面；修改配置时必须重新输入。</p>

  <fieldset>
    <legend>Provider</legend>
    <label for="user-id">User ID</label>
    <input id="user-id" value="local-user" autocomplete="off">

    <label for="provider">Provider</label>
    <select id="provider">
      <option value="openai_compatible">OpenAI-compatible</option>
    </select>

    <label for="base-url">Base URL</label>
    <input id="base-url" placeholder="https://example.com/v1" autocomplete="off">

    <label for="model">Model</label>
    <input id="model" placeholder="model-name" autocomplete="off">

    <label for="api-key">API Key</label>
    <input id="api-key" type="password" autocomplete="new-password" placeholder="Required when saving">

    <label for="timeout">Timeout seconds</label>
    <input id="timeout" type="number" min="0.1" max="300" step="0.1" value="60">

    <div>
      <button id="load" type="button">Load</button>
      <button id="save" type="button">Save</button>
      <button id="test" type="button">Test connection</button>
      <button id="delete" type="button">Delete config</button>
    </div>
  </fieldset>

  <h2>Status</h2>
  <pre id="status">Not loaded.</pre>

  <fieldset>
    <legend>Structured Analysis</legend>
    <p class="note">Connection test only verifies endpoint / credential / model reachability. Formal analysis still runs through the existing StructuredAnalysis validation pipeline.</p>
    <label for="conversation-id">Conversation ID</label>
    <input id="conversation-id" autocomplete="off">
    <button id="run-analysis" type="button">Run structured analysis</button>
  </fieldset>

  <h2>Analysis result</h2>
  <pre id="analysis-result">No analysis run.</pre>

<script>
(() => {
  const byId = (id) => document.getElementById(id);
  const status = byId('status');
  const analysisResult = byId('analysis-result');

  function userId() {
    const value = byId('user-id').value.trim();
    if (!value) throw new Error('User ID is required');
    return value;
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('X-User-ID', userId());
    if (options.body) headers.set('Content-Type', 'application/json');
    const response = await fetch(path, { ...options, headers });
    if (response.status === 204) return null;
    const text = await response.text();
    let data = null;
    if (text) {
      try { data = JSON.parse(text); } catch (_) { data = text; }
    }
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : data;
      throw new Error(typeof detail === 'string' ? detail : `HTTP ${response.status}`);
    }
    return data;
  }

  function renderStatus(message) {
    status.textContent = message;
  }

  async function loadConfig() {
    const config = await api('/api/v1/settings/llm');
    byId('api-key').value = '';
    if (!config) {
      byId('base-url').value = '';
      byId('model').value = '';
      byId('timeout').value = '60';
      renderStatus('No provider config saved for this user.');
      return;
    }
    byId('provider').value = config.provider;
    byId('base-url').value = config.base_url;
    byId('model').value = config.model;
    byId('timeout').value = String(config.timeout_seconds);
    renderStatus(`Loaded ${config.provider} / ${config.model}. API key configured: ${Boolean(config.api_key_configured)}.`);
  }

  async function saveConfig() {
    const key = byId('api-key').value;
    if (!key) throw new Error('API Key is required when saving provider config');
    const payload = {
      provider: byId('provider').value,
      base_url: byId('base-url').value.trim(),
      model: byId('model').value.trim(),
      api_key: key,
      timeout_seconds: Number(byId('timeout').value),
    };
    const saved = await api('/api/v1/settings/llm', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    byId('api-key').value = '';
    renderStatus(`Saved ${saved.provider} / ${saved.model}. API key is stored server-side and is not returned.`);
  }

  async function testConnection() {
    const result = await api('/api/v1/settings/llm/test', { method: 'POST' });
    renderStatus(result && result.status === 'ok' ? 'Connection test succeeded.' : 'Connection test returned an unexpected response.');
  }

  async function deleteConfig() {
    await api('/api/v1/settings/llm', { method: 'DELETE' });
    byId('api-key').value = '';
    byId('base-url').value = '';
    byId('model').value = '';
    byId('timeout').value = '60';
    renderStatus('Provider config deleted. Runtime will use the existing default provider behavior.');
  }

  async function runAnalysis() {
    const conversationId = byId('conversation-id').value.trim();
    if (!conversationId) throw new Error('Conversation ID is required');
    analysisResult.textContent = 'Running...';
    const result = await api(`/api/v1/conversations/${encodeURIComponent(conversationId)}/analysis/structured`);
    analysisResult.textContent = JSON.stringify(result, null, 2);
  }

  const bind = (id, fn, target = status) => {
    byId(id).addEventListener('click', async () => {
      try { await fn(); }
      catch (error) { target.textContent = error instanceof Error ? error.message : String(error); }
    });
  };

  bind('load', loadConfig);
  bind('save', saveConfig);
  bind('test', testConnection);
  bind('delete', deleteConfig);
  bind('run-analysis', runAnalysis, analysisResult);
})();
</script>
</body>
</html>
'''
