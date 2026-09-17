from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.llm_provider_config import (
    LLMProviderConfigResponse,
    LLMProviderConfigUpdate,
)
from app.services.llm import LLMAnalysisError
from app.services.llm_provider_config import (
    LLMProviderConfigError,
    LLMProviderConfigService,
)


router = APIRouter(
    prefix="/settings/llm",
    tags=["settings"],
)

service = LLMProviderConfigService()


@router.get(
    "",
    response_model=LLMProviderConfigResponse | None,
    status_code=status.HTTP_200_OK,
)
def get_llm_provider_config(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        return service.get(conn, user_id)


@router.put(
    "",
    response_model=LLMProviderConfigResponse,
    status_code=status.HTTP_200_OK,
)
def put_llm_provider_config(
    payload: LLMProviderConfigUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.save(conn, user_id, payload)
    except LLMProviderConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post(
    "/test",
    status_code=status.HTTP_200_OK,
)
def test_llm_provider_connection(
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.test_connection(conn, user_id)
    except LLMProviderConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except LLMAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {"status": "ok"}


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_llm_provider_config(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        service.delete(conn, user_id)
