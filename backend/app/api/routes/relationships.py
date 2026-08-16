import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.repositories.relationship import RelationshipRepository
from app.schemas.relationship import (
    RelationshipCreate,
    RelationshipResponse,
    RelationshipUpdate,
)

router = APIRouter(
    prefix="/relationships",
    tags=["relationships"],
)

repository = RelationshipRepository()


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
        person = conn.execute(
            """
            SELECT id
            FROM persons
            WHERE id = ?
              AND user_id = ?
            """,
            (payload.person_id, user_id),
        ).fetchone()

        if person is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found",
            )

        try:
            relationship = repository.create(
                conn,
                user_id,
                payload.person_id,
                payload.status,
                payload.stage,
                payload.long_term_goal,
                payload.current_goal,
                payload.notes,
            )
        except sqlite3.IntegrityError as exc:
            error_message = str(exc)

            if (
                "UNIQUE constraint failed: relationships.user_id, relationships.person_id"
                in error_message
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Relationship already exists for this person",
                ) from exc

            raise

    return row_to_dict(relationship)


@router.get("", response_model=list[RelationshipResponse])
def list_relationships(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        relationships = repository.list(conn, user_id)

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
        relationship = repository.get(
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
        relationship = repository.update(
            conn,
            user_id,
            relationship_id,
            payload.status,
            payload.stage,
            payload.long_term_goal,
            payload.current_goal,
            payload.notes,
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
        deleted = repository.delete(
            conn,
            user_id,
            relationship_id,
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
