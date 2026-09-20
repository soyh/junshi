def test_password_change_fields_are_cleared_with_session(client):
    html = client.get("/app").text

    assert "const baseClearSessionForAccountSecurity = clearSession;" in html
    assert "clearSession = function(message = 'Not authenticated.')" in html
    assert "clearPasswordChangeFields();" in html
    assert "changePasswordStatus.textContent = 'Login before changing password.';" in html
    assert "baseClearSessionForAccountSecurity(message);" in html

    wrapper_start = html.index("const baseClearSessionForAccountSecurity = clearSession;")
    lifecycle_start = html.index("const actionReanalysisStatus = byId('action-reanalysis-status')")
    assert wrapper_start < lifecycle_start
