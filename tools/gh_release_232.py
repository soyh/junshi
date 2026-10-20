"""Create the Build 232 release and upload its installer."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
TAG = "pc-bridge-plugin-5"
NAME = "PC 通道插件版 Build 232（多通道独立 · 无头浏览器）"
BODY = ROOT / "build" / "release-body-232.md"
ASSET = ROOT / "desktop" / "builds" / "pc-v232" / "JunshiPC-232-Windows-x64.zip"


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
    headers = {
        "Authorization": f"token {token()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "junshi-bridge-build",
    }
    with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=120) as client:
        response = client.get(f"/repos/soyh/junshi/releases/tags/{TAG}")
        if response.status_code == 404:
            payload = {
                "tag_name": TAG,
                "name": NAME,
                "body": BODY.read_text(encoding="utf-8"),
            }
            response = client.post("/repos/soyh/junshi/releases", json=payload)
            print("create", response.status_code, flush=True)
            response.raise_for_status()
        elif response.status_code == 200:
            # Refresh the notes so the published page matches this build.
            release_id = response.json()["id"]
            patch = client.patch(
                f"/repos/soyh/junshi/releases/{release_id}",
                json={"name": NAME, "body": BODY.read_text(encoding="utf-8")},
            )
            print("update", patch.status_code, flush=True)
            response = patch
        release = response.json()
        print("release", release["id"], release["html_url"], flush=True)

        existing = {asset["name"]: asset for asset in release.get("assets", [])}
        if ASSET.name in existing and existing[ASSET.name]["state"] == "uploaded":
            print("asset already uploaded", existing[ASSET.name]["size"], flush=True)
            return

        url = f"https://uploads.github.com/repos/soyh/junshi/releases/{release['id']}/assets"
        started = time.time()
        with httpx.Client(timeout=httpx.Timeout(3600.0, connect=60.0)) as upload:
            with ASSET.open("rb") as handle:
                response = upload.post(
                    url,
                    params={"name": ASSET.name},
                    headers={
                        "Authorization": f"token {token()}",
                        "Content-Type": "application/zip",
                        "User-Agent": "junshi-bridge-build",
                    },
                    content=handle,
                )
        print("upload", response.status_code, f"{time.time() - started:.1f}s", flush=True)
        if response.status_code >= 300:
            print(response.text[:500], flush=True)
            sys.exit(1)
        asset = response.json()
        print("asset", asset["id"], asset["state"], asset["size"], flush=True)


main()
