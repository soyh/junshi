from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import _fastapi_surface_options


def _settings(*, app_env: str, app_debug: bool) -> Settings:
    return Settings(
        app_env=app_env,
        app_debug=app_debug,
        _env_file=None,
    )


def test_production_forces_debug_off_and_disables_api_docs():
    options = _fastapi_surface_options(
        _settings(app_env="production", app_debug=True)
    )

    assert options == {
        "debug": False,
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


def test_production_surface_has_no_docs_redoc_or_openapi_routes():
    app = FastAPI(
        **_fastapi_surface_options(
            _settings(app_env="PrOdUcTiOn", app_debug=True)
        )
    )
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert app.debug is False


def test_development_keeps_docs_and_respects_debug_setting():
    app = FastAPI(
        **_fastapi_surface_options(
            _settings(app_env="development", app_debug=True)
        )
    )
    client = TestClient(app)

    assert app.debug is True
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_non_production_can_disable_debug_without_disabling_docs():
    app = FastAPI(
        **_fastapi_surface_options(
            _settings(app_env="test", app_debug=False)
        )
    )
    client = TestClient(app)

    assert app.debug is False
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
