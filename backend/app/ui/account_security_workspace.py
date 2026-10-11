ACCOUNT_SECURITY_HTML = r'''
  <fieldset id="account-security" class="wide">
    <legend>Account Security</legend>
    <p class="note">修改密码和 session 管理继续复用现有 authenticated account API。敏感输入只存在当前页面内存/DOM，不写入浏览器持久化存储。</p>
    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="change-password-heading">
        <h2 id="change-password-heading">Change password</h2>
        <label for="current-password-change">Current password</label>
        <input id="current-password-change" class="requires-auth" type="password" autocomplete="current-password" disabled>
        <label for="new-password-change">New password</label>
        <input id="new-password-change" class="requires-auth" type="password" autocomplete="new-password" minlength="12" disabled>
        <label for="confirm-new-password-change">Confirm new password</label>
        <input id="confirm-new-password-change" class="requires-auth" type="password" autocomplete="new-password" minlength="12" disabled>
        <button id="change-password" class="requires-auth" type="button" disabled>Change password</button>
        <div id="change-password-status" class="status">Login before changing password.</div>
      </section>

      <section class="workspace-card" aria-labelledby="selective-session-heading">
        <h2 id="selective-session-heading">Selective session revocation</h2>
        <p class="note">当前 session 使用上方 Logout / Rotate；这里仅选择并撤销某一个其它 active session，不会批量撤销。</p>
        <button id="load-security-sessions" class="requires-auth" type="button" disabled>Refresh other sessions</button>
        <label for="security-session-select">Other active session</label>
        <select id="security-session-select" class="requires-auth" size="5" disabled></select>
        <button id="revoke-selected-session" class="requires-auth" type="button" disabled>Revoke selected session</button>
        <div id="security-session-status" class="status">Login to inspect other sessions.</div>
      </section>
    </div>
  </fieldset>
'''


ACCOUNT_SECURITY_SCRIPT = r'''
  const changePasswordStatus = byId('change-password-status');
  const securitySessionStatus = byId('security-session-status');
  let selectedSecuritySessionId = null;

  function clearPasswordChangeFields() {
    byId('current-password-change').value = '';
    byId('new-password-change').value = '';
    byId('confirm-new-password-change').value = '';
  }

  function clearSelectiveSessions(message = 'Login to inspect other sessions.') {
    selectedSecuritySessionId = null;
    resetSelect('security-session-select', 'No other session selected');
    securitySessionStatus.textContent = message;
  }

  async function changeAccountPassword() {
    const currentPassword = byId('current-password-change').value;
    const newPassword = byId('new-password-change').value;
    const confirmPassword = byId('confirm-new-password-change').value;
    if (!currentPassword) throw new Error('Current password is required');
    if (newPassword.length < 12) throw new Error('New password must contain at least 12 characters');
    if (newPassword !== confirmPassword) throw new Error('New password confirmation does not match');

    changePasswordStatus.textContent = 'Changing password...';
    const data = await api('/api/v1/auth/password', {
      method: 'PUT',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
    clearPasswordChangeFields();
    establishSession(data, 'Password changed.');
    await loadSessions();
    await loadSelectiveSessions();
    changePasswordStatus.textContent = `Password changed. New session expires at ${data.expires_at}.`;
  }

  async function loadSelectiveSessions() {
    const sessions = await api('/api/v1/auth/sessions');
    const others = sessions.filter((item) => !item.current);
    if (!others.some((item) => item.id === selectedSecuritySessionId)) {
      selectedSecuritySessionId = null;
    }
    renderSelect(
      'security-session-select',
      others,
      (item) => `created ${item.created_at} · expires ${item.expires_at}`,
      'No other session selected',
      selectedSecuritySessionId,
    );
    securitySessionStatus.textContent = `${others.length} other active session(s).`;
  }

  function selectSecuritySession() {
    selectedSecuritySessionId = byId('security-session-select').value || null;
  }

  async function revokeSelectedSecuritySession() {
    if (!selectedSecuritySessionId) throw new Error('Select another session first');
    const revokingId = selectedSecuritySessionId;
    if (!window.confirm('Revoke the selected other session?')) return;
    await api(`/api/v1/auth/sessions/${encodeURIComponent(revokingId)}`, {
      method: 'DELETE',
    });
    selectedSecuritySessionId = null;
    await loadSelectiveSessions();
    await loadSessions();
    securitySessionStatus.textContent = 'Selected session revoked.';
  }

  const baseClearSessionForAccountSecurity = clearSession;
  clearSession = function(message = 'Not authenticated.') {
    clearPasswordChangeFields();
    clearSelectiveSessions();
    changePasswordStatus.textContent = 'Login before changing password.';
    baseClearSessionForAccountSecurity(message);
  };

  bind('change-password', changeAccountPassword, changePasswordStatus);
  bind('load-security-sessions', loadSelectiveSessions, securitySessionStatus);
  bind('revoke-selected-session', revokeSelectedSecuritySession, securitySessionStatus);
  byId('security-session-select').addEventListener('change', selectSecuritySession);
'''
