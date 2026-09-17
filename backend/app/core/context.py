import hmac

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    """Resolve the authenticated user boundary for API requests.

    Production accepts only the server-configured Bearer token and maps it to
    the configured local user. The legacy X-User-ID/development fallback is
    retained outside production so the existing MVP/test contracts can migrate
    without weakening the production boundary.
    """
    settings = get_settings()
    is_production = settings.app_env.lower() == "production"

    if authorization:
        scheme, separator, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token:
            raise _unauthorized("invalid bearer authorization")

        configured_token = settings.auth_bearer_token
        if configured_token and hmac.compare_digest(token, configured_token):
            return settings.local_user_id

        raise _unauthorized("invalid bearer token")

    if is_production:
        if x_user_id:
            raise _unauthorized("X-User-ID is not accepted in production")
        if not settings.auth_bearer_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="production authentication is not configured",
            )
        raise _unauthorized("bearer token required")

    if x_user_id:
        return x_user_id

    return settings.local_user_id
