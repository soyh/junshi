import sqlite3

from app.repositories.action_plan_snapshot import ActionPlanSnapshotRepository
from app.services.action_plan import ActionPlanService


USER_A = "00000000-0000-0000-0000-000000000001"
USER_B = "00000000-0000-0000-0000-000000000002"
PERSON_ID = "person-shared-test"
RECOMMENDATION_ID = "recommendation-shared-test"


def snapshot_data(action: str):
    recommendation = {
        "id": RECOMMENDATION_ID,
        "action": action,
        "evidence_source_ids": ["message-shared"],
    }
    evidence = [{
        "source_id": "message-shared",
        "source_type": "message",
        "content": "scope-isolated evidence",
    }]
    action_plan = ActionPlanService.build_action_plan([recommendation], evidence)[0]
    return recommendation, action_plan, evidence


def create_table(conn):
    conn.execute(
        """
        CREATE TABLE action_plan_snapshots (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            recommendation_id TEXT NOT NULL,
            recommendation_json TEXT NOT NULL,
            action_plan_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, person_id, recommendation_id)
        )
        """
    )


def test_action_plan_snapshots_are_scoped_by_user_and_person():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_table(conn)

    repository = ActionPlanSnapshotRepository()
    recommendation_a, action_plan_a, evidence = snapshot_data("只对用户 A 保持低压力互动")
    recommendation_b, action_plan_b, _ = snapshot_data("只对用户 B 保持低压力互动")

    repository.upsert(conn, USER_A, PERSON_ID, recommendation_a, action_plan_a, evidence)
    repository.upsert(conn, USER_B, PERSON_ID, recommendation_b, action_plan_b, evidence)

    snapshots_a = repository.list_for_person(conn, USER_A, PERSON_ID)
    snapshots_b = repository.list_for_person(conn, USER_B, PERSON_ID)

    assert len(snapshots_a) == 1
    assert len(snapshots_b) == 1
    assert snapshots_a[0]["recommendation"]["action"] == "只对用户 A 保持低压力互动"
    assert snapshots_b[0]["recommendation"]["action"] == "只对用户 B 保持低压力互动"


def test_snapshot_repository_never_returns_other_user_or_person_snapshot():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_table(conn)

    repository = ActionPlanSnapshotRepository()
    recommendation, action_plan, evidence = snapshot_data("用户 A 专属行动")
    repository.upsert(conn, USER_A, PERSON_ID, recommendation, action_plan, evidence)

    assert repository.list_for_person(conn, USER_B, PERSON_ID) == []
    assert repository.list_for_person(conn, USER_A, "other-person") == []
