from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.action_feedback_learning_synthesis import ActionFeedbackLearningSynthesisResponse
from app.services.action_feedback_learning_synthesis import ActionFeedbackLearningSynthesisService


router = APIRouter(
    prefix="/persons/{person_id}/action-plan/feedback",
    tags=["action-feedback"],
)

service = ActionFeedbackLearningSynthesisService()


@router.get(
    "/learning-synthesis",
    response_model=ActionFeedbackLearningSynthesisResponse,
    status_code=status.HTTP_200_OK,
)
def get_action_feedback_learning_synthesis(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_synthesis(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
