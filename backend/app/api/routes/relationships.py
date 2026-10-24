from fastapi import APIRouter, Depends, HTTPException, status
from typing import get_args

from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.core.sentinels import UNSET
from app.domain.errors import (
    PersonNotFoundError,
    RelationshipAlreadyExistsError,
)
from app.schemas.relationship import (
    Intent,
    RelationshipCreate,
    RelationshipResponse,
    RelationshipUpdate,
)
from app.services.relationship import RelationshipService

router = APIRouter(
    prefix="/relationships",
    tags=["relationships"],
)

service = RelationshipService()


def row_to_dict(row):
    return dict(row) if row is not None else None


@router.post(
    "",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_relationship(
    payload: RelationshipCreate,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        try:
            relationship = service.create(
                conn,
                user_id,
                payload.person_id,
                payload.status,
                payload.stage,
                payload.long_term_goal,
                payload.current_goal,
                payload.notes,
                payload.intent,
            )
        except PersonNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found",
            ) from exc
        except RelationshipAlreadyExistsError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Relationship already exists for this person",
            ) from exc

    return row_to_dict(relationship)


@router.get("", response_model=list[RelationshipResponse])
def list_relationships(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        relationships = service.list(conn, user_id)

    return [row_to_dict(item) for item in relationships]


@router.get(
    "/{relationship_id}",
    response_model=RelationshipResponse,
)
def get_relationship(
    relationship_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        relationship = service.get(
            conn,
            user_id,
            relationship_id,
        )

    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )

    return row_to_dict(relationship)


@router.patch(
    "/{relationship_id}",
    response_model=RelationshipResponse,
)
def update_relationship(
    relationship_id: str,
    payload: RelationshipUpdate,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        relationship = service.update(
            conn,
            user_id,
            relationship_id,
            payload.status
            if "status" in payload.model_fields_set
            else UNSET,
            payload.stage
            if "stage" in payload.model_fields_set
            else UNSET,
            payload.long_term_goal
            if "long_term_goal" in payload.model_fields_set
            else UNSET,
            payload.current_goal
            if "current_goal" in payload.model_fields_set
            else UNSET,
            payload.notes
            if "notes" in payload.model_fields_set
            else UNSET,
            payload.intent
            if "intent" in payload.model_fields_set
            else UNSET,
        )

    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )

    return row_to_dict(relationship)


@router.delete(
    "/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_relationship(
    relationship_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        deleted = service.delete(
            conn,
            user_id,
            relationship_id,
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )


class BatchIntentBody(BaseModel):
    person_ids: list[str] = Field(min_length=1, max_length=200)
    intent: str = "unsure"


@router.post("/batch-intent", response_model=list[RelationshipResponse])
def set_intent_for_many(
    payload: BatchIntentBody,
    user_id: str = Depends(get_current_user_id),
):
    """Set the same 聊天目的 on many people at once."""
    if payload.intent not in get_args(Intent):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid intent: {payload.intent}",
        )
    with get_connection() as conn:
        rows = service.set_intent_many(conn, user_id, payload.person_ids, payload.intent)

    return [row_to_dict(item) for item in rows]
