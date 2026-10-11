from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.analysis_strategy import AnalysisStrategyContextResponse
from app.services.analysis_strategy import AnalysisStrategyService
from app.services.llm import LLMAnalysisError
from app.services.llm_provider_config import (
    LLMProviderConfigError,
    LLMProviderConfigService,
)
from app.services.qwen_provider import QwenProvider


router = APIRouter(
    prefix="/conversations/{conversation_id}/strategy",
    tags=["strategy"],
)

service = AnalysisStrategyService()
provider_config_service = LLMProviderConfigService()


def _build_provider(conn, user_id: str):
    if provider_config_service.get(conn, user_id) is None:
        return QwenProvider()
    return provider_config_service.build_provider(conn, user_id)


@router.get(
    "/context",
    response_model=AnalysisStrategyContextResponse,
    status_code=status.HTTP_200_OK,
)
def get_analysis_strategy_context(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.build_strategy_context(
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
            detail="LLM analysis failed",
        ) from exc
