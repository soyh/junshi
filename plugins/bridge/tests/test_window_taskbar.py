"""After parking, the browser window must also lose its taskbar button."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lovebridge import window  # noqa: E402


class _FakeUser32:
    def __init__(self) -> None:
        self.style = window.WS_EX_APPWINDOW
        self.position = None
        self.flags = 0

    def GetWindowLongW(self, hwnd, index):  # noqa: ANN001
        return self.style

    def SetWindowLongW(self, hwnd, index, value):  # noqa: ANN001
        self.style = value
        return value

    def SetWindowPos(self, hwnd, after, x, y, cx, cy, flags):  # noqa: ANN001
        self.position = (x, y)
        self.flags = flags
        return 1

    def ShowWindow(self, hwnd, command):  # noqa: ANN001
        return 1

    def SetForegroundWindow(self, hwnd):  # noqa: ANN001
        return 1

    def IsWindow(self, hwnd):  # noqa: ANN001
        return True


def _wire(monkeypatch):
    fake = _FakeUser32()
    monkeypatch.setattr(window, "IS_WINDOWS", True)
    monkeypatch.setattr(window.ctypes, "windll", SimpleNamespace(user32=fake))
    monkeypatch.setattr(window, "_find", lambda *args, **kwargs: [4242])
    return fake


def test_hide_drops_the_taskbar_button(monkeypatch):
    fake = _wire(monkeypatch)
    assert window.hide(mode="hide") == 1
    assert fake.style & window.WS_EX_TOOLWINDOW, "window must become a tool window"
    assert not fake.style & window.WS_EX_APPWINDOW, "app window flag must be cleared"
    assert fake.position == window.OFFSCREEN
    assert fake.flags & window.SWP_FRAMECHANGED, "style change needs a frame refresh"
    assert window.taskbar_visible(4242) is False


def test_show_restores_the_taskbar_button(monkeypatch):
    fake = _wire(monkeypatch)
    window.hide(mode="hide")
    assert window.show() == 1
    assert not fake.style & window.WS_EX_TOOLWINDOW
    assert fake.style & window.WS_EX_APPWINDOW
    assert fake.position == window.ONSCREEN
    assert window.taskbar_visible(4242) is True


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
