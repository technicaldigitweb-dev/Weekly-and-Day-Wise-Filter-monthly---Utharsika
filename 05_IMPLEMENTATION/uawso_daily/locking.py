"""
Single-run file lock for uawso_daily - prevents a second concurrent run
(e.g. a slow scheduled run overlapping a manual run) from starting while
one is already active.

Mechanism: a lock file containing {pid, started_at, run_id} JSON, created
with an exclusive (O_CREAT|O_EXCL) open so two processes racing to create
it cannot both succeed. A PostgreSQL advisory lock is documented as an
alternative (see README "Recovery steps") but not implemented here, since
a local file lock is sufficient for a single-VM cron deployment and adds
no database dependency to the lock check itself.

Stale-lock handling: a lock is considered stale only if BOTH (a) its
recorded PID is no longer a running process on this machine, AND (b) it
is older than STALE_LOCK_MAX_AGE_SECONDS. Both conditions are required
before a stale lock is auto-cleared - a lock is never deleted purely
because it is "old" (a slow-but-legitimate run must not be killed), and
never purely because "the PID looks free" (PID reuse could otherwise
cause a live lock to be misidentified as stale).
"""
import json
import os
import time

STALE_LOCK_MAX_AGE_SECONDS = 6 * 60 * 60  # 6 hours - far longer than any real run should take


class LockHeldError(Exception):
    """Raised when another run currently holds the lock."""


def _pid_is_running(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # exists, just owned by another user


class RunLock:
    def __init__(self, lock_path: str, run_id: str):
        self.lock_path = lock_path
        self.run_id = run_id
        self._acquired = False

    def _read_existing(self):
        try:
            with open(self.lock_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def acquire(self):
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        existing = self._read_existing()
        if existing is not None:
            age = time.time() - existing.get("started_at_epoch", 0)
            pid_alive = _pid_is_running(existing.get("pid", -1))
            if pid_alive or age < STALE_LOCK_MAX_AGE_SECONDS:
                raise LockHeldError(
                    f"RUN_ALREADY_IN_PROGRESS: lock held by pid={existing.get('pid')} "
                    f"run_id={existing.get('run_id')} started_at={existing.get('started_at')} "
                    f"(pid_alive={pid_alive}, age_seconds={age:.0f})"
                )
            # Stale: PID confirmed dead AND lock older than the max age - safe to reclaim.
            try:
                os.remove(self.lock_path)
            except FileNotFoundError:
                pass

        payload = {
            "pid": os.getpid(),
            "run_id": self.run_id,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "started_at_epoch": time.time(),
        }
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._acquired = True
        except FileExistsError:
            raise LockHeldError("RUN_ALREADY_IN_PROGRESS: lock file was created by a concurrent process just now")

    def release(self):
        if self._acquired:
            try:
                os.remove(self.lock_path)
            except FileNotFoundError:
                pass
            self._acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        # Released on success, controlled failure, AND exception - always.
        self.release()
        return False
