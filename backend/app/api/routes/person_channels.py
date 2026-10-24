from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.services.person_channel import (
    PersonChannelConflict,
    PersonChannelError,
    PersonChannelService,
    extract_wechat_id,
)
from app.services.person_conversation import PersonNotFoundForConversation

router = APIRouter(prefix="/persons", tags=["person-channels"])

service = PersonChannelService()


class ChannelLink(BaseModel):
    platform: str = Field(min_length=1, max_length=40)
    account_handle: str = Field(min_length=1, max_length=120)
    display_name: str = Field(default="", max_length=120)
    reassign: bool = False


class ResolveQuery(BaseModel):
    platform: str = Field(min_length=1, max_length=40)
    account_handle: str = Field(min_length=1, max_length=120)


class WeChatId(BaseModel):
    wechat_id: str = Field(default="", max_length=60)


class CaptureText(BaseModel):
    text: str = Field(default="", max_length=4000)


@router.post("/resolve-channel")
def resolve_channel(payload: ResolveQuery, user_id: str = Depends(get_current_user_id)):
    """Bridge asks: this 小红书 / Soul / WeChat handle — whose conversation is it?

    A 404 means "not linked yet"; the bridge then creates the person and links it,
    so the second channel of the same human lands on the same conversation.
    """
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        found = service.resolve(
            conn, user_id, platform=payload.platform, handle=payload.account_handle
        )
        if found is None:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="This handle is not linked yet"
            )
        conn.commit()
        return found


@router.post("/{person_id}/channels")
def link_channel(person_id: str, payload: ChannelLink, user_id: str = Depends(get_current_user_id)):
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            result = service.link(
                conn,
                user_id,
                person_id,
                platform=payload.platform,
                handle=payload.account_handle,
                display_name=payload.display_name,
                reassign=payload.reassign,
            )
            conn.commit()
            return result
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except PersonChannelConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except PersonChannelError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from None


@router.get("/{person_id}/channels")
def list_channels(person_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        with get_connection() as conn:
            return {"items": service.for_person(conn, user_id, person_id)}
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None


@router.delete("/{person_id}/channels/{platform}/{account_handle}")
def unlink_channel(
    person_id: str, platform: str, account_handle: str, user_id: str = Depends(get_current_user_id)
):
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            result = service.unlink(conn, user_id, person_id, platform, account_handle)
            conn.commit()
            return result
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None


@router.put("/{person_id}/wechat")
def set_wechat_id(person_id: str, payload: WeChatId, user_id: str = Depends(get_current_user_id)):
    """The counterpart's WeChat id lives on the person record (one per person)."""
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            result = service.set_wechat_id(conn, user_id, person_id, payload.wechat_id)
            conn.commit()
            return result
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None


@router.post("/{person_id}/wechat/capture")
def capture_wechat(
    person_id: str, payload: CaptureText, user_id: str = Depends(get_current_user_id)
):
    """The bridge posts what the counterpart said; the server stores a handle.

    Only fills an empty slot: an id the user typed by hand always wins.
    """
    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            aliases = service.account_aliases(conn, user_id)
            stored = service.capture_wechat_id(
                conn, user_id, person_id, payload.text, aliases
            )
            conn.commit()
            return {
                "person_id": person_id,
                "wechat_id": stored,
                "detected": extract_wechat_id(payload.text, aliases),
            }
    except PersonNotFoundForConversation as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
