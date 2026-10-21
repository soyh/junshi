"""Channel bridge plugin: multi-profile configuration and process control.

Each profile is an isolated bridge instance: its own 军师 account, channel,
browser login state, state database, log and PID. Several profiles can run at
the same time (多开); each runs in its own JunshiBridge.exe process.

WeChat limitation: one Windows session can only have one logged-in WeChat
account, so a second WeChat profile needs another Windows user/VM. 小红书 and
Soul use separate browser profiles per profile and can run in parallel.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import uuid
from datetime import datetime, timezone
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


def profiles_dir() -> Path:
    path = plugin_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def profile_dir(profile_id: str) -> Path:
    path = profiles_dir() / profile_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path(profile_id: str) -> Path:
    return profile_dir(profile_id) / "config.toml"


def pid_path(profile_id: str) -> Path:
    return profile_dir(profile_id) / "bridge.pid"


def status_path(profile_id: str) -> Path:
    return profile_dir(profile_id) / "status.json"


def _toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_config(
    name: str,
    server: str,
    username: str,
    password: str,
    channel: str,
    dry_run: bool = True,
    daily_cap: int = 30,
    quiet: tuple[str, str] = DEFAULT_QUIET,
    verify_tls: bool = True,
    browser_dir: str | None = None,
    headless: bool = True,
    browser_window: str = "hide",
    rules: str = "",
) -> str:
    if channel not in set(CHANNELS) | {"mock"}:
        raise ValueError("不支持的平台通道")
    if not server.strip():
        raise ValueError("请填写服务器地址")
    if not username.strip() or not password:
        raise ValueError("请填写军师账号与密码")
    verify = "true" if verify_tls and not server.startswith("http://") else "false"
    text = f"""[profile]
name = {_toml(name.strip() or "未命名通道")}

[app]
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
rules = {_toml(str(rules or "").strip())}
max_concurrency = 2
browser_window = {_toml(browser_window)}
state_path = "state.sqlite3"

[channel]
kind = {_toml(channel)}
"""
    if channel in ("xhs", "soul"):
        text += (
            f"\n[channel.{channel}]\n"
            f"profile_dir = {_toml(browser_dir or '')}\n"
            "interval = 4.0\n"
            f"headless = {'true' if headless else 'false'}\n"
            f"window_mode = {_toml(browser_window)}\n"
        )
    return text


def save_profile(profile_id: str, **kwargs) -> Path:
    channel = kwargs.get("channel", "wechat")
    kwargs.setdefault("browser_dir", str(profile_dir(profile_id) / "browser" / channel))
    path = config_path(profile_id)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(build_config(**kwargs), encoding="utf-8")
    temporary.replace(path)
    return path


def _read(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return {}


def summary(profile_id: str) -> dict:
    data = _read(config_path(profile_id))
    app = data.get("app", {})
    bot = data.get("bot", {})
    channel = data.get("channel", {})
    profile = data.get("profile", {})
    quiet = bot.get("quiet_hours") or list(DEFAULT_QUIET)
    return {
        "id": profile_id,
        "name": str(profile.get("name") or profile_id),
        "server": str(app.get("base_url", "")),
        "username": str(app.get("username", "")),
        "password": str(app.get("password", "")),
        "channel": str(channel.get("kind", "wechat")),
        "headless": bool(channel.get(str(channel.get("kind", "")), {}).get("headless", True)),
        "browser_window": str(bot.get("browser_window", "hide")).lower(),
        "dry_run": bool(bot.get("dry_run", True)),
        "daily_cap": int(bot.get("daily_reply_cap", 30)),
        "quiet": (str(quiet[0]), str(quiet[1])),
        "verify_tls": bool(app.get("verify_tls", True)),
        "rules": str(bot.get("rules", "")),
        "running": is_running(profile_id),
        "status": local_status(profile_id)["status"],
    }


def _migrate_legacy() -> None:
    legacy = plugin_dir() / "config.toml"
    if not legacy.is_file():
        return
    if any(path.is_dir() for path in profiles_dir().iterdir()):
        return
    target = profile_dir("default")
    for item in (legacy, plugin_dir() / "bridge.pid", plugin_dir() / "state.sqlite3"):
        if item.is_file():
            shutil.copy2(item, target / item.name)
            item.unlink(missing_ok=True)


def list_profiles() -> list[dict]:
    _migrate_legacy()
    items = []
    for path in sorted(profiles_dir().iterdir()):
        if not path.is_dir() or not (path / "config.toml").is_file():
            continue
        items.append(summary(path.name))
    return items


def create_profile(name: str = "新通道", **kwargs) -> str:
    """Create a profile; with complete settings the config is written at once."""
    profile_id = uuid.uuid4().hex[:8]
    profile_dir(profile_id)
    required = {"server", "username", "password", "channel"}
    if required <= kwargs.keys():
        kwargs.setdefault("name", name)
        channel = kwargs.get("channel", "wechat")
        kwargs.setdefault("browser_dir", str(profile_dir(profile_id) / "browser" / channel))
        save_profile(profile_id, **kwargs)
    return profile_id


def delete_profile(profile_id: str) -> None:
    stop(profile_id)
    shutil.rmtree(profile_dir(profile_id), ignore_errors=True)


def _install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def executable_command(profile_id: str, subcommand: str = "run") -> tuple[list[str], dict | None]:
    config = config_path(profile_id)
    root = _install_root()
    for candidate in (root / "JunshiBridge" / "JunshiBridge.exe", root / "JunshiBridge.exe"):
        if candidate.is_file():
            return [str(candidate), "--config", str(config), subcommand], None
    plugins = root / "plugins" / "bridge"
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(plugins) + (os.pathsep + existing if existing else "")
    return [sys.executable, "-m", "lovebridge", "--config", str(config), subcommand], environment


def show_browser(profile_id: str) -> bool:
    """Bring a parked browser window back to the desktop (no restart)."""
    return _window_action(profile_id, "show")


def hide_browser(profile_id: str) -> bool:
    """Move the automation browser off the desktop while the bridge keeps running."""
    return _window_action(profile_id, "hide")


def _window_action(profile_id: str, action: str) -> bool:
    if not is_running(profile_id):
        return False
    command, environment = executable_command(profile_id, "window")
    command += ["--action", action]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        result = subprocess.run(
            command,
            cwd=str(profile_dir(profile_id)),
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def start(profile_id: str) -> int:
    if not config_path(profile_id).is_file():
        raise ValueError("请先保存通道配置")
    if is_running(profile_id):
        return read_pid(profile_id) or 0
    command, environment = executable_command(profile_id)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    process = subprocess.Popen(
        command,
        cwd=str(profile_dir(profile_id)),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    pid_path(profile_id).write_text(str(process.pid), encoding="ascii")
    return process.pid


def read_pid(profile_id: str) -> int | None:
    try:
        return int(pid_path(profile_id).read_text(encoding="ascii").strip())
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


def is_running(profile_id: str) -> bool:
    pid = read_pid(profile_id)
    return bool(pid and _pid_alive(pid))


def stop(profile_id: str) -> bool:
    pid = read_pid(profile_id)
    if not pid or not _pid_alive(pid):
        pid_path(profile_id).unlink(missing_ok=True)
        return False
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, check=False)
    else:
        os.kill(pid, 15)
    pid_path(profile_id).unlink(missing_ok=True)
    return True


def stop_all() -> int:
    count = 0
    for item in list_profiles():
        if stop(item["id"]):
            count += 1
    return count


def fetch_status(client) -> list[dict]:  # noqa: ANN001
    """Deprecated: the server aggregates per channel and cannot tell profiles apart.

    Kept for callers that only need the raw server rows; the desktop panel now
    reads the local status.json written by each bridge process.
    """
    rows = client.request("GET", "/bridge/status")
    return rows if isinstance(rows, list) else []


def read_status(profile_id: str) -> dict:
    try:
        data = json.loads(status_path(profile_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def local_status(profile_id: str) -> dict:
    """Current state of one profile, from its own process and status.json."""
    data = read_status(profile_id)
    running = is_running(profile_id)
    state = str(data.get("status") or "")
    updated = str(data.get("updated_at") or "")
    fresh = False
    if updated:
        try:
            fresh = (datetime.now() - datetime.fromisoformat(updated)).total_seconds() <= 120
        except ValueError:
            fresh = False
    outbox = data.get("outbox") if isinstance(data.get("outbox"), dict) else {}
    queued = int(outbox.get("queued") or 0)
    failed = int(outbox.get("failed") or 0)
    if not running:
        state = "未运行"
    elif not state:
        state = "启动中"
    elif state in ("online", "未登录") and not fresh:
        state = "无响应（心跳过期）"
    elif state == "online":
        state = "在线"
    if running and queued:
        state = f"{state} · 待重试 {queued}"
    if running and failed:
        state = f"{state} · {failed} 条未发出"
    return {
        "running": running,
        "pid": read_pid(profile_id),
        "status": state,
        "updated_at": updated,
        "replies_today": int(data.get("replies_today") or 0),
        "queued": queued,
        "failed": failed,
        "error": str(data.get("error") or ""),
    }


def status_lines(profiles: list[dict]) -> list[str]:
    """One line per profile — never merge profiles of the same platform."""
    lines = []
    for item in profiles:
        detail = local_status(item["id"])
        label = CHANNELS.get(item.get("channel", ""), item.get("channel", ""))
        stamp = detail["updated_at"][11:19] if len(detail["updated_at"]) >= 19 else "从未"
        line = (
            f"{label}｜{item.get('name', item['id'])}：{detail['status']}"
            f" · 今日回复 {detail['replies_today']} · 更新 {stamp}"
        )
        if detail.get("error"):
            line += f"｜{detail['error'][:40]}"
        lines.append(line)
    return lines or ["尚未创建通道：点「新建通道」为每个平台各建一个。"]
