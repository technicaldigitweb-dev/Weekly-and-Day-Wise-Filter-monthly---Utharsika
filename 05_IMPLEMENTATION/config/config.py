"""
UAWSO configuration loader.

All values that vary by environment (database credentials, connection
target) come from environment variables only. Nothing secret is
hardcoded here or defaulted to a real value - see .env.example for the
list of variables an operator must set before running main.py.
"""

import os
from dataclasses import dataclass


PROJECT_NAME = "Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report"
PROJECT_CODE = "UAWSO"
REQUIREMENT_ID = "PH-2026-07-UTHAR03"
DEVELOPER = "Satheskanth"
BUSINESS_VALIDATOR = "Satheesvaran"
ASSIGNED_USER = "utharsika"
TEAM = "PH Team"
ASSIGNED_USER_TEAM = "ph_priors"
TIMEZONE = "Asia/Colombo"
PHASE_LEVEL = 1
DAILY_PUBLICATION_DEADLINE_LOCAL = "06:00"

# Mandatory transaction filters (never parameterized away - see
# 04_DESIGN/UAWSO_BUSINESS_RULES_SPEC.md Section 1).
SOURCE_NAME_FILTER = "AMAZON"
MARKET_PLACE_FILTER = "UK"
ORDER_STATUS_FILTER = "Completed"
AMAZON_CHANNEL_CODE = 1  # ph_cate_products.which_channel

ACHIEVEMENT_TARGET_MULTIPLIER = 1.30


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: str
    dbname: str
    user: str
    password: str


_ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), ".env")


def _load_env_file_if_present() -> None:
    """
    Loads KEY=VALUE pairs from config/.env into os.environ, without
    overriding any variable the process already has set - so real
    process/session environment variables always take precedence over
    the .env file. Never logs values. No-op if the file doesn't exist.
    """
    if not os.path.exists(_ENV_FILE_PATH):
        return
    with open(_ENV_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def load_db_config() -> DBConfig:
    """
    Reads DB connection settings from environment variables, falling
    back to config/.env for any not already set in the process
    environment (see _load_env_file_if_present). Raises immediately (no
    hardcoded default) if any are still missing, so a misconfigured
    environment fails loudly instead of silently pointing at the wrong
    database.
    """
    _load_env_file_if_present()
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "See 05_IMPLEMENTATION/config/.env.example for the full list."
        )
    return DBConfig(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
    )


def redact(value: str) -> str:
    """Never print a credential value directly - use this in any log line."""
    return "[REDACTED]" if value else "[EMPTY]"
