"""Console output that never kills the bridge.

The bridge runs as a Windows GUI executable whose stdout may be missing, and
when it is a console it defaults to the OEM code page (GBK on Chinese Windows).
A nick name with an emoji used to raise UnicodeEncodeError from ``print`` deep
inside a log call and take the whole process down, so every log line goes
through this helper instead.
"""

from __future__ import annotations

import sys


def write_line(line: str) -> None:
    stream = sys.stdout
    if stream is None:
        return
    try:
        print(line, flush=True)
        return
    except (UnicodeEncodeError, ValueError, OSError):
        pass
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return
    try:
        buffer.write((line + "\n").encode("utf-8", "replace"))
        buffer.flush()
    except (OSError, ValueError):
        pass
