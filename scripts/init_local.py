"""Create a fresh, private loopback installation; never overwrite user data."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from cryptography.fernet import Fernet


def initialize(root: Path, port: int = 18080) -> Path:
    root = root.resolve()
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    config = root / ".env"
    if config.exists() or config.is_symlink() or (root / "backend/.env").exists() or (root / "backend/.env").is_symlink():
        raise ValueError("Existing configuration found. Preserve it; do not initialize again.")
    for name in ("data", "logs"):
        folder = root / name
        if folder.is_symlink():
            raise ValueError("Storage directory must not be a symlink")
        if folder.exists() and any(p.name != ".gitkeep" for p in folder.iterdir()):
            raise ValueError("Existing runtime data found. Use the documented upgrade/restore procedure.")
    # Single quotes and forward slashes keep dotenv paths portable, including spaces.
    if any(c in str(root) for c in "'\n\r"):
        raise ValueError("Choose an installation path without quotes or line breaks")
    paths = {
        "DATABASE_PATH": root / "data/app.sqlite3",
        "MEDIA_STORAGE_DIRECTORY": root / "data/media",
        "LOG_DIR": root / "logs",
        "PORTABLE_BACKUP_DIRECTORY": root / "data/recovery_exports",
    }
    lines = ["APP_NAME=AI Love Strategist", "APP_ENV=production", "APP_DEBUG=false",
             "HOST=127.0.0.1", f"PORT={port}", "LOG_LEVEL=INFO",
             "AUTH_BOOTSTRAP_ENABLED=false", "AUTH_BEARER_TOKEN="]
    lines += [f"{key}='{path.as_posix()}'" for key, path in paths.items()]
    lines += ["LLM_CONFIG_ENCRYPTION_KEY=" + Fernet.generate_key().decode("ascii"),
              "PORTABLE_BACKUP_ENCRYPTION_KEY=" + Fernet.generate_key().decode("ascii"),
              "PORTABLE_BACKUP_KEEP=7"]
    for directory in (root / "data/media", root / "data/backups", root / "data/recovery_exports", root / "logs"):
        directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines) + "\n")
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    try:
        initialize(Path(__file__).resolve().parents[1], args.port)
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Initialization refused: {exc}") from exc
    print("Local configuration created. Keys were generated privately, not printed.")
    print("Keep .env with your private backups; never commit it.")
    print("Start from the repository root: python -m app.server")
    print(f"Open http://127.0.0.1:{args.port}/app")


if __name__ == "__main__":
    main()
