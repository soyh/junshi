import pytest

from app.core.database import get_connection
from app.services.person import PersonService
from app.services.relationship import RelationshipService


LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "11111111-1111-1111-1111-111111111111"


def test_person_service_crud(client):
    service = PersonService()

    with get_connection() as conn:
        person = service.create(
            conn,
            LOCAL_USER_ID,
            "Service测试对象",
            "ServiceA",
            "TEST-004",
        )

        person_id = person["id"]

        assert service.get(
            conn,
            LOCAL_USER_ID,
            person_id,
        )["name"] == "Service测试对象"

        updated = service.update(
            conn,
            LOCAL_USER_ID,
            person_id,
            None,
            None,
            "TEST-004 UPDATED",
        )

        assert updated["notes"] == "TEST-004 UPDATED"

        assert service.get(
            conn,
            OTHER_USER_ID,
            person_id,
        ) is None

        assert service.delete(
            conn,
            LOCAL_USER_ID,
            person_id,
        ) is True

        assert service.get(
            conn,
            LOCAL_USER_ID,
            person_id,
        ) is None


def test_relationship_service_requires_owned_person(client):
    person_service = PersonService()
    relationship_service = RelationshipService()

    with get_connection() as conn:
        person = person_service.create(
            conn,
            LOCAL_USER_ID,
            "Service关系对象",
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
            "TEST-004",
        )

        assert relationship["person_id"] == person_id

        with pytest.raises(ValueError, match="Person not found"):
            relationship_service.create(
                conn,
                OTHER_USER_ID,
                person_id,
                "active",
                "initial_contact",
                None,
                None,
                None,
            )
