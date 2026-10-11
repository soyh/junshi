import os
import sqlite3
from contextlib import contextmanager

from app.config.settings import get_settings


def initialize_database() -> None:
    settings = get_settings()

    db_dir = os.path.dirname(settings.database_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")


@contextmanager
def get_connection():
    settings = get_settings()

    conn = sqlite3.connect(
        settings.database_path,
        timeout=5.0,
    )
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
