import secrets

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings


_SECURE_ENVS = {"production", "staging"}


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, separator, value = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer":
        return None

    token = value.strip()
    return token or None


def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    """Resolve the request principal without allowing production user spoofing.

    When AUTH_BEARER_TOKEN is configured, only a matching Bearer credential is
    accepted and the authenticated principal is the configured LOCAL_USER_ID.
    X-User-ID cannot select or override that principal.

    Development/test keeps the historical X-User-ID fallback so existing local
    workflows and regression tests remain usable. Production/staging fail closed
    if authentication has not been configured.
    """
    settings = get_settings()
    configured = settings.auth_bearer_token

    if configured is not None:
        candidate = _bearer_token(authorization)
        expected = configured.get_secret_value()
        if candidate is None or not secrets.compare_digest(candidate, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return settings.local_user_id

    if settings.app_env.strip().lower() in _SECURE_ENVS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="authentication is not configured",
        )

    if x_user_id:
        return x_user_id

    return settings.local_user_id
