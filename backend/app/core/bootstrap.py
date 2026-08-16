import logging

from app.config.settings import get_settings
from app.core.database import get_connection

logger = logging.getLogger(__name__)


def ensure_local_user() -> None:
    settings = get_settings()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id)
            VALUES (?)
            """,
            (settings.local_user_id,),
        )

    logger.info(
        "Local user ensured: %s",
        settings.local_user_id,
    )
