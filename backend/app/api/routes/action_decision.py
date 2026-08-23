from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.action_decision import (
    ActionDecisionContextResponse,
    ActionDecisionCreate,
    ActionDecisionResponse,
)
from app.services.action_decision import ActionDecisionService


router = APIRouter(
    prefix="/persons/{person_id}/action-plan/decisions",
    tags=["action-decisions"],
)

service = ActionDecisionService()


@router.get(
    "/context",
    response_model=ActionDecisionContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_action_decision_context(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "",
    response_model=ActionDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_action_decision(
    person_id: str,
    payload: ActionDecisionCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.create_decision(
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
