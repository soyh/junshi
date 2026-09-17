from app.services.action_plan import ActionPlanService


class RecordingSnapshotRepository:
    def __init__(self):
        self.calls = []

    def upsert(self, conn, user_id, person_id, recommendation, action_plan, evidence):
        self.calls.append(
            {
                "user_id": user_id,
                "person_id": person_id,
                "recommendation": recommendation,
                "action_plan": action_plan,
                "evidence": evidence,
            }
        )


def test_persist_action_plan_stores_only_recommendations_that_have_proposals():
    repository = RecordingSnapshotRepository()
    service = ActionPlanService(snapshot_repository=repository)
    recommendations = [
        {
            "id": "r-valid",
            "action": "提出轻量邀请",
            "evidence_source_ids": ["e1"],
        },
        {
            "id": "r-invalid",
            "action": "没有进入 action plan 的行动",
            "evidence_source_ids": ["missing"],
        },
    ]
    action_plan = service.build_action_plan(
        recommendations,
        [{"source_id": "e1", "source_type": "message"}],
    )

    service.persist_action_plan(
        object(),
        "user-1",
        "person-1",
        recommendations,
        action_plan,
        [{"source_id": "e1", "source_type": "message"}],
    )

    assert len(repository.calls) == 1
    assert repository.calls[0]["recommendation"]["id"] == "r-valid"
    assert repository.calls[0]["action_plan"]["recommendation_id"] == "r-valid"


def test_persist_action_plan_does_not_persist_orphan_action_plan_items():
    repository = RecordingSnapshotRepository()
    service = ActionPlanService(snapshot_repository=repository)
    recommendations = [
        {
            "id": "r-valid",
            "action": "提出轻量邀请",
            "evidence_source_ids": ["e1"],
        }
    ]

    service.persist_action_plan(
        object(),
        "user-1",
        "person-1",
        recommendations,
        [
            {
                "recommendation_id": "r-orphan",
                "action": "不应被持久化",
                "evidence_source_ids": ["e1"],
                "status": "proposed",
                "requires_user_confirmation": True,
            }
        ],
        [{"source_id": "e1", "source_type": "message"}],
    )

    assert repository.calls == []
