import atexit
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Production hosts use an absolute default DATABASE_PATH under /opt.  Pytest may
# collect or execute tests that do not request the client fixture, so relying on
# per-test monkeypatching alone is not a sufficient safety boundary.  Install a
# process-wide disposable default before importing any application modules.
# Individual tests remain free to monkeypatch DATABASE_PATH to their own tmp_path.
_TEST_PROCESS_ROOT = Path(tempfile.mkdtemp(prefix="ai-love-strategist-pytest-"))
os.environ["DATABASE_PATH"] = str(_TEST_PROCESS_ROOT / "default.sqlite3")
os.environ["LOG_DIR"] = str(_TEST_PROCESS_ROOT / "logs")
atexit.register(shutil.rmtree, _TEST_PROCESS_ROOT, ignore_errors=True)

from app.config.settings import get_settings
from app.core.database import get_connection
from app.main import app
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


class LegacyIsolationSessionAdapter:
    """Run historical user-isolation tests through real auth sessions.

    Older business tests used X-User-ID as a convenient way to select a foreign
    user. TEST-122 retires that header at the application boundary. Rather than
    weakening production authentication or rewriting dozens of otherwise valid
    business-isolation assertions, this test-only adapter translates the legacy
    test input into a real opaque DB-backed Bearer session before the request
    reaches FastAPI.

    Auth contract tests bypass this adapter so X-User-ID rejection is exercised
    exactly as it is in production code.
    """

    def __init__(self, client: TestClient):
        self._client = client
        self._tokens_by_user_id: dict[str, str] = {}

    def __getattr__(self, name):
        return getattr(self._client, name)

    @staticmethod
    def _pop_legacy_user_id(headers: dict) -> str | None:
        for key in list(headers):
            if str(key).lower() == "x-user-id":
                value = headers.pop(key)
                return str(value)
        return None

    @staticmethod
    def _has_authorization(headers: dict) -> bool:
        return any(str(key).lower() == "authorization" for key in headers)

    def _token_for_user(self, user_id: str) -> str:
        existing = self._tokens_by_user_id.get(user_id)
        if existing is not None:
            return existing

        with get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
            created = auth_session_service.create(conn, user_id)

        self._tokens_by_user_id[user_id] = created.access_token
        return created.access_token

    def _translated_kwargs(self, kwargs: dict) -> dict:
        raw_headers = kwargs.get("headers")
        if not raw_headers:
            return kwargs

        headers = dict(raw_headers)
        user_id = self._pop_legacy_user_id(headers)
        if user_id is None:
            return kwargs

        if not self._has_authorization(headers):
            headers["Authorization"] = f"Bearer {self._token_for_user(user_id)}"

        translated = dict(kwargs)
        translated["headers"] = headers
        return translated

    def request(self, method: str, url, **kwargs):
        return self._client.request(method, url, **self._translated_kwargs(kwargs))

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url, **kwargs):
        return self.request("HEAD", url, **kwargs)


@pytest.fixture()
def client(tmp_path, monkeypatch, request):
    database_path = tmp_path / "test.sqlite3"

    monkeypatch.setenv("DATABASE_PATH", str(database_path))

    get_settings.cache_clear()

    with TestClient(app) as test_client:
        test_filename = request.node.path.name
        if test_filename.startswith("test_auth_"):
            yield test_client
        else:
            yield LegacyIsolationSessionAdapter(test_client)

    get_settings.cache_clear()
