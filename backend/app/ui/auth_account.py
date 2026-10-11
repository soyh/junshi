AUTH_ACCOUNT_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Account & Session</title>
  <style>
    :root { color-scheme: light dark; font-family: Arial, sans-serif; }
    body { max-width: 920px; margin: 32px auto; padding: 0 20px; }
    fieldset { margin: 20px 0; padding: 18px; border-radius: 8px; }
    label { display: block; margin: 12px 0 4px; font-weight: 600; }
    input, button { font: inherit; }
    input { width: 100%; box-sizing: border-box; padding: 9px; }
    button { margin: 12px 8px 0 0; padding: 9px 14px; cursor: pointer; }
    #status, #sessions { white-space: pre-wrap; overflow-wrap: anywhere; padding: 12px; border-radius: 6px; background: rgba(127,127,127,.12); }
    .note { opacity: .78; font-size: .92rem; }
    .session-row { padding: 10px 0; border-bottom: 1px solid rgba(127,127,127,.25); }
    .session-row:last-child { border-bottom: 0; }
  </style>
</head>
<body>
  <h1>Account & Session</h1>
  <p class="note">Session access token 仅保存在当前页面 JavaScript 内存中，不写入浏览器持久化存储或页面 DOM。关闭或刷新页面后需要重新登录。</p>

  <fieldset>
    <legend>Register</legend>
    <label for="register-username">Username</label>
    <input id="register-username" autocomplete="username">
    <label for="register-password">Password</label>
    <input id="register-password" type="password" autocomplete="new-password">
    <button id="register" type="button">Register</button>
  </fieldset>

  <fieldset>
    <legend>Login</legend>
    <label for="login-username">Username</label>
    <input id="login-username" autocomplete="username">
    <label for="login-password">Password</label>
    <input id="login-password" type="password" autocomplete="current-password">
    <button id="login" type="button">Login</button>
    <button id="logout" type="button">Logout current session</button>
  </fieldset>

  <h2>Status</h2>
  <pre id="status">Not authenticated.</pre>

  <fieldset>
    <legend>Sessions</legend>
    <button id="load-sessions" type="button">Refresh sessions</button>
    <button id="revoke-others" type="button">Revoke other sessions</button>
    <button id="rotate" type="button">Rotate current session</button>
    <div id="sessions">No sessions loaded.</div>
  </fieldset>

  <fieldset>
    <legend>Change password</legend>
    <label for="current-password">Current password</label>
    <input id="current-password" type="password" autocomplete="current-password">
    <label for="new-password">New password</label>
    <input id="new-password" type="password" autocomplete="new-password">
    <button id="change-password" type="button">Change password</button>
  </fieldset>

  <fieldset>
    <legend>Account recovery</legend>
    <p class="note">Account recovery is currently unavailable because no verified email, SMS, or external identity recovery channel is configured. This UI does not provide an unverified password-reset path.</p>
  </fieldset>

<script>
(() => {
  const byId = (id) => document.getElementById(id);
  const status = byId('status');
  const sessionsNode = byId('sessions');
  let currentAccessToken = null;

  function requireToken() {
    if (!currentAccessToken) throw new Error('Login is required');
    return currentAccessToken;
  }

  async function request(path, options = {}, authenticated = true) {
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

  function setAuthenticatedSession(data, message) {
    if (!data || !data.access_token) throw new Error('Server did not return a session token');
    currentAccessToken = data.access_token;
    status.textContent = `${message} Session expires at ${data.expires_at}.`;
  }

  function clearAuthenticatedSession(message = 'Not authenticated.') {
    currentAccessToken = null;
    status.textContent = message;
    sessionsNode.textContent = 'No sessions loaded.';
  }

  async function register() {
    const username = byId('register-username').value.trim();
    const password = byId('register-password').value;
    if (!username || !password) throw new Error('Username and password are required');
    const data = await request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }, false);
    byId('register-password').value = '';
    setAuthenticatedSession(data, 'Registered and authenticated.');
    await loadSessions();
  }

  async function login() {
    const username = byId('login-username').value.trim();
    const password = byId('login-password').value;
    if (!username || !password) throw new Error('Username and password are required');
    const data = await request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }, false);
    byId('login-password').value = '';
    setAuthenticatedSession(data, 'Authenticated.');
    await loadSessions();
  }

  function renderSessions(sessions) {
    sessionsNode.textContent = '';
    if (!sessions.length) {
      sessionsNode.textContent = 'No active sessions.';
      return;
    }
    for (const session of sessions) {
      const row = document.createElement('div');
      row.className = 'session-row';
      const description = document.createElement('span');
      description.textContent = `${session.current ? 'Current' : 'Other'} session · created ${session.created_at} · expires ${session.expires_at}`;
      row.appendChild(description);
      if (!session.current) {
        const revoke = document.createElement('button');
        revoke.type = 'button';
        revoke.textContent = 'Revoke';
        revoke.addEventListener('click', async () => {
          try {
            await request(`/api/v1/auth/sessions/${encodeURIComponent(session.id)}`, { method: 'DELETE' });
            status.textContent = 'Session revoked.';
            await loadSessions();
          } catch (error) {
            status.textContent = error instanceof Error ? error.message : String(error);
          }
        });
        row.appendChild(revoke);
      }
      sessionsNode.appendChild(row);
    }
  }

  async function loadSessions() {
    const sessions = await request('/api/v1/auth/sessions');
    renderSessions(sessions);
  }

  async function revokeOthers() {
    const result = await request('/api/v1/auth/sessions/others', { method: 'DELETE' });
    status.textContent = `Revoked ${result.revoked} other session(s).`;
    await loadSessions();
  }

  async function rotate() {
    const data = await request('/api/v1/auth/session/rotate', { method: 'POST' });
    setAuthenticatedSession(data, 'Current session rotated.');
    await loadSessions();
  }

  async function logout() {
    await request('/api/v1/auth/session', { method: 'DELETE' });
    clearAuthenticatedSession('Logged out.');
  }

  async function changePassword() {
    const currentPassword = byId('current-password').value;
    const newPassword = byId('new-password').value;
    if (!currentPassword || !newPassword) throw new Error('Current and new password are required');
    const data = await request('/api/v1/auth/password', {
      method: 'PUT',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
    byId('current-password').value = '';
    byId('new-password').value = '';
    setAuthenticatedSession(data, 'Password changed; previous sessions were revoked.');
    await loadSessions();
  }

  const bind = (id, fn) => {
    byId(id).addEventListener('click', async () => {
      try { await fn(); }
      catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
    });
  };

  bind('register', register);
  bind('login', login);
  bind('load-sessions', loadSessions);
  bind('revoke-others', revokeOthers);
  bind('rotate', rotate);
  bind('logout', logout);
  bind('change-password', changePassword);
})();
</script>
</body>
</html>
'''
