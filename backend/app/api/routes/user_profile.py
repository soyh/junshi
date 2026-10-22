from fastapi import APIRouter, Depends

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.user_profile import UserProfilePayload, UserProfileResponse
from app.services.reply_templates import as_payload as reply_templates
from app.services.user_profile import UserProfileService


router = APIRouter(prefix="/settings", tags=["user-profile"])

service = UserProfileService()


@router.get("/profile", response_model=UserProfileResponse)
def read_profile(user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        return service.get(conn, user_id)


@router.put("/profile", response_model=UserProfileResponse)
def write_profile(
    payload: UserProfilePayload,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        return service.save(conn, user_id, payload)


@router.get("/reply-templates")
def list_reply_templates():
    """Ready-made rule text; the user still edits whatever they pick."""
    return {"templates": reply_templates()}
