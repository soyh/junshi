from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.relationship_state import RelationshipStateResponse
from app.services.relationship_state import RelationshipStateService


router = APIRouter(
    prefix="/persons/{person_id}/relationship-analysis",
    tags=["relationship-analysis"],
)

service = RelationshipStateService()


@router.get(
    "/state",
    response_model=RelationshipStateResponse,
    status_code=status.HTTP_200_OK,
)
def get_relationship_state(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_state(
                conn,
                user_id,
                person_id,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
