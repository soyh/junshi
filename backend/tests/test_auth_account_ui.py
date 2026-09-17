def test_auth_account_ui_is_served_and_hidden_from_openapi(client):
    response = client.get("/api/v1/auth/ui")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Account & Session" in response.text

    openapi = client.get("/openapi.json").json()
    assert "/api/v1/auth/ui" not in openapi["paths"]


def test_auth_account_ui_keeps_session_token_in_page_memory_only(client):
    html = client.get("/api/v1/auth/ui").text

    assert "let currentAccessToken = null" in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert "id=\"access-token\"" not in html


def test_auth_account_ui_uses_verified_auth_endpoints_and_password_fields(client):
    html = client.get("/api/v1/auth/ui").text

    for path in (
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/sessions",
        "/api/v1/auth/sessions/others",
        "/api/v1/auth/session/rotate",
        "/api/v1/auth/session",
        "/api/v1/auth/password",
    ):
        assert path in html

    assert 'id="register-password" type="password"' in html
    assert 'id="login-password" type="password"' in html
    assert 'id="current-password" type="password"' in html
    assert 'id="new-password" type="password"' in html
    assert "data.access_token" in html
    assert "currentAccessToken = data.access_token" in html


def test_auth_account_ui_does_not_offer_unverified_recovery(client):
    html = client.get("/api/v1/auth/ui").text

    assert "Account recovery is currently unavailable" in html
    assert "no verified email, SMS, or external identity recovery channel" in html
    assert "/auth/recover" not in html
    assert "/auth/reset" not in html
    assert "forgot-password" not in html.lower()
