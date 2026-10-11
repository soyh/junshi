from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategy_decision_execution import (
    StrategyDecisionExecutionCreate,
    StrategyDecisionExecutionResponse,
    StrategyDecisionExecutionContextResponse,
)
from app.services.strategy_decision_execution import StrategyDecisionExecutionService


router = APIRouter(
    prefix="/persons/{person_id}/strategy-decision",
    tags=["strategy-decision"],
)

service = StrategyDecisionExecutionService()


@router.get(
    "/execution-context",
    response_model=StrategyDecisionExecutionContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_execution_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/executions/{decision_id}",
    response_model=StrategyDecisionExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_strategy_decision_execution(
    person_id: str,
    decision_id: str,
    payload: StrategyDecisionExecutionCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.create_execution(
                conn,
                user_id,
                person_id,
                decision_id,
                payload.executed_at.isoformat() if payload.executed_at else None,
                payload.note,
            )
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_404_NOT_FOUND if detail == "action decision not found" else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=detail) from exc
