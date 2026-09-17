import hmac

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise _unauthorized("bearer token required")

    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token:
        raise _unauthorized("invalid bearer authorization")
    return token


def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    """Resolve the authenticated user boundary for API requests.

    Opaque auth sessions are resolved server-side to users.id. The legacy
    server-configured Bearer bootstrap remains explicit opt-in only.
    X-User-ID is never accepted as an identity source in any environment.
    Development/test without a Bearer token continues to use LOCAL_USER_ID.
    """
    settings = get_settings()
    is_production = settings.app_env.lower() == "production"

    if x_user_id:
        raise _unauthorized("X-User-ID is not accepted")

    if authorization:
        token = parse_bearer_token(authorization)

        with get_connection() as conn:
            session_user_id = auth_session_service.resolve(conn, token)
        if session_user_id is not None:
            return session_user_id

        configured_token = settings.auth_bearer_token
        if (
            settings.auth_bootstrap_enabled
            and configured_token
            and hmac.compare_digest(token, configured_token)
        ):
            return settings.local_user_id

        raise _unauthorized("invalid bearer token")

    if is_production:
        if settings.auth_bootstrap_enabled and not settings.auth_bearer_token:
            with get_connection() as conn:
                sessions_configured = auth_session_service.has_active_sessions(conn)
            if not sessions_configured:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="production authentication is not configured",
                )

        raise _unauthorized("bearer token required")

    return settings.local_user_id
