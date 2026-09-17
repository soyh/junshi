def test_provider_settings_ui_is_served_and_uses_existing_provider_api(client):
    response = client.get("/api/v1/settings/llm/ui")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    body = response.text
    assert "LLM Provider Settings" in body
    assert "X-User-ID" in body
    assert "/api/v1/settings/llm" in body
    assert "/api/v1/settings/llm/test" in body
    assert "/analysis/structured" in body
    assert 'type="password"' in body


def test_provider_settings_ui_requires_explicit_user_scope_and_does_not_store_secrets_client_side(client):
    response = client.get("/api/v1/settings/llm/ui")
    body = response.text

    assert 'id="user-id" value=' not in body
    assert "localStorage" not in body
    assert "sessionStorage" not in body
    assert ".innerHTML" not in body
    assert "api-key').value = ''" in body
    assert "API key is stored server-side and is not returned" in body


def test_provider_settings_ui_is_not_added_to_public_openapi_schema(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/settings/llm/ui" not in response.json()["paths"]
