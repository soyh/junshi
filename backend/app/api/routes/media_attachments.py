from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import ConversationNotFoundError
from app.schemas.media_attachment import (
    MediaAttachmentAnalysisResponse,
    MediaAttachmentResponse,
)
from app.services.media_attachment import MediaAttachmentError, MediaAttachmentService


router = APIRouter(tags=["media"])
service = MediaAttachmentService()


def _row(row):
    return dict(row) if row is not None else None


@router.post(
    "/conversations/{conversation_id}/media",
    response_model=MediaAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    sent_at: str | None = Form(default=None),
    user_id: str = Depends(get_current_user_id),
):
    try:
        content = await file.read()
        with get_connection() as conn:
            row = service.create(
                conn,
                user_id=user_id,
                conversation_id=conversation_id,
                original_filename=file.filename or "upload",
                mime_type=file.content_type or "application/octet-stream",
                content=content,
                sent_at=sent_at,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc
    except MediaAttachmentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _row(row)


@router.get(
    "/conversations/{conversation_id}/media",
    response_model=list[MediaAttachmentResponse],
)
def list_media_attachments(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            rows = service.list_for_conversation(conn, user_id, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc
    return [_row(row) for row in rows]


@router.post(
    "/media/{attachment_id}/analyze",
    response_model=MediaAttachmentAnalysisResponse,
)
def analyze_media_attachment(
    attachment_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            row, evidence_message_id = service.analyze(conn, user_id, attachment_id)
    except MediaAttachmentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "attachment": _row(row),
        "evidence_message_id": evidence_message_id,
    }


@router.delete(
    "/media/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_media_attachment(
    attachment_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete(conn, user_id, attachment_id)
    except MediaAttachmentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
