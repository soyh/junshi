from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ReferenceType = Literal["document", "skill"]


class ModelReferenceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    reference_type: ReferenceType
    original_filename: str | None = None
    mime_type: str | None = None
    description: str | None = None
    enabled_by_default: bool
    priority: int
    created_at: str
    updated_at: str
    content_chars: int
    content_preview: str
    effective_enabled: bool
    effective_priority: int
    override_enabled: bool | None = None
    override_priority: int | None = None


class ModelReferenceUpdate(BaseModel):
    name: str | None = None
    reference_type: ReferenceType | None = None
    description: str | None = None
    enabled_by_default: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=10000)


class ConversationReferenceOverrideUpdate(BaseModel):
    enabled: bool
    priority: int | None = Field(default=None, ge=0, le=10000)


class ModelReferenceContextResponse(BaseModel):
    conversation_id: str
    count: int
    policy: dict[str, str]
    items: list[dict]
