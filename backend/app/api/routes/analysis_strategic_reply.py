from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.analysis_strategic_reply import AnalysisStrategicReplyContextResponse
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService
from app.services.llm import LLMAnalysisError
from app.services.llm_provider_config import (
    LLMProviderConfigError,
    LLMProviderConfigService,
)
from app.services.qwen_provider import QwenProvider


router = APIRouter(
    prefix="/conversations/{conversation_id}/strategic-reply",
    tags=["strategic-reply"],
)

service = AnalysisStrategicReplyService()
provider_config_service = LLMProviderConfigService()


def _build_provider(conn, user_id: str):
    if provider_config_service.get(conn, user_id) is None:
        return QwenProvider()
    return provider_config_service.build_provider(conn, user_id)


def _safe_llm_failure_detail(exc: LLMAnalysisError) -> str:
    raw_message = str(exc)
    message = raw_message.lower()
    marker = "invalid structured analysis fields="
    if marker in message:
        raw_fields = raw_message.split("fields=", 1)[1]
        safe_fields = "".join(
            character
            for character in raw_fields
            if character.isalnum() or character in "._,-[]"
        )[:240]
        return (
            "LLM analysis failed: invalid structured response"
            + (f" (fields: {safe_fields})" if safe_fields else "")
        )
    if "invalid structured analysis" in message:
        return "LLM analysis failed: invalid structured response"
    if (
        "no fresh recommendation" in message
        or "stale strategic reply provenance" in message
    ):
        return "LLM analysis failed: latest conversation was not incorporated"
    if "strategic reply request failed" in message:
        return "LLM analysis failed: strategic reply provider request failed"
    if "provider request failed" in message:
        return "LLM analysis failed: provider request failed"
    if "api key" in message or "not configured" in message:
        return "LLM analysis failed: provider configuration"
    if "non-object" in message or "non-text" in message:
        return "LLM analysis failed: invalid provider response"
    return "LLM analysis failed"


@router.get(
    "/context",
    response_model=AnalysisStrategicReplyContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_analysis_strategic_reply_context(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.build_context(
                conn,
                user_id,
                conversation_id,
                provider=_build_provider(conn, user_id),
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LLMProviderConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except LLMAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_llm_failure_detail(exc),
        ) from exc
