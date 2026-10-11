from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.ui.auth_account import AUTH_ACCOUNT_HTML


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get(
    "/ui",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_auth_account_ui():
    return HTMLResponse(AUTH_ACCOUNT_HTML)
