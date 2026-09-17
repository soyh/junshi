from fastapi import APIRouter, HTTPException, status

from app.core.database import get_connection
from app.schemas.auth_account import AuthLoginRequest, AuthRegisterRequest
from app.schemas.auth_session import AuthSessionResponse
from app.services.auth_account import (
    AuthAccountConflict,
    AuthAccountInvalidCredentials,
    AuthAccountService,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

service = AuthAccountService()


def _session_response(created) -> AuthSessionResponse:
    return AuthSessionResponse(
        access_token=created.access_token,
        expires_at=created.expires_at,
    )


@router.post(
    "/register",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: AuthRegisterRequest):
    try:
        with get_connection() as conn:
            created = service.register(
                conn,
                payload.username,
                payload.password.get_secret_value(),
            )
    except AuthAccountConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None

    return _session_response(created)


@router.post(
    "/login",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login(payload: AuthLoginRequest):
    try:
        with get_connection() as conn:
            created = service.login(
                conn,
                payload.username,
                payload.password.get_secret_value(),
            )
    except AuthAccountInvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from None

    return _session_response(created)
