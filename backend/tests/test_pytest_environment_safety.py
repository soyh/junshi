import os
from pathlib import Path


def test_pytest_process_default_database_isolated_from_production():
    configured = Path(os.environ["DATABASE_PATH"]).resolve()
    production = Path("/opt/ai-love-strategist/data/app.sqlite3").resolve()

    assert configured != production
    assert configured.name == "default.sqlite3"
    assert configured.parent.name.startswith("ai-love-strategist-pytest-")
