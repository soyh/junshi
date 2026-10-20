"""Channel bridge plugin: configuration and process control.

The bridge is bundled as a separate executable (JunshiBridge.exe) because it
drives WeChat / Edge automation and must never block or crash the assistant.
This module owns its config file and lifecycle; the GUI only calls into it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

CHANNELS = {"wechat": "微信", "xhs": "小红书", "soul": "Soul"}
CHANNEL_LABELS = {label: key for key, label in CHANNELS.items()}
DEFAULT_QUIET = ("03:00", "05:30")


def app_data_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "JunshiPC"


def plugin_dir() -> Path:
    path = app_data_dir() / "bridge"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return plugin_dir() / "config.toml"


def pid_path() -> Path:
    return plugin_dir() / "bridge.pid"


def _toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_config(
    server: str,
    username: str,
    password: str,
    channel: str,
    dry_run: bool = True,
    daily_cap: int = 30,
    quiet: tuple[str, str] = DEFAULT_QUIET,
    verify_tls: bool = True,
) -> str:
    if channel not in CHANNELS:
        raise ValueError("不支持的平台通道")
    if not server.strip():
        raise ValueError("请填写服务器地址")
    if not username.strip() or not password:
        raise ValueError("请填写军师账号与密码")
    verify = "true" if verify_tls and not server.startswith("http://") else "false"
    return f"""[app]
base_url = {_toml(server.strip())}
username = {_toml(username.strip())}
password = {_toml(password)}
verify_tls = {verify}
timeout_seconds = 120

[bot]
dry_run = {"true" if dry_run else "false"}
auto_create_person = true
auto_merge_same_name = false
debounce_seconds = 4
max_debounce_seconds = 20
human_delay_seconds = [2.0, 6.0]
daily_reply_cap = {int(daily_cap)}
quiet_hours = [{_toml(quiet[0])}, {_toml(quiet[1])}]
max_reply_chars = 500
reply_to_groups = false
max_concurrency = 2
state_path = "state.sqlite3"

[channel]
kind = {_toml(channel)}
"""


def save_config(**kwargs) -> Path:
    text = build_config(**kwargs)
    path = config_path()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
    return path


def load_config_summary() -> dict:
    try:
        data = tomllib.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return {}
    app = data.get("app", {})
    bot = data.get("bot", {})
    channel = data.get("channel", {})
    quiet = bot.get("quiet_hours") or list(DEFAULT_QUIET)
    return {
        "server": str(app.get("base_url", "")),
        "username": str(app.get("username", "")),
        "password": str(app.get("password", "")),
        "channel": str(channel.get("kind", "wechat")),
        "dry_run": bool(bot.get("dry_run", True)),
        "daily_cap": int(bot.get("daily_reply_cap", 30)),
        "quiet": (str(quiet[0]), str(quiet[1])),
        "verify_tls": bool(app.get("verify_tls", True)),
    }


def _install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def executable_command(config: Path) -> tuple[list[str], dict | None]:
    root = _install_root()
    for candidate in (root / "JunshiBridge" / "JunshiBridge.exe", root / "JunshiBridge.exe"):
        if candidate.is_file():
            return [str(candidate), "--config", str(config), "run"], None
    plugins = root / "plugins" / "bridge"
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(plugins) + (os.pathsep + existing if existing else "")
    return [sys.executable, "-m", "lovebridge", "--config", str(config), "run"], environment


def start(config: Path | None = None) -> int:
    config = config or config_path()
    if not config.is_file():
        raise ValueError("尚未保存通道配置")
    if is_running():
        return read_pid() or 0
    command, environment = executable_command(config)
    flags = 0
    if sys.platform == "win32":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        command,
        cwd=str(plugin_dir()),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    pid_path().write_text(str(process.pid), encoding="ascii")
    return process.pid


def read_pid() -> int | None:
    try:
        return int(pid_path().read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        import ctypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        kernel.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_running() -> bool:
    pid = read_pid()
    return bool(pid and _pid_alive(pid))


def stop() -> bool:
    pid = read_pid()
    if not pid or not _pid_alive(pid):
        pid_path().unlink(missing_ok=True)
        return False
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, check=False) if sys.platform == "win32" else os.kill(pid, 15)
    pid_path().unlink(missing_ok=True)
    return True


def fetch_status(client) -> list[dict]:
    rows = client.request("GET", "/bridge/status")
    return rows if isinstance(rows, list) else []


def status_lines(rows: list[dict]) -> list[str]:
    by_key = {}
    for row in rows:
        channel = "wechat" if row.get("channel") == "wechatauto" else row.get("channel")
        by_key[channel] = row
    lines = []
    for key in ("wechat", "xhs", "soul"):
        row = by_key.get(key)
        label = CHANNELS[key]
        if row:
            state = "在线" if row.get("status") == "online" else str(row.get("status"))
            lines.append(f"{label}：{state} · 今日回复 {row.get('replies_today', 0)} · {row.get('updated_at', '')}")
        else:
            lines.append(f"{label}：未上报")
    return lines
