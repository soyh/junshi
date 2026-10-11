from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.ui.provider_settings import PROVIDER_SETTINGS_HTML


router = APIRouter(
    prefix="/settings/llm",
    tags=["settings"],
)


@router.get(
    "/ui",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_llm_provider_settings_ui():
    return HTMLResponse(PROVIDER_SETTINGS_HTML)
