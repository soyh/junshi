from app.services.strategy_decision_execution import StrategyDecisionExecutionService


class ScopedDecisionRepository:
    def __init__(self):
        self.decisions = {
            ("u1", "p1", "d1"): {"id": "d1", "decision": "confirmed"},
            ("u2", "p1", "d1"): {"id": "d1", "decision": "confirmed"},
        }
        self.calls = []

    def get(self, conn, user_id, person_id, decision_id):
        return self.decisions.get((user_id, person_id, decision_id))


class EmptyExecutionRepository:
    def __init__(self):
        self.calls = []

    def get_by_decision(self, conn, user_id, person_id, decision_id):
        return None

    def create(self, conn, user_id, person_id, decision_id, executed_at, note):
        self.calls.append((user_id, person_id, decision_id))
        return {"id": "execution-1", "user_id": user_id, "person_id": person_id}


class EmptyOutcomeRepository:
    def get_by_decision(self, conn, user_id, person_id, decision_id):
        return None


def test_execution_uses_exact_user_and_person_scope_for_decision():
    decision_repository = ScopedDecisionRepository()
    execution_repository = EmptyExecutionRepository()
    service = StrategyDecisionExecutionService(
        decision_repository=decision_repository,
        execution_repository=execution_repository,
        outcome_repository=EmptyOutcomeRepository(),
    )

    result = service.create_execution(object(), "u1", "p1", "d1", None, None)

    assert result["user_id"] == "u1"
    assert result["person_id"] == "p1"
    assert execution_repository.calls == [("u1", "p1", "d1")]


def test_execution_does_not_cross_person_scope():
    decision_repository = ScopedDecisionRepository()
    execution_repository = EmptyExecutionRepository()
    service = StrategyDecisionExecutionService(
        decision_repository=decision_repository,
        execution_repository=execution_repository,
        outcome_repository=EmptyOutcomeRepository(),
    )

    try:
        service.create_execution(object(), "u1", "p2", "d1", None, None)
    except ValueError as exc:
        assert str(exc) == "action decision not found"
    else:
        raise AssertionError("execution must not cross person scope")

    assert execution_repository.calls == []
