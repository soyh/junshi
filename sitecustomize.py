"""Make the backend package importable from the repository root.

Python automatically imports ``sitecustomize`` during interpreter startup when
this repository root is on ``sys.path``.  The application package lives under
``backend/app`` rather than at the repository root, so add ``backend`` to the
module search path without changing application imports or business logic.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "backend"

if BACKEND_ROOT.is_dir():
    backend_root = str(BACKEND_ROOT)
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
