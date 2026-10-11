def test_product_shell_is_served_at_top_level_and_hidden_from_openapi(client):
    response = client.get("/app")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "AI Love Strategist" in response.text

    openapi = client.get("/openapi.json").json()
    assert "/app" not in openapi["paths"]


def test_product_shell_keeps_session_token_in_single_page_memory_only(client):
    html = client.get("/app").text

    assert "let currentAccessToken = null" in html
    assert "currentAccessToken = data.access_token" in html
    assert "currentAccessToken = null" in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    assert 'id="access-token"' not in html
    assert "access_token=" not in html
    assert "?token=" not in html


def test_product_shell_uses_verified_account_and_session_endpoints(client):
    html = client.get("/app").text

    for path in (
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/session",
        "/api/v1/auth/sessions",
        "/api/v1/auth/session/rotate",
        "/api/v1/auth/sessions/others",
    ):
        assert path in html

    assert 'id="password" type="password"' in html
    assert "data.access_token" in html
    assert "setAuthenticatedControls(true)" in html
    assert "setAuthenticatedControls(false)" in html


def test_product_shell_shares_authenticated_session_with_provider_settings(client):
    html = client.get("/app").text

    assert "/api/v1/settings/llm" in html
    assert "/api/v1/settings/llm/test" in html
    assert 'id="api-key" type="password"' in html
    assert "API key is stored server-side and is not returned" in html
    assert "byId('api-key').value = ''" in html
    assert 'id="load-provider" class="requires-auth" type="button" disabled' in html
    assert 'id="save-provider" class="requires-auth" type="button" disabled' in html


def test_product_shell_exposes_structured_analysis_through_existing_pipeline(client):
    html = client.get("/app").text

    assert "Structured Analysis" in html
    assert "/analysis/structured" in html
    assert "encodeURIComponent(conversationId)" in html
    assert "正式分析继续经过现有 StructuredAnalysis 验证链" in html
    assert 'id="run-analysis" class="requires-auth" type="button" disabled' in html


def test_product_shell_does_not_pretend_unimplemented_business_pages_exist(client):
    html = client.get("/app").text

    assert "Person、Relationship、Conversation、Recommendation、Action Plan、Execution、Outcome、Feedback、Learning 与 Re-analysis" in html
    assert "不伪造尚未完成的业务页面" in html
    assert "/app/persons" not in html
    assert "/app/relationships" not in html
    assert "/app/conversations" not in html
