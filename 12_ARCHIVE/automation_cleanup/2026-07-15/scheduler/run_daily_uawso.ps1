# UAWSO daily scheduler wrapper.
#
# Intended to be invoked by a Windows Scheduled Task (see
# UAWSO_SCHEDULER_DESIGN.md for the exact `schtasks` registration
# command - NOT YET REGISTERED as of this build; registration requires
# a separate, explicitly confirmed step).
#
# This script assumes PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD are
# already present in the Scheduled Task's own environment (configured
# via the Task Scheduler UI/schtasks, never written into this file).

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\LED237\Documents\Projects\Weekly and Day Wise Filter monthly"
$Implementation = Join-Path $ProjectRoot "05_IMPLEMENTATION"
$Python = "C:\Users\LED237\AppData\Local\Programs\Python\Python311\python.exe"

Set-Location $Implementation

foreach ($var in @("PGHOST","PGPORT","PGDATABASE","PGUSER","PGPASSWORD")) {
    if (-not (Test-Path "env:$var")) {
        Write-Error "Missing required environment variable: $var"
        exit 1
    }
}

& $Python main.py --publish --i-understand-this-writes-to-production
exit $LASTEXITCODE
