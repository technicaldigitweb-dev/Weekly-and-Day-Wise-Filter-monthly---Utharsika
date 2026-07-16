"""
ph_task publication wrapper for uawso_daily.

Imports and calls the existing, approved src/ph_task_publisher.py directly
(find_active_same_date_row / reject_row / publish_report) - no INSERT/UPDATE
SQL is duplicated here. Rules enforced at THIS layer, on top of what
publish_report() already enforces:
  - a fresh date (no active row yet) always publishes as is_correction=False
    (INSERT only, never touches any other date's row).
  - a same-day corrected version (idempotency case D) is the ONLY case that
    passes is_correction=True, and only for the run's own run_date - this
    module never rejects/updates a row for any date other than the one it
    was called for.
  - a row for a DIFFERENT date is never read, rejected, or updated by this
    module - find_active_same_date_row() itself is already scoped by
    report_date via the task_id prefix, so this is structural, not just a
    convention.
"""
import os
import sys
from dataclasses import dataclass
from typing import Optional

IMPL_ROOT = os.path.join(os.path.dirname(__file__), "..")
if IMPL_ROOT not in sys.path:
    sys.path.insert(0, IMPL_ROOT)

from config.config import load_db_config  # noqa: E402
from src import ph_task_publisher  # noqa: E402
from src.version_resolver import format_task_id  # noqa: E402

from .rendering import sha256_of_text


class CriticalPostCommitMismatchError(Exception):
    """Raised when the committed row's stored HTML hash does not match the local file hash - do not silently continue."""


@dataclass
class PublicationOutcome:
    action: str  # "inserted" | "already_published_matches" | "skipped_not_correction"
    row_id: Optional[int]
    task_id: str
    committed: bool
    detail: str


def _connect():
    import psycopg2
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname,
                             user=cfg.user, password=cfg.password, connect_timeout=15)
    return conn  # NOT autocommit/readonly - publish_report() manages the transaction itself


def find_active_row_for_date(report_date):
    conn = _connect()
    try:
        return ph_task_publisher.find_active_same_date_row(conn, report_date)
    finally:
        conn.rollback()
        conn.close()


def publish(*, report_date, version, task_name, html_content, description, is_correction: bool) -> PublicationOutcome:
    conn = _connect()
    try:
        result = ph_task_publisher.publish_report(
            conn, report_date=report_date, version=version, task_name=task_name,
            html_content=html_content, description=description, is_correction=is_correction,
        )
    finally:
        conn.close()

    if not result.duplicate_check_passed:
        return PublicationOutcome(
            action="skipped_not_correction", row_id=None, task_id=result.task_id,
            committed=False, detail=result.detail,
        )
    if not result.committed:
        raise RuntimeError(f"PUBLICATION_FAILED: {result.detail}")

    return PublicationOutcome(
        action="inserted", row_id=result.inserted_row_id, task_id=result.task_id,
        committed=True, detail=result.detail,
    )


def verify_post_commit_hash(row_id: int, local_html: str) -> None:
    """
    Post-commit safety net: re-reads the committed row's stored html_content
    directly (a fresh SELECT, not trusting the in-process result object) and
    compares its SHA-256 to the local staged/output file's SHA-256. Raises
    CriticalPostCommitMismatchError - never silently continues - if they differ.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT html_content FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": row_id},
            )
            row = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()

    if row is None:
        raise CriticalPostCommitMismatchError(f"CRITICAL_POST_COMMIT_MISMATCH: row id={row_id} not found on re-read.")

    stored_hash = sha256_of_text(row[0])
    local_hash = sha256_of_text(local_html)
    if stored_hash != local_hash:
        raise CriticalPostCommitMismatchError(
            f"CRITICAL_POST_COMMIT_MISMATCH: row id={row_id} stored_hash={stored_hash} local_hash={local_hash}"
        )


def build_task_id(report_date, version: int) -> str:
    return format_task_id(report_date, version)


def count_active_rows_for_date(report_date) -> int:
    """Used for the DUPLICATE_ACTIVE_OUTPUT check - independent of find_active_same_date_row's LIMIT 1."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM tech_team_outputs.ph_task "
                "WHERE project_code = %(pc)s AND task_id LIKE %(prefix)s AND version_status <> 'rejected'",
                {"pc": "UAWSO", "prefix": f"UAWSO-{report_date.isoformat()}-utharsika-%"},
            )
            return cur.fetchone()[0]
    finally:
        conn.rollback()
        conn.close()
