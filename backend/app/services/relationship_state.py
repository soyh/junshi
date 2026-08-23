import sqlite3

from app.domain.errors import PersonNotFoundError
from app.repositories.relationship_state import RelationshipStateRepository


class RelationshipStateService:
    def __init__(self, repository: RelationshipStateRepository | None = None):
        self.repository = repository or RelationshipStateRepository()

    def get_state(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> dict:
        person, relationship, messages, interactions = self.repository.get_state(
            conn,
            user_id,
            person_id,
        )

        if person is None:
            raise PersonNotFoundError("Person not found")

        if relationship is None:
            raise ValueError("Relationship not found")

        evidence: list[dict] = []

        for message in messages:
            evidence.append(
                {
                    "source_type": "message",
                    "source_id": message["id"],
                    "person_id": person_id,
                    "conversation_id": message["conversation_id"],
                    "occurred_at": message["sent_at"],
                    "content": message["content"],
                    "metadata": {"sender_type": message["sender_type"]},
                }
            )

        for interaction in interactions:
            evidence.append(
                {
                    "source_type": "interaction",
                    "source_id": interaction["id"],
                    "person_id": person_id,
                    "conversation_id": None,
                    "occurred_at": interaction["occurred_at"],
                    "content": interaction["content"],
                    "metadata": {
                        "type": interaction["type"],
                        "relationship_id": interaction["relationship_id"],
                    },
                }
            )

        evidence.sort(
            key=lambda item: (
                item["occurred_at"],
                item["source_type"],
                item["source_id"],
            )
        )

        current_state = {
            "status": relationship["status"],
            "stage": relationship["stage"],
            "long_term_goal": relationship["long_term_goal"],
            "current_goal": relationship["current_goal"],
        }

        return {
            "person": dict(person),
            "relationship": dict(relationship),
            "current_state": current_state,
            "evidence": evidence,
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
        }
