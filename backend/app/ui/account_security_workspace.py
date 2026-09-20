ACCOUNT_SECURITY_HTML = r'''
  <fieldset id="account-security" class="wide">
    <legend>Account Security</legend>
    <p class="note">修改密码继续复用现有 authenticated account API。成功后服务端会签发新的 session，页面立即切换到新 token；密码不会持久化到浏览器存储。</p>
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
    </div>
  </fieldset>
'''


ACCOUNT_SECURITY_SCRIPT = r'''
  const changePasswordStatus = byId('change-password-status');

  function clearPasswordChangeFields() {
    byId('current-password-change').value = '';
    byId('new-password-change').value = '';
    byId('confirm-new-password-change').value = '';
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
    changePasswordStatus.textContent = `Password changed. New session expires at ${data.expires_at}.`;
  }

  const baseClearSessionForAccountSecurity = clearSession;
  clearSession = function(message = 'Not authenticated.') {
    clearPasswordChangeFields();
    changePasswordStatus.textContent = 'Login before changing password.';
    baseClearSessionForAccountSecurity(message);
  };

  bind('change-password', changeAccountPassword, changePasswordStatus);
'''
