from fastapi import APIRouter, Depends, Query

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.timeline import TimelineResponse
from app.services.timeline import TimelineService

router = APIRouter(prefix="/persons/{person_id}/timeline", tags=["timeline"])

service = TimelineService()


@router.get("", response_model=TimelineResponse)
def get_person_timeline(
    person_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        items, total = service.list(
            conn,
            user_id,
            person_id,
            limit,
            offset,
        )

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "total": total,
    }
