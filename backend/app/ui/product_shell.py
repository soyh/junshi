PRODUCT_SHELL_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Love Strategist</title>
  <style>
    :root { color-scheme: light dark; font-family: Arial, sans-serif; }
    body { max-width: 1080px; margin: 28px auto; padding: 0 20px 48px; }
    header { margin-bottom: 24px; }
    nav { display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0 24px; }
    nav a { padding: 8px 12px; border: 1px solid rgba(127,127,127,.35); border-radius: 8px; text-decoration: none; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
    fieldset { margin: 0; padding: 18px; border-radius: 10px; min-width: 0; }
    label { display: block; margin: 12px 0 4px; font-weight: 600; }
    input, select, button { font: inherit; }
    input, select { width: 100%; box-sizing: border-box; padding: 9px; }
    button { margin: 12px 8px 0 0; padding: 9px 14px; cursor: pointer; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    .note { opacity: .78; font-size: .92rem; }
    .status { white-space: pre-wrap; overflow-wrap: anywhere; padding: 12px; border-radius: 6px; background: rgba(127,127,127,.12); min-height: 2.5em; }
    .session-row { padding: 8px 0; border-bottom: 1px solid rgba(127,127,127,.25); }
    .session-row:last-child { border-bottom: 0; }
    .wide { grid-column: 1 / -1; }
    code { overflow-wrap: anywhere; }
  </style>
</head>
<body>
<header>
  <h1>AI Love Strategist</h1>
  <p class="note">登录态仅保存在当前页面运行内存中。页面刷新或关闭后需要重新登录；session token 不会被写入页面字段、URL 或浏览器持久化存储。</p>
  <nav aria-label="Product sections">
    <a href="#account">Account</a>
    <a href="#provider">LLM Provider</a>
    <a href="#analysis">Structured Analysis</a>
    <a href="#workspace">Workspace</a>
  </nav>
</header>

<div class="grid">
  <fieldset id="account">
    <legend>Account</legend>
    <label for="username">Username</label>
    <input id="username" autocomplete="username">
    <label for="password">Password</label>
    <input id="password" type="password" autocomplete="current-password">
    <button id="register" type="button">Register</button>
    <button id="login" type="button">Login</button>
    <button id="logout" type="button" disabled>Logout</button>
    <p class="note">注册和登录直接使用已验证的账号/session API，不在前端实现第二套认证规则。</p>
    <div id="auth-status" class="status">Not authenticated.</div>
  </fieldset>

  <fieldset>
    <legend>Session management</legend>
    <button id="load-sessions" class="requires-auth" type="button" disabled>Refresh sessions</button>
    <button id="rotate-session" class="requires-auth" type="button" disabled>Rotate current session</button>
    <button id="revoke-others" class="requires-auth" type="button" disabled>Revoke other sessions</button>
    <div id="sessions" class="status">Login to manage sessions.</div>
  </fieldset>

  <fieldset id="provider" class="wide">
    <legend>LLM Provider</legend>
    <p class="note">Provider API Key 只提交给服务端加密保存，不会从服务端读取回页面。</p>
    <label for="provider-name">Provider</label>
    <select id="provider-name">
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
      <button id="load-provider" class="requires-auth" type="button" disabled>Load</button>
      <button id="save-provider" class="requires-auth" type="button" disabled>Save</button>
      <button id="test-provider" class="requires-auth" type="button" disabled>Test connection</button>
      <button id="delete-provider" class="requires-auth" type="button" disabled>Delete config</button>
    </div>
    <div id="provider-status" class="status">Login before managing provider settings.</div>
  </fieldset>

  <fieldset id="analysis" class="wide">
    <legend>Structured Analysis</legend>
    <p class="note">正式分析继续经过现有 StructuredAnalysis 验证链；此页面只提供统一入口。</p>
    <label for="conversation-id">Conversation ID</label>
    <input id="conversation-id" autocomplete="off">
    <button id="run-analysis" class="requires-auth" type="button" disabled>Run structured analysis</button>
    <div id="analysis-result" class="status">Login before running analysis.</div>
  </fieldset>

  <fieldset id="workspace" class="wide">
    <legend>Workspace</legend>
    <p>核心后端模块已包括 Person、Relationship、Conversation、Recommendation、Action Plan、Execution、Outcome、Feedback、Learning 与 Re-analysis。</p>
    <p class="note">本阶段只统一身份与 Provider/Analysis 入口，不伪造尚未完成的业务页面。后续 UI 将在同一 authenticated shell 中逐步接入。</p>
  </fieldset>
</div>

<script>
(() => {
  const byId = (id) => document.getElementById(id);
  const authStatus = byId('auth-status');
  const sessionsNode = byId('sessions');
  const providerStatus = byId('provider-status');
  const analysisResult = byId('analysis-result');
  let currentAccessToken = null;

  function requireToken() {
    if (!currentAccessToken) throw new Error('Login is required');
    return currentAccessToken;
  }

  function setAuthenticatedControls(enabled) {
    document.querySelectorAll('.requires-auth').forEach((node) => { node.disabled = !enabled; });
    byId('logout').disabled = !enabled;
  }

  async function api(path, options = {}, authenticated = true) {
    const headers = new Headers(options.headers || {});
    if (authenticated) headers.set('Authorization', `Bearer ${requireToken()}`);
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
      const error = new Error(typeof detail === 'string' ? detail : `HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function establishSession(data, message) {
    if (!data || !data.access_token) throw new Error('Server did not return a session token');
    currentAccessToken = data.access_token;
    byId('password').value = '';
    authStatus.textContent = `${message} Session expires at ${data.expires_at}.`;
    setAuthenticatedControls(true);
  }

  function clearSession(message = 'Not authenticated.') {
    currentAccessToken = null;
    authStatus.textContent = message;
    sessionsNode.textContent = 'Login to manage sessions.';
    providerStatus.textContent = 'Login before managing provider settings.';
    analysisResult.textContent = 'Login before running analysis.';
    byId('api-key').value = '';
    setAuthenticatedControls(false);
  }

  async function register() {
    const username = byId('username').value.trim();
    const password = byId('password').value;
    if (!username || !password) throw new Error('Username and password are required');
    const data = await api('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }, false);
    establishSession(data, 'Registered and authenticated.');
    await loadProvider();
  }

  async function login() {
    const username = byId('username').value.trim();
    const password = byId('password').value;
    if (!username || !password) throw new Error('Username and password are required');
    const data = await api('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }, false);
    establishSession(data, 'Authenticated.');
    await loadProvider();
  }

  async function logout() {
    await api('/api/v1/auth/session', { method: 'DELETE' });
    clearSession('Logged out.');
  }

  function renderSessions(items) {
    sessionsNode.textContent = '';
    if (!Array.isArray(items) || items.length === 0) {
      sessionsNode.textContent = 'No active sessions.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const marker = item.current ? 'current' : 'other';
      row.textContent = `${marker} session · created ${item.created_at} · expires ${item.expires_at}`;
      sessionsNode.appendChild(row);
    });
  }

  async function loadSessions() {
    renderSessions(await api('/api/v1/auth/sessions'));
  }

  async function rotateSession() {
    const data = await api('/api/v1/auth/session/rotate', { method: 'POST' });
    establishSession(data, 'Session rotated.');
    await loadSessions();
  }

  async function revokeOthers() {
    await api('/api/v1/auth/sessions/others', { method: 'DELETE' });
    await loadSessions();
  }

  async function loadProvider() {
    const config = await api('/api/v1/settings/llm');
    byId('api-key').value = '';
    if (!config) {
      byId('base-url').value = '';
      byId('model').value = '';
      byId('timeout').value = '60';
      providerStatus.textContent = 'No provider config saved for this authenticated user.';
      return;
    }
    byId('provider-name').value = config.provider;
    byId('base-url').value = config.base_url;
    byId('model').value = config.model;
    byId('timeout').value = String(config.timeout_seconds);
    providerStatus.textContent = `Loaded ${config.provider} / ${config.model}. API key configured: ${Boolean(config.api_key_configured)}.`;
  }

  async function saveProvider() {
    const key = byId('api-key').value;
    if (!key) throw new Error('API Key is required when saving provider config');
    const payload = {
      provider: byId('provider-name').value,
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
    providerStatus.textContent = `Saved ${saved.provider} / ${saved.model}. API key is stored server-side and is not returned.`;
  }

  async function testProvider() {
    const result = await api('/api/v1/settings/llm/test', { method: 'POST' });
    providerStatus.textContent = result && result.status === 'ok' ? 'Connection test succeeded.' : 'Connection test returned an unexpected response.';
  }

  async function deleteProvider() {
    await api('/api/v1/settings/llm', { method: 'DELETE' });
    byId('api-key').value = '';
    byId('base-url').value = '';
    byId('model').value = '';
    byId('timeout').value = '60';
    providerStatus.textContent = 'Provider config deleted.';
  }

  async function runAnalysis() {
    const conversationId = byId('conversation-id').value.trim();
    if (!conversationId) throw new Error('Conversation ID is required');
    analysisResult.textContent = 'Running...';
    const result = await api(`/api/v1/conversations/${encodeURIComponent(conversationId)}/analysis/structured`);
    analysisResult.textContent = JSON.stringify(result, null, 2);
  }

  const bind = (id, fn, target = authStatus) => {
    byId(id).addEventListener('click', async () => {
      try { await fn(); }
      catch (error) { target.textContent = error instanceof Error ? error.message : String(error); }
    });
  };

  bind('register', register);
  bind('login', login);
  bind('logout', logout);
  bind('load-sessions', loadSessions, sessionsNode);
  bind('rotate-session', rotateSession, sessionsNode);
  bind('revoke-others', revokeOthers, sessionsNode);
  bind('load-provider', loadProvider, providerStatus);
  bind('save-provider', saveProvider, providerStatus);
  bind('test-provider', testProvider, providerStatus);
  bind('delete-provider', deleteProvider, providerStatus);
  bind('run-analysis', runAnalysis, analysisResult);
  clearSession();
})();
</script>
</body>
</html>
'''
