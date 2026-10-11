import pytest

from app.core.database import get_connection
from app.domain.errors import (
    ConversationNotFoundError,
    InvalidMessageSenderTypeError,
    MessageNotFoundError,
)
from app.services.conversation import ConversationService
from app.services.message import MessageService
from app.services.person import PersonService


LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "11111111-1111-1111-1111-111111111111"


def create_conversation(
    conn,
    user_id=LOCAL_USER_ID,
):
    person_service = PersonService()
    conversation_service = ConversationService()

    person = person_service.create(
        conn,
        user_id,
        "Message Service测试对象",
        None,
        None,
    )

    return conversation_service.create(
        conn,
        user_id,
        person["id"],
        None,
        "Message测试会话",
        "active",
    )


def test_message_service_crud(client):
    service = MessageService()

    with get_connection() as conn:
        conversation = create_conversation(conn)

        message = service.create(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
            "user",
            "第一条消息",
            "2026-08-17T13:00:00+00:00",
        )

        message_id = message["id"]

        assert message["conversation_id"] == conversation["id"]
        assert message["sender_type"] == "user"
        assert message["content"] == "第一条消息"
        assert message["sent_at"] == (
            "2026-08-17T13:00:00+00:00"
        )

        assert service.get(
            conn,
            LOCAL_USER_ID,
            message_id,
        )["content"] == "第一条消息"

        messages = service.list(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
        )

        assert len(messages) == 1
        assert messages[0]["id"] == message_id

        assert service.delete(
            conn,
            LOCAL_USER_ID,
            message_id,
        ) is True

        with pytest.raises(
            MessageNotFoundError,
            match="Message not found",
        ):
            service.get(
                conn,
                LOCAL_USER_ID,
                message_id,
            )


def test_message_service_requires_existing_conversation(client):
    service = MessageService()

    with get_connection() as conn:
        with pytest.raises(
            ConversationNotFoundError,
            match="Conversation not found",
        ):
            service.create(
                conn,
                LOCAL_USER_ID,
                "00000000-0000-0000-0000-000000000099",
                "user",
                "不存在会话的消息",
                None,
            )


def test_message_service_rejects_invalid_sender_type(client):
    service = MessageService()

    with get_connection() as conn:
        conversation = create_conversation(conn)

        with pytest.raises(
            InvalidMessageSenderTypeError,
            match="Invalid message sender type",
        ):
            service.create(
                conn,
                LOCAL_USER_ID,
                conversation["id"],
                "invalid",
                "非法发送者",
                None,
            )


def test_message_service_user_isolation(client):
    service = MessageService()

    with get_connection() as conn:
        conversation = create_conversation(conn)

        message = service.create(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
            "user",
            "私有消息",
            None,
        )

        message_id = message["id"]

        with pytest.raises(
            MessageNotFoundError,
            match="Message not found",
        ):
            service.get(
                conn,
                OTHER_USER_ID,
                message_id,
            )

        with pytest.raises(
            ConversationNotFoundError,
            match="Conversation not found",
        ):
            service.list(
                conn,
                OTHER_USER_ID,
                conversation["id"],
            )

        with pytest.raises(
            MessageNotFoundError,
            match="Message not found",
        ):
            service.delete(
                conn,
                OTHER_USER_ID,
                message_id,
            )


def test_message_service_orders_by_sent_at(client):
    service = MessageService()

    with get_connection() as conn:
        conversation = create_conversation(conn)

        service.create(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
            "assistant",
            "第二条",
            "2026-08-17T13:02:00+00:00",
        )

        service.create(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
            "user",
            "第一条",
            "2026-08-17T13:01:00+00:00",
        )

        messages = service.list(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
        )

        assert [item["content"] for item in messages] == [
            "第一条",
            "第二条",
        ]


def test_message_service_supports_all_sender_types(client):
    service = MessageService()

    with get_connection() as conn:
        conversation = create_conversation(conn)

        for sender_type in (
            "user",
            "person",
            "system",
            "assistant",
        ):
            message = service.create(
                conn,
                LOCAL_USER_ID,
                conversation["id"],
                sender_type,
                f"{sender_type}消息",
                None,
            )

            assert message["sender_type"] == sender_type

        messages = service.list(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
        )

        assert len(messages) == 4
