from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import PersonNotFoundError
from app.schemas.text_import import TextImportRequest, TextImportResponse
from app.services.text_import_service import TextImportService


router = APIRouter(
    prefix="/text-imports",
    tags=["text-import"],
)

service = TextImportService()


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
            )
    except PersonNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
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
