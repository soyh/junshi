from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.context import get_current_user_id, parse_bearer_token
from app.core.database import get_connection
from app.schemas.auth_session import AuthSessionResponse, AuthSessionSummary
from app.services.auth_session import AuthSessionError, AuthSessionService


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

service = AuthSessionService()


@router.post(
    "/sessions",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_auth_session(
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            created = service.create(conn, user_id)
    except AuthSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None

    return AuthSessionResponse(
        access_token=created.access_token,
        expires_at=created.expires_at,
    )


@router.get(
    "/sessions",
    response_model=list[AuthSessionSummary],
)
def list_auth_sessions(
    authorization: str | None = Header(default=None),
    user_id: str = Depends(get_current_user_id),
):
    token = parse_bearer_token(authorization)

    with get_connection() as conn:
        current_session = service.get_active_session(conn, token)
        sessions = service.list_active_for_user(conn, user_id)

    current_session_id = None
    if current_session is not None and current_session.user_id == user_id:
        current_session_id = current_session.id

    return [
        AuthSessionSummary(
            id=session.id,
            expires_at=session.expires_at,
            created_at=session.created_at,
            current=session.id == current_session_id,
        )
        for session in sessions
    ]


@router.delete(
    "/sessions/others",
    status_code=status.HTTP_200_OK,
)
def revoke_other_auth_sessions(
    authorization: str | None = Header(default=None),
    user_id: str = Depends(get_current_user_id),
):
    token = parse_bearer_token(authorization)

    try:
        with get_connection() as conn:
            revoked = service.revoke_other_sessions(conn, user_id, token)
    except AuthSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    return {"revoked": revoked}


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_auth_session_by_id(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        revoked = service.revoke_for_user(conn, user_id, session_id)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="auth session not found",
        )


@router.post(
    "/session/rotate",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def rotate_current_auth_session(
    authorization: str | None = Header(default=None),
    user_id: str = Depends(get_current_user_id),
):
    token = parse_bearer_token(authorization)

    try:
        with get_connection() as conn:
            created = service.rotate(conn, user_id, token)
    except AuthSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    return AuthSessionResponse(
        access_token=created.access_token,
        expires_at=created.expires_at,
    )


@router.delete(
    "/session",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_current_auth_session(
    authorization: str | None = Header(default=None),
    user_id: str = Depends(get_current_user_id),
):
    token = parse_bearer_token(authorization)

    with get_connection() as conn:
        resolved_user_id = service.resolve(conn, token)
        if resolved_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current bearer token is not a revocable auth session",
            )
        service.revoke(conn, token)
