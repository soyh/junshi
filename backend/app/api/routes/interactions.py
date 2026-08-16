from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import (
    InteractionNotFoundError,
    InvalidInteractionTypeError,
    PersonNotFoundError,
    RelationshipNotFoundError,
)
from app.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
)
from app.services.interaction import InteractionService


router = APIRouter(
    prefix="/interactions",
    tags=["interactions"],
)

service = InteractionService()


def row_to_dict(row):
    return dict(row) if row is not None else None


@router.post(
    "",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interaction(
    payload: InteractionCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            interaction = service.create(
                conn,
                user_id,
                payload.person_id,
                payload.relationship_id,
                payload.type,
                payload.occurred_at,
                payload.content,
            )
    except PersonNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    except RelationshipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
    except InvalidInteractionTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return row_to_dict(interaction)


@router.get(
    "",
    response_model=list[InteractionResponse],
)
def list_interactions(
    person_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            interactions = service.list(
                conn,
                user_id,
                person_id,
            )
    except PersonNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    return [
        row_to_dict(interaction)
        for interaction in interactions
    ]


@router.get(
    "/{interaction_id}",
    response_model=InteractionResponse,
)
def get_interaction(
    interaction_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            interaction = service.get(
                conn,
                user_id,
                interaction_id,
            )
    except InteractionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )

    return row_to_dict(interaction)


@router.patch(
    "/{interaction_id}",
    response_model=InteractionResponse,
)
def update_interaction(
    interaction_id: str,
    payload: InteractionUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            interaction = service.update(
                conn,
                user_id,
                interaction_id,
                payload.relationship_id,
                payload.type,
                payload.occurred_at,
                payload.content,
            )
    except InteractionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )
    except RelationshipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
    except InvalidInteractionTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return row_to_dict(interaction)


@router.delete(
    "/{interaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_interaction(
    interaction_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete(
                conn,
                user_id,
                interaction_id,
            )
    except InteractionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )
