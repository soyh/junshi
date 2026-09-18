from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.ui.conversation_content_workspace import (
    CONVERSATION_CONTENT_HTML,
    CONVERSATION_CONTENT_SCRIPT,
)
from app.ui.product_shell import PRODUCT_SHELL_HTML


router = APIRouter(tags=["ui"])


def build_product_shell_html() -> str:
    provider_marker = '  <fieldset id="provider" class="wide">'
    script_marker = "  clearSession();\n})();"

    if provider_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell provider insertion marker not found")
    if script_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell script insertion marker not found")

    html = PRODUCT_SHELL_HTML.replace(
        provider_marker,
        f"{CONVERSATION_CONTENT_HTML}\n{provider_marker}",
        1,
    )
    return html.replace(
        script_marker,
        f"{CONVERSATION_CONTENT_SCRIPT}\n\n{script_marker}",
        1,
    )


PRODUCT_SHELL_WITH_CONTENT_HTML = build_product_shell_html()


@router.get(
    "/app",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_product_shell():
    return HTMLResponse(PRODUCT_SHELL_WITH_CONTENT_HTML)
