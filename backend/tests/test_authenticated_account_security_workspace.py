PASSWORD = "account-security-password"


def _register(client, username: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_password_change_fields_are_cleared_with_session(client):
    html = client.get("/app").text

    assert "const baseClearSessionForAccountSecurity = clearSession;" in html
    assert "clearSession = function(message = 'Not authenticated.')" in html
    assert "clearPasswordChangeFields();" in html
    assert "clearSelectiveSessions();" in html
    assert "changePasswordStatus.textContent = 'Login before changing password.';" in html
    assert "baseClearSessionForAccountSecurity(message);" in html

    wrapper_start = html.index("const baseClearSessionForAccountSecurity = clearSession;")
    lifecycle_start = html.index(
        "const actionReanalysisInputStatus = byId('action-reanalysis-input-status')"
    )
    assert wrapper_start < lifecycle_start


def test_account_security_exposes_selective_other_session_revocation(client):
    html = client.get("/app").text

    assert 'id="load-security-sessions"' in html
    assert 'id="security-session-select"' in html
    assert 'id="revoke-selected-session"' in html
    assert "const others = sessions.filter((item) => !item.current);" in html
    assert "window.confirm('Revoke the selected other session?')" in html
    assert "/api/v1/auth/sessions/${encodeURIComponent(revokingId)}" in html
    assert "method: 'DELETE'" in html


def test_selective_session_revoke_keeps_current_session_and_revokes_only_target(client):
    current_token = _register(client, "account-security-selective")
    current_headers = _auth(current_token)

    second_response = client.post("/api/v1/auth/sessions", headers=current_headers)
    assert second_response.status_code == 201
    second_token = second_response.json()["access_token"]

    sessions = client.get("/api/v1/auth/sessions", headers=current_headers)
    assert sessions.status_code == 200
    items = sessions.json()
    current = next(item for item in items if item["current"])
    other = next(item for item in items if not item["current"])

    revoked = client.delete(
        f"/api/v1/auth/sessions/{other['id']}",
        headers=current_headers,
    )
    assert revoked.status_code == 204

    still_current = client.get("/api/v1/auth/sessions", headers=current_headers)
    assert still_current.status_code == 200
    remaining = still_current.json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == current["id"]
    assert remaining[0]["current"] is True

    assert client.get("/api/v1/auth/sessions", headers=_auth(second_token)).status_code == 401
