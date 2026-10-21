"""Park the automation browser window off-screen without stopping it.

Playwright fixes ``headless`` when the browser starts: a running window cannot
be switched to headless, only restarted. Restarting costs a login re-check and
can trip the platform's risk control, and *minimizing* makes Chromium throttle
timers, so the compromise is to move the window off the visible desktop:

* it disappears from the taskbar and from the screen;
* the page keeps running at full speed (the window is still "visible" to
  Chromium, so no background throttling);
* it can be brought back at any time with :func:`show`.

Everything here is Windows-only and best effort: on any failure the browser is
simply left where it is.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import os
import sys
import time
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"

SW_MINIMIZE = 6
SW_RESTORE = 9
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
TH32CS_SNAPPROCESS = 0x00000002

OFFSCREEN = (-30000, -30000)
ONSCREEN = (120, 120)
_CHROME_WINDOW_CLASS = "Chrome_WidgetWin_1"


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


def _children_by_parent() -> dict[int, list[int]]:
    """pid -> [child pids], from a Toolhelp32 snapshot."""
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1:
        return {}
    children: dict[int, list[int]] = {}
    try:
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return {}
        while True:
            children.setdefault(int(entry.th32ParentProcessID), []).append(
                int(entry.th32ProcessID)
            )
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        kernel32.CloseHandle(snapshot)
    return children


def descendants(root: int, limit: int = 4000) -> set[int]:
    """Every process below ``root`` (the browser is a grandchild of the bridge)."""
    children = _children_by_parent()
    found: set[int] = set()
    queue = [int(root)]
    while queue and len(found) < limit:
        for child in children.get(queue.pop(), []):
            if child not in found:
                found.add(child)
                queue.append(child)
    return found


def _browser_windows(pids: set[int]) -> list[int]:
    user32 = ctypes.windll.user32
    found: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def visit(hwnd, _param):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            name = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, name, 64)
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, 256)
            # Untitled Chrome_WidgetWin_1 windows are browser furniture
            # (shadows, first-run placeholders); moving them does nothing.
            if name.value == _CHROME_WINDOW_CLASS and title.value.strip():
                found.append(int(hwnd))
        return True

    user32.EnumWindows(callback_type(visit), 0)
    return found


def _window_record() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) / "JunshiPC" / "bridge" if base else Path.home() / ".junshi"
    root.mkdir(parents=True, exist_ok=True)
    return root / "window-handles.json"


def _remember(profile_key: str, handles: list[int]) -> None:
    path = _window_record()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data[profile_key] = handles
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def remembered(profile_key: str) -> list[int]:
    try:
        data = json.loads(_window_record().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    value = data.get(profile_key)
    return [int(h) for h in value] if isinstance(value, list) else []


def _find(
    root_pids: list[int] | None = None,
    profile_key: str | None = None,
    wait: float = 12.0,
) -> list[int]:
    """Locate this bridge's Chromium windows, waiting for the browser to appear."""
    deadline = time.time() + max(0.0, wait)
    while True:
        pids: set[int] = set()
        for root in root_pids or [os.getpid()]:
            try:
                pids |= descendants(root)
            except Exception:
                continue
        handles = _browser_windows(pids) if pids else []
        if handles or time.time() >= deadline:
            if handles and profile_key:
                _remember(profile_key, handles)
            return handles
        time.sleep(0.5)


def _ex_style(hwnd: int) -> int:
    return ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)


def _set_ex_style(hwnd: int, value: int) -> None:
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, value)


def taskbar_visible(hwnd: int) -> bool:
    """False when the window carries WS_EX_TOOLWINDOW (no taskbar button)."""
    if not IS_WINDOWS:
        return True
    return not (_ex_style(hwnd) & WS_EX_TOOLWINDOW)


def hide(
    root_pids: list[int] | None = None,
    *,
    profile_key: str | None = None,
    mode: str = "hide",
    wait: float = 12.0,
) -> int:
    """Park the window off-screen and drop it from the taskbar. Returns windows touched."""
    if not IS_WINDOWS:
        return 0
    user32 = ctypes.windll.user32
    handles = _find(root_pids, profile_key, wait=wait)
    if not handles:
        return 0
    touched = 0
    for hwnd in handles:
        try:
            if mode == "minimize":
                user32.ShowWindow(hwnd, SW_MINIMIZE)
            else:
                # Moving alone leaves a taskbar button that restores the page, so
                # the window also becomes a tool window: no taskbar entry, no
                # Alt-Tab entry, and still "visible" to Chromium (no throttling).
                _set_ex_style(
                    hwnd, (_ex_style(hwnd) | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW,
                )
                user32.SetWindowPos(
                    hwnd, 0, OFFSCREEN[0], OFFSCREEN[1], 0, 0,
                    SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
                )
            touched += 1
        except Exception:
            continue
    return touched


def show(
    root_pids: list[int] | None = None,
    *,
    profile_key: str | None = None,
    wait: float = 3.0,
) -> int:
    """Bring the parked window back to the visible desktop and focus it."""
    if not IS_WINDOWS:
        return 0
    user32 = ctypes.windll.user32
    handles = _find(root_pids, profile_key, wait=wait)
    if not handles and profile_key:
        handles = [h for h in remembered(profile_key) if user32.IsWindow(h)]
    touched = 0
    for hwnd in handles:
        try:
            user32.ShowWindow(hwnd, SW_RESTORE)
            _set_ex_style(hwnd, (_ex_style(hwnd) & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW)
            user32.SetWindowPos(
                hwnd, 0, ONSCREEN[0], ONSCREEN[1], 0, 0,
                SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )
            user32.SetForegroundWindow(hwnd)
            touched += 1
        except Exception:
            continue
    return touched


if __name__ == "__main__":  # manual probe: python -m lovebridge.window hide|show [pid]
    action = sys.argv[1] if len(sys.argv) > 1 else "hide"
    roots = [int(sys.argv[2])] if len(sys.argv) > 2 else None
    print(action, hide(roots) if action == "hide" else show(roots))
