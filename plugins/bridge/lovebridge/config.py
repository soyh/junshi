"""Configuration loading for lovebridge.

One TOML file describes how to reach the app, how the bot should behave, and
which channel adapter to run.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppConfig:
    base_url: str
    username: str
    password: str
    verify_tls: bool = True
    timeout_seconds: float = 120.0


@dataclass(frozen=True)
class BotConfig:
    dry_run: bool = True
    auto_create_person: bool = True
    auto_merge_same_name: bool = False
    debounce_seconds: float = 4.0
    max_debounce_seconds: float = 20.0
    human_delay_seconds: tuple[float, float] = (1.5, 5.0)
    daily_reply_cap: int = 150
    quiet_hours: tuple[str, str] | None = None
    max_reply_chars: int = 500
    reply_to_groups: bool = False
    max_concurrency: int = 3
    browser_window: str = "hide"
    state_path: Path = Path("bridge-state.sqlite3")


@dataclass(frozen=True)
class ChannelConfig:
    kind: str
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Config:
    app: AppConfig
    bot: BotConfig
    channel: ChannelConfig
    source_path: Path


def _require(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"missing [{section}] {key}")
    return mapping[key]


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config not found: {path}")

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc

    app_raw = raw.get("app", {})
    app = AppConfig(
        base_url=str(_require(app_raw, "base_url", "app")).rstrip("/"),
        username=str(_require(app_raw, "username", "app")),
        password=str(_require(app_raw, "password", "app")),
        verify_tls=bool(app_raw.get("verify_tls", True)),
        timeout_seconds=float(app_raw.get("timeout_seconds", 120.0)),
    )

    bot_raw = raw.get("bot", {})
    delay = bot_raw.get("human_delay_seconds", [1.5, 5.0])
    if isinstance(delay, (int, float)):
        delay = (0.0, float(delay))
    if not (isinstance(delay, (list, tuple)) and len(delay) == 2 and delay[0] <= delay[1]):
        raise ConfigError("[bot] human_delay_seconds must be a number or [min, max]")

    quiet = bot_raw.get("quiet_hours")
    if quiet is not None:
        if not (isinstance(quiet, (list, tuple)) and len(quiet) == 2):
            raise ConfigError('[bot] quiet_hours must be ["HH:MM", "HH:MM"]')
        quiet = (str(quiet[0]), str(quiet[1]))

    state_path = Path(bot_raw.get("state_path", "bridge-state.sqlite3"))
    if not state_path.is_absolute():
        state_path = path.parent / state_path

    bot = BotConfig(
        dry_run=bool(bot_raw.get("dry_run", True)),
        auto_create_person=bool(bot_raw.get("auto_create_person", True)),
        auto_merge_same_name=bool(bot_raw.get("auto_merge_same_name", False)),
        debounce_seconds=float(bot_raw.get("debounce_seconds", 4.0)),
        max_debounce_seconds=float(bot_raw.get("max_debounce_seconds", 20.0)),
        human_delay_seconds=(float(delay[0]), float(delay[1])),
        daily_reply_cap=int(bot_raw.get("daily_reply_cap", 150)),
        quiet_hours=quiet,
        max_reply_chars=int(bot_raw.get("max_reply_chars", 500)),
        reply_to_groups=bool(bot_raw.get("reply_to_groups", False)),
        max_concurrency=max(1, int(bot_raw.get("max_concurrency", 3))),
        browser_window=str(bot_raw.get("browser_window", "hide")).lower(),
        state_path=state_path,
    )

    channel_raw = raw.get("channel", {})
    kind = str(channel_raw.get("kind", "mock")).lower()
    settings = {k: v for k, v in channel_raw.items() if k != "kind" and not isinstance(v, dict)}
    # Allow either flat keys under [channel] or a nested [channel.<kind>] table.
    nested = channel_raw.get(kind)
    if isinstance(nested, dict):
        settings.update(nested)
    if kind == "webhook":
        settings.setdefault("listen_host", "127.0.0.1")
        settings.setdefault("listen_port", 18200)
        settings.setdefault("path", "/inbound")
        settings.setdefault("send_timeout", 30)

    if kind not in {"mock", "webhook", "wcferry", "wxhook", "wechatauto", "xhs", "soul"}:
        raise ConfigError(f"unknown channel kind: {kind}")

    return Config(app=app, bot=bot, channel=ChannelConfig(kind=kind, settings=settings), source_path=path)
