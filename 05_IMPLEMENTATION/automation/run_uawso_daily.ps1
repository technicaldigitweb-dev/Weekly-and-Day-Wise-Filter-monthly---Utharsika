#Requires -Version 5.1
<#
.SYNOPSIS
    UAWSO daily automation entry point. Called by Windows Task Scheduler
    ("UAWSO Daily 11-30 - Satheskanth") at 11:30 AM local time (Sri Lanka
    Standard Time / Asia/Colombo, UTC+05:30, no DST).

.DESCRIPTION
    Thin wrapper only: resolves the project root, loads DB credentials
    from the local (untracked) env file, acquires a single-run lock so
    overlapping/duplicate scheduled runs cannot execute concurrently,
    then calls uawso_daily_runner.py. All real logic (extraction,
    generation, validation, Historical Output Protection, ph_task
    publication) lives in that Python orchestrator, not here.

.PARAMETER DryRun
    Passed straight through to uawso_daily_runner.py as --dry-run.
    Default is dry-run unless -Publish is also given.

.PARAMETER Publish
    Passed straight through to uawso_daily_runner.py as --publish.
    Performs the real HTML write + ph_task insert.
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$AutomationDir = Join-Path $ProjectRoot '05_IMPLEMENTATION\automation'
$CheckpointsDir = Join-Path $ProjectRoot '07_EVIDENCE\automation\checkpoints'
$FailuresDir = Join-Path $ProjectRoot '07_EVIDENCE\automation\failures'
$LockPath = Join-Path $CheckpointsDir 'uawso_daily.lock'
$EnvFile = Join-Path $ProjectRoot '05_IMPLEMENTATION\config\.env.local'

New-Item -ItemType Directory -Force -Path $CheckpointsDir | Out-Null
New-Item -ItemType Directory -Force -Path $FailuresDir | Out-Null

function Write-FailureLog {
    param([string]$Code, [string]$Detail)
    $ts = Get-Date -Format 'yyyy-MM-dd_HHmmss'
    $path = Join-Path $FailuresDir "${ts}_uawso_wrapper_failure.md"
    @"
# UAWSO Wrapper Failure

**Code:** $Code
**Detail:** $Detail
**Timestamp:** $(Get-Date -Format 'o')
**Host:** $env:COMPUTERNAME
**User context:** $env:USERNAME
"@ | Set-Content -Path $path -Encoding utf8
    Write-Error "$Code`: $Detail (see $path)"
}

# --- Load DB credentials from the local, untracked env file (never
# hardcoded, never committed) if present. Task Scheduler's own
# "run whether user is logged on or not" environment does not inherit
# an interactive user's PowerShell profile, so this file is the
# unattended credential mechanism - see the automation README's
# "Unattended credential handling" section for setup instructions and
# the BLOCKED_CREDENTIAL_SETUP condition if this file cannot be created
# safely on this machine.
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
            $parts = $line.Split('=', 2)
            [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), 'Process')
        }
    }
} else {
    Write-FailureLog -Code 'BLOCKED_CREDENTIAL_SETUP' `
        -Detail "No unattended credential file found at $EnvFile. Required env vars (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD) must be supplied some other way before this task can run unattended. See 05_IMPLEMENTATION\automation\README.md."
    exit 1
}

foreach ($var in @('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD')) {
    if (-not [System.Environment]::GetEnvironmentVariable($var, 'Process')) {
        Write-FailureLog -Code 'BLOCKED_CREDENTIAL_SETUP' -Detail "Required environment variable $var is not set after loading $EnvFile."
        exit 1
    }
}

# --- Single-run lock: reject overlapping runs (e.g. a retry fired by
# Task Scheduler while a previous run is still executing).
$lockAcquired = $false
try {
    $lockStream = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
}
catch [System.IO.IOException] {
    Write-FailureLog -Code 'OVERLAPPING_RUN_REJECTED' -Detail "Lock file $LockPath is already held by another instance. Refusing to start a concurrent run."
    exit 1
}

try {
    $lockAcquired = $true
    $writer = New-Object System.IO.StreamWriter($lockStream)
    $writer.WriteLine("pid=$PID started=$(Get-Date -Format 'o') host=$env:COMPUTERNAME")
    $writer.Flush()

    $mode = if ($Publish) { '--publish' } elseif ($DryRun) { '--dry-run' } else { '--dry-run' }

    Write-Host "Acquired lock $LockPath. Invoking uawso_daily_runner.py $mode ..."
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue)
    if (-not $pythonExe) {
        Write-FailureLog -Code 'PYTHON_NOT_FOUND' -Detail 'No python executable found on PATH for the account running this task.'
        exit 1
    }

    & python (Join-Path $AutomationDir 'uawso_daily_runner.py') $mode
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-FailureLog -Code 'RUNNER_NONZERO_EXIT' -Detail "uawso_daily_runner.py exited with code $exitCode (mode=$mode). See 07_EVIDENCE\automation\failures and 07_EVIDENCE\automation\runs for details."
    } else {
        Write-Host "uawso_daily_runner.py completed successfully (mode=$mode)."
    }

    exit $exitCode
}
catch {
    Write-FailureLog -Code 'WRAPPER_EXCEPTION' -Detail $_.Exception.Message
    exit 1
}
finally {
    if ($lockAcquired) {
        $writer.Dispose()
        $lockStream.Dispose()
        Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue
    }
}
