import pytest

from app import server
from app.config.settings import Settings


def _settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "host": "127.0.0.1",
        "port": 18080,
        "log_level": "INFO",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_launcher_is_loopback_single_worker_and_no_proxy_trust():
    options = server._uvicorn_options(_settings())

    assert options == {
        "host": "127.0.0.1",
        "port": 18080,
        "workers": 1,
        "reload": False,
        "proxy_headers": False,
        "forwarded_allow_ips": "",
        "server_header": False,
        "log_level": "info",
    }


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "::1"])
def test_production_launcher_accepts_loopback_hosts(host):
    options = server._uvicorn_options(_settings(host=host))

    assert options["host"] == host
    assert options["proxy_headers"] is False


def test_production_launcher_rejects_public_or_wildcard_bind():
    with pytest.raises(RuntimeError, match="loopback HOST"):
        server._uvicorn_options(_settings(host="0.0.0.0"))


def test_non_production_can_explicitly_use_non_loopback_bind():
    options = server._uvicorn_options(
        _settings(app_env="development", host="0.0.0.0", port=19090)
    )

    assert options["host"] == "0.0.0.0"
    assert options["port"] == 19090
    assert options["proxy_headers"] is False


def test_main_uses_import_string_and_secure_options(monkeypatch):
    current_settings = _settings(port=18181, log_level="WARNING")
    captured = {}

    monkeypatch.setattr(server, "get_settings", lambda: current_settings)

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured["kwargs"] = kwargs

    monkeypatch.setattr(server.uvicorn, "run", fake_run)

    server.main()

    assert captured["app"] == "app.main:app"
    assert captured["kwargs"] == {
        "host": "127.0.0.1",
        "port": 18181,
        "workers": 1,
        "reload": False,
        "proxy_headers": False,
        "forwarded_allow_ips": "",
        "server_header": False,
        "log_level": "warning",
    }
