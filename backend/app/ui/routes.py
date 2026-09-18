from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.ui.product_shell import PRODUCT_SHELL_HTML


router = APIRouter(tags=["ui"])


@router.get(
    "/app",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_product_shell():
    return HTMLResponse(PRODUCT_SHELL_HTML)
