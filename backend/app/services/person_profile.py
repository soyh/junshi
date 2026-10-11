import sqlite3

from app.repositories.person_profile import PersonProfileRepository
from app.schemas.person_profile import PersonProfileResponse


class PersonProfileService:
    def __init__(self, repository: PersonProfileRepository | None = None):
        self.repository = repository or PersonProfileRepository()

    def get(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
    ) -> PersonProfileResponse | None:
        person = self.repository.get(conn, user_id, person_id)
        if person is None:
            return None

        relationships = self.repository.list_relationships(
            conn,
            user_id,
            person_id,
        )
        statistics = self.repository.get_statistics(
            conn,
            user_id,
            person_id,
        )
        latest_interaction = self.repository.get_latest_interaction(
            conn,
            user_id,
            person_id,
        )

        return PersonProfileResponse(
            person=dict(person),
            relationships=[dict(row) for row in relationships],
            statistics={
                "relationship_count": statistics["relationship_count"],
                "conversation_count": statistics["conversation_count"],
                "interaction_count": statistics["interaction_count"],
                "message_count": statistics["message_count"],
            },
            latest_interaction=(
                dict(latest_interaction)
                if latest_interaction is not None
                else None
            ),
        )
