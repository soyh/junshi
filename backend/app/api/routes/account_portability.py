import sqlite3

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.context import get_current_user_id
from app.services.account_portability import MAX_ENCRYPTED, export_account, import_account

router = APIRouter(prefix='/account-transfer', tags=['account-transfer'])


class ExportInput(BaseModel):
    password: str = Field(min_length=12, max_length=256)


@router.post('/export')
def export_data(payload: ExportInput, user_id=Depends(get_current_user_id)):
    try:
        data = export_account(user_id, payload.password)
    except (ValueError, OSError):
        raise HTTPException(422, '完整导出失败：请检查媒体是否完整及数据量是否超过 64 MiB；未生成不完整数据包。') from None
    return Response(data, media_type='application/octet-stream', headers={
        'Content-Disposition': 'attachment; filename="junshi-account.jsa"', 'Cache-Control': 'no-store'})


@router.post('/import')
def import_data(password: str = Form(min_length=12, max_length=256), file: UploadFile = File(), user_id=Depends(get_current_user_id)):
    raw = file.file.read(MAX_ENCRYPTED + 1)
    try:
        return import_account(user_id, raw, password)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    except (sqlite3.Error, OSError, TypeError, KeyError):
        raise HTTPException(409, '导入失败：数据格式或标识冲突，数据库变更已回退；请使用另一套部署的空白账号。') from None
