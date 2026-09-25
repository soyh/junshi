from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.reference_context import (
    ConversationReferenceOverrideUpdate,
    ModelReferenceContextResponse,
    ModelReferenceResponse,
    ModelReferenceUpdate,
)
from app.services.reference_context import (
    ReferenceContextError,
    ReferenceContextService,
    ReferenceNotFoundError,
    UnsupportedReferenceFileError,
)


router = APIRouter(tags=["model-references"])
service = ReferenceContextService()


def _not_found_or_unprocessable(exc: ReferenceContextError) -> HTTPException:
    if isinstance(exc, ReferenceNotFoundError) or str(exc) == "Conversation not found":
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


@router.post(
    "/references",
    response_model=ModelReferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_model_reference(
    file: UploadFile = File(...),
    reference_type: str = Form(default="auto"),
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    enabled_by_default: bool = Form(default=True),
    priority: int = Form(default=100),
    user_id: str = Depends(get_current_user_id),
):
    try:
        content = await file.read()
        with get_connection() as conn:
            return service.create(
                conn,
                user_id=user_id,
                filename=file.filename or "reference",
                mime_type=file.content_type,
                content=content,
                requested_type=reference_type,
                name=name,
                description=description,
                enabled_by_default=enabled_by_default,
                priority=priority,
            )
    except (ReferenceContextError, UnsupportedReferenceFileError) as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.get(
    "/references",
    response_model=list[ModelReferenceResponse],
)
def list_model_references(
    conversation_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.list_references(conn, user_id, conversation_id)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.patch(
    "/references/{reference_id}",
    response_model=ModelReferenceResponse,
)
def update_model_reference(
    reference_id: str,
    payload: ModelReferenceUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.update(
                conn,
                user_id,
                reference_id,
                payload.model_dump(exclude_unset=True),
            )
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.delete(
    "/references/{reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_model_reference(
    reference_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete(conn, user_id, reference_id)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.put(
    "/conversations/{conversation_id}/references/{reference_id}",
    response_model=ModelReferenceResponse,
)
def set_conversation_reference_override(
    conversation_id: str,
    reference_id: str,
    payload: ConversationReferenceOverrideUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.set_conversation_override(
                conn,
                user_id=user_id,
                conversation_id=conversation_id,
                reference_id=reference_id,
                enabled=payload.enabled,
                priority=payload.priority,
            )
            items = service.list_references(conn, user_id, conversation_id)
            return next(item for item in items if item["id"] == reference_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Reference not found") from exc
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.delete(
    "/conversations/{conversation_id}/references/{reference_id}/override",
    response_model=ModelReferenceResponse,
)
def clear_conversation_reference_override(
    conversation_id: str,
    reference_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.clear_conversation_override(
                conn,
                user_id=user_id,
                conversation_id=conversation_id,
                reference_id=reference_id,
            )
            items = service.list_references(conn, user_id, conversation_id)
            return next(item for item in items if item["id"] == reference_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Reference not found") from exc
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.get(
    "/conversations/{conversation_id}/references/context",
    response_model=ModelReferenceContextResponse,
)
def get_conversation_reference_context(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.build_context(conn, user_id, conversation_id)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc
