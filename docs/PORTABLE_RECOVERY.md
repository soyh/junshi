# Portable Recovery

TEST-150 treats the production server as replaceable. Source code is retained in GitHub; durable application data is pulled to a trusted Windows computer.

## What is preserved

A Windows snapshot contains:

- `*.recovery.enc`: AES-GCM encrypted recovery bundle containing a verified managed SQLite backup and its manifest.
- `production.env.dpapi`: production `.env` protected with Windows DPAPI for the current Windows user/current computer.
- `recovery.json`: source Git commit, bundle SHA-256, source DB SHA-256, and recovery metadata.

No plaintext `.env` is intentionally retained in the snapshot directory.

## One-time server configuration

Generate a recovery key on the server:

```bash
cd /opt/ai-love-strategist
.venv/bin/python -m app.portable_backup --generate-key
```

Store the generated value only as `PORTABLE_BACKUP_ENCRYPTION_KEY` in `/opt/ai-love-strategist/.env`, with the file remaining mode `0600`.

The repository also provides `scripts/server/prepare-portable-recovery.sh`, which can generate the key internally without printing it, configure the portable export directory, run focused validation, restart the application through the existing systemd readiness gate, and create the first verified recovery bundle.

The Windows backup process protects the full production `.env` with DPAPI, so this key is recoverable when replacing the server. Do not commit the real key or `.env` to GitHub.

## Pull a backup to Windows

Open PowerShell from a clone of this repository and run:

```powershell
.\scripts\windows\backup-pull.ps1 -Server root@SERVER_IP
```

Or configure an SSH alias named `junshi-prod` and omit `-Server`.

Default local location:

```text
%USERPROFILE%\AI-Love-Strategist-Backup\snapshots\<UTC timestamp>\
```

The script:

1. asks the server to create a fresh managed SQLite backup;
2. wraps it in an authenticated encrypted recovery bundle;
3. downloads the encrypted bundle with SCP;
4. verifies its SHA-256 on Windows;
5. downloads `.env` only to a temporary file;
6. protects `.env` with Windows DPAPI and removes the plaintext temporary file;
7. writes `recovery.json`;
8. applies local snapshot retention.

A backup is considered off-server only after this Windows pull completes successfully.

## Stage a recovery on a replacement server

After cloning the repository and creating the Python environment on the replacement server:

```powershell
.\scripts\windows\restore-push.ps1 `
  -Snapshot "$env:USERPROFILE\AI-Love-Strategist-Backup\snapshots\YYYYMMDDTHHMMSSZ" `
  -Server root@NEW_SERVER_IP
```

This is stage-only by default. It uploads only the encrypted recovery bundle to the private recovery staging directory. It does not decrypt or upload `.env`, stop services, or restore the database.

## Apply the restore

Only after verifying the target server is the intended replacement server:

```powershell
.\scripts\windows\restore-push.ps1 `
  -Snapshot "$env:USERPROFILE\AI-Love-Strategist-Backup\snapshots\YYYYMMDDTHHMMSSZ" `
  -Server root@NEW_SERVER_IP `
  -ApplyRestore
```

Only the explicit apply path decrypts the DPAPI-protected `.env` on Windows and transfers it over SSH to the replacement server. The apply path then:

1. installs `.env` as mode `0600`;
2. decrypts the portable recovery bundle;
3. re-verifies the managed SQLite manifest and SHA-256;
4. stops the application watchdog and backup timers;
5. stops `ai-love-strategist.service`;
6. runs the existing offline-confirmed restore path;
7. restores file permissions;
8. starts the application;
9. checks live, ready, and release preflight;
10. restarts the existing backup/watchdog timers.

Port `8899` is never part of the portable recovery workflow.

## Important limitation

`production.env.dpapi` is protected for the Windows user/computer that created it. If that Windows computer is also lost, the DPAPI-protected `.env` cannot be assumed recoverable. For higher durability, keep an additional encrypted copy of the Windows backup directory on another trusted local disk or offline medium.
