from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategy_decision_learning_bridge import StrategyDecisionLearningBridgeResponse
from app.services.strategy_decision_learning_bridge import StrategyDecisionLearningBridgeService


router = APIRouter(
    prefix="/persons/{person_id}/learning-strategy/strategy-decision",
    tags=["learning-strategy"],
)

service = StrategyDecisionLearningBridgeService()


@router.get(
    "/context",
    response_model=StrategyDecisionLearningBridgeResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_learning_bridge(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
