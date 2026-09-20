from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _server_script() -> str:
    return (_root() / "scripts/server/bootstrap-replacement-server.sh").read_text(encoding="utf-8")


def _windows_script() -> str:
    return (_root() / "scripts/windows/replacement-restore.ps1").read_text(encoding="utf-8")


def test_replacement_server_refuses_apply_or_default_path_on_active_production_runtime():
    script = _server_script()
    assert 'ACTIVE_RUNTIME=1' in script
    assert '[ "$APPLY" -eq 1 ] || [ "$PROJECT" = "$PRODUCTION_PROJECT" ]' in script
    assert 'fail "target-has-active-production-runtime"' in script


def test_active_production_allows_only_isolated_stage_project():
    script = _server_script()
    assert 'PRODUCTION_PROJECT="/opt/ai-love-strategist"' in script
    assert 'stage-only is allowed only with a different' in script
    stage_gate = script.index('if [ "$APPLY" -ne 1 ]; then')
    env_install = script.index('install -m 0600 "$ENV_FILE" "$PROJECT/.env"')
    assert stage_gate < env_install


def test_replacement_server_checks_out_snapshot_exact_commit():
    script = _server_script()
    assert 'git checkout --detach "$SOURCE_HEAD"' in script
    assert '[ "$(git rev-parse HEAD)" = "$SOURCE_HEAD" ]' in script
    assert 'source-head-checkout-mismatch' in script


def test_stage_only_path_never_installs_env_or_restores_database():
    script = _server_script()
    stage_gate = script.index('if [ "$APPLY" -ne 1 ]; then')
    env_install = script.index('install -m 0600 "$ENV_FILE" "$PROJECT/.env"')
    restore = script.index('"$PY" -m app.restore')
    assert stage_gate < env_install < restore
    assert 'echo "ENV_TRANSFERRED=NO"' in script
    assert 'echo "DATABASE_RESTORE_EXECUTED=NO"' in script


def test_restore_verifies_bundle_manifest_before_offline_restore():
    script = _server_script()
    verify_bundle = script.index('app.portable_backup --verify')
    verify_manifest = script.index('app.backup --verify-manifest')
    restore = script.index('"$PY" -m app.restore')
    assert verify_bundle < verify_manifest < restore
    assert '--offline-confirmed' in script


def test_restore_installs_systemd_only_after_database_exists():
    script = _server_script()
    restore = script.index('"$PY" -m app.restore')
    installer = script.index('deploy/systemd/install.sh')
    service_start = script.index('systemctl start "$SERVICE"')
    assert restore < installer < service_start
    assert 'app.probe live --json' in script
    assert 'app.probe ready --json' in script
    assert 'app.preflight --json' in script


def test_alibaba_linux_bootstrap_keeps_system_python_untouched():
    script = _server_script()
    assert 'dnf install -y git iproute python3.11' in script
    assert 'never replace the' in script
    assert 'alternatives' not in script
    assert 'ln -s' not in script


def test_replacement_server_only_observes_reserved_8899():
    script = _server_script()
    assert ':8899 ' in script
    assert 'PORT8899_BEFORE' in script
    assert 'PORT8899_AFTER' in script
    assert 'reserved-port-8899-owner-changed' in script
    for forbidden in ('kill ', 'pkill ', 'fuser '):
        assert forbidden not in script


def test_windows_driver_uses_snapshot_metadata_and_local_sha_before_upload():
    script = _windows_script()
    assert '$sourceHead = [string]$metadata.source_head' in script
    assert "$sourceHead -notmatch '^[0-9a-fA-F]{40}$'" in script
    hash_check = script.index('$actualSha = (Get-FileHash')
    upload = script.index('Invoke-Scp $bootstrapLocal')
    assert hash_check < upload
    assert '$actualSha -ne $expectedSha' in script


def test_windows_apply_requires_second_replacement_confirmation():
    script = _windows_script()
    assert '[switch]$ApplyRestore' in script
    assert '[switch]$ConfirmReplacementServer' in script
    assert 'if (-not $ConfirmReplacementServer)' in script
    assert '-ApplyRestore also requires -ConfirmReplacementServer' in script


def test_windows_stage_only_never_unprotects_or_uploads_env():
    script = _windows_script()
    stage_gate = script.index('if (-not $ApplyRestore)')
    unprotect = script.index('Unprotect-DpapiFile $envProtected $plainEnv')
    env_upload = script.index('Invoke-Scp $plainEnv "$Server`:$remoteEnv"')
    assert stage_gate < unprotect < env_upload
    assert 'Write-Host "ENV_TRANSFERRED=NO"' in script
    assert 'Write-Host "DATABASE_RESTORE_EXECUTED=NO"' in script


def test_windows_plaintext_env_is_always_deleted_locally():
    script = _windows_script()
    assert 'finally {' in script
    assert 'Remove-Item -Force -LiteralPath $plainEnv' in script
