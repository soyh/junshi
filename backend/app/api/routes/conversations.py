from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.core.sentinels import UNSET
from app.domain.errors import (
    ConversationNotFoundError,
    InvalidConversationStatusError,
    PersonNotFoundError,
    RelationshipNotFoundError,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation import ConversationService


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)

service = ConversationService()


def row_to_dict(row):
    return dict(row) if row is not None else None


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conversation = service.create(
                conn,
                user_id,
                payload.person_id,
                payload.relationship_id,
                payload.title,
                payload.status,
            )
    except PersonNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        ) from exc
    except RelationshipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        ) from exc
    except InvalidConversationStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return row_to_dict(conversation)


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_conversations(
    person_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conversations = service.list(
                conn,
                user_id,
                person_id,
            )
    except PersonNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        ) from exc

    return [
        row_to_dict(conversation)
        for conversation in conversations
    ]


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conversation = service.get(
                conn,
                user_id,
                conversation_id,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    return row_to_dict(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conversation = service.update(
                conn,
                user_id,
                conversation_id,
                payload.relationship_id
                if "relationship_id" in payload.model_fields_set
                else UNSET,
                payload.title
                if "title" in payload.model_fields_set
                else UNSET,
                payload.status
                if "status" in payload.model_fields_set
                else UNSET,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    except RelationshipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        ) from exc
    except InvalidConversationStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return row_to_dict(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete(
                conn,
                user_id,
                conversation_id,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
