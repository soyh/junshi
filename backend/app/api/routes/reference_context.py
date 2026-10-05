from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.reference_context import (
    ReferenceBatchUpdate,
    ReferenceContentUpdate,
    ReferenceGuideCreate,
    ConversationReferenceOverrideUpdate,
    ReferenceRetrievalContextResponse,
    ModelReferenceResponse,
    ModelReferenceUpdate,
)
from app.services.reference_context import (
    ReferenceContextError,
    ReferenceEditConflict,
    ReferenceContextService,
    ReferenceNotFoundError,
    UnsupportedReferenceFileError,
)


router = APIRouter(tags=["model-references"])
service = ReferenceContextService()


@router.get("/references/catalog", response_model=ReferenceRetrievalContextResponse)
def get_global_reference_catalog(response: Response, user_id: str = Depends(get_current_user_id)):
    response.headers["Cache-Control"] = "no-store"
    try:
        with get_connection() as conn:
            return service.build_context(conn, user_id)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.post("/references/guide", response_model=dict[str, str], status_code=201)
def create_global_reference_guide(payload: ReferenceGuideCreate, response: Response,
                                  user_id: str = Depends(get_current_user_id)):
    response.headers["Cache-Control"] = "no-store"
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="请填写主题指南文件名。")
    if not name.lower().endswith(".md"):
        name += ".md"
    if "/" in name or "\\" in name or not payload.content.strip():
        raise HTTPException(status_code=422, detail="请填写有效的 Markdown 文件名和非空内容。")
    try:
        with get_connection() as conn:
            item = service.create(conn, user_id=user_id, filename=name, mime_type="text/markdown",
                                  content=payload.content.encode("utf-8"), requested_type="document",
                                  name=name, enabled_by_default=True, priority=10)
            return service.get_editor(conn, user_id, item["id"])
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.post("/references/batch", response_model=dict[str, int])
def batch_update_model_references(
    payload: ReferenceBatchUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            count = service.batch_update(
                conn, user_id, payload.reference_ids, payload.action,
                payload.scope, payload.conversation_id,
            )
        return {"updated_count": count}
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.get("/references/{reference_id}/content", response_model=dict[str, str])
def get_model_reference_content(
    reference_id: str,
    response: Response,
    user_id: str = Depends(get_current_user_id),
):
    response.headers["Cache-Control"] = "no-store"
    try:
        with get_connection() as conn:
            return service.get_content(conn, user_id, reference_id)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


def _not_found_or_unprocessable(exc: ReferenceContextError) -> HTTPException:
    if isinstance(exc, ReferenceEditConflict):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ReferenceNotFoundError) or str(exc) == "Conversation not found":
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/references/{reference_id}/editor", response_model=dict[str, str])
def get_reference_editor(reference_id: str, response: Response,
                         user_id: str = Depends(get_current_user_id)):
    response.headers["Cache-Control"] = "no-store"
    try:
        with get_connection() as conn:
            return service.get_editor(conn, user_id, reference_id)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


@router.put("/references/{reference_id}/content", response_model=dict[str, str])
def update_reference_content(reference_id: str, payload: ReferenceContentUpdate,
                             response: Response, user_id: str = Depends(get_current_user_id)):
    response.headers["Cache-Control"] = "no-store"
    try:
        with get_connection() as conn:
            return service.update_content(conn, user_id, reference_id, payload.content, payload.expected_revision)
    except ReferenceContextError as exc:
        raise _not_found_or_unprocessable(exc) from exc


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
    response_model=ReferenceRetrievalContextResponse,
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
