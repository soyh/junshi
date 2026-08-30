"""Compatibility package exposing the backend application from project root."""

from pathlib import Path

_BACKEND_APP = Path(__file__).resolve().parent.parent / "backend" / "app"

if not _BACKEND_APP.is_dir():
    raise ImportError(f"Backend application package not found: {_BACKEND_APP}")

# Keep the canonical backend package location visible to Python submodule imports.
__path__ = [str(_BACKEND_APP)]

# Preserve the existing project-root import contract:
# import app -> backend/app/__init__.py
__file__ = str(_BACKEND_APP / "__init__.py")
