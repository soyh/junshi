"""Start a configured local installation and open its page when ready."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ready(base_url: str, app_name: str) -> bool:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(base_url + "/health", timeout=1) as response:
            identity = json.load(response)
        with opener.open(base_url + "/health/ready", timeout=1) as response:
            health = json.load(response)
        return identity.get("service") == app_name and health.get("status") == "ready"
    except (OSError, ValueError, AttributeError):
        return False


def port_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def open_page(url: str) -> None:
    print(f"Open: {url}", flush=True)
    try:
        if not webbrowser.open(url):
            print("Browser did not open automatically. Copy the address above.")
    except webbrowser.Error:
        print("Browser unavailable. Copy the address above.")


def launch(host: str, port: int, app_name: str, timeout: float = 60) -> int:
    base = f"http://[{host}]:{port}" if ":" in host else f"http://{host}:{port}"
    if port_in_use(host, port):
        if ready(base, app_name):
            print("Application is already running; opening its page.")
            open_page(base + "/app")
            return 0
        print(f"Port {port} is occupied or the service is not ready. No process was stopped.")
        print("Check the existing window or change PORT in your private .env.")
        return 1
    process = subprocess.Popen([sys.executable, "-m", "app.server"], cwd=ROOT)
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                print("Server exited before becoming ready. See its error above.")
                return 1
            if ready(base, app_name):
                open_page(base + "/app")
                print("Keep this window open. Press Ctrl+C to stop the application.", flush=True)
                return process.wait()
            time.sleep(0.25)
        print("Startup timed out. See server output above; browser was not opened.")
        return 1
    except KeyboardInterrupt:
        print("\nStopping the application started by this window...")
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    if not (ROOT / ".env").is_file() and not (ROOT / "backend/.env").is_file():
        print("Configuration missing. Run .venv\\Scripts\\python.exe scripts/init_local.py first.")
        return 1
    sys.path.insert(0, str(ROOT))
    try:
        from app.config.settings import get_settings
        from app.server import _is_loopback_host
        settings = get_settings()
        if not _is_loopback_host(settings.host):
            print("This local launcher requires a loopback HOST (127.0.0.1 or localhost).")
            return 1
        return launch(settings.host, settings.port, settings.app_name)
    except Exception as exc:
        # Settings validation may include sensitive input: never print its values.
        print(f"Cannot start ({type(exc).__name__}). Check dependencies and private configuration.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
