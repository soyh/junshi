from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.strategic_reply import StrategicReplyContextResponse
from app.services.strategic_reply_learning_strategy_bridge import (
    StrategicReplyLearningStrategyBridgeService,
)


router = APIRouter(
    prefix="/persons/{person_id}/strategic-reply",
    tags=["strategic-reply"],
)

service = StrategicReplyLearningStrategyBridgeService()


@router.get(
    "/context",
    response_model=StrategicReplyContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_strategic_reply_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
