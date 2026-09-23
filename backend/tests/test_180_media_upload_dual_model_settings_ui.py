import json

import httpx

from app.services.media_attachment import MediaAttachmentService
from app.services.openai_chat_provider import OpenAICompatibleProvider
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_test180_ui_exposes_visible_media_upload_surface():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "聊天截图 / 图片 / 视频" in html
    assert "fileInput.id = 'client-media-file'" in html
    assert "image/jpeg,image/png,image/webp,image/gif" in html
    assert "video/mp4,video/webm,video/quicktime" in html
    assert "upload.id = 'client-media-upload'" in html
    assert "上传并识别" in html
    assert "new FormData()" in html
    assert "/api/v1/conversations/${encodeURIComponent(conversationId)}/media" in html
    assert "/api/v1/media/${encodeURIComponent(attachment.id)}/analyze" in html
    assert "item.message_id ? '已写入会话证据' : '尚未生成会话证据'" in html
    assert "${item.analysis_status || 'unknown'}" in html
    assert "识别结果已作为媒体证据加入当前会话" in html
    assert "视频当前按关键帧进行视觉分析" in html


def test_test180_ui_exposes_independent_primary_and_vision_credentials():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "主文本 / 分析模型" in html
    assert "视觉 / 图片视频模型" in html
    assert "name: `dual-${role}-name`" in html
    assert "provider: `dual-${role}-provider`" in html
    assert "baseUrl: `dual-${role}-base-url`" in html
    assert "model: `dual-${role}-model`" in html
    assert "apiKey: `dual-${role}-api-key`" in html
    assert "timeout: `dual-${role}-timeout`" in html

    assert "savePrimary.id = 'dual-primary-save'" in html
    assert "testPrimary.id = 'dual-primary-test'" in html
    assert "saveVision.id = 'dual-vision-save'" in html
    assert "testVision.id = 'dual-vision-test'" in html
    assert "follow.id = 'dual-vision-follow-primary'" in html
    assert "两套配置的 Provider、API Key、Base URL、Model、Timeout 可完全不同" in html
    assert "高级：Profile 管理与兼容设置" in html


def test_media_payload_matches_verified_openai_compatible_image_format(tmp_path):
    image = tmp_path / "screenshot.png"
    image.write_bytes(b"fake-image")
    captured = {}

    def handler(request: httpx.Request):
        payload = json.loads(request.content.decode("utf-8"))
        captured["payload"] = payload
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "media_summary": "chat screenshot",
                                    "visible_text": ["hello"],
                                    "emotional_signals": [],
                                    "interaction_signals": [],
                                    "uncertainty": [],
                                }
                            )
                        }
                    }
                ]
            },
            request=request,
        )

    provider = OpenAICompatibleProvider(
        api_key="secret",
        base_url="https://provider.example/v1",
        model="vision-model",
        timeout_seconds=5,
        provider_name="test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = MediaAttachmentService()._analyze_with_provider(
        provider,
        {
            "media_type": "image",
            "mime_type": "image/png",
            "storage_path": str(image),
        },
    )

    assert json.loads(result)["media_summary"] == "chat screenshot"
    content = captured["payload"]["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert set(content[1]["image_url"]) == {"url"}
    assert "detail" not in content[1]["image_url"]


def test_media_analysis_persists_system_evidence_message(monkeypatch):
    captured = {}

    class Repository:
        def get(self, conn, user_id, attachment_id):
            return {
                "conversation_id": "conversation-1",
                "media_type": "image",
                "mime_type": "image/png",
                "storage_path": "/not-used.png",
                "sent_at": "2026-09-24T00:00:00+08:00",
            }

        def mark_completed(
            self,
            conn,
            user_id,
            attachment_id,
            analysis_text,
            evidence_message_id,
        ):
            captured["analysis_text"] = analysis_text
            captured["evidence_message_id"] = evidence_message_id
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
            captured["conversation_id"] = conversation_id
            captured["sender_type"] = sender_type
            captured["content"] = content
            captured["sent_at"] = sent_at
            return {"id": "media-evidence-1"}

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
        lambda actual_provider, row: json.dumps(
            {
                "media_summary": "visible chat",
                "visible_text": ["hello"],
                "emotional_signals": [],
                "interaction_signals": [],
                "uncertainty": ["speaker identity not inferred"],
            },
            ensure_ascii=False,
        ),
    )

    updated, evidence_id = service.analyze(
        object(),
        "user-1",
        "attachment-1",
    )

    assert updated["status"] == "completed"
    assert evidence_id == "media-evidence-1"
    assert captured["conversation_id"] == "conversation-1"
    assert captured["sender_type"] == "system"
    assert captured["sent_at"] == "2026-09-24T00:00:00+08:00"
    assert captured["content"].startswith("[媒体证据:image] ")
    assert "visible chat" in captured["content"]
    assert captured["evidence_message_id"] == "media-evidence-1"
