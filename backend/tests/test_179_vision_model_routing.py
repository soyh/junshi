from pathlib import Path

from cryptography.fernet import Fernet

from app.config.settings import Settings, get_settings
from app.core.database import get_connection
from app.services.llm_provider_config import LLMProviderConfigService
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

    primary = _profile(
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
            primary["id"] if False else primary.get("user_id", "00000000-0000-0000-0000-000000000001"),
        )
        vision_provider = LLMVisionProviderService().build_provider(
            conn,
            "00000000-0000-0000-0000-000000000001",
        )

    assert primary_provider.model == "text-model"
    assert vision_provider.model == "vision-model"
    assert vision_provider.api_key == "vision-secret"

    get_settings.cache_clear()


def test_vision_selection_falls_back_to_primary_when_unset_or_deleted(client, monkeypatch):
    _enable_llm_encryption(monkeypatch)

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
            "00000000-0000-0000-0000-000000000001",
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
            "00000000-0000-0000-0000-000000000001",
        )
    assert fallback_after_delete.model == "primary-model"

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

    env_files = Settings.model_config["env_file"]
    assert len(env_files) == 2
    assert all(Path(path).is_absolute() for path in env_files)
    assert str(env_files[0]).endswith("/.env")
    assert str(env_files[1]).endswith("/backend/.env")
