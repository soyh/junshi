import json
from pathlib import Path

import httpx

from app.services.media_attachment import MediaAttachmentService
from app.services.openai_chat_provider import OpenAICompatibleProvider
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_main_app_exposes_media_upload_surface():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert "图片 / 视频" in html
    assert "client-media-file" in html
    assert "上传并识别" in html
    assert "image/jpeg" in html
    assert "video/mp4" in html
    assert "/media/" in html
    assert "系统证据加入完整会话链路" in html


def test_media_provider_payload_uses_image_content_without_secret(monkeypatch, tmp_path):
    image = tmp_path / "sample.png"
    image.write_bytes(b"fake-image")
    captured = {}

    def handler(request: httpx.Request):
        payload = json.loads(request.content.decode("utf-8"))
        captured["payload"] = payload
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "media_summary": "a sticker",
                                    "visible_text": [],
                                    "emotional_signals": ["playful"],
                                    "interaction_signals": [],
                                    "uncertainty": ["context needed"],
                                }
                            )
                        }
                    }
                ]
            },
            request=request,
        )

    provider = OpenAICompatibleProvider(
        api_key="secret-test-key",
        base_url="https://provider.example/v1",
        model="vision-model",
        timeout_seconds=5,
        provider_name="test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    row = {
        "media_type": "image",
        "mime_type": "image/png",
        "storage_path": str(image),
    }

    result = MediaAttachmentService()._analyze_with_provider(provider, row)
    parsed = json.loads(result)
    assert parsed["media_summary"] == "a sticker"
    parts = captured["payload"]["messages"][0]["content"]
    assert parts[0]["type"] == "text"
    assert parts[1]["type"] == "image_url"
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert "secret-test-key" not in result
    assert captured["authorization"] == "Bearer secret-test-key"


def test_media_response_schema_does_not_expose_storage_path():
    from app.schemas.media_attachment import MediaAttachmentResponse

    fields = set(MediaAttachmentResponse.model_fields)
    assert "storage_path" not in fields
    assert "sha256" not in fields
    assert "analysis_text" in fields


def test_media_migration_allows_repeated_same_file():
    migration = Path(__file__).parents[1] / "migrations" / "015_media_attachments.sql"
    sql = migration.read_text()
    assert "CREATE TABLE IF NOT EXISTS media_attachments" in sql
    assert "CREATE UNIQUE INDEX" not in sql
    assert "idx_media_attachments_sha256" in sql
