[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,
    [string]$Server = "junshi-prod",
    [string]$ProjectPath = "/opt/ai-love-strategist",
    [switch]$ApplyRestore
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is missing: $Name"
    }
}

function Invoke-SshText([string]$RemoteCommand) {
    $output = & ssh $Server $RemoteCommand 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH command failed: $($output -join [Environment]::NewLine)"
    }
    return ($output -join [Environment]::NewLine).Trim()
}

function Invoke-Scp([string]$Source, [string]$Destination) {
    & scp -q $Source $Destination
    if ($LASTEXITCODE -ne 0) {
        throw "SCP failed for $Source"
    }
}

function Unprotect-DpapiFile([string]$ProtectedPath, [string]$PlainPath) {
    $cipherText = [IO.File]::ReadAllText($ProtectedPath).Trim()
    $secure = ConvertTo-SecureString $cipherText
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        [IO.File]::WriteAllText($PlainPath, $plain, [Text.UTF8Encoding]::new($false))
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

Require-Command "ssh"
Require-Command "scp"

$SnapshotPath = (Resolve-Path -LiteralPath $Snapshot).Path
$MetadataPath = Join-Path $SnapshotPath "recovery.json"
if (-not (Test-Path -LiteralPath $MetadataPath)) {
    throw "recovery.json is missing from snapshot"
}

$metadata = Get-Content -Raw -LiteralPath $MetadataPath | ConvertFrom-Json
$bundlePath = Join-Path $SnapshotPath ([string]$metadata.bundle_file)
$envProtected = Join-Path $SnapshotPath ([string]$metadata.env_backup)

if (-not (Test-Path -LiteralPath $bundlePath)) {
    throw "Recovery bundle is missing"
}
if (-not (Test-Path -LiteralPath $envProtected)) {
    throw "Protected production environment backup is missing"
}

$actualSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $bundlePath).Hash.ToLowerInvariant()
$expectedSha = ([string]$metadata.bundle_sha256).ToLowerInvariant()
if ($actualSha -ne $expectedSha) {
    throw "Local recovery bundle SHA256 verification failed"
}

$plainEnv = Join-Path $env:TEMP ("ai-love-strategist-env-" + [Guid]::NewGuid().ToString("N") + ".tmp")
$remoteStage = "$ProjectPath/data/recovery-incoming"
$remoteBundle = "$remoteStage/$([IO.Path]::GetFileName($bundlePath))"
$remoteEnv = "$remoteStage/production.env.pending"

try {
    Unprotect-DpapiFile $envProtected $plainEnv

    Invoke-SshText "install -d -m 0700 '$remoteStage'"
    Invoke-Scp $bundlePath "$Server`:$remoteBundle"
    Invoke-Scp $plainEnv "$Server`:$remoteEnv"
    Invoke-SshText "chmod 0600 '$remoteBundle' '$remoteEnv'"

    if (-not $ApplyRestore) {
        Write-Host "RESTORE_PUSH=STAGED"
        Write-Host "REMOTE_BUNDLE=$remoteBundle"
        Write-Host "APPLY_RESTORE=NO"
        return
    }

    $remoteScript = @"
set -euo pipefail
PROJECT='$ProjectPath'
PY='${ProjectPath}/.venv/bin/python'
STAGE='$remoteStage'
BUNDLE='$remoteBundle'
EXTRACT_DIR='${remoteStage}/extracted'
SERVICE='ai-love-strategist.service'
BACKUP_TIMER='ai-love-strategist-backup.timer'
WATCHDOG_TIMER='ai-love-strategist-watchdog.timer'

install -m 0600 '$remoteEnv' "`$PROJECT/.env"
rm -rf "`$EXTRACT_DIR"
install -d -m 0700 "`$EXTRACT_DIR"
cd "`$PROJECT/backend"
EXTRACT_JSON="`$("`$PY" -m app.portable_backup --extract "`$BUNDLE" --destination-dir "`$EXTRACT_DIR" --json)"
BACKUP="`$(printf '%s' "`$EXTRACT_JSON" | "`$PY" -c 'import json,sys; print(json.load(sys.stdin)["backup"])')"
MANIFEST="`$(printf '%s' "`$EXTRACT_JSON" | "`$PY" -c 'import json,sys; print(json.load(sys.stdin)["manifest"])')"
"`$PY" -m app.backup --verify-manifest "`$MANIFEST"

systemctl stop "`$WATCHDOG_TIMER" || true
systemctl stop "`$BACKUP_TIMER" || true
trap 'systemctl start ai-love-strategist-backup.timer >/dev/null 2>&1 || true; systemctl start ai-love-strategist-watchdog.timer >/dev/null 2>&1 || true' EXIT
systemctl stop "`$SERVICE"
if systemctl is-active --quiet "`$SERVICE"; then
    echo 'application service did not stop' >&2
    exit 1
fi
"`$PY" -m app.restore --backup "`$BACKUP" --destination "`$PROJECT/data/app.sqlite3" --offline-confirmed
chmod 0600 "`$PROJECT/.env" "`$PROJECT/data/app.sqlite3"
systemctl start "`$SERVICE"
"`$PY" -m app.probe live --json
"`$PY" -m app.probe ready --json
"`$PY" -m app.preflight --json
systemctl start "`$BACKUP_TIMER"
systemctl start "`$WATCHDOG_TIMER"
trap - EXIT
printf '%s\n' 'RESTORE_APPLY=PASSED'
"@

    $result = Invoke-SshText $remoteScript
    Write-Host $result
    Write-Host "RESTORE_PUSH=PASSED"
    Write-Host "APPLY_RESTORE=YES"
}
finally {
    if (Test-Path -LiteralPath $plainEnv) {
        Remove-Item -Force -LiteralPath $plainEnv
    }
}
