from pathlib import Path


def test_server_preparation_is_fail_closed_and_never_restores_database():
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts/server/prepare-portable-recovery.sh").read_text(encoding="utf-8")

    assert "set -euo pipefail" in script
    assert "app.backup >/dev/null" in script
    assert "app.portable_backup --check --json" in script
    assert "app.portable_backup --prepare --json" in script
    assert "app.portable_backup --verify" in script
    assert "systemctl restart \"$SERVICE\"" in script
    assert "app.probe live --json" in script
    assert "app.probe ready --json" in script
    assert "app.preflight --json" in script
    assert "PORTABLE_BACKUP_ENCRYPTION_KEY" in script
    assert "os.urandom(32)" in script
    assert "chmod 0600 \"$ENV_FILE\"" in script
    assert "app.restore" not in script
    assert "DATABASE_RESTORE_EXECUTED=NO" in script


def test_server_preparation_only_observes_reserved_8899_owner():
    root = Path(__file__).resolve().parents[2]
    script = (root / "scripts/server/prepare-portable-recovery.sh").read_text(encoding="utf-8")

    assert ":8899 " in script
    assert "PORT8899_BEFORE" in script
    assert "PORT8899_AFTER" in script
    assert "kill" not in script
    assert "pkill" not in script
    assert "fuser" not in script


def test_windows_remote_commands_use_project_root_for_dotenv_loading():
    root = Path(__file__).resolve().parents[2]
    pull = (root / "scripts/windows/backup-pull.ps1").read_text(encoding="utf-8")
    restore = (root / "scripts/windows/restore-push.ps1").read_text(encoding="utf-8")

    assert "cd '$ProjectPath' && '$ProjectPath/.venv/bin/python' -m app.portable_backup" in pull
    assert "cd '$ProjectPath/backend'" not in pull
    assert 'cd "`$PROJECT"' in restore
    assert 'cd "`$PROJECT/backend"' not in restore
