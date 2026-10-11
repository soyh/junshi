from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import ConversationNotFoundError
from app.schemas.media_attachment import (
    MediaAttachmentAnalysisResponse,
    MediaAttachmentResponse,
)
from app.services.media_attachment import (
    MediaAnalysisInProgressError,
    MediaAttachmentError,
)
from app.services.media_chat_time import TimedMediaAttachmentService


router = APIRouter(tags=["media"])
service = TimedMediaAttachmentService()


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


def _fail_media_analysis_claim_best_effort(
    user_id: str,
    attachment_id: str,
    claim_token: str | None,
) -> None:
    if not claim_token:
        return
    try:
        with get_connection() as conn:
            service.fail_claimed_analysis(
                conn,
                user_id,
                attachment_id,
                claim_token,
            )
    except Exception:
        # The original analysis error is more useful to the caller. A claim also
        # has a bounded lease so a crashed cleanup cannot block retries forever.
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
    claim_token: str | None = None
    try:
        with get_connection() as conn:
            claimed_row, claim_token, existing_message_id = service.claim_analysis(
                conn,
                user_id,
                attachment_id,
            )

        if existing_message_id:
            return {
                "attachment": _row(claimed_row),
                "evidence_message_id": existing_message_id,
            }

        if not claim_token:
            raise MediaAnalysisInProgressError("media analysis claim unavailable")

        try:
            # Provider configuration is read in a short transaction. The external
            # vision request itself runs after that transaction has closed.
            with get_connection() as conn:
                media_row, provider = service.prepare_claimed_analysis(
                    conn,
                    user_id,
                    attachment_id,
                    claim_token,
                )

            analysis_text = service.analyze_claimed_media(provider, media_row)

            with get_connection() as conn:
                updated, evidence_message_id = service.complete_claimed_analysis(
                    conn,
                    user_id,
                    attachment_id,
                    claim_token,
                    analysis_text,
                )
        except Exception:
            _fail_media_analysis_claim_best_effort(
                user_id,
                attachment_id,
                claim_token,
            )
            raise

    except MediaAnalysisInProgressError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except MediaAttachmentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "attachment": _row(updated),
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
