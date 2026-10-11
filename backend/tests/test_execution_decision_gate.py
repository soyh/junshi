from app.services.strategy_decision_execution import StrategyDecisionExecutionService


class RecordingRepository:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def get(self, conn, user_id, person_id, decision_id):
        return self.decision

    def create(self, conn, user_id, person_id, decision_id, executed_at, note):
        self.calls.append((user_id, person_id, decision_id, executed_at, note))
        return {"id": "execution-1"}


class EmptyRepository:
    def get_by_decision(self, conn, user_id, person_id, decision_id):
        return None


def test_execution_rejects_rejected_decision():
    repository = RecordingRepository({"id": "d1", "decision": "rejected"})
    service = StrategyDecisionExecutionService(
        decision_repository=repository,
        execution_repository=EmptyRepository(),
        outcome_repository=EmptyRepository(),
    )

    try:
        service.create_execution(object(), "u1", "p1", "d1", None, None)
    except ValueError as exc:
        assert str(exc) == "execution requires a confirmed action decision"
    else:
        raise AssertionError("rejected decisions must never execute")

    assert repository.calls == []


def test_execution_accepts_only_confirmed_decision():
    decision_repository = RecordingRepository({"id": "d1", "decision": "confirmed"})
    execution_repository = RecordingRepository(None)
    execution_repository.get_by_decision = lambda conn, user_id, person_id, decision_id: None
    service = StrategyDecisionExecutionService(
        decision_repository=decision_repository,
        execution_repository=execution_repository,
        outcome_repository=EmptyRepository(),
    )

    result = service.create_execution(object(), "u1", "p1", "d1", None, "explicit execution")

    assert result == {"id": "execution-1"}
    assert execution_repository.calls == [("u1", "p1", "d1", None, "explicit execution")]


def test_execution_is_blocked_once_outcome_exists():
    decision_repository = RecordingRepository({"id": "d1", "decision": "confirmed"})
    outcome_repository = EmptyRepository()
    outcome_repository.get_by_decision = lambda conn, user_id, person_id, decision_id: {"id": "o1"}
    execution_repository = EmptyRepository()
    execution_repository.get_by_decision = lambda conn, user_id, person_id, decision_id: None

    service = StrategyDecisionExecutionService(
        decision_repository=decision_repository,
        execution_repository=execution_repository,
        outcome_repository=outcome_repository,
    )

    try:
        service.create_execution(object(), "u1", "p1", "d1", None, None)
    except ValueError as exc:
        assert str(exc) == "execution is not available after an action outcome"
    else:
        raise AssertionError("execution must not be recreated after outcome")

    assert decision_repository.calls == []
