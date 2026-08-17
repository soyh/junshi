import pytest
from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "test.sqlite3"

    monkeypatch.setenv("DATABASE_PATH", str(database_path))

    get_settings.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
