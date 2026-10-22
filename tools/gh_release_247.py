"""Create the Build 247 release and upload its installer with curl.

httpx uploads stall on this network (proxy fake-IP), curl --retry works.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
TAG = "pc-bridge-plugin-20"
NAME = "PC 通道插件版 Build 247（老家/当前所在地/工作地址 · 手机端键盘与消息编辑）"
BODY = ROOT / "build" / "release-body-247.md"
ASSET = ROOT / "builds" / "pc-v247" / "JunshiPC-247-Windows-x64.zip"


def token() -> str:
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


def main() -> None:
    if not ASSET.is_file():
        raise SystemExit(f"missing asset: {ASSET}")
    digest = hashlib.sha256(ASSET.read_bytes()).hexdigest()
    body = BODY.read_text(encoding="utf-8").replace("__SIZE__", str(ASSET.stat().st_size)).replace(
        "__SHA__", digest
    )
    headers = {
        "Authorization": f"token {token()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "junshi-bridge-build",
    }
    with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=120) as client:
        response = client.get(f"/repos/soyh/junshi/releases/tags/{TAG}")
        if response.status_code == 404:
            payload = {"tag_name": TAG, "name": NAME, "body": body}
            response = client.post("/repos/soyh/junshi/releases", json=payload)
            print("create", response.status_code, flush=True)
            response.raise_for_status()
        elif response.status_code == 200:
            release_id = response.json()["id"]
            response = client.patch(
                f"/repos/soyh/junshi/releases/{release_id}", json={"name": NAME, "body": body}
            )
            print("update", response.status_code, flush=True)
            response.raise_for_status()
        release = response.json()
        print("release", release["id"], release["html_url"], flush=True)

        existing = {asset["name"]: asset for asset in release.get("assets", [])}
        if ASSET.name in existing and existing[ASSET.name]["state"] == "uploaded":
            print("asset already uploaded", existing[ASSET.name]["size"], flush=True)
            return

        url = (
            f"https://uploads.github.com/repos/soyh/junshi/releases/{release['id']}"
            f"/assets?name={ASSET.name}"
        )
        command = [
            "curl", "-sS", "--http1.1", "--retry", "6", "--retry-all-errors",
            "--connect-timeout", "30", "--max-time", "3600",
            "-o", str(ROOT / "build" / "upload-247.json"),
            "-w", "%{http_code} time=%{time_total}s speed=%{speed_download}B/s\n",
            "-X", "POST",
            "-H", f"Authorization: Bearer {token()}",
            "-H", "Content-Type: application/zip",
            "-H", "User-Agent: junshi-bridge-build",
            "-T", str(ASSET), url,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        print("upload", result.stdout.strip(), result.stderr.strip()[:300], flush=True)
        if not result.stdout.startswith("201"):
            sys.exit(1)
        print((ROOT / "build" / "upload-247.json").read_text(encoding="utf-8")[:400], flush=True)


main()
