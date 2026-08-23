import sqlite3

from app.repositories.evidence import EvidenceRepository
from app.schemas.evidence import EvidenceItem


class EvidenceService:
    def __init__(self, repository: EvidenceRepository | None = None):
        self.repository = repository or EvidenceRepository()

    def get_conversation_evidence(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        conversation_id: str,
    ) -> tuple[str, str, list[EvidenceItem]] | None:
        conversation, messages, interactions = self.repository.get_conversation_evidence(
            conn, user_id, conversation_id
        )

        if conversation is None:
            return None

        evidence: list[EvidenceItem] = []

        for message in messages:
            evidence.append(
                EvidenceItem(
                    source_type="message",
                    source_id=message["id"],
                    person_id=conversation["person_id"],
                    conversation_id=conversation_id,
                    occurred_at=message["sent_at"],
                    content=message["content"],
                    metadata={
                        "sender_type": message["sender_type"],
                    },
                )
            )

        for interaction in interactions:
            evidence.append(
                EvidenceItem(
                    source_type="interaction",
                    source_id=interaction["id"],
                    person_id=interaction["person_id"],
                    conversation_id=None,
                    occurred_at=interaction["occurred_at"],
                    content=interaction["content"],
                    metadata={
                        "type": interaction["type"],
                        "relationship_id": interaction["relationship_id"],
                    },
                )
            )

        evidence.sort(
            key=lambda item: (
                item.occurred_at,
                item.source_type,
                item.source_id,
            )
        )

        return conversation["id"], conversation["person_id"], evidence
