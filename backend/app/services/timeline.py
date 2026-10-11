import sqlite3

from app.domain.errors import PersonNotFoundError
from app.repositories.person import PersonRepository
from app.repositories.timeline import TimelineRepository


class TimelineService:
    def __init__(
        self,
        repository: TimelineRepository | None = None,
        person_repository: PersonRepository | None = None,
    ):
        self.repository = repository or TimelineRepository()
        self.person_repository = person_repository or PersonRepository()

    def _validate_person(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> None:
        person = self.person_repository.get(
            conn,
            user_id,
            person_id,
        )

        if person is None:
            raise PersonNotFoundError("Person not found")

    def list(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]:
        self._validate_person(conn, user_id, person_id)

        rows = self.repository.list_events(
            conn,
            user_id,
            person_id,
            limit,
            offset,
        )
        total = self.repository.count_events(
            conn,
            user_id,
            person_id,
        )

        events = []
        for row in rows:
            source_type = row["source_type"]
            source_id = row["source_id"]

            if source_type == "interaction":
                interaction_type = row["interaction_type"]
                event_type = f"interaction.{interaction_type}"
                title = interaction_type.replace("_", " ").title()
                metadata = {
                    "interaction_type": interaction_type,
                }
                if row["conversation_id"] is not None:
                    metadata["conversation_id"] = row["conversation_id"]
            elif source_type == "conversation":
                event_type = "conversation.created"
                title = "Conversation created"
                metadata = {
                    "status": row["conversation_status"],
                }
            else:
                sender_type = row["sender_type"]
                event_type = f"message.{sender_type}"
                title = "Message"
                metadata = {
                    "conversation_id": row["conversation_id"],
                    "sender_type": sender_type,
                }

            events.append(
                {
                    "id": f"{source_type}:{source_id}",
                    "user_id": row["user_id"],
                    "person_id": row["person_id"],
                    "event_type": event_type,
                    "occurred_at": row["occurred_at"],
                    "source_type": source_type,
                    "source_id": source_id,
                    "title": title,
                    "content": (
                        row["content"]
                        if source_type != "conversation"
                        else row["conversation_title"]
                    ),
                    "metadata": metadata,
                }
            )

        return events, total
