from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.model_reference import (
    ModelReferenceAssetResponse,
    ModelReferenceAssetUpdate,
    ModelReferenceContext,
)
from app.services.model_reference import ModelReferenceError, ModelReferenceService


router = APIRouter(prefix="/model-references", tags=["model-references"])
service = ModelReferenceService()


@router.post(
    "",
    response_model=ModelReferenceAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_model_reference(
    file: UploadFile = File(...),
    asset_type: Literal["auto", "document", "skill"] = Form(default="auto"),
    title: str | None = Form(default=None),
    user_id: str = Depends(get_current_user_id),
):
    try:
        content = await file.read()
        with get_connection() as conn:
            return service.create(
                conn,
                user_id=user_id,
                original_filename=file.filename or "reference.txt",
                mime_type=file.content_type or "application/octet-stream",
                content=content,
                asset_type=asset_type,
                title=title,
            )
    except ModelReferenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[ModelReferenceAssetResponse])
def list_model_references(user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        return service.list(conn, user_id)


@router.get("/context-preview", response_model=ModelReferenceContext)
def preview_model_reference_context(user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        return service.build_context(conn, user_id)


@router.patch("/{asset_id}", response_model=ModelReferenceAssetResponse)
def update_model_reference(
    asset_id: str,
    payload: ModelReferenceAssetUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.update(
                conn,
                user_id,
                asset_id,
                title=payload.title,
                asset_type=payload.asset_type,
                enabled=payload.enabled,
            )
    except ModelReferenceError as exc:
        code = 404 if "not found" in str(exc).lower() else 422
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_reference(
    asset_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete(conn, user_id, asset_id)
    except ModelReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
