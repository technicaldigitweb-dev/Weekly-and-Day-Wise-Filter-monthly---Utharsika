"""
UAWSO ph_task publisher.

Implements the Phase 8 publication sequence and the Same-Date
Correction Rule from 04_DESIGN/UAWSO_PH_TASK_PUBLICATION_PLAN.md.

IMPORTANT: this module performs a real INSERT/UPDATE against a shared
production table (tech_team_outputs.ph_task) that is visible on a real
user's dashboard. Per the stage's execution rules, publish_report()
must only be called after (a) validation has passed, and (b) explicit
human go-ahead has been given for the first live run - see
10_HANDOVER/UAWSO_HANDOVER.md for the current gate status. This module
is deliberately never invoked by this session's dry run.
"""

from dataclasses import dataclass
from typing import Optional

from config.config import (
    PROJECT_NAME, PROJECT_CODE, TEAM, DEVELOPER, ASSIGNED_USER,
    ASSIGNED_USER_TEAM, PHASE_LEVEL,
)
from src.version_resolver import format_task_id


@dataclass
class PublicationResult:
    inserted_row_id: Optional[int]
    task_id: str
    task_name: str
    version_level: int
    same_day_active_row_count: int
    duplicate_check_passed: bool
    committed: bool
    detail: str


def find_active_same_date_row(conn, report_date):
    """Pre-insert duplicate check: is there already an active (non-rejected) row for this date?"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, task_id, version_level
            FROM tech_team_outputs.ph_task
            WHERE project_code = %(project_code)s
              AND task_id LIKE %(task_id_prefix)s
              AND version_status <> 'rejected'
            ORDER BY version_level DESC
            LIMIT 1
            """,
            {"project_code": PROJECT_CODE, "task_id_prefix": f"UAWSO-{report_date.isoformat()}-utharsika-%"},
        )
        return cur.fetchone()


def reject_row(conn, row_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE tech_team_outputs.ph_task SET version_status = 'rejected', updated_at = now() WHERE id = %(id)s",
            {"id": row_id},
        )


def publish_report(conn, *, report_date, version, task_name, html_content, description, is_correction: bool):
    """
    Executes the full guarded publish sequence:
    1. pre-insert duplicate check
    2. transaction begin (conn must NOT be in autocommit mode)
    3. (correction only) reject the superseded same-date row
    4. insert
    5. read-back verification
    6. commit only when correct; rollback otherwise
    7. confirm exactly one active row remains for report_date
    """
    task_id = format_task_id(report_date, version)

    existing = find_active_same_date_row(conn, report_date)
    duplicate_check_passed = True
    if existing and not is_correction:
        # An active row already exists and this is NOT a declared correction -
        # refuse to publish a second active row for the same date.
        return PublicationResult(
            inserted_row_id=None, task_id=task_id, task_name=task_name, version_level=version,
            same_day_active_row_count=1, duplicate_check_passed=False, committed=False,
            detail=f"Active row already exists for {report_date} (id={existing[0]}); not a declared correction - refusing to insert a duplicate.",
        )

    try:
        if is_correction and existing:
            reject_row(conn, existing[0])

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tech_team_outputs.ph_task
                    (project_name, project_code, task_name, task_id, team, developer,
                     assigned_user, assigned_user_team, html_content, description,
                     phase_level, version_level, version_status)
                VALUES
                    (%(project_name)s, %(project_code)s, %(task_name)s, %(task_id)s, %(team)s, %(developer)s,
                     %(assigned_user)s, %(assigned_user_team)s, %(html_content)s, %(description)s,
                     %(phase_level)s, %(version_level)s, 'released')
                RETURNING id
                """,
                {
                    "project_name": PROJECT_NAME, "project_code": PROJECT_CODE, "task_name": task_name,
                    "task_id": task_id, "team": TEAM, "developer": DEVELOPER,
                    "assigned_user": ASSIGNED_USER, "assigned_user_team": ASSIGNED_USER_TEAM,
                    "html_content": html_content, "description": description,
                    "phase_level": PHASE_LEVEL, "version_level": version,
                },
            )
            new_id = cur.fetchone()[0]

            # Read-back verification
            cur.execute(
                "SELECT project_code, task_id, assigned_user, assigned_user_team, version_status, html_content "
                "FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": new_id},
            )
            row = cur.fetchone()
            row_ok = (
                row is not None
                and row[0] == PROJECT_CODE and row[1] == task_id
                and row[2] == ASSIGNED_USER and row[3] == ASSIGNED_USER_TEAM
                and row[4] == "released" and row[5] == html_content
            )

            cur.execute(
                "SELECT COUNT(*) FROM tech_team_outputs.ph_task "
                "WHERE project_code = %(project_code)s AND task_id LIKE %(prefix)s AND version_status <> 'rejected'",
                {"project_code": PROJECT_CODE, "prefix": f"UAWSO-{report_date.isoformat()}-utharsika-%"},
            )
            active_count = cur.fetchone()[0]

        if row_ok and active_count == 1:
            conn.commit()
            return PublicationResult(
                inserted_row_id=new_id, task_id=task_id, task_name=task_name, version_level=version,
                same_day_active_row_count=active_count, duplicate_check_passed=duplicate_check_passed,
                committed=True, detail="Inserted, read-back verified, exactly one active row confirmed, committed.",
            )
        else:
            conn.rollback()
            return PublicationResult(
                inserted_row_id=None, task_id=task_id, task_name=task_name, version_level=version,
                same_day_active_row_count=active_count, duplicate_check_passed=duplicate_check_passed,
                committed=False, detail=f"Read-back verification failed or active_count={active_count} != 1 - rolled back.",
            )
    except Exception as exc:
        conn.rollback()
        return PublicationResult(
            inserted_row_id=None, task_id=task_id, task_name=task_name, version_level=version,
            same_day_active_row_count=0, duplicate_check_passed=duplicate_check_passed,
            committed=False, detail=f"Exception during publish, rolled back: {exc}",
        )
