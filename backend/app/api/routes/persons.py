from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.person import (
    PersonCreate,
    PersonResponse,
    PersonUpdate,
)
from app.services.person import PersonService

router = APIRouter(prefix="/persons", tags=["persons"])

service = PersonService()


def row_to_dict(row):
    return dict(row) if row is not None else None


@router.post(
    "",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_person(
    payload: PersonCreate,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        person = service.create(
            conn,
            user_id,
            payload.name,
            payload.nickname,
            payload.notes,
        )

    return row_to_dict(person)


@router.get("", response_model=list[PersonResponse])
def list_persons(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        persons = service.list(conn, user_id)

    return [row_to_dict(person) for person in persons]


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        person = service.get(conn, user_id, person_id)

    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    return row_to_dict(person)


@router.patch("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: str,
    payload: PersonUpdate,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        person = service.update(
            conn,
            user_id,
            person_id,
            payload.name,
            payload.nickname,
            payload.notes,
        )

    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    return row_to_dict(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(
    person_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        deleted = service.delete(conn, user_id, person_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
