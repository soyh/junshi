from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategy_decision import StrategyDecisionContextResponse
from app.services.strategy_decision import StrategyDecisionContextService


router = APIRouter(
    prefix="/persons/{person_id}/strategy-decision",
    tags=["strategy-decision"],
)

service = StrategyDecisionContextService()


@router.get(
    "/context",
    response_model=StrategyDecisionContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
