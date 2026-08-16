from fastapi import Header

from app.config.settings import get_settings


def get_current_user_id(
    x_user_id: str | None = Header(default=None),
) -> str:
    """
    MVP 阶段暂不实现完整认证系统。

    如果请求携带 X-User-ID，则使用该 ID；
    否则使用本地开发用户。

    正式多人版本必须替换为认证后的 user_id，
    不允许客户端任意伪造身份。
    """
    if x_user_id:
        return x_user_id

    return get_settings().local_user_id
