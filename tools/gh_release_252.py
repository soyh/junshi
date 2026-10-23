"""Publish Build 252 on GitHub with retries (the network here is very slow)."""

import hashlib
import json
import time
import urllib.request
from pathlib import Path

TAG = "pc-bridge-plugin-25"
NAME = "JunshiPC-252-Windows-x64.zip"
ZIP = Path("builds/pc-v252") / NAME
BODY = Path("build/release-body-252.md")


def token() -> str:
    import subprocess

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


def request(url, data=None, method=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "junshi-release")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    return urllib.request.urlopen(req, timeout=180)


def main() -> None:
    digest = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    print("zip", ZIP.stat().st_size, digest, flush=True)
    payload = json.dumps(
        {
            "tag_name": TAG,
            "target_commitish": "feature/person-merge",
            "name": "Build 252 — 看得到判断，更快",
            "body": BODY.read_text(encoding="utf-8"),
            "draft": False,
            "prerelease": False,
        }
    ).encode()
    for attempt in range(1, 9):
        try:
            with request(
                "https://api.github.com/repos/soyh/junshi/releases",
                data=payload,
                method="POST",
                headers={"Content-Type": "application/json"},
            ) as response:
                release = json.load(response)
            break
        except Exception as exc:  # noqa: BLE001 - retry through a flaky network
            print(f"create attempt {attempt}: {exc}", flush=True)
            time.sleep(5 * attempt)
    else:
        raise SystemExit("could not create the release")
    print("release", release["id"], release["html_url"], flush=True)

    upload_url = release["upload_url"].split("{")[0] + f"?name={NAME}"
    data = ZIP.read_bytes()
    for attempt in range(1, 13):
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
                "upload",
                response.status,
                f"time={time.time() - started:.3f}s",
                asset["id"],
                asset["size"],
                flush=True,
            )
            break
        except Exception as exc:  # noqa: BLE001
            print(f"upload attempt {attempt}: {exc}", flush=True)
            time.sleep(10)
    else:
        raise SystemExit("could not upload the asset")


if __name__ == "__main__":
    main()
