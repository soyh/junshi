import sqlite3

from app.domain.errors import PersonNotFoundError
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.repositories.person import PersonRepository
from app.schemas.text_import import TextImportCandidate
from app.services.text_import_parser import parse_text, validate_candidates


class TextImportService:
    def __init__(
        self,
        person_repository: PersonRepository | None = None,
        conversation_repository: ConversationRepository | None = None,
        message_repository: MessageRepository | None = None,
    ):
        self.person_repository = person_repository or PersonRepository()
        self.conversation_repository = (
            conversation_repository or ConversationRepository()
        )
        self.message_repository = message_repository or MessageRepository()

    def import_text(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        text: str,
        title: str | None,
    ) -> tuple[sqlite3.Row, list[sqlite3.Row], list[TextImportCandidate]]:
        person = self.person_repository.get(conn, user_id, person_id)
        if person is None:
            raise PersonNotFoundError("Person not found")

        candidates = validate_candidates(parse_text(text))

        conversation = self.conversation_repository.create(
            conn,
            user_id,
            person_id,
            None,
            title,
            "active",
        )

        messages: list[sqlite3.Row] = []
        for candidate in candidates:
            messages.append(
                self.message_repository.create(
                    conn,
                    user_id,
                    conversation["id"],
                    candidate.sender_type,
                    candidate.content,
                    candidate.sent_at,
                )
            )

        return conversation, messages, candidates
