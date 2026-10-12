"""Exercise a clean install and non-overwrite guards using disposable data."""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


def run():
    with tempfile.TemporaryDirectory(prefix="junshi-install-") as temporary:
        root = Path(temporary) / "installation with spaces"
        root.mkdir()
        for name in ("app", "backend/app", "backend/migrations"):
            shutil.copytree(SOURCE / name, root / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (root / "scripts").mkdir()
        shutil.copy2(SOURCE / "scripts/init_local.py", root / "scripts/init_local.py")
        shutil.copy2(SOURCE / "scripts/start_local.py", root / "scripts/start_local.py")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("APP_", "DATABASE_", "MEDIA_", "LOG_", "AUTH_", "LLM_", "PORTABLE_", "QWEN_", "DASHSCOPE_", "LOCAL_USER_")) and k.upper() not in {"HOST", "PORT", "PYTHONPATH"}}
        command = [sys.executable, "scripts/init_local.py", "--port", str(port)]
        subprocess.run(command, cwd=root, env=env, check=True)
        original = (root / ".env").read_bytes()
        refusal = subprocess.run(command, cwd=root, env=env, capture_output=True)
        assert refusal.returncode != 0 and (root / ".env").read_bytes() == original
        # Prevent initializing over a backend override or pre-existing database.
        (root / ".env").unlink()
        (root / "backend/.env").write_text("APP_ENV=production\n", encoding="utf8")
        assert subprocess.run(command, cwd=root, env=env, capture_output=True).returncode != 0
        (root / "backend/.env").unlink()
        (root / "data/app.sqlite3").write_bytes(b"existing data sentinel")
        assert subprocess.run(command, cwd=root, env=env, capture_output=True).returncode != 0
        assert (root / "data/app.sqlite3").read_bytes() == b"existing data sentinel"
        (root / "data/app.sqlite3").unlink()
        (root / ".env").write_bytes(original)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with (root / "smoke.log").open("w", encoding="utf8") as log:
            process = subprocess.Popen([sys.executable, "-m", "app.server"], cwd=root, env=env, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        raise AssertionError("Local server exited; inspect disposable smoke log")
                    try:
                        with opener.open(f"http://127.0.0.1:{port}/health/ready", timeout=2) as response:
                            ready = json.load(response)
                        break
                    except OSError:
                        time.sleep(0.2)
                else:
                    raise AssertionError("Local server did not become ready")
                assert ready["status"] == "ready"
                assert ready["migrations"]["applied_count"] == 22
                with opener.open(f"http://127.0.0.1:{port}/app", timeout=5) as response:
                    assert response.status == 200 and len(response.read()) > 1000
                # Exercise configured port discovery and reuse against a real server,
                # replacing only the browser itself in headless CI.
                probe = (
                    "import sys; sys.path.insert(0, 'scripts'); import start_local; "
                    "opened=[]; start_local.webbrowser.open=lambda url: opened.append(url) or True; "
                    "assert start_local.main()==0; "
                    f"assert opened==['http://127.0.0.1:{port}/app']"
                )
                subprocess.run([sys.executable, "-c", probe], cwd=root, env=env, check=True, timeout=15)
            finally:
                process.terminate()
                process.wait(timeout=15)
    print("Fresh local install, existing data guards, 22 migrations and /app: PASS")


if __name__ == "__main__":
    run()
