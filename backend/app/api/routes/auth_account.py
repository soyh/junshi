from fastapi import APIRouter, HTTPException, status

from app.core.database import get_connection
from app.schemas.auth_account import AuthLoginRequest, AuthRegisterRequest
from app.schemas.auth_session import AuthSessionResponse
from app.services.auth_account import (
    AuthAccountConflict,
    AuthAccountInvalidCredentials,
    AuthAccountService,
)
from app.services.auth_login_throttle import AuthLoginThrottleService


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

service = AuthAccountService()
throttle_service = AuthLoginThrottleService()


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
    created = None
    invalid_credentials = False
    retry_after = None

    with get_connection() as conn:
        retry_after = throttle_service.retry_after_seconds(
            conn,
            payload.username,
        )
        if retry_after is None:
            try:
                created = service.login(
                    conn,
                    payload.username,
                    payload.password.get_secret_value(),
                )
            except AuthAccountInvalidCredentials:
                throttle_service.record_failure(conn, payload.username)
                invalid_credentials = True
            else:
                throttle_service.clear(conn, payload.username)

    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many login attempts",
            headers={"Retry-After": str(retry_after)},
        )

    if invalid_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        )

    return _session_response(created)
