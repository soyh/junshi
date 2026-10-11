from __future__ import annotations

from ipaddress import ip_address

import uvicorn

from app.config.settings import Settings, get_settings


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True

    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _uvicorn_options(current_settings: Settings) -> dict[str, object]:
    is_production = current_settings.app_env.lower() == "production"
    if is_production and not _is_loopback_host(current_settings.host):
        raise RuntimeError(
            "production launcher requires a loopback HOST until a trusted "
            "reverse-proxy boundary is explicitly configured"
        )

    return {
        "host": current_settings.host,
        "port": current_settings.port,
        "workers": 1,
        "reload": False,
        "proxy_headers": False,
        "forwarded_allow_ips": "",
        "server_header": False,
        "log_level": current_settings.log_level.lower(),
    }


def main() -> None:
    current_settings = get_settings()
    uvicorn.run(
        "app.main:app",
        **_uvicorn_options(current_settings),
    )


if __name__ == "__main__":
    main()
