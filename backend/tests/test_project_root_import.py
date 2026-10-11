from pathlib import Path
import subprocess
import sys


def test_app_imports_from_project_root_without_pythonpath():
    project_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app; print(app.__file__)",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert str(project_root / "backend" / "app" / "__init__.py") in result.stdout
