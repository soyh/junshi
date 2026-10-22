"""Publish the signed Android 1.0.2 APK to its own release."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
TAG = "android-v1.0.2"
NAME = "Android 1.0.2（小窗输入不再闪 · 消息弹层编辑）"
ASSET = Path("C:/Users/12274/Documents/deepseek-harness/default-workspace/JunshiAndroid-1.0.2.apk")
BODY = ROOT / "android" / "RELEASE.md"


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
    digest = hashlib.sha256(ASSET.read_bytes()).hexdigest()
    text = BODY.read_text(encoding="utf-8")
    first = text.split("\n# Android 1.0.1")[0]
    body = first.replace("## Android", "## Android") + f"\nAPK SHA-256：`{digest}`。\n"
    headers = {
        "Authorization": f"token {token()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "junshi-bridge-build",
    }
    with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=120) as client:
        response = client.get(f"/repos/soyh/junshi/releases/tags/{TAG}")
        if response.status_code == 404:
            response = client.post(
                "/repos/soyh/junshi/releases",
                json={"tag_name": TAG, "name": NAME, "body": body},
            )
            print("create", response.status_code, flush=True)
            response.raise_for_status()
        else:
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
            "--connect-timeout", "30", "--max-time", "1800",
            "-o", str(ROOT / "build" / "upload-android-102.json"),
            "-w", "%{http_code} time=%{time_total}s speed=%{speed_download}B/s\n",
            "-X", "POST",
            "-H", f"Authorization: Bearer {token()}",
            "-H", "Content-Type: application/vnd.android.package-archive",
            "-H", "User-Agent: junshi-bridge-build",
            "-T", str(ASSET), url,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        print("upload", result.stdout.strip(), result.stderr.strip()[:300], flush=True)
        if not result.stdout.startswith("201"):
            raise SystemExit(1)


main()
