"""Entry point for the bundled channel bridge executable.

Usage:
    JunshiBridge.exe --config <path> run
    JunshiBridge.exe --config <path> doctor
"""

from lovebridge.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
