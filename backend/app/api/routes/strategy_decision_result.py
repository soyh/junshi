from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategy_decision_result import (
    StrategyDecisionResultContextResponse,
    StrategyDecisionResultSynthesisResponse,
)
from app.services.strategy_decision_result import StrategyDecisionResultService
from app.services.strategy_decision_result_synthesis import StrategyDecisionResultSynthesisService


router = APIRouter(
    prefix="/persons/{person_id}/strategy-decision",
    tags=["strategy-decision"],
)

result_service = StrategyDecisionResultService()
synthesis_service = StrategyDecisionResultSynthesisService()


@router.get(
    "/result-context",
    response_model=StrategyDecisionResultContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_result_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return result_service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/result-synthesis",
    response_model=StrategyDecisionResultSynthesisResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_result_synthesis(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return synthesis_service.get_synthesis(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
