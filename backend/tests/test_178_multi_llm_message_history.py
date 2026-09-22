from cryptography.fernet import Fernet

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.message import MessageService


LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")


def _create_conversation(client):
    person = client.post("/api/v1/persons", json={"name": "TEST-178 history person"})
    assert person.status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person.json()["id"], "title": "TEST-178 history"},
    )
    assert conversation.status_code == 201
    return conversation.json()["id"]


def test_multiple_llm_profiles_can_coexist_and_active_profile_drives_legacy_api(client, monkeypatch):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()

    first = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": "DeepSeek main",
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "api_key": "secret-deepseek",
            "timeout_seconds": 45,
            "activate": True,
        },
    )
    assert first.status_code == 201
    assert first.json()["is_active"] is True
    assert "api_key" not in first.json()

    second = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": "OpenAI vision",
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-test-vision",
            "api_key": "secret-openai",
            "timeout_seconds": 60,
        },
    )
    assert second.status_code == 201
    assert second.json()["is_active"] is False

    profiles = client.get("/api/v1/settings/llm/profiles")
    assert profiles.status_code == 200
    assert len(profiles.json()) == 2
    assert all("api_key" not in item for item in profiles.json())

    activated = client.post(
        f"/api/v1/settings/llm/profiles/{second.json()['id']}/activate"
    )
    assert activated.status_code == 200
    assert activated.json()["is_active"] is True

    legacy_active = client.get("/api/v1/settings/llm")
    assert legacy_active.status_code == 200
    assert legacy_active.json()["provider"] == "openai"
    assert legacy_active.json()["model"] == "gpt-test-vision"
    assert "api_key" not in legacy_active.json()

    other_user = client.get(
        "/api/v1/settings/llm/profiles",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert other_user.status_code == 200
    assert other_user.json() == []

    foreign_activate = client.post(
        f"/api/v1/settings/llm/profiles/{second.json()['id']}/activate",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert foreign_activate.status_code == 404

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT api_key_encrypted FROM user_llm_profiles WHERE user_id = ?",
            (LOCAL_USER_ID,),
        ).fetchall()
        assert len(rows) == 2
        encrypted_values = {row["api_key_encrypted"] for row in rows}
        assert "secret-deepseek" not in encrypted_values
        assert "secret-openai" not in encrypted_values

    get_settings.cache_clear()


def test_profile_can_be_modified_without_resending_api_key(client, monkeypatch):
    monkeypatch.setenv("LLM_CONFIG_ENCRYPTION_KEY", ENCRYPTION_KEY)
    get_settings.cache_clear()
    created = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": "Custom",
            "provider": "openai_compatible",
            "base_url": "https://provider.example/v1",
            "model": "model-a",
            "api_key": "profile-secret",
            "activate": True,
        },
    )
    assert created.status_code == 201

    updated = client.patch(
        f"/api/v1/settings/llm/profiles/{created.json()['id']}",
        json={"name": "Custom updated", "model": "model-b"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Custom updated"
    assert updated.json()["model"] == "model-b"
    assert updated.json()["api_key_configured"] is True

    get_settings.cache_clear()


def test_message_api_defaults_to_latest_100_but_canonical_service_keeps_full_history(client):
    conversation_id = _create_conversation(client)
    for index in range(105):
        created = client.post(
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": "user" if index % 2 == 0 else "person",
                "content": f"message-{index:03d}",
                "sent_at": f"2026-09-22T12:{index // 60:02d}:{index % 60:02d}+00:00",
            },
        )
        assert created.status_code == 201

    response = client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert response.status_code == 200
    displayed = response.json()
    assert len(displayed) == 100
    assert displayed[0]["content"] == "message-005"
    assert displayed[-1]["content"] == "message-104"

    with get_connection() as conn:
        canonical = MessageService().list(conn, LOCAL_USER_ID, conversation_id)
    assert len(canonical) == 105
    assert canonical[0]["content"] == "message-000"
    assert canonical[-1]["content"] == "message-104"


def test_message_time_window_and_patch_are_user_scoped(client):
    conversation_id = _create_conversation(client)
    ids = []
    for minute in range(5):
        created = client.post(
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": "user",
                "content": f"window-{minute}",
                "sent_at": f"2026-09-22T10:0{minute}:00+00:00",
            },
        )
        assert created.status_code == 201
        ids.append(created.json()["id"])

    filtered = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={
            "from": "2026-09-22T10:01:00+00:00",
            "to": "2026-09-22T10:03:00+00:00",
            "limit": 100,
        },
    )
    assert filtered.status_code == 200
    assert [item["content"] for item in filtered.json()] == [
        "window-1",
        "window-2",
        "window-3",
    ]

    patched = client.patch(
        f"/api/v1/messages/{ids[2]}",
        json={
            "sender_type": "person",
            "content": "window-2-edited",
            "sent_at": "2026-09-22T10:02:30+00:00",
        },
    )
    assert patched.status_code == 200
    assert patched.json()["sender_type"] == "person"
    assert patched.json()["content"] == "window-2-edited"
    assert patched.json()["sent_at"] == "2026-09-22T10:02:30+00:00"

    foreign_patch = client.patch(
        f"/api/v1/messages/{ids[2]}",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
        json={"content": "cross-user edit"},
    )
    assert foreign_patch.status_code == 404


def test_authenticated_ui_exposes_profiles_history_editing_and_default_100():
    from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML

    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert "client-llm-profile-select" in html
    assert "新建配置" in html
    assert "设为当前" in html
    assert "/settings/llm/profiles" in html
    assert "client-message-limit" in html
    assert "最新100条" in html
    assert "limit: 100" in html
    assert "method: 'PATCH'" in html
    assert "历史消息删除" in html
    assert "AI 分析仍使用" in html or "AI 分析始终参考" in html
    assert "innerHTML" not in html
