from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.services.person_merge import (
    PersonMergeService,
    PersonNotFoundForMerge,
    SamePersonMerge,
)

router = APIRouter(prefix="/persons", tags=["person-merge"])

service = PersonMergeService()


class MergeRequest(BaseModel):
    source_person_id: str = Field(min_length=1, max_length=64)


@router.post("/{person_id}/merge", status_code=status.HTTP_200_OK)
def merge_person(
    person_id: str,
    payload: MergeRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return service.merge(conn, user_id, person_id, payload.source_person_id)
    except SamePersonMerge as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except PersonNotFoundForMerge as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
