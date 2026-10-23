import json
import logging
import sqlite3

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
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

# The long-term archive is refreshed in the background once this many new
# messages have piled up since the last pass; below it, replies just reuse what
# is already known and nothing extra is spent per message.
MEMORY_BATCH_TRIGGER = 6


def _memory_needs_refresh(
    conn, user_id: str, conversation_id: str
) -> tuple[str, bool]:
    row = conn.execute(
        "SELECT person_id FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if row is None:
        return "", False
    person_id = str(row["person_id"])
    total = conn.execute(
        "SELECT COUNT(*) FROM messages m JOIN conversations c ON c.id = m.conversation_id "
        "WHERE c.person_id = ? AND m.user_id = ?",
        (person_id, user_id),
    ).fetchone()[0]
    memory = conn.execute(
        "SELECT coverage_json FROM person_memories WHERE person_id = ? AND user_id = ?",
        (person_id, user_id),
    ).fetchone()
    covered = 0
    if memory is not None:
        try:
            covered = len(json.loads(memory["coverage_json"] or "{}"))
        except (TypeError, ValueError):
            covered = 0
    return person_id, (total - covered) >= MEMORY_BATCH_TRIGGER


def _schedule_memory_refresh(background, conn, user_id: str, conversation_id: str) -> None:
    """Fold new messages into the long-term archive without delaying the reply."""
    try:
        person_id, behind = _memory_needs_refresh(conn, user_id, conversation_id)
    except sqlite3.OperationalError:
        return
    if not behind or not person_id:
        return
    from app.services.person_memory import background_refresh

    background.add_task(background_refresh, user_id, person_id)


def _build_provider(conn, user_id: str):
    if provider_config_service.get(conn, user_id) is None:
        return QwenProvider()
    return provider_config_service.build_provider(conn, user_id)


class ChannelRulesBody(BaseModel):
    rules: str = ""
    self_profile: dict[str, str] = {}
    # An option the user picked from the plan card; skips the planner call and
    # drafts that tactic instead of the recommended one.
    option: dict | None = None


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
    background: BackgroundTasks,
    request_id: UUID | None = None,
    user_id: str = Depends(get_current_user_id),
):
    return _reply_context(conversation_id, request_id, "", {}, user_id, None, background)


@router.post(
    "/context",
    response_model=AnalysisStrategicReplyContextResponse,
    status_code=status.HTTP_200_OK,
)
def post_analysis_strategic_reply_context(
    conversation_id: str,
    background: BackgroundTasks,
    body: ChannelRulesBody | None = None,
    request_id: UUID | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """Same pipeline as GET, plus optional per-channel style rules from the bridge."""
    return _reply_context(
        conversation_id,
        request_id,
        (body.rules if body else ""),
        (body.self_profile if body else {}),
        user_id,
        (body.option if body else None),
        background,
    )


def _reply_context(
    conversation_id: str,
    request_id: UUID | None,
    channel_rules: str,
    self_profile: dict[str, str],
    user_id: str,
    option: dict | None = None,
    background: BackgroundTasks | None = None,
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
                channel_rules=channel_rules,
                self_profile=self_profile,
                option=option,
                **kwargs,
            )
            if progress: progress('complete')
            completed = True
            if background is not None:
                _schedule_memory_refresh(background, conn, user_id, conversation_id)
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
        logging.getLogger(__name__).warning(
            "strategic-reply failed conversation=%s: %s: %s",
            conversation_id, type(exc).__name__, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_llm_failure_detail(exc),
        ) from exc
    finally:
        reply_priority.leave(user_id)
        if progress and not completed:
            progress('failed')


@router.get('/plan')
def get_stored_plan(conversation_id: str,
                    user_id: str = Depends(get_current_user_id)):
    """Latest plan for this conversation, including ones the bridge generated."""
    from app.services import strategic_plan
    with get_connection() as conn:
        if not conn.execute(
            'SELECT 1 FROM conversations WHERE id=? AND user_id=?',
            (conversation_id, user_id),
        ).fetchone():
            raise HTTPException(404, 'Conversation not found')
        return {"plan": strategic_plan.load_plan(conn, user_id, conversation_id)}


@router.get('/progress/{request_id}')
def get_reply_progress(conversation_id: str, request_id: UUID,
                       user_id: str = Depends(get_current_user_id)):
    from app.services.reply_progress import read
    with get_connection() as conn:
        if not conn.execute('SELECT 1 FROM conversations WHERE id=? AND user_id=?',(conversation_id,user_id)).fetchone():
            raise HTTPException(404,'Conversation not found')
    return read(user_id,conversation_id,str(request_id))
