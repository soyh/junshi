# Replacement Server Recovery

TEST-151 extends TEST-150 portable recovery so a replacement server can be rebuilt from a trusted Windows snapshot without manually preparing the project checkout or Python environment first.

## Recovery model

The recovery inputs are:

- GitHub repository `soyh/junshi` for source code and deployment files.
- A trusted Windows snapshot created by `scripts/windows/backup-pull.ps1`.
- SSH root access to a replacement Linux server.

The Windows snapshot remains the authority for the application data and production `.env`. `recovery.json` also records the exact Git `source_head` that produced the snapshot. Replacement recovery checks out that exact commit instead of blindly using the latest branch.

## Safety boundary

The replacement bootstrap refuses to run if `ai-love-strategist.service` is already active. This is deliberate: TEST-151 is for a replacement server, not an in-place restore of the currently running production server.

Stage-only is the default. It:

1. verifies the Windows bundle SHA-256;
2. uploads only the encrypted bundle and bootstrap helper;
3. installs missing Git/Python prerequisites when supported;
4. clones the repository;
5. checks out the snapshot's exact `source_head` in detached HEAD mode;
6. builds `.venv` and installs application requirements;
7. stages the encrypted bundle;
8. does **not** decrypt/upload `.env`;
9. does **not** restore the database;
10. does **not** start the application.

The reserved port `8899` is observation-only and must keep the same owner before/after a run.

## Stage a replacement server

From the Windows clone containing the TEST-151 scripts:

```powershell
.\scripts\windows\replacement-restore.ps1 `
  -Snapshot "$env:USERPROFILE\AI-Love-Strategist-Backup\snapshots\YYYYMMDDTHHMMSSZ" `
  -Server "root@NEW_SERVER_IP"
```

Expected result includes:

```text
REPLACEMENT_BOOTSTRAP=STAGED
REPLACEMENT_RESTORE=STAGED
ENV_TRANSFERRED=NO
DATABASE_RESTORE_EXECUTED=NO
```

## Apply recovery

Only after confirming the SSH target is the intended replacement server:

```powershell
.\scripts\windows\replacement-restore.ps1 `
  -Snapshot "$env:USERPROFILE\AI-Love-Strategist-Backup\snapshots\YYYYMMDDTHHMMSSZ" `
  -Server "root@NEW_SERVER_IP" `
  -ApplyRestore `
  -ConfirmReplacementServer
```

Both switches are required for destructive restore behavior.

The apply path:

1. decrypts `production.env.dpapi` only on the trusted Windows computer;
2. uploads the temporary production `.env` over SSH and deletes the local plaintext temp file in `finally`;
3. installs `.env` on the replacement server as mode `0600` and removes the staging plaintext copy;
4. verifies/decrypts the portable bundle;
5. verifies the managed backup manifest and SQLite integrity;
6. performs the existing offline-confirmed atomic SQLite restore;
7. creates a fresh managed backup from the restored DB;
8. runs release preflight;
9. installs/enables the existing systemd runtime, backup timer, and watchdog timer;
10. starts the runtime and verifies liveness, readiness, and post-start preflight;
11. starts backup/watchdog timers;
12. verifies the reserved `8899` owner did not change.

Expected final result includes:

```text
REPLACEMENT_RECOVERY=PASSED
REPLACEMENT_RESTORE=PASSED
DATABASE_RESTORE_EXECUTED=YES
```

## Alibaba Cloud Linux 3

Alibaba Cloud Linux 3 keeps its system `python3` on an older version for system tooling. The bootstrap installs the version-suffixed `python3.11` package alongside the system interpreter and creates the project virtual environment from that binary. It never rewires `/usr/bin/python3`.

## Existing prepared-server restore

`scripts/windows/restore-push.ps1` remains available for a server that has already been cloned, configured, and provisioned. For a genuinely empty replacement server, prefer `replacement-restore.ps1`.

## Verification requirement

TEST-151 is not complete merely because the scripts pass CI. Final verification requires a real disposable/replacement server drill using a Windows snapshot: stage first, then explicit apply, then confirm live/ready/preflight and the restored application data. The current production server must not be used as the destructive drill target.
