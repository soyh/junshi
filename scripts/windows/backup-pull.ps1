[CmdletBinding()]
param(
    [string]$Server = "junshi-prod",
    [string]$ProjectPath = "/opt/ai-love-strategist",
    [string]$LocalRoot = "$env:USERPROFILE\AI-Love-Strategist-Backup",
    [ValidateRange(1, 365)]
    [int]$Keep = 30
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

Require-Command "ssh"
Require-Command "scp"

$SnapshotsRoot = Join-Path $LocalRoot "snapshots"
New-Item -ItemType Directory -Force -Path $SnapshotsRoot | Out-Null

$Timestamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$Snapshot = Join-Path $SnapshotsRoot $Timestamp
New-Item -ItemType Directory -Path $Snapshot | Out-Null

$EnvTemp = Join-Path $Snapshot ".env.plain.tmp"
$EnvProtected = Join-Path $Snapshot "production.env.dpapi"

try {
    # Run from the same project root used by systemd so pydantic-settings finds
    # /opt/ai-love-strategist/.env instead of looking under backend/.
    $prepareCommand = "cd '$ProjectPath' && '$ProjectPath/.venv/bin/python' -m app.portable_backup --prepare --json"
    $prepareRaw = Invoke-SshText $prepareCommand
    $prepare = $prepareRaw | ConvertFrom-Json

    if (-not $prepare.ok) {
        throw "Server portable backup preparation failed"
    }

    $bundleRemote = [string]$prepare.bundle
    $bundleName = [IO.Path]::GetFileName($bundleRemote)
    $bundleLocal = Join-Path $Snapshot $bundleName

    Invoke-Scp "$Server`:$bundleRemote" $bundleLocal

    $localSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $bundleLocal).Hash.ToLowerInvariant()
    $expectedSha = ([string]$prepare.bundle_sha256).ToLowerInvariant()
    if ($localSha -ne $expectedSha) {
        throw "Downloaded recovery bundle SHA256 does not match the server result"
    }

    $repoHead = Invoke-SshText "git -C '$ProjectPath' rev-parse HEAD"

    Invoke-Scp "$Server`:$ProjectPath/.env" $EnvTemp
    $plainEnv = [IO.File]::ReadAllText($EnvTemp)
    $secureEnv = ConvertTo-SecureString $plainEnv -AsPlainText -Force
    $protectedEnv = ConvertFrom-SecureString $secureEnv
    [IO.File]::WriteAllText(
        $EnvProtected,
        $protectedEnv,
        [Text.UTF8Encoding]::new($false)
    )
    Remove-Item -Force -LiteralPath $EnvTemp

    $metadata = [ordered]@{
        schema_version = 1
        created_at_utc = [DateTime]::UtcNow.ToString("o")
        repository = "soyh/junshi"
        source_head = $repoHead
        server_alias = $Server
        project_path = $ProjectPath
        bundle_file = $bundleName
        bundle_sha256 = $localSha
        source_backup_filename = [string]$prepare.source_backup_filename
        source_backup_sha256 = [string]$prepare.source_sha256
        env_backup = "production.env.dpapi"
        env_protection = "Windows DPAPI current user/current computer"
        database_restore_executed = $false
    }
    $metadata | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $Snapshot "recovery.json")

    $snapshots = Get-ChildItem -LiteralPath $SnapshotsRoot -Directory | Sort-Object Name -Descending
    $snapshots | Select-Object -Skip $Keep | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }

    Write-Host "BACKUP_PULL=PASSED"
    Write-Host "SNAPSHOT=$Snapshot"
    Write-Host "SOURCE_HEAD=$repoHead"
    Write-Host "BUNDLE_SHA256=$localSha"
}
catch {
    if (Test-Path -LiteralPath $EnvTemp) {
        Remove-Item -Force -LiteralPath $EnvTemp
    }
    if (Test-Path -LiteralPath $Snapshot) {
        Remove-Item -Recurse -Force -LiteralPath $Snapshot
    }
    Write-Error $_
    exit 1
}
