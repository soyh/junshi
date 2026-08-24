from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategy_decision_confirmation import (
    StrategyDecisionConfirmationCreate,
    StrategyDecisionConfirmationCreatedResponse,
    StrategyDecisionConfirmationResponse,
)
from app.services.strategy_decision_confirmation import StrategyDecisionConfirmationService


router = APIRouter(
    prefix="/persons/{person_id}/strategy-decision",
    tags=["strategy-decision"],
)

service = StrategyDecisionConfirmationService()


@router.get(
    "/confirmation-context",
    response_model=StrategyDecisionConfirmationResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_confirmation_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/confirmations",
    response_model=StrategyDecisionConfirmationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_strategy_decision_confirmation(
    person_id: str,
    payload: StrategyDecisionConfirmationCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.create_confirmation(
                conn,
                user_id,
                person_id,
                payload.recommendation_id,
                payload.decision,
                payload.note,
            )
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if "person" in detail or "relationship" in detail
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=detail) from exc
