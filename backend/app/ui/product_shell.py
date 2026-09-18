PRODUCT_SHELL_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Love Strategist</title>
  <style>
    :root { color-scheme: light dark; font-family: Arial, sans-serif; }
    body { max-width: 1180px; margin: 28px auto; padding: 0 20px 48px; }
    header { margin-bottom: 24px; }
    nav { display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0 24px; }
    nav a { padding: 8px 12px; border: 1px solid rgba(127,127,127,.35); border-radius: 8px; text-decoration: none; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
    .workspace-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
    .workspace-card { padding: 14px; border: 1px solid rgba(127,127,127,.3); border-radius: 8px; }
    fieldset { margin: 0; padding: 18px; border-radius: 10px; min-width: 0; }
    label { display: block; margin: 12px 0 4px; font-weight: 600; }
    input, select, textarea, button { font: inherit; }
    input, select, textarea { width: 100%; box-sizing: border-box; padding: 9px; }
    textarea { min-height: 72px; resize: vertical; }
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
    <a href="#workspace">Workspace</a>
    <a href="#provider">LLM Provider</a>
    <a href="#analysis">Structured Analysis</a>
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

  <fieldset id="workspace" class="wide">
    <legend>Workspace</legend>
    <p>核心后端模块已包括 Person、Relationship、Conversation、Recommendation、Action Plan、Execution、Outcome、Feedback、Learning 与 Re-analysis。</p>
    <p class="note">TEST-136 只把 Person、Relationship、Conversation 的既有 API 接入统一 authenticated shell。Recommendation 及后续生命周期仍不伪造尚未完成的业务页面。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="person-heading">
        <h2 id="person-heading">Person</h2>
        <label for="person-name">Name</label>
        <input id="person-name" autocomplete="off" maxlength="200">
        <label for="person-nickname">Nickname</label>
        <input id="person-nickname" autocomplete="off" maxlength="200">
        <label for="person-notes">Notes</label>
        <textarea id="person-notes"></textarea>
        <button id="load-persons" class="requires-auth" type="button" disabled>Refresh persons</button>
        <button id="create-person" class="requires-auth" type="button" disabled>Create person</button>
        <label for="person-select">Current person</label>
        <select id="person-select" class="requires-auth" size="6" disabled></select>
        <div id="person-status" class="status">Login to load persons.</div>
      </section>

      <section class="workspace-card" aria-labelledby="relationship-heading">
        <h2 id="relationship-heading">Relationship</h2>
        <p class="note">Relationship 始终绑定当前选中的 Person；服务端继续负责 scope 与 canonical consistency 校验。</p>
        <label for="relationship-state">Status</label>
        <input id="relationship-state" value="unknown" autocomplete="off">
        <label for="relationship-stage">Stage</label>
        <input id="relationship-stage" value="unknown" autocomplete="off">
        <label for="relationship-long-term-goal">Long-term goal</label>
        <textarea id="relationship-long-term-goal"></textarea>
        <label for="relationship-current-goal">Current goal</label>
        <textarea id="relationship-current-goal"></textarea>
        <label for="relationship-notes">Notes</label>
        <textarea id="relationship-notes"></textarea>
        <button id="load-relationships" class="requires-auth" type="button" disabled>Refresh relationships</button>
        <button id="create-relationship" class="requires-auth" type="button" disabled>Create relationship</button>
        <label for="relationship-select">Current relationship</label>
        <select id="relationship-select" class="requires-auth" size="6" disabled></select>
        <div id="relationship-status" class="status">Select a person first.</div>
      </section>

      <section class="workspace-card" aria-labelledby="conversation-heading">
        <h2 id="conversation-heading">Conversation</h2>
        <p class="note">Conversation 必须绑定当前 Person；当前 Relationship 可选。选择 Conversation 后会同步到 Structured Analysis。</p>
        <label for="conversation-title">Title</label>
        <input id="conversation-title" autocomplete="off">
        <label for="conversation-state">Status</label>
        <select id="conversation-state" class="requires-auth" disabled>
          <option value="active">active</option>
          <option value="archived">archived</option>
        </select>
        <button id="load-conversations" class="requires-auth" type="button" disabled>Refresh conversations</button>
        <button id="create-conversation" class="requires-auth" type="button" disabled>Create conversation</button>
        <label for="conversation-select">Current conversation</label>
        <select id="conversation-select" class="requires-auth" size="6" disabled></select>
        <div id="conversation-status" class="status">Select a person first.</div>
      </section>
    </div>
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
</div>

<script>
(() => {
  const byId = (id) => document.getElementById(id);
  const authStatus = byId('auth-status');
  const sessionsNode = byId('sessions');
  const providerStatus = byId('provider-status');
  const analysisResult = byId('analysis-result');
  const personStatus = byId('person-status');
  const relationshipStatus = byId('relationship-status');
  const conversationStatus = byId('conversation-status');
  let currentAccessToken = null;
  let selectedPersonId = null;
  let selectedRelationshipId = null;
  let selectedConversationId = null;

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

  function resetSelect(id, placeholder) {
    const select = byId(id);
    select.replaceChildren();
    const option = document.createElement('option');
    option.value = '';
    option.textContent = placeholder;
    select.appendChild(option);
    select.value = '';
  }

  function renderSelect(id, items, labelFor, placeholder, selectedValue = null) {
    const select = byId(id);
    select.replaceChildren();
    const empty = document.createElement('option');
    empty.value = '';
    empty.textContent = placeholder;
    select.appendChild(empty);
    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = labelFor(item);
      select.appendChild(option);
    });
    select.value = selectedValue && items.some((item) => item.id === selectedValue) ? selectedValue : '';
  }

  function nullableText(id) {
    const value = byId(id).value.trim();
    return value || null;
  }

  function resetWorkspace(message = 'Login to load persons.') {
    selectedPersonId = null;
    selectedRelationshipId = null;
    selectedConversationId = null;
    resetSelect('person-select', 'No person selected');
    resetSelect('relationship-select', 'Select a person first');
    resetSelect('conversation-select', 'Select a person first');
    byId('conversation-id').value = '';
    personStatus.textContent = message;
    relationshipStatus.textContent = 'Select a person first.';
    conversationStatus.textContent = 'Select a person first.';
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
    resetWorkspace();
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
    await loadWorkspace();
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
    await loadWorkspace();
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

  async function loadPersons() {
    const items = await api('/api/v1/persons');
    if (!items.some((item) => item.id === selectedPersonId)) {
      selectedPersonId = null;
      selectedRelationshipId = null;
      selectedConversationId = null;
      byId('conversation-id').value = '';
    }
    renderSelect(
      'person-select',
      items,
      (item) => item.nickname ? `${item.name} (${item.nickname})` : item.name,
      'No person selected',
      selectedPersonId,
    );
    personStatus.textContent = `${items.length} person(s) available.`;
    if (selectedPersonId) {
      await loadRelationships();
      await loadConversations();
    } else {
      resetSelect('relationship-select', 'Select a person first');
      resetSelect('conversation-select', 'Select a person first');
      relationshipStatus.textContent = 'Select a person first.';
      conversationStatus.textContent = 'Select a person first.';
    }
  }

  async function createPerson() {
    const name = byId('person-name').value.trim();
    if (!name) throw new Error('Person name is required');
    const created = await api('/api/v1/persons', {
      method: 'POST',
      body: JSON.stringify({
        name,
        nickname: nullableText('person-nickname'),
        notes: nullableText('person-notes'),
      }),
    });
    selectedPersonId = created.id;
    selectedRelationshipId = null;
    selectedConversationId = null;
    byId('person-name').value = '';
    byId('person-nickname').value = '';
    byId('person-notes').value = '';
    await loadPersons();
    personStatus.textContent = `Created and selected ${created.name}.`;
  }

  async function loadRelationships() {
    if (!selectedPersonId) {
      resetSelect('relationship-select', 'Select a person first');
      relationshipStatus.textContent = 'Select a person first.';
      return;
    }
    const allItems = await api('/api/v1/relationships');
    const items = allItems.filter((item) => item.person_id === selectedPersonId);
    if (!items.some((item) => item.id === selectedRelationshipId)) selectedRelationshipId = null;
    renderSelect(
      'relationship-select',
      items,
      (item) => `${item.status} · ${item.stage}`,
      'No relationship selected',
      selectedRelationshipId,
    );
    relationshipStatus.textContent = `${items.length} relationship(s) for current person.`;
  }

  async function createRelationship() {
    if (!selectedPersonId) throw new Error('Select a person before creating a relationship');
    const created = await api('/api/v1/relationships', {
      method: 'POST',
      body: JSON.stringify({
        person_id: selectedPersonId,
        status: byId('relationship-state').value.trim() || 'unknown',
        stage: byId('relationship-stage').value.trim() || 'unknown',
        long_term_goal: nullableText('relationship-long-term-goal'),
        current_goal: nullableText('relationship-current-goal'),
        notes: nullableText('relationship-notes'),
      }),
    });
    selectedRelationshipId = created.id;
    await loadRelationships();
    relationshipStatus.textContent = `Created and selected relationship ${created.status} · ${created.stage}.`;
  }

  async function loadConversations() {
    if (!selectedPersonId) {
      resetSelect('conversation-select', 'Select a person first');
      conversationStatus.textContent = 'Select a person first.';
      return;
    }
    const items = await api(`/api/v1/conversations?person_id=${encodeURIComponent(selectedPersonId)}`);
    if (!items.some((item) => item.id === selectedConversationId)) {
      selectedConversationId = null;
      byId('conversation-id').value = '';
    }
    renderSelect(
      'conversation-select',
      items,
      (item) => `${item.title || '(untitled)'} · ${item.status}`,
      'No conversation selected',
      selectedConversationId,
    );
    conversationStatus.textContent = `${items.length} conversation(s) for current person.`;
  }

  async function createConversation() {
    if (!selectedPersonId) throw new Error('Select a person before creating a conversation');
    const created = await api('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({
        person_id: selectedPersonId,
        relationship_id: selectedRelationshipId || null,
        title: nullableText('conversation-title'),
        status: byId('conversation-state').value,
      }),
    });
    selectedConversationId = created.id;
    byId('conversation-title').value = '';
    byId('conversation-id').value = created.id;
    await loadConversations();
    conversationStatus.textContent = `Created and selected ${created.title || '(untitled)'}.`;
  }

  async function loadWorkspace() {
    await loadPersons();
  }

  async function selectPerson() {
    selectedPersonId = byId('person-select').value || null;
    selectedRelationshipId = null;
    selectedConversationId = null;
    byId('conversation-id').value = '';
    await loadRelationships();
    await loadConversations();
  }

  function selectRelationship() {
    selectedRelationshipId = byId('relationship-select').value || null;
  }

  function selectConversation() {
    selectedConversationId = byId('conversation-select').value || null;
    byId('conversation-id').value = selectedConversationId || '';
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
  bind('load-persons', loadPersons, personStatus);
  bind('create-person', createPerson, personStatus);
  bind('load-relationships', loadRelationships, relationshipStatus);
  bind('create-relationship', createRelationship, relationshipStatus);
  bind('load-conversations', loadConversations, conversationStatus);
  bind('create-conversation', createConversation, conversationStatus);
  bind('run-analysis', runAnalysis, analysisResult);

  byId('person-select').addEventListener('change', async () => {
    try { await selectPerson(); }
    catch (error) { personStatus.textContent = error instanceof Error ? error.message : String(error); }
  });
  byId('relationship-select').addEventListener('change', selectRelationship);
  byId('conversation-select').addEventListener('change', selectConversation);

  clearSession();
})();
</script>
</body>
</html>
'''
