"""Retry the Build 253 asset upload on the existing release."""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

TAG = "pc-bridge-plugin-26"
NAME = "JunshiPC-253-Windows-x64.zip"
ZIP = Path("builds/pc-v253") / NAME


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


def request(url, data=None, method=None, headers=None, timeout=900):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "junshi-release")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    return urllib.request.urlopen(req, timeout=timeout)


def main() -> None:
    with request(f"https://api.github.com/repos/soyh/junshi/releases/tags/{TAG}") as response:
        release = json.load(response)
    print("release", release["id"], release["html_url"], flush=True)
    for asset in release.get("assets", []):
        if asset["name"] == NAME:
            print("deleting stale asset", asset["id"], flush=True)
            request(
                f"https://api.github.com/repos/soyh/junshi/releases/assets/{asset['id']}",
                method="DELETE",
            )
    upload_url = release["upload_url"].split("{")[0] + f"?name={NAME}"
    data = ZIP.read_bytes()
    for attempt in range(1, 21):
        try:
            started = time.time()
            with request(
                upload_url,
                data=data,
                method="POST",
                headers={"Content-Type": "application/zip"},
            ) as response:
                asset = json.load(response)
            print(
                "uploaded",
                response.status,
                f"time={time.time() - started:.1f}s",
                asset["id"],
                asset["size"],
                asset["digest"] if "digest" in asset else "",
                flush=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 - the network here drops often
            print(f"attempt {attempt}: {exc}", flush=True)
            time.sleep(15)
    raise SystemExit("upload failed")


if __name__ == "__main__":
    main()
