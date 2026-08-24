from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.action_feedback_learning import ActionFeedbackLearningResponse
from app.services.action_feedback_learning import ActionFeedbackLearningService


router = APIRouter(
    prefix="/persons/{person_id}/action-plan/feedback",
    tags=["action-feedback"],
)

service = ActionFeedbackLearningService()


@router.get(
    "/learning-input",
    response_model=ActionFeedbackLearningResponse,
    status_code=status.HTTP_200_OK,
)
def get_action_feedback_learning_input(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_learning_input(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
