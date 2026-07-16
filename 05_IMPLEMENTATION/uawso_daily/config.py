"""
Non-secret configuration for uawso_daily.

Database credentials are NEVER read or stored here - they come exclusively
from the existing, approved 05_IMPLEMENTATION/config/.env mechanism via
config.config.load_db_config(), the same mechanism every prior UAWSO
publication in this project has used. This module only holds operational
settings: timezone, dates, retry counts, directories, feature toggles.

All values are overridable via environment variables (see
05_IMPLEMENTATION/config/uawso_daily.example.env for the full list).
Nothing here is a secret - safe to log in full.
"""
import os
from dataclasses import dataclass
from datetime import date

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
IMPL_ROOT = os.path.join(os.path.dirname(__file__), "..")
RUNTIME_DIR = os.path.join(IMPL_ROOT, "runtime", "uawso_daily")
LOCKS_DIR = os.path.join(RUNTIME_DIR, "locks")
STATE_DIR = os.path.join(RUNTIME_DIR, "state")
LOGS_DIR = os.path.join(RUNTIME_DIR, "logs")
STAGING_ROOT_DIR = os.path.join(RUNTIME_DIR, "staging")
OUTPUTS_DIR = os.path.join(ROOT, "09_OUTPUTS")
EVIDENCE_DIR = os.path.join(ROOT, "07_EVIDENCE")


def _env_str(name, default):
    return os.getenv(name, default)


def _env_int(name, default):
    val = os.getenv(name)
    return int(val) if val not in (None, "") else default


def _env_bool(name, default):
    val = os.getenv(name)
    if val is None or val == "":
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _env_date(name, default_iso):
    val = os.getenv(name, default_iso)
    return date.fromisoformat(val)


@dataclass(frozen=True)
class AutomationConfig:
    timezone_name: str
    project_code: str
    assigned_user: str
    assigned_user_team: str
    report_start_date: date
    freshness_tolerance_days: int
    db_retry_count: int
    db_retry_base_delay_seconds: float
    output_dir: str
    evidence_dir: str
    publication_enabled: bool
    dry_run_default: bool
    log_retention_days: int


def load_automation_config() -> AutomationConfig:
    return AutomationConfig(
        timezone_name=_env_str("UAWSO_TIMEZONE", "Asia/Colombo"),
        project_code=_env_str("UAWSO_PROJECT_CODE", "UAWSO"),
        assigned_user=_env_str("UAWSO_ASSIGNED_USER", "utharsika"),
        assigned_user_team=_env_str("UAWSO_ASSIGNED_USER_TEAM", "ph_priors"),
        report_start_date=_env_date("UAWSO_REPORT_START_DATE", "2025-01-01"),
        freshness_tolerance_days=_env_int("UAWSO_FRESHNESS_TOLERANCE_DAYS", 0),
        db_retry_count=_env_int("UAWSO_DB_RETRY_COUNT", 3),
        db_retry_base_delay_seconds=float(_env_str("UAWSO_DB_RETRY_BASE_DELAY_SECONDS", "2")),
        output_dir=_env_str("UAWSO_OUTPUT_DIR", OUTPUTS_DIR),
        evidence_dir=_env_str("UAWSO_EVIDENCE_DIR", EVIDENCE_DIR),
        publication_enabled=_env_bool("UAWSO_PUBLICATION_ENABLED", True),
        dry_run_default=_env_bool("UAWSO_DRY_RUN_DEFAULT", False),
        log_retention_days=_env_int("UAWSO_LOG_RETENTION_DAYS", 30),
    )


def ensure_runtime_dirs():
    for d in (RUNTIME_DIR, LOCKS_DIR, STATE_DIR, LOGS_DIR, STAGING_ROOT_DIR):
        os.makedirs(d, exist_ok=True)
