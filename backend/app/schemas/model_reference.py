from typing import Literal

from pydantic import BaseModel, Field


ReferenceAssetType = Literal["document", "skill"]
ReferenceUploadType = Literal["auto", "document", "skill"]


class ModelReferenceAssetResponse(BaseModel):
    id: str
    user_id: str
    asset_type: ReferenceAssetType
    title: str
    original_filename: str
    mime_type: str
    size_bytes: int
    content_sha256: str
    char_count: int
    content_preview: str
    enabled: bool
    created_at: str
    updated_at: str


class ModelReferenceAssetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    asset_type: ReferenceAssetType | None = None
    enabled: bool | None = None


class ModelReferenceContextItem(BaseModel):
    id: str
    asset_type: ReferenceAssetType
    title: str
    content: str
    truncated: bool = False


class ModelReferenceContext(BaseModel):
    precedence: list[str]
    usage_rules: list[str]
    items: list[ModelReferenceContextItem]
    enabled_count: int
    skill_count: int
    document_count: int
    truncated: bool = False
