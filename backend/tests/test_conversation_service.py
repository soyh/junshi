import pytest

from app.core.database import get_connection
from app.domain.errors import (
    ConversationNotFoundError,
    InvalidConversationStatusError,
    PersonNotFoundError,
    RelationshipNotFoundError,
)
from app.services.conversation import ConversationService
from app.services.person import PersonService
from app.services.relationship import RelationshipService


LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "11111111-1111-1111-1111-111111111111"


def test_conversation_service_crud(client):
    person_service = PersonService()
    conversation_service = ConversationService()

    with get_connection() as conn:
        person = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation测试对象",
            "ConversationA",
            "TEST-007",
        )

        person_id = person["id"]

        conversation = conversation_service.create(
            conn,
            LOCAL_USER_ID,
            person_id,
            None,
            "第一次聊天",
            "active",
        )

        conversation_id = conversation["id"]

        assert conversation["user_id"] == LOCAL_USER_ID
        assert conversation["person_id"] == person_id
        assert conversation["relationship_id"] is None
        assert conversation["title"] == "第一次聊天"
        assert conversation["status"] == "active"

        fetched = conversation_service.get(
            conn,
            LOCAL_USER_ID,
            conversation_id,
        )

        assert fetched["id"] == conversation_id

        updated = conversation_service.update(
            conn,
            LOCAL_USER_ID,
            conversation_id,
            title="第一次聊天 UPDATED",
            status="archived",
        )

        assert updated["title"] == "第一次聊天 UPDATED"
        assert updated["status"] == "archived"

        conversations = conversation_service.list(
            conn,
            LOCAL_USER_ID,
        )

        assert len(conversations) == 1
        assert conversations[0]["id"] == conversation_id

        assert conversation_service.delete(
            conn,
            LOCAL_USER_ID,
            conversation_id,
        ) is True

        with pytest.raises(
            ConversationNotFoundError,
            match="Conversation not found",
        ):
            conversation_service.get(
                conn,
                LOCAL_USER_ID,
                conversation_id,
            )


def test_conversation_service_requires_owned_person(client):
    conversation_service = ConversationService()

    with get_connection() as conn:
        with pytest.raises(
            PersonNotFoundError,
            match="Person not found",
        ):
            conversation_service.create(
                conn,
                OTHER_USER_ID,
                "00000000-0000-0000-0000-000000000099",
                None,
                "非法会话",
                "active",
            )


def test_conversation_service_validates_relationship_person(
    client,
):
    person_service = PersonService()
    relationship_service = RelationshipService()
    conversation_service = ConversationService()

    with get_connection() as conn:
        person_a = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation对象A",
            None,
            None,
        )

        person_b = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation对象B",
            None,
            None,
        )

        person_a_id = person_a["id"]
        person_b_id = person_b["id"]

        relationship_a = relationship_service.create(
            conn,
            LOCAL_USER_ID,
            person_a_id,
            "active",
            "initial_contact",
            None,
            None,
            None,
        )

        relationship_a_id = relationship_a["id"]

        with pytest.raises(
            RelationshipNotFoundError,
            match="Relationship not found",
        ):
            conversation_service.create(
                conn,
                LOCAL_USER_ID,
                person_b_id,
                relationship_a_id,
                "错误关系",
                "active",
            )


def test_conversation_service_accepts_owned_relationship(
    client,
):
    person_service = PersonService()
    relationship_service = RelationshipService()
    conversation_service = ConversationService()

    with get_connection() as conn:
        person = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation关系对象",
            None,
            None,
        )

        person_id = person["id"]

        relationship = relationship_service.create(
            conn,
            LOCAL_USER_ID,
            person_id,
            "active",
            "initial_contact",
            "长期目标",
            "当前目标",
            None,
        )

        relationship_id = relationship["id"]

        conversation = conversation_service.create(
            conn,
            LOCAL_USER_ID,
            person_id,
            relationship_id,
            "关联关系的会话",
            "active",
        )

        assert conversation["relationship_id"] == relationship_id
        assert conversation["person_id"] == person_id


def test_conversation_service_validates_status(client):
    person_service = PersonService()
    conversation_service = ConversationService()

    with get_connection() as conn:
        person = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation状态对象",
            None,
            None,
        )

        person_id = person["id"]

        with pytest.raises(
            InvalidConversationStatusError,
            match="Invalid conversation status",
        ):
            conversation_service.create(
                conn,
                LOCAL_USER_ID,
                person_id,
                None,
                "非法状态会话",
                "invalid",
            )

        conversation = conversation_service.create(
            conn,
            LOCAL_USER_ID,
            person_id,
            None,
            "正常状态会话",
            "active",
        )

        with pytest.raises(
            InvalidConversationStatusError,
            match="Invalid conversation status",
        ):
            conversation_service.update(
                conn,
                LOCAL_USER_ID,
                conversation["id"],
                status="invalid",
            )

        with pytest.raises(
            InvalidConversationStatusError,
            match="Conversation status cannot be null",
        ):
            conversation_service.update(
                conn,
                LOCAL_USER_ID,
                conversation["id"],
                status=None,
            )


def test_conversation_service_update_preserves_omitted_fields(
    client,
):
    person_service = PersonService()
    conversation_service = ConversationService()

    with get_connection() as conn:
        person = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation PATCH 对象",
            None,
            None,
        )

        conversation = conversation_service.create(
            conn,
            LOCAL_USER_ID,
            person["id"],
            None,
            "原始标题",
            "active",
        )

        updated = conversation_service.update(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
            title="新标题",
        )

        assert updated["title"] == "新标题"
        assert updated["status"] == "active"
        assert updated["relationship_id"] is None


def test_conversation_service_user_isolation(client):
    person_service = PersonService()
    conversation_service = ConversationService()

    with get_connection() as conn:
        person = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Conversation隔离对象",
            None,
            None,
        )

        conversation = conversation_service.create(
            conn,
            LOCAL_USER_ID,
            person["id"],
            None,
            "私有会话",
            "active",
        )

        conversation_id = conversation["id"]

        with pytest.raises(
            ConversationNotFoundError,
            match="Conversation not found",
        ):
            conversation_service.get(
                conn,
                OTHER_USER_ID,
                conversation_id,
            )

        assert conversation_service.list(
            conn,
            OTHER_USER_ID,
        ) == []

        with pytest.raises(
            ConversationNotFoundError,
            match="Conversation not found",
        ):
            conversation_service.delete(
                conn,
                OTHER_USER_ID,
                conversation_id,
            )
