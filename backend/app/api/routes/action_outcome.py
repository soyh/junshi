from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.action_outcome import ActionOutcomeCreate, ActionOutcomeResponse
from app.services.action_outcome import ActionOutcomeService


router = APIRouter(
    prefix="/persons/{person_id}/action-plan/outcomes",
    tags=["action-outcomes"],
)

service = ActionOutcomeService()


@router.get(
    "",
    response_model=list[ActionOutcomeResponse],
    status_code=status.HTTP_200_OK,
)
def list_action_outcomes(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        return service.list_outcomes(conn, user_id, person_id)


@router.post(
    "/{decision_id}",
    response_model=ActionOutcomeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_action_outcome(
    person_id: str,
    decision_id: str,
    payload: ActionOutcomeCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.create_outcome(
                conn,
                user_id,
                person_id,
                decision_id,
                payload.outcome,
                payload.note,
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
