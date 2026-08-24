from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.memory_learning_synthesis import MemoryLearningSynthesisResponse
from app.services.memory_learning_synthesis import MemoryLearningSynthesisService


router = APIRouter(
    prefix="/persons/{person_id}/memory-updates",
    tags=["memory-updates"],
)

service = MemoryLearningSynthesisService()


@router.get(
    "/learning-synthesis",
    response_model=MemoryLearningSynthesisResponse,
    status_code=status.HTTP_200_OK,
)
def get_memory_learning_synthesis(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.get_context(conn, user_id, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
