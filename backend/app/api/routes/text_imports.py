from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import ConversationNotFoundError, PersonNotFoundError
from app.schemas.text_import import TextImportRequest, TextImportResponse, NamedChatPreviewRequest
from app.services.named_chat_parser import parse_named_chat
from fastapi.responses import JSONResponse
from app.services.text_import_service import TextImportService


router = APIRouter(
    prefix="/text-imports",
    tags=["text-import"],
)

service = TextImportService()


@router.post("/preview")
def preview_named_chat(payload: NamedChatPreviewRequest,
                       user_id: str = Depends(get_current_user_id)):
    try:
        return JSONResponse(parse_named_chat(payload.text, payload.utc_offset),
                            headers={"Cache-Control": "no-store"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "",
    response_model=TextImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_text(
    payload: TextImportRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conversation, messages, candidates = service.import_text(
                conn,
                user_id,
                payload.person_id,
                payload.text,
                payload.title,
                payload.auto_sort_by_sent_at,
                payload.conversation_id,
                payload.source_format,
                payload.self_name,
                payload.other_name,
                payload.utc_offset,
            )
    except PersonNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        ) from exc
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return TextImportResponse(
        conversation_id=conversation["id"],
        person_id=payload.person_id,
        message_ids=[message["id"] for message in messages],
        imported_count=len(messages),
        candidates=candidates,
    )
