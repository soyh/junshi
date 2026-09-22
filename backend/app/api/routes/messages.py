from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import (
    ConversationNotFoundError,
    InvalidMessageSenderTypeError,
    MessageNotFoundError,
)
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)
from app.services.message import MessageService


router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)

service = MessageService()


def row_to_dict(row):
    return dict(row) if row is not None else None


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    payload: MessageCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            message = service.create(
                conn,
                user_id,
                payload.conversation_id,
                payload.sender_type,
                payload.content,
                payload.sent_at,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    except InvalidMessageSenderTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return row_to_dict(message)


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
)
def get_message(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            message = service.get(
                conn,
                user_id,
                message_id,
            )
    except MessageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        ) from exc

    return row_to_dict(message)


@router.patch(
    "/{message_id}",
    response_model=MessageResponse,
)
def update_message(
    message_id: str,
    payload: MessageUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            message = service.update(
                conn,
                user_id,
                message_id,
                sender_type=payload.sender_type,
                content=payload.content,
                sent_at=payload.sent_at,
                fields_set=set(payload.model_fields_set),
            )
    except MessageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        ) from exc
    except (InvalidMessageSenderTypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return row_to_dict(message)


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_message(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete(
                conn,
                user_id,
                message_id,
            )
    except MessageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        ) from exc


conversation_messages_router = APIRouter(
    prefix="/conversations",
    tags=["messages"],
)


@conversation_messages_router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def list_conversation_messages(
    conversation_id: str,
    from_time: str | None = Query(default=None, alias="from"),
    to_time: str | None = Query(default=None, alias="to"),
    before: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            messages = service.list_window(
                conn,
                user_id,
                conversation_id,
                from_time=from_time,
                to_time=to_time,
                before=before,
                limit=limit,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    return [row_to_dict(message) for message in messages]
