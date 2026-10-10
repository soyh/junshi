from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.analysis_strategic_reply import AnalysisStrategicReplyContextResponse
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService
from app.services.llm import LLMAnalysisError, LLMRequestError, LatestTurnError
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
    if isinstance(exc, LatestTurnError) and exc.exhausted:
        stage = "分析阶段未形成基于最新消息的建议" if exc.stage == "analysis" else "回复阶段未正确引用最新消息"
        return f"LLM analysis failed: {stage}；已自动纠正 {exc.corrections} 次，仍未通过校验。请稍后重试或切换模型。"
    if isinstance(exc, LLMRequestError):
        return "LLM analysis failed: " + LLMRequestError.MESSAGES[exc.category]
    raw_message = str(exc)
    message = raw_message.lower()
    if "invalid strategic reply" in message or "no usable strategic reply draft" in message:
        return "LLM analysis failed: 模型未返回有效回复草稿，请重新生成；本次未生成可用建议。"
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
    request_id: UUID | None = None,
    user_id: str = Depends(get_current_user_id),
):
    from app.services.reply_progress import publish
    progress = (lambda stage, attempt=0: publish(user_id,conversation_id,str(request_id),stage,attempt)) if request_id else None
    completed = False
    from app.services import reply_priority
    reply_priority.enter(user_id)
    try:
        with get_connection() as conn:
            kwargs = {'progress': progress} if progress else {}
            result = service.build_context(
                conn,
                user_id,
                conversation_id,
                provider=_build_provider(conn, user_id),
                **kwargs,
            )
            if progress: progress('complete')
            completed = True
            return result
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
    finally:
        reply_priority.leave(user_id)
        if progress and not completed:
            progress('failed')


@router.get('/progress/{request_id}')
def get_reply_progress(conversation_id: str, request_id: UUID,
                       user_id: str = Depends(get_current_user_id)):
    from app.services.reply_progress import read
    with get_connection() as conn:
        if not conn.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(conversation_id,user_id)).fetchone():
            raise HTTPException(404,'Conversation not found')
    return read(user_id,conversation_id,str(request_id))
