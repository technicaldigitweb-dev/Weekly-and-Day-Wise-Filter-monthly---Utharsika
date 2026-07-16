"""
UAWSO version resolver.

Tracks version numbers (v001, v002, ...) per the One-Day-One-File rule:
- version increases once per SUCCESSFULLY PUBLISHED reporting day.
- a failed attempt does not consume a version.
- a same-day retry (before success) reuses the same PLANNED version.
- naming: YYYY-MM-DD_utharsika_vNNN, where YYYY-MM-DD = report_date.

State is persisted to 05_IMPLEMENTATION/state/version_state.json so
version numbers survive across process restarts. This file lives
inside the approved project root only.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import date

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "version_state.json")


@dataclass
class VersionState:
    last_published_report_date: str  # ISO date string, or "" if none yet
    last_published_version: int      # 0 if none yet


def _load_state() -> VersionState:
    if not os.path.exists(STATE_PATH):
        return VersionState(last_published_report_date="", last_published_version=0)
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return VersionState(**data)


def _save_state(state: VersionState) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2)


def resolve_planned_version(report_date: date) -> int:
    """
    Returns the version number to USE for this report_date without
    consuming/persisting anything - safe to call repeatedly (e.g. on
    retries) before a successful publish.
    """
    state = _load_state()
    if state.last_published_report_date == report_date.isoformat():
        # Same-day retry after a prior success on this exact date (e.g. a
        # correction flow) - see Same-Date Correction Rule in the
        # publication plan for how the *next* version is then chosen.
        return state.last_published_version
    return state.last_published_version + 1


def consume_version_on_success(report_date: date, version: int) -> None:
    """
    Call ONLY after a ph_task row has been successfully committed and
    read back. Persists the version as consumed so the next distinct
    report_date receives version+1.
    """
    state = VersionState(last_published_report_date=report_date.isoformat(), last_published_version=version)
    _save_state(state)


def format_output_identity(report_date: date, version: int) -> str:
    return f"{report_date.isoformat()}_utharsika_v{version:03d}"


def format_task_id(report_date: date, version: int) -> str:
    return f"UAWSO-{report_date.isoformat()}-utharsika-v{version:03d}"
