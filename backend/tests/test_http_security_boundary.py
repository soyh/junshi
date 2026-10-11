SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
}


def _assert_security_headers(response):
    for name, expected in SECURITY_HEADERS.items():
        assert response.headers.get(name) == expected


def test_security_headers_apply_to_health_and_not_found(client):
    health = client.get("/health")
    missing = client.get("/does-not-exist")

    assert health.status_code == 200
    assert missing.status_code == 404
    _assert_security_headers(health)
    _assert_security_headers(missing)


def test_auth_responses_are_no_store(client):
    response = client.get("/api/v1/auth/ui")

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    _assert_security_headers(response)


def test_settings_responses_are_no_store(client):
    response = client.get("/api/v1/settings/llm")

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    _assert_security_headers(response)


def test_non_sensitive_health_does_not_force_no_store(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("cache-control") != "no-store"


def test_default_app_does_not_enable_cross_origin_cors(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://untrusted.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_registration_uses_response_bearer_token_not_cookie(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "http-security-user",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 201
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert "set-cookie" not in response.headers
    assert response.headers.get("cache-control") == "no-store"
    _assert_security_headers(response)
