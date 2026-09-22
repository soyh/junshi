from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.llm_provider_config import (
    LLMProviderConfigResponse,
    LLMProviderConfigUpdate,
    LLMProviderProfileCreate,
    LLMProviderProfileResponse,
    LLMProviderProfileUpdate,
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


def _config_error(exc: LLMProviderConfigError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if "not found" in str(exc).lower()
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return HTTPException(status_code=status_code, detail=str(exc))


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
        raise _config_error(exc) from exc


@router.post(
    "/test",
    status_code=status.HTTP_200_OK,
)
def test_llm_provider_connection(
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            result = service.test_connection(conn, user_id)
    except LLMProviderConfigError as exc:
        raise _config_error(exc) from exc
    except LLMAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if result is None:
        return {"status": "ok"}
    return result


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_llm_provider_config(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        service.delete(conn, user_id)


@router.get(
    "/profiles",
    response_model=list[LLMProviderProfileResponse],
)
def list_llm_provider_profiles(
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        return service.list_profiles(conn, user_id)


@router.post(
    "/profiles",
    response_model=LLMProviderProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_llm_provider_profile(
    payload: LLMProviderProfileCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.create_profile(conn, user_id, payload)
    except LLMProviderConfigError as exc:
        raise _config_error(exc) from exc


@router.put(
    "/profiles/{profile_id}",
    response_model=LLMProviderProfileResponse,
)
def update_llm_provider_profile(
    profile_id: str,
    payload: LLMProviderProfileUpdate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.update_profile(conn, user_id, profile_id, payload)
    except LLMProviderConfigError as exc:
        raise _config_error(exc) from exc


@router.post(
    "/profiles/{profile_id}/activate",
    response_model=LLMProviderProfileResponse,
)
def activate_llm_provider_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            return service.activate_profile(conn, user_id, profile_id)
    except LLMProviderConfigError as exc:
        raise _config_error(exc) from exc


@router.post(
    "/profiles/{profile_id}/test",
    status_code=status.HTTP_200_OK,
)
def test_llm_provider_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            result = service.test_profile_connection(conn, user_id, profile_id)
    except LLMProviderConfigError as exc:
        raise _config_error(exc) from exc
    except LLMAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    if result is None:
        return {"status": "ok"}
    return result


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_llm_provider_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            service.delete_profile(conn, user_id, profile_id)
    except LLMProviderConfigError as exc:
        raise _config_error(exc) from exc
