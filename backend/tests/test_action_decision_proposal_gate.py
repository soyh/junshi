from app.services.action_decision import ActionDecisionService


class FakeActionPlanService:
    def __init__(self, action_plan):
        self.action_plan = action_plan

    def get_context(self, conn, user_id, person_id):
        return {
            "person": {"id": person_id},
            "relationship": {"id": "rel-1"},
            "action_plan": self.action_plan,
            "action_constraints": {},
        }


class RecordingRepository:
    def __init__(self):
        self.calls = []

    def create(self, conn, user_id, person_id, recommendation_id, decision, note):
        self.calls.append((user_id, person_id, recommendation_id, decision, note))
        return {"id": "decision-1"}


def test_confirmed_decision_requires_proposed_action_plan():
    repository = RecordingRepository()
    service = ActionDecisionService(
        action_plan_service=FakeActionPlanService(
            [{
                "recommendation_id": "r1",
                "action": "提出轻量邀请",
                "status": "confirmed",
                "requires_user_confirmation": True,
            }]
        ),
        repository=repository,
    )

    try:
        service.create_decision(object(), "user-1", "person-1", "r1", "confirmed", None)
    except ValueError as exc:
        assert str(exc) == "recommendation is not an available proposed action"
    else:
        raise AssertionError("confirmed decision must reject non-proposed action plan")

    assert repository.calls == []


def test_confirmed_decision_requires_user_confirmation_flag_on_proposal():
    repository = RecordingRepository()
    service = ActionDecisionService(
        action_plan_service=FakeActionPlanService(
            [{
                "recommendation_id": "r1",
                "action": "提出轻量邀请",
                "status": "proposed",
                "requires_user_confirmation": False,
            }]
        ),
        repository=repository,
    )

    try:
        service.create_decision(object(), "user-1", "person-1", "r1", "confirmed", None)
    except ValueError as exc:
        assert str(exc) == "recommendation is not an available proposed action"
    else:
        raise AssertionError("proposal without confirmation gate must be rejected")

    assert repository.calls == []


def test_confirmed_decision_accepts_explicit_proposed_confirmation_required_action():
    repository = RecordingRepository()
    service = ActionDecisionService(
        action_plan_service=FakeActionPlanService(
            [{
                "recommendation_id": "r1",
                "action": "提出轻量邀请",
                "status": "proposed",
                "requires_user_confirmation": True,
            }]
        ),
        repository=repository,
    )

    result = service.create_decision(
        object(), "user-1", "person-1", "r1", "confirmed", "用户明确确认"
    )

    assert result == {"id": "decision-1"}
    assert repository.calls == [
        ("user-1", "person-1", "r1", "confirmed", "用户明确确认")
    ]
