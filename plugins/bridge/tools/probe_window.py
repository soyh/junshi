"""Real probe: park a browser window off-screen, then bring it back.

Run with a Python that has no Playwright requirement:

    python plugins/bridge/tools/probe_window.py
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lovebridge import window  # noqa: E402

EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def rect(hwnd: int) -> tuple[int, int, int, int]:
    box = wt.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(box))
    return box.left, box.top, box.right, box.bottom


def handles_for(pid: int) -> list[int]:
    return window._find([pid], wait=10)


def main() -> None:
    profile = Path(tempfile.mkdtemp(prefix="probe-window-"))
    browser = subprocess.Popen(
        [
            str(EDGE),
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1000,700",
            "about:blank",
        ]
    )
    try:
        time.sleep(3)
        before = handles_for(browser.pid)
        print("windows:", before)
        assert before, "no browser window found"
        print("rect before:", [rect(h) for h in before])

        assert window.hide([browser.pid], mode="hide") >= 1
        time.sleep(1)
        after = [rect(h) for h in window._find([browser.pid], wait=2)]
        print("rect after hide:", after)
        assert after and all(x <= -10000 for x, *_ in after), after

        assert window.show([browser.pid]) >= 1
        time.sleep(1)
        restored = [rect(h) for h in window._find([browser.pid], wait=2)]
        print("rect after show:", restored)
        assert restored and all(x > -1000 for x, *_ in restored), restored
        print("PASS: hide moves off-screen, show restores")
    finally:
        browser.kill()


if __name__ == "__main__":
    main()
