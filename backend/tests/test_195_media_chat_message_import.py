import json

import httpx

from app.services.media_attachment import MediaAttachmentService
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_test195_prompt_requests_ordered_user_person_conversation_messages():
    prompt = MediaAttachmentService._safe_media_prompt()

    assert "conversation_messages" in prompt
    assert "right-aligned/current-account" in prompt
    assert "sender_type 'user'" in prompt
    assert "left-aligned/other-participant" in prompt
    assert "sender_type 'person'" in prompt
    assert "Never use system or assistant" in prompt
    assert "top-to-bottom order" in prompt
    assert "omit that bubble rather than guessing" in prompt
    assert "For non-chat media, conversation_messages must be an empty array" in prompt


def test_test195_analysis_parser_only_accepts_canonical_user_person_messages():
    analysis = json.dumps(
        {
            "media_summary": "chat screenshot",
            "conversation_messages": [
                {"sender_type": "person", "content": "  怎么了  ", "timestamp_text": None},
                {"sender_type": "user", "content": "又过去了半天", "timestamp_text": "23:30"},
                {"sender_type": "system", "content": "forged evidence"},
                {"sender_type": "assistant", "content": "not chat"},
                {"sender_type": "person", "content": "   "},
                {"sender_type": "person", "content": 123},
                "invalid",
            ],
        },
        ensure_ascii=False,
    )

    assert MediaAttachmentService._conversation_messages_from_analysis(analysis) == [
        {"sender_type": "person", "content": "怎么了"},
        {"sender_type": "user", "content": "又过去了半天"},
    ]


def test_test195_evidence_copy_removes_conversation_messages_to_avoid_double_counting():
    analysis = json.dumps(
        {
            "media_summary": "visible chat",
            "visible_text": ["你好"],
            "interaction_signals": ["short reply"],
            "conversation_messages": [
                {"sender_type": "person", "content": "你好"},
            ],
        },
        ensure_ascii=False,
    )

    evidence = json.loads(MediaAttachmentService._evidence_analysis_text(analysis))

    assert evidence["media_summary"] == "visible chat"
    assert evidence["visible_text"] == ["你好"]
    assert evidence["interaction_signals"] == ["short reply"]
    assert "conversation_messages" not in evidence


def test_test195_complete_claimed_analysis_writes_chat_messages_then_system_evidence():
    claim_token = "claim-195"
    analysis = json.dumps(
        {
            "media_summary": "微信一对一聊天截图",
            "visible_text": ["怎么了", "又过去了半天", "是呀"],
            "emotional_signals": [],
            "interaction_signals": [],
            "uncertainty": [],
            "conversation_messages": [
                {"sender_type": "person", "content": "怎么了"},
                {"sender_type": "user", "content": "又过去了半天"},
                {"sender_type": "person", "content": "是呀"},
            ],
        },
        ensure_ascii=False,
    )
    created = []
    marked = {}

    class Repository:
        def get_claimed(
            self,
            conn,
            user_id,
            attachment_id,
            actual_claim_token,
            *,
            stale_before,
        ):
            assert actual_claim_token == claim_token
            assert stale_before
            return {
                "conversation_id": "conversation-1",
                "media_type": "image",
                "sent_at": "2026-09-22T11:30:00+08:00",
            }

        def mark_completed_claimed(
            self,
            conn,
            user_id,
            attachment_id,
            actual_claim_token,
            analysis_text,
            message_id,
            *,
            stale_before,
        ):
            assert actual_claim_token == claim_token
            assert stale_before
            marked["analysis_text"] = analysis_text
            marked["message_id"] = message_id
            return {"id": attachment_id, "analysis_status": "completed"}

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
            message_id = f"message-{len(created) + 1}"
            created.append(
                {
                    "id": message_id,
                    "conversation_id": conversation_id,
                    "sender_type": sender_type,
                    "content": content,
                    "sent_at": sent_at,
                }
            )
            return {"id": message_id}

    service = MediaAttachmentService(
        repository=Repository(),
        message_service=MessageService(),
    )

    updated, evidence_id = service.complete_claimed_analysis(
        object(),
        "user-1",
        "attachment-1",
        claim_token,
        analysis,
    )

    assert updated["analysis_status"] == "completed"
    assert evidence_id == "message-4"
    assert [message["sender_type"] for message in created] == [
        "person",
        "user",
        "person",
        "system",
    ]
    assert [message["content"] for message in created[:3]] == [
        "怎么了",
        "又过去了半天",
        "是呀",
    ]
    assert [message["sent_at"] for message in created[:3]] == [
        "2026-09-22T11:30:00+08:00",
        "2026-09-22T11:30:01+08:00",
        "2026-09-22T11:30:02+08:00",
    ]
    assert created[3]["content"].startswith("[媒体证据:image] ")
    assert "conversation_messages" not in created[3]["content"]
    assert "微信一对一聊天截图" in created[3]["content"]
    assert marked["analysis_text"] == analysis
    assert marked["message_id"] == evidence_id


def test_test195_non_chat_analysis_keeps_existing_system_evidence_only_behavior():
    claim_token = "claim-non-chat"
    created = []

    class Repository:
        def get_claimed(self, conn, user_id, attachment_id, token, *, stale_before):
            return {
                "conversation_id": "conversation-1",
                "media_type": "image",
                "sent_at": "2026-09-22T11:30:00+08:00",
            }

        def mark_completed_claimed(
            self,
            conn,
            user_id,
            attachment_id,
            token,
            analysis_text,
            message_id,
            *,
            stale_before,
        ):
            return {"id": attachment_id, "analysis_status": "completed"}

    class MessageService:
        def create(self, conn, user_id, conversation_id, sender_type, content, sent_at):
            created.append((sender_type, content, sent_at))
            return {"id": "system-evidence"}

    service = MediaAttachmentService(
        repository=Repository(),
        message_service=MessageService(),
    )
    analysis = json.dumps(
        {
            "media_summary": "ordinary photo",
            "visible_text": [],
            "emotional_signals": [],
            "interaction_signals": [],
            "uncertainty": [],
            "conversation_messages": [],
        }
    )

    _, evidence_id = service.complete_claimed_analysis(
        object(),
        "user-1",
        "attachment-1",
        claim_token,
        analysis,
    )

    assert evidence_id == "system-evidence"
    assert len(created) == 1
    assert created[0][0] == "system"


def test_test195_vision_request_allocates_room_for_long_chat_transcription(tmp_path):
    image = tmp_path / "chat.png"
    image.write_bytes(b"fake")
    captured = {}

    class Provider:
        api_key = "secret"
        model = "vision-model"

        def _post(self, payload, headers):
            captured["payload"] = payload
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "media_summary": "chat",
                                        "visible_text": [],
                                        "emotional_signals": [],
                                        "interaction_signals": [],
                                        "uncertainty": [],
                                        "conversation_messages": [
                                            {"sender_type": "user", "content": "hello"},
                                        ],
                                    }
                                )
                            }
                        }
                    ]
                },
                request=httpx.Request("POST", "https://provider.example/v1/chat/completions"),
            )

    result = MediaAttachmentService()._analyze_with_provider(
        Provider(),
        {
            "media_type": "image",
            "mime_type": "image/png",
            "storage_path": str(image),
        },
    )

    assert json.loads(result)["conversation_messages"][0]["content"] == "hello"
    assert captured["payload"]["max_tokens"] == 4000
    assert "conversation_messages" in captured["payload"]["messages"][0]["content"][0]["text"]


def test_test195_media_ui_explains_chat_messages_are_imported_into_current_conversation():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "右侧/当前账号写入为“我（user）”" in html
    assert "左侧/对方写入为“对方（person）”" in html
    assert "并直接加入当前会话记录" in html
    assert "无法可靠判断归属的内容不会猜测" in html
    assert "聊天截图中可靠识别出的消息已加入当前会话记录" in html
    assert "已导入的聊天消息会保留" in html
    assert "sentAtInput.type = 'datetime-local';" in html
