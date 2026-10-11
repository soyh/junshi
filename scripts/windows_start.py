"""Use the customer's Python environment without creating a virtual environment."""
import importlib.metadata
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("fastapi", "uvicorn", "pydantic", "pydantic-settings", "httpx",
            "cryptography", "python-multipart", "imageio-ffmpeg")


def main():
    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required.")
        return 1
    print(f"Using Python {sys.version.split()[0]}: {sys.executable}", flush=True)
    missing = []
    for package in PACKAGES:
        try:
            importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(package)
    if missing:
        print("Missing application dependencies: " + ", ".join(missing))
        print("Run this command in PowerShell, then double-click the launcher again:")
        # PowerShell single-quote escaping handles spaces and apostrophes in paths.
        executable = sys.executable.replace("'", "''")
        requirements = str(ROOT / "backend/requirements.txt").replace("'", "''")
        print(f"& '{executable}' -m pip install -r '{requirements}'")
        print("No packages were installed or changed automatically.")
        return 1
    if not (ROOT / ".env").exists() and not (ROOT / "backend/.env").exists():
        result = subprocess.run([sys.executable, str(ROOT / "scripts/init_local.py")], cwd=ROOT)
        if result.returncode:
            return result.returncode
    import start_local
    return start_local.main()


if __name__ == "__main__":
    raise SystemExit(main())
