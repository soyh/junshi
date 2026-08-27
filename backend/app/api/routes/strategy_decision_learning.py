from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategy_decision_learning import StrategyDecisionLearningInputResponse
from app.services.strategy_decision_learning import StrategyDecisionLearningService


router = APIRouter(
    prefix="/persons/{person_id}/strategy-decision",
    tags=["strategy-decision"],
)

service = StrategyDecisionLearningService()


@router.get(
    "/learning-input",
    response_model=StrategyDecisionLearningInputResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategy_decision_learning_input(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_learning_input(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
