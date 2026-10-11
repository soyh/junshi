"""Check tracked public files; report paths only, never secret values."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
problems = []
for name in filter(None, paths):
    path = ROOT / name
    if not path.is_file():
        continue
    base = path.name.lower()
    private = (
        (base.startswith(".env") and base != ".env.example")
        or base.endswith((".sqlite", ".sqlite3", ".db", "-wal", "-shm", ".pem", ".key", ".bundle", ".log"))
        or (name.startswith(("data/", "logs/")) and base != ".gitkeep")
        or base in {"id_rsa", "id_ed25519"}
    )
    if private:
        problems.append(f"Private file type: {name}")
        continue
    text = path.read_bytes().decode("utf-8", errors="replace")
    if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,})\b", text):
        problems.append(f"Possible credential: {name}")
if problems:
    raise SystemExit("\n".join(problems))
print("Public tracked-file checks: PASS (does not replace manual review)")
