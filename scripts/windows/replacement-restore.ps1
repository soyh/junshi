[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Snapshot,
    [string]$Server = "junshi-replacement",
    [string]$ProjectPath = "/opt/ai-love-strategist",
    [string]$Repository = "https://github.com/soyh/junshi.git",
    [switch]$ApplyRestore,
    [switch]$ConfirmReplacementServer
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is missing: $Name"
    }
}

function Assert-SafeShellValue([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "$Name must not be empty"
    }
    if ($Value.Contains("'") -or $Value.Contains("`n") -or $Value.Contains("`r")) {
        throw "$Name contains unsupported shell characters"
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

Assert-SafeShellValue "Server" $Server
Assert-SafeShellValue "ProjectPath" $ProjectPath
Assert-SafeShellValue "Repository" $Repository

$SnapshotPath = (Resolve-Path -LiteralPath $Snapshot).Path
$MetadataPath = Join-Path $SnapshotPath "recovery.json"
if (-not (Test-Path -LiteralPath $MetadataPath)) {
    throw "recovery.json is missing from snapshot"
}

$metadata = Get-Content -Raw -LiteralPath $MetadataPath | ConvertFrom-Json
$sourceHead = [string]$metadata.source_head
if ($sourceHead -notmatch '^[0-9a-fA-F]{40}$') {
    throw "Snapshot source_head is not a 40-character Git commit SHA"
}

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

$bootstrapLocal = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\server\bootstrap-replacement-server.sh")).Path
$remoteStage = "/root/ai-love-strategist-recovery-stage"
$remoteBootstrap = "$remoteStage/bootstrap-replacement-server.sh"
$remoteBundle = "$remoteStage/$([IO.Path]::GetFileName($bundlePath))"
$remoteEnv = "$remoteStage/production.env.pending"
$plainEnv = Join-Path $env:TEMP ("ai-love-strategist-replacement-env-" + [Guid]::NewGuid().ToString("N") + ".tmp")

try {
    Invoke-SshText "install -d -m 0700 '$remoteStage'"
    Invoke-Scp $bootstrapLocal "$Server`:$remoteBootstrap"
    Invoke-Scp $bundlePath "$Server`:$remoteBundle"
    Invoke-SshText "chmod 0700 '$remoteBootstrap'; chmod 0600 '$remoteBundle'"

    $baseCommand = "bash '$remoteBootstrap' --repository '$Repository' --source-head '$sourceHead' --project '$ProjectPath' --bundle '$remoteBundle'"

    if (-not $ApplyRestore) {
        $result = Invoke-SshText $baseCommand
        Write-Host $result
        Write-Host "REPLACEMENT_RESTORE=STAGED"
        Write-Host "SOURCE_HEAD=$sourceHead"
        Write-Host "ENV_TRANSFERRED=NO"
        Write-Host "DATABASE_RESTORE_EXECUTED=NO"
        return
    }

    if (-not $ConfirmReplacementServer) {
        throw "-ApplyRestore also requires -ConfirmReplacementServer"
    }

    Unprotect-DpapiFile $envProtected $plainEnv
    Invoke-Scp $plainEnv "$Server`:$remoteEnv"
    Invoke-SshText "chmod 0600 '$remoteEnv'"

    $applyCommand = "$baseCommand --env-file '$remoteEnv' --apply"
    $result = Invoke-SshText $applyCommand
    Write-Host $result
    Write-Host "REPLACEMENT_RESTORE=PASSED"
    Write-Host "SOURCE_HEAD=$sourceHead"
    Write-Host "APPLY_RESTORE=YES"
}
finally {
    if (Test-Path -LiteralPath $plainEnv) {
        Remove-Item -Force -LiteralPath $plainEnv
    }
}
