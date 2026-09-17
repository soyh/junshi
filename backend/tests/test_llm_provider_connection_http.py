from app.services.llm import LLMAnalysisError
from app.api.routes.llm_provider_config import service
from app.services.llm_provider_config import LLMProviderConfigError


def test_connection_endpoint_returns_ok_for_current_user(client, monkeypatch):
    calls = []

    def fake_test_connection(conn, user_id):
        calls.append(user_id)

    monkeypatch.setattr(service, "test_connection", fake_test_connection)

    response = client.post(
        "/api/v1/settings/llm/test",
        headers={"X-User-ID": "user-a"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == ["user-a"]


def test_connection_endpoint_maps_provider_configuration_error_to_503(client, monkeypatch):
    def fake_test_connection(conn, user_id):
        raise LLMProviderConfigError("stored provider configuration is invalid")

    monkeypatch.setattr(service, "test_connection", fake_test_connection)

    response = client.post(
        "/api/v1/settings/llm/test",
        headers={"X-User-ID": "user-a"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "stored provider configuration is invalid"


def test_connection_endpoint_maps_upstream_failure_to_502(client, monkeypatch):
    def fake_test_connection(conn, user_id):
        raise LLMAnalysisError("LLM provider connection test failed")

    monkeypatch.setattr(service, "test_connection", fake_test_connection)

    response = client.post(
        "/api/v1/settings/llm/test",
        headers={"X-User-ID": "user-a"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM provider connection test failed"
