import base64
import json
import struct
from pathlib import Path

import httpx
from cryptography.fernet import Fernet

from app.config.settings import Settings, get_settings
from app.core.database import get_connection
from app.services.llm_provider_config import LLMProviderConfigService
from app.services.media_attachment import MediaAttachmentService
from app.services.openai_chat_provider import OpenAICompatibleProvider
from app.services.vision_llm_provider import LLMVisionProviderService
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def _enable_llm_encryption(monkeypatch):
    monkeypatch.setenv(
        "LLM_CONFIG_ENCRYPTION_KEY",
        Fernet.generate_key().decode("ascii"),
    )
    get_settings.cache_clear()


def _profile(client, *, name, model, api_key, activate=False):
    response = client.post(
        "/api/v1/settings/llm/profiles",
        json={
            "name": name,
            "provider": "openai_compatible",
            "base_url": "https://provider.example/v1",
            "model": model,
            "api_key": api_key,
            "timeout_seconds": 30,
            "activate": activate,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_primary_and_vision_profiles_are_selected_independently(client, monkeypatch):
    _enable_llm_encryption(monkeypatch)
    user_id = get_settings().local_user_id

    _profile(
        client,
        name="Primary text",
        model="text-model",
        api_key="text-secret",
        activate=True,
    )
    vision = _profile(
        client,
        name="Vision media",
        model="vision-model",
        api_key="vision-secret",
    )

    selected = client.put(
        "/api/v1/settings/llm/vision",
        json={"profile_id": vision["id"]},
    )
    assert selected.status_code == 200
    assert selected.json()["profile_id"] == vision["id"]
    assert selected.json()["model"] == "vision-model"
    assert "api_key" not in selected.json()

    legacy_primary = client.get("/api/v1/settings/llm")
    assert legacy_primary.status_code == 200
    assert legacy_primary.json()["model"] == "text-model"

    with get_connection() as conn:
        primary_provider = LLMProviderConfigService().build_provider(
            conn,
            user_id,
        )
        vision_provider = LLMVisionProviderService().build_provider(
            conn,
            user_id,
        )

    assert primary_provider.model == "text-model"
    assert primary_provider.api_key == "text-secret"
    assert vision_provider.model == "vision-model"
    assert vision_provider.api_key == "vision-secret"

    get_settings.cache_clear()


def test_vision_selection_falls_back_to_primary_when_unset_or_deleted(client, monkeypatch):
    _enable_llm_encryption(monkeypatch)
    user_id = get_settings().local_user_id

    primary = _profile(
        client,
        name="Primary",
        model="primary-model",
        api_key="primary-secret",
        activate=True,
    )
    vision = _profile(
        client,
        name="Vision",
        model="vision-model",
        api_key="vision-secret",
    )

    empty = client.get("/api/v1/settings/llm/vision")
    assert empty.status_code == 200
    assert empty.json() is None

    with get_connection() as conn:
        fallback = LLMVisionProviderService().build_provider(
            conn,
            user_id,
        )
    assert fallback.model == "primary-model"

    selected = client.put(
        "/api/v1/settings/llm/vision",
        json={"profile_id": vision["id"]},
    )
    assert selected.status_code == 200

    deleted = client.delete(
        f"/api/v1/settings/llm/profiles/{vision['id']}"
    )
    assert deleted.status_code == 204

    stale = client.get("/api/v1/settings/llm/vision")
    assert stale.status_code == 200
    assert stale.json() is None

    with get_connection() as conn:
        fallback_after_delete = LLMVisionProviderService().build_provider(
            conn,
            user_id,
        )
        selection_count = conn.execute(
            "SELECT COUNT(*) FROM user_llm_vision_profile_selection"
        ).fetchone()[0]
    assert fallback_after_delete.model == "primary-model"
    assert selection_count == 0

    cleared = client.delete("/api/v1/settings/llm/vision")
    assert cleared.status_code == 204
    assert primary["is_active"] is True

    get_settings.cache_clear()


def test_vision_selection_rejects_profile_from_another_user(client, monkeypatch):
    _enable_llm_encryption(monkeypatch)

    profile = _profile(
        client,
        name="Owned profile",
        model="owned-model",
        api_key="owned-secret",
        activate=True,
    )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_llm_provider_profiles (
                id, user_id, name, provider, base_url, model,
                timeout_seconds, api_key_encrypted, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                "foreign-profile",
                "other-user",
                "Foreign",
                "openai_compatible",
                "https://provider.example/v1",
                "foreign-model",
                30,
                "not-used",
            ),
        )

    response = client.put(
        "/api/v1/settings/llm/vision",
        json={"profile_id": "foreign-profile"},
    )
    assert response.status_code == 404

    current = client.get("/api/v1/settings/llm")
    assert current.status_code == 200
    assert current.json()["model"] == profile["model"]

    get_settings.cache_clear()


def test_vision_capability_test_sends_real_image_request(client, monkeypatch):
    _enable_llm_encryption(monkeypatch)
    captured = {}

    _profile(
        client,
        name="Primary",
        model="primary-model",
        api_key="primary-secret",
        activate=True,
    )
    vision = _profile(
        client,
        name="Vision",
        model="vision-model",
        api_key="vision-secret",
    )
    assert client.put(
        "/api/v1/settings/llm/vision",
        json={"profile_id": vision["id"]},
    ).status_code == 200

    def handler(request: httpx.Request):
        payload = json.loads(request.content.decode("utf-8"))
        captured["payload"] = payload
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "OK"}}
                ]
            },
            request=request,
        )

    provider = OpenAICompatibleProvider(
        api_key="vision-secret",
        base_url="https://provider.example/v1",
        model="vision-model",
        timeout_seconds=5,
        provider_name="test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    monkeypatch.setattr(
        LLMVisionProviderService,
        "build_provider",
        lambda self, conn, user_id: provider,
    )

    response = client.post("/api/v1/settings/llm/vision/test")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model"] == "vision-model"

    content = captured["payload"]["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"
    image_part = content[1]["image_url"]
    assert set(image_part) == {"url"}
    assert image_part["url"].startswith("data:image/png;base64,")

    encoded = image_part["url"].split(",", 1)[1]
    png = base64.b64decode(encoded)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (64, 64)

    get_settings.cache_clear()


def test_media_analysis_uses_vision_resolver(monkeypatch):
    captured = {}

    class Repository:
        def get(self, conn, user_id, attachment_id):
            return {
                "conversation_id": "conversation-1",
                "media_type": "image",
                "sent_at": "2026-09-23T00:00:00+00:00",
            }

        def mark_completed(
            self,
            conn,
            user_id,
            attachment_id,
            analysis_text,
            evidence_message_id,
        ):
            return {"id": attachment_id, "status": "completed"}

        def mark_failed(self, conn, user_id, attachment_id):
            raise AssertionError("media analysis should not fail")

    class MessageService:
        def create(
            self,
            conn,
            user_id,
            conversation_id,
            sender_type,
            content,
            sent_at,
        ):
            return {"id": "evidence-1"}

    provider = OpenAICompatibleProvider(
        api_key="vision-secret",
        base_url="https://provider.example/v1",
        model="vision-model",
        timeout_seconds=5,
        provider_name="test",
    )

    service = MediaAttachmentService(
        repository=Repository(),
        message_service=MessageService(),
    )
    monkeypatch.setattr(
        service.vision_provider_service,
        "build_provider",
        lambda conn, user_id: provider,
    )
    monkeypatch.setattr(
        service,
        "_analyze_with_provider",
        lambda actual_provider, row: captured.setdefault(
            "model",
            actual_provider.model,
        ) or "{}",
    )

    updated, evidence_id = service.analyze(
        object(),
        "user-1",
        "attachment-1",
    )
    assert captured["model"] == "vision-model"
    assert updated["status"] == "completed"
    assert evidence_id == "evidence-1"


def test_test179_ui_exposes_primary_and_vision_roles():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert "主模型 / 视觉模型" in html
    assert "设为主模型" in html
    assert "设为视觉模型" in html
    assert "视觉跟随主模型" in html
    assert "/api/v1/settings/llm/vision" in html


def test_test179_migration_and_runtime_env_paths_are_stable():
    migration = (
        Path(__file__).parents[1]
        / "migrations"
        / "017_vision_llm_profile_selection.sql"
    )
    sql = migration.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS user_llm_vision_profile_selection" in sql
    assert "ON DELETE CASCADE" in sql

    env_files = Settings.model_config["env_file"]
    assert len(env_files) == 2
    assert all(Path(path).is_absolute() for path in env_files)
    assert str(env_files[0]).endswith("/.env")
    assert str(env_files[1]).endswith("/backend/.env")
