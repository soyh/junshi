from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.learning_strategy import LearningStrategyContextResponse
from app.services.learning_strategy_context import LearningStrategyContextService


router = APIRouter(
    prefix="/persons/{person_id}/learning-strategy",
    tags=["learning-strategy"],
)

service = LearningStrategyContextService()


@router.get(
    "/context",
    response_model=LearningStrategyContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_learning_strategy_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
