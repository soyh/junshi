import json

from app.api.routes import media_attachments
from app.services.media_chat_time import TimedMediaAttachmentService
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_test196_production_route_uses_timed_media_service():
    assert isinstance(media_attachments.service, TimedMediaAttachmentService)


def test_test196_prompt_requests_visible_chat_time_markers_without_status_bar_clock():
    prompt = TimedMediaAttachmentService._safe_media_prompt()

    assert "time_markers" in prompt
    assert "before_message_index" in prompt
    assert "timestamp_text" in prompt
    assert "date_context_text" in prompt
    assert "Exclude phone status-bar clocks" in prompt
    assert "Never invent, normalize, infer, or repair a missing date or time" in prompt


def test_test196_full_date_marker_overrides_fallback_and_propagates_in_order():
    analysis = json.dumps(
        {
            "conversation_messages": [
                {"sender_type": "person", "content": "第一条"},
                {"sender_type": "user", "content": "第二条"},
                {"sender_type": "person", "content": "第三条"},
            ],
            "time_markers": [
                {"before_message_index": 0, "text": "9月22日 11:30"},
                {"before_message_index": 2, "text": "13:42"},
            ],
        },
        ensure_ascii=False,
    )

    assert TimedMediaAttachmentService._resolved_message_sent_ats(
        analysis,
        "2026-09-24T16:30:20+08:00",
    ) == [
        "2026-09-22T11:30:00+08:00",
        "2026-09-22T11:30:01+08:00",
        "2026-09-22T13:42:00+08:00",
    ]


def test_test196_relative_day_and_chinese_day_period_are_resolved_from_evidence_time():
    analysis = json.dumps(
        {
            "conversation_messages": [
                {"sender_type": "person", "content": "昨天的消息"},
                {"sender_type": "user", "content": "后续消息"},
            ],
            "time_markers": [
                {"before_message_index": 0, "text": "昨天 下午3:05"},
            ],
        },
        ensure_ascii=False,
    )

    assert TimedMediaAttachmentService._resolved_message_sent_ats(
        analysis,
        "2026-09-24T16:30:20+08:00",
    ) == [
        "2026-09-23T15:05:00+08:00",
        "2026-09-23T15:05:01+08:00",
    ]


def test_test196_message_timestamp_can_override_separator_time():
    analysis = json.dumps(
        {
            "conversation_messages": [
                {
                    "sender_type": "person",
                    "content": "带逐条时间",
                    "date_context_text": "2026-09-23",
                    "timestamp_text": "上午 9:19",
                },
                {"sender_type": "user", "content": "下一条"},
            ],
            "time_markers": [],
        },
        ensure_ascii=False,
    )

    assert TimedMediaAttachmentService._resolved_message_sent_ats(
        analysis,
        "2026-09-24T16:30:20+08:00",
    ) == [
        "2026-09-23T09:19:00+08:00",
        "2026-09-23T09:19:01+08:00",
    ]


def test_test196_unparseable_time_never_replaces_fallback_evidence_time():
    analysis = json.dumps(
        {
            "conversation_messages": [
                {"sender_type": "person", "content": "第一条", "timestamp_text": "大概午后"},
                {"sender_type": "user", "content": "第二条"},
            ],
            "time_markers": [
                {"before_message_index": 0, "text": "可能是昨天"},
            ],
        },
        ensure_ascii=False,
    )

    assert TimedMediaAttachmentService._resolved_message_sent_ats(
        analysis,
        "2026-09-22T11:30:00+08:00",
    ) == [
        "2026-09-22T11:30:00+08:00",
        "2026-09-22T11:30:01+08:00",
    ]


def test_test196_no_visible_time_uses_fallback_evidence_time_in_visual_order():
    analysis = json.dumps(
        {
            "conversation_messages": [
                {"sender_type": "person", "content": "没有时间一"},
                {"sender_type": "user", "content": "没有时间二"},
                {"sender_type": "person", "content": "没有时间三"},
            ],
            "time_markers": [],
        },
        ensure_ascii=False,
    )

    assert TimedMediaAttachmentService._resolved_message_sent_ats(
        analysis,
        "2026-09-22T11:30:00+08:00",
    ) == [
        "2026-09-22T11:30:00+08:00",
        "2026-09-22T11:30:01+08:00",
        "2026-09-22T11:30:02+08:00",
    ]


def test_test196_complete_analysis_writes_extracted_times_into_canonical_messages():
    claim_token = "claim-196"
    created = []

    class Repository:
        def get_claimed(self, conn, user_id, attachment_id, token, *, stale_before):
            assert token == claim_token
            return {
                "conversation_id": "conversation-1",
                "media_type": "image",
                "sent_at": "2026-09-24T16:30:20+08:00",
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
            assert token == claim_token
            return {"id": attachment_id, "analysis_status": "completed"}

    class MessageService:
        def create(self, conn, user_id, conversation_id, sender_type, content, sent_at):
            created.append(
                {
                    "sender_type": sender_type,
                    "content": content,
                    "sent_at": sent_at,
                }
            )
            return {"id": f"message-{len(created)}"}

    analysis = json.dumps(
        {
            "media_summary": "聊天截图",
            "conversation_messages": [
                {"sender_type": "person", "content": "怎么了"},
                {"sender_type": "user", "content": "上班上班"},
            ],
            "time_markers": [
                {"before_message_index": 0, "text": "9月23日 13:42"},
            ],
        },
        ensure_ascii=False,
    )

    service = TimedMediaAttachmentService(
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
    assert evidence_id == "message-3"
    assert [item["sender_type"] for item in created] == ["person", "user", "system"]
    assert [item["sent_at"] for item in created[:2]] == [
        "2026-09-23T13:42:00+08:00",
        "2026-09-23T13:42:01+08:00",
    ]
    assert created[2]["sent_at"] == "2026-09-24T16:30:20+08:00"
    assert "time_markers" in created[2]["content"]
    assert "conversation_messages" not in created[2]["content"]


def test_test196_only_new_media_import_surface_remains_in_product_html():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "card.id = 'client-media-import-card';" in html
    assert "card.id = 'client-media-card';" not in html
    assert html.count("fileInput.id = 'client-media-file';") == 1
    assert html.count("sentAtInput.id = 'client-media-sent-at';") == 1
    assert html.count("actions.id = 'client-media-actions';") == 1
    assert html.count("list.id = 'client-media-list';") == 1
    assert "legacy media upload controls were removed" in html


def test_test196_legacy_conversation_features_remain_after_media_surface_removal():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "client-edit-conversation" in html
    assert "client-save-conversation" in html
    assert "client-delete-conversation" in html
    assert "client-message-from" in html
    assert "client-message-to" in html
    assert "按时间显示" in html
    assert "显示全部" in html
