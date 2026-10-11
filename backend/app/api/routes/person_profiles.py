from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.person_profile import PersonProfileResponse
from app.services.person_profile import PersonProfileService


router = APIRouter(prefix="/persons", tags=["person-profile"])

service = PersonProfileService()


@router.get(
    "/{person_id}/profile",
    response_model=PersonProfileResponse,
)
def get_person_profile(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        profile = service.get(conn, user_id, person_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    return profile
