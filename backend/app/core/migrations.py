import logging
import os

from app.config.settings import get_settings
from app.core.database import get_connection

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    settings = get_settings()

    migration_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../migrations",
        )
    )

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        files = sorted(
            filename
            for filename in os.listdir(migration_dir)
            if filename.endswith(".sql")
        )

        for filename in files:
            version = filename.split("_", 1)[0]

            exists = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,),
            ).fetchone()

            if exists:
                continue

            path = os.path.join(migration_dir, filename)

            with open(path, "r", encoding="utf-8") as file:
                sql = file.read()

            logger.info("Applying migration: %s", filename)

            conn.executescript(sql)

            conn.execute(
                "INSERT INTO schema_migrations(version) VALUES (?)",
                (version,),
            )

            logger.info("Migration applied: %s", filename)
