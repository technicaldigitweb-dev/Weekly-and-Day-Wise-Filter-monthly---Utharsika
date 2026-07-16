"""
UAWSO controlled ph_task HTML replacement.

Updates ONLY html_content and updated_at on the single, already-existing
UAWSO v001 row - never inserts, never touches task_id/assigned_user/
assigned_user_team/report identity/version columns. Requires the UPDATE
to affect exactly one row before committing; rolls back otherwise.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReplaceResult:
    matched_row_id: Optional[int]
    rows_affected: int
    committed: bool
    detail: str


def find_unique_target_row(conn, *, task_id, assigned_user, project_code):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, task_id, assigned_user, assigned_user_team, task_name, version_level, version_status
            FROM tech_team_outputs.ph_task
            WHERE task_id = %(task_id)s AND assigned_user = %(assigned_user)s AND project_code = %(project_code)s
            """,
            {"task_id": task_id, "assigned_user": assigned_user, "project_code": project_code},
        )
        return cur.fetchall()


def replace_html_content(conn, *, task_id, assigned_user, project_code, new_html_content) -> ReplaceResult:
    """
    Guarded sequence: locate the unique target row -> UPDATE only
    html_content/updated_at, scoped by id AND task_id AND assigned_user
    (belt-and-braces WHERE clause) -> verify exactly one row affected ->
    commit or rollback.
    """
    matches = find_unique_target_row(conn, task_id=task_id, assigned_user=assigned_user, project_code=project_code)
    if len(matches) != 1:
        return ReplaceResult(
            matched_row_id=None, rows_affected=0, committed=False,
            detail=f"Expected exactly 1 matching row, found {len(matches)} - refusing to update.",
        )
    target_id = matches[0][0]

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tech_team_outputs.ph_task
                SET html_content = %(new_html)s, updated_at = now()
                WHERE id = %(id)s AND task_id = %(task_id)s AND assigned_user = %(assigned_user)s
                """,
                {"new_html": new_html_content, "id": target_id, "task_id": task_id, "assigned_user": assigned_user},
            )
            rows_affected = cur.rowcount

        if rows_affected == 1:
            conn.commit()
            return ReplaceResult(matched_row_id=target_id, rows_affected=rows_affected, committed=True, detail="Updated and committed.")
        else:
            conn.rollback()
            return ReplaceResult(matched_row_id=target_id, rows_affected=rows_affected, committed=False, detail=f"rows_affected={rows_affected} != 1 - rolled back.")
    except Exception as exc:
        conn.rollback()
        return ReplaceResult(matched_row_id=None, rows_affected=0, committed=False, detail=f"Exception, rolled back: {exc}")
