# UAWSO Daily Scheduled Task — Registration Status

**Status: NOT REGISTERED on this machine. Blocked on Administrator elevation, not on database credentials.**

## What was attempted (2026-07-15, all real commands, all failed the same way)

An unattended ("run whether logged on or not") Scheduled Task requires either:
1. A principal that never needs a password (`NT AUTHORITY\SYSTEM`), or
2. An S4U logon (no stored password, but still privileged to configure), or
3. A stored user password (`/RU <user> /RP <password>`) — explicitly out of scope; no
   Windows account password was supplied to me and none should ever be hardcoded into a
   script per this project's rules.

Both (1) and (2) were tried from the actual build session, non-elevated:

```
> schtasks /Create /TN "UAWSO_Test_Probe" /TR "cmd.exe /c echo hi" /SC DAILY /ST 11:30 /RU "SYSTEM" /RL LIMITED /F
ERROR: Access is denied.

> Register-ScheduledTask -TaskName "UAWSO_Test_S4U" -Trigger $trigger -Action $action `
      -Principal (New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited)
Access is denied.
```

For comparison, creating a task under the **current interactive user with no special
principal** succeeds without elevation, but Task Scheduler reports `Logon Mode:
Interactive only` — i.e. it would only run while `LED237` is actually logged in, which
does not satisfy the "runs even when logged out" requirement from the task
specification:

```
> schtasks /Create /TN "UAWSO_Test_Probe2" /TR "cmd.exe /c echo hi" /SC DAILY /ST 11:30 /F
SUCCESS: ... Logon Mode: Interactive only
```

**Conclusion:** registering a truly unattended task on this machine requires local
Administrator rights. The current session (Claude Code running as `LED237`, a standard,
non-elevated account) does not have them and cannot obtain them non-interactively (no UAC
prompt is reachable from this environment). This is a **privilege blocker, not a
credential-design blocker** — the database credential mechanism (`.env.local`, see
`05_IMPLEMENTATION\automation\README.md`) is fully built and already verified working; only
the OS-level task registration step needs elevation.

## What is already fully prepared

- `07_EVIDENCE\automation\scheduler\UAWSO_Daily_11-30_Satheskanth.xml` — a complete,
  importable Task Scheduler XML definition: trigger daily 11:30 AM local time
  (Sri Lanka Standard Time / Asia/Colombo, UTC+05:30, no DST — confirmed via
  `Get-TimeZone` on this machine on 2026-07-15), principal `NT AUTHORITY\SYSTEM` (SID `S-1-5-18`,
  `RunLevel HighestAvailable` — SYSTEM never needs a stored password and is not
  restricted to "logged on" sessions), `StartWhenAvailable=true` (fires late if the
  machine was off/asleep at 11:30), retry 3 times at 5-minute intervals on failure,
  2-hour execution time limit, `MultipleInstancesPolicy=IgnoreNew` (a second trigger
  cannot start a concurrent run — this is a second, OS-level layer of protection on top
  of the PowerShell wrapper's own file lock). The action runs
  `run_uawso_daily.ps1 -Publish` via the full path to `powershell.exe`.
- **The XML's `<Enabled>` flag is deliberately set to `false`.** Even once an
  administrator registers it, it will not fire automatically until explicitly enabled.
  This is a separate, intentional safety gate on top of the elevation blocker: this
  automation has not yet completed a single real unattended `-Publish` run, so it should
  not be left live to fire autonomously at the very next 11:30 AM before a human has
  reviewed the first supervised run's output. See the final response's recommended
  next step.

## To complete registration (requires an Administrator-elevated PowerShell)

```powershell
schtasks /Create /TN "UAWSO Daily 11-30 - Satheskanth" `
  /XML "C:\Users\LED237\Documents\Projects\Weekly and Day Wise Filter monthly\07_EVIDENCE\automation\scheduler\UAWSO_Daily_11-30_Satheskanth.xml"
```

After registering, verify the SYSTEM-context unattended path works before enabling the
daily trigger, e.g.:

```powershell
schtasks /Run /TN "UAWSO Daily 11-30 - Satheskanth"
# then inspect 07_EVIDENCE\automation\runs\<today>\ and 07_EVIDENCE\automation\failures\
```

Only enable the daily trigger (`schtasks /Change /TN "UAWSO Daily 11-30 - Satheskanth" /ENABLE`)
once that first supervised run has been reviewed and confirmed correct.
