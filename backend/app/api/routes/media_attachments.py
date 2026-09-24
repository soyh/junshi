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


def _cleanup_unreferenced_blob_best_effort(user_id: str, storage_path: str | None) -> None:
    if not storage_path:
        return
    try:
        with get_connection() as conn:
            service.cleanup_unreferenced_blob(conn, user_id, storage_path)
    except Exception:
        # Canonical database state already won. A leftover blob is recoverable and
        # safer than converting a cleanup failure into a misleading API failure.
        pass


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
    row = None
    try:
        content = await file.read()
        try:
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
        except Exception:
            if row is not None:
                _cleanup_unreferenced_blob_best_effort(
                    user_id,
                    row["storage_path"],
                )
            raise
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
    cleanup_path = None
    try:
        with get_connection() as conn:
            cleanup_path = service.delete(
                conn,
                user_id,
                attachment_id,
                defer_blob_cleanup=True,
            )
    except MediaAttachmentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # This runs only after get_connection() has committed successfully. Re-check
    # references in a fresh transaction before touching the physical blob.
    _cleanup_unreferenced_blob_best_effort(user_id, cleanup_path)
