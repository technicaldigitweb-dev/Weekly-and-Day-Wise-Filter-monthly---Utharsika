# UAWSO Scheduler Design

**What this asset is:** The scheduler mechanism, schedule, and registration command for the daily UAWSO run.

**Why it exists:** To document exactly how automation will be configured before it is registered with the OS.

**Business question supported:** "How and when will this run automatically?"

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Designed, **not yet registered**. Registration is gated pending explicit go-ahead (see `10_HANDOVER\UAWSO_HANDOVER.md`) because it authorizes unattended recurring writes to a shared production table.
**Next action:** On confirmation, run the registration command below from an elevated PowerShell session.

---

## Mechanism

Windows Task Scheduler (`schtasks`), running `05_IMPLEMENTATION\scheduler\run_daily_uawso.ps1` via `powershell.exe`.

## Schedule

- **Frequency:** Daily
- **Timezone:** `Asia/Colombo` (the task's trigger time must be set with this in mind - Windows Task Scheduler triggers on local machine time, so if the host machine's local timezone is not already `Asia/Colombo`, the trigger time must be converted to the host's local equivalent at registration time)
- **Start time (proposed, per this stage's instruction to choose a safe time):** `03:00 Asia/Colombo` — chosen to give a 3-hour buffer before the 06:00 Asia/Colombo publication deadline, comfortably covering the pipeline's expected runtime (schema-light aggregate queries over three periods, no heavy compute) plus room for one automatic retry on transient failure.
- **Daily publication deadline:** `06:00 Asia/Colombo` (from Project Identity, this execution stage).

## Command (not yet executed)

```text
schtasks /Create /TN "UAWSO_Daily_Report" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"C:\Users\LED237\Documents\Projects\Weekly and Day Wise Filter monthly\05_IMPLEMENTATION\scheduler\run_daily_uawso.ps1\"" /SC DAILY /ST 03:00 /RU "SYSTEM" /RL LIMITED
```

(The exact `/ST` clock value must be adjusted to the host machine's local timezone equivalent of 03:00 Asia/Colombo at registration time.)

## Working directory

`C:\Users\LED237\Documents\Projects\Weekly and Day Wise Filter monthly\05_IMPLEMENTATION` (set inside the wrapper script via `Set-Location`).

## Configuration path

`05_IMPLEMENTATION\config\config.py` (constants) + environment variables (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`) supplied to the Scheduled Task's own environment - never written into any file in this project.

## Logs

`07_EVIDENCE\execution_logs\YYYY-MM-DD_utharsika_vNNN_EXECUTION_LOG.md`, one per report date, written by `src/logger.py` during the run.

## Enable / Disable

```text
schtasks /Change /TN "UAWSO_Daily_Report" /DISABLE
schtasks /Change /TN "UAWSO_Daily_Report" /ENABLE
```

## Retry behaviour

`main.py --publish` performs its own pre-insert duplicate check (see `src/ph_task_publisher.py`), so a Task Scheduler-level retry (e.g. `/RI` restart interval) is safe: a retry after a transient failure will find no active same-date row yet and proceed normally; a retry after a successful publish will find the active row and refuse to insert a duplicate (see `find_active_same_date_row`).

## Next scheduled run

Not applicable until the task is registered.

## Explicitly Out of Scope This Build

The `schtasks /Create` command above has **not** been run. No Scheduled Task named `UAWSO_Daily_Report` exists yet on this machine.
