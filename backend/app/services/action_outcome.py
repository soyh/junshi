import sqlite3

from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_outcome import ActionOutcomeRepository


class ActionOutcomeService:
    def __init__(
        self,
        decision_repository: ActionDecisionRepository | None = None,
        outcome_repository: ActionOutcomeRepository | None = None,
    ):
        self.decision_repository = decision_repository or ActionDecisionRepository()
        self.outcome_repository = outcome_repository or ActionOutcomeRepository()

    def list_outcomes(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> list[dict]:
        return self.outcome_repository.list_for_person(conn, user_id, person_id)

    def create_outcome(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        person_id: str,
        decision_id: str,
        outcome: str,
        note: str | None,
    ) -> dict:
        decision = self.decision_repository.get(conn, user_id, person_id, decision_id)
        if decision is None:
            raise ValueError("action decision not found")
        if decision["decision"] != "confirmed":
            raise ValueError("outcome requires a confirmed action decision")

        return self.outcome_repository.create(
            conn,
            user_id,
            person_id,
            decision_id,
            outcome,
            note,
        )
