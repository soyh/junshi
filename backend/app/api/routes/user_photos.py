"""本人照片库接口：网页上传，桥接按需取图发送。"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.services import user_photos

router = APIRouter(prefix='/settings/photos', tags=['photos'])

ERRORS = {
    "unsupported-image": (400, "只支持 JPG / PNG / WebP"),
    "empty-image": (400, "文件是空的"),
    "image-too-large": (413, "单张照片不能超过 8MB"),
}


@router.get('')
def list_photos(user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        return {"photos": user_photos.list_photos(conn, user_id)}


@router.post('', status_code=201)
async def upload(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user_id: str = Depends(get_current_user_id),
):
    raw = await file.read()
    with get_connection() as conn:
        try:
            saved = user_photos.add_photo(
                conn, user_id,
                content=raw,
                mime=file.content_type or "image/jpeg",
                filename=file.filename or "",
                caption=caption,
            )
        except ValueError as exc:
            status, detail = ERRORS.get(str(exc), (400, "无法保存这张照片"))
            raise HTTPException(status, detail) from None
    return saved


@router.delete('/{photo_id}')
def remove(photo_id: str, user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        if not user_photos.delete_photo(conn, user_id, photo_id):
            raise HTTPException(404, "Photo not found")
    return {"status": "deleted"}


@router.get('/{photo_id}/image')
def image(photo_id: str, user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        row = user_photos.read_photo(conn, user_id, photo_id)
    if row is None:
        raise HTTPException(404, "Photo not found")
    return Response(
        content=row["content"],
        media_type=row["mime"],
        headers={"Cache-Control": "private, max-age=300"},
    )
