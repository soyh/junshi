from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.services.person_conversation import (
    ConversationNotOwned,
    PersonConversationService,
    PersonNotFoundForConversation,
)

router = APIRouter(prefix="/persons", tags=["person-conversation"])

service = PersonConversationService()


class ConsolidateRequest(BaseModel):
    target_conversation_id: str | None = Field(default=None, max_length=64)


@router.get("/{person_id}/primary-conversation")
def get_primary_conversation(person_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return dict(service.ensure_primary(conn, user_id, person_id))
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None


@router.get("/{person_id}/consolidate-preview")
def preview_consolidation(
    person_id: str,
    target_conversation_id: str | None = Query(default=None, max_length=64),
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.preview(conn, user_id, person_id, target_conversation_id)
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except ConversationNotOwned as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None


@router.post("/{person_id}/consolidate")
def consolidate_conversations(
    person_id: str,
    payload: ConsolidateRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return service.consolidate(conn, user_id, person_id, payload.target_conversation_id)
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except ConversationNotOwned as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
