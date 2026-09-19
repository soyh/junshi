from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEMD = ROOT / "deploy" / "systemd"


def _read(name: str) -> str:
    return (SYSTEMD / name).read_text(encoding="utf-8")


def test_runtime_unit_maps_verified_supervision_contract():
    unit = _read("ai-love-strategist.service")

    assert "WorkingDirectory=/opt/ai-love-strategist" in unit
    assert (
        "ExecStartPre=/opt/ai-love-strategist/.venv/bin/python "
        "-m app.preflight --json"
    ) in unit
    assert (
        "ExecStart=/opt/ai-love-strategist/.venv/bin/python -m app.server"
    ) in unit
    assert "Restart=on-failure" in unit
    assert "RestartSec=5" in unit
    assert "KillSignal=SIGTERM" in unit
    assert "TimeoutStopSec=30" in unit
    assert "UMask=0077" in unit
    assert "WantedBy=multi-user.target" in unit


def test_runtime_unit_enforces_backup_retention_before_preflight_and_start():
    unit = _read("ai-love-strategist.service")

    backup = (
        "ExecStartPre=/opt/ai-love-strategist/.venv/bin/python -m app.backup"
    )
    retention = (
        "ExecStartPre=/opt/ai-love-strategist/.venv/bin/python -m app.backup "
        "--retention-dir /opt/ai-love-strategist/data/backups "
        "--keep 7 --apply-retention"
    )
    preflight = (
        "ExecStartPre=/opt/ai-love-strategist/.venv/bin/python "
        "-m app.preflight --json"
    )
    start = (
        "ExecStart=/opt/ai-love-strategist/.venv/bin/python -m app.server"
    )

    assert backup in unit
    assert retention in unit
    assert preflight in unit
    assert start in unit
    assert unit.index(backup) < unit.index(retention) < unit.index(preflight) < unit.index(start)


def test_runtime_unit_preserves_secure_runtime_boundary():
    unit = _read("ai-love-strategist.service")

    assert "8899" not in unit
    assert "EnvironmentFile=" not in unit
    assert "bash -c" not in unit
    assert "sh -c" not in unit
    assert "nohup" not in unit
    assert "uvicorn" not in unit
    assert "python -m app.server" in unit


def test_backup_unit_creates_managed_backup_then_applies_verified_retention():
    unit = _read("ai-love-strategist-backup.service")

    backup_command = (
        "ExecStart=/opt/ai-love-strategist/.venv/bin/python -m app.backup"
    )
    retention_command = (
        "ExecStart=/opt/ai-love-strategist/.venv/bin/python -m app.backup "
        "--retention-dir /opt/ai-love-strategist/data/backups "
        "--keep 7 --apply-retention"
    )

    assert "Type=oneshot" in unit
    assert "ConditionPathExists=/opt/ai-love-strategist/data/app.sqlite3" in unit
    assert backup_command in unit
    assert retention_command in unit
    assert unit.index(backup_command) < unit.index(retention_command)
    assert "UMask=0077" in unit
    assert "8899" not in unit


def test_backup_timer_is_daily_persistent_and_bounded():
    timer = _read("ai-love-strategist-backup.timer")

    assert "OnCalendar=daily" in timer
    assert "Persistent=true" in timer
    assert "RandomizedDelaySec=15m" in timer
    assert "AccuracySec=1m" in timer
    assert "Unit=ai-love-strategist-backup.service" in timer
    assert "WantedBy=timers.target" in timer


def test_installer_hardens_sensitive_file_permissions_without_runtime_activation():
    installer = _read("install.sh")

    assert 'chmod 0600 "$PROJECT/.env" "$PROJECT/data/app.sqlite3"' in installer
    assert "-exec chmod 0600 {} +" in installer
    assert "systemctl daemon-reload" in installer
    assert "systemctl enable ai-love-strategist.service" in installer
    assert "systemctl enable ai-love-strategist-backup.timer" in installer

    forbidden = (
        "systemctl start ",
        "systemctl restart ",
        "systemctl stop ",
        "systemctl enable --now",
    )
    assert all(item not in installer for item in forbidden)


def test_installer_never_targets_reserved_port_or_unrelated_service():
    installer = _read("install.sh")

    assert "8899" not in installer
    assert "/opt/trand" not in installer
