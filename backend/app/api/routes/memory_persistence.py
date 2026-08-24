from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.memory_persistence import MemoryPersistResponse
from app.services.memory_persistence import MemoryPersistenceService


router = APIRouter(
    prefix="/persons/{person_id}/memory-updates",
    tags=["memory-updates"],
)

service = MemoryPersistenceService()


@router.post(
    "/{candidate_id}/persist",
    response_model=MemoryPersistResponse,
    status_code=status.HTTP_201_CREATED,
)
def persist_memory_update(
    person_id: str,
    candidate_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.persist_candidate(conn, user_id, person_id, candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
