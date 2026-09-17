from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.context import get_current_user_id, parse_bearer_token
from app.core.database import get_connection
from app.schemas.auth_session import AuthSessionResponse
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
