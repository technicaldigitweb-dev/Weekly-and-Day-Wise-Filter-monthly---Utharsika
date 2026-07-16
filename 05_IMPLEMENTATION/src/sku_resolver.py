"""
UAWSO assigned-SKU resolver.

Resolves the distinct set of Amazon ASINs assigned to a given PH user
via public.user -> public.ph_categories -> public.ph_cate_products,
per 04_DESIGN/UAWSO_SOURCE_TO_TARGET_MAPPING.md Section 0.

Deliberately does NOT touch order_transaction.user_name - assignment
is defined solely by the category chain, never by transaction-level
attribution (stage brief, Strict Utharsika-Only Product Scope).
"""

import os
from dataclasses import dataclass

SQL_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "01_resolve_assigned_asins.sql")


@dataclass(frozen=True)
class AssignedSkuResult:
    assigned_user: str
    channel_code: int
    asin_count: int
    asins: frozenset


def resolve_assigned_asins(conn, assigned_user: str, channel_code: int) -> AssignedSkuResult:
    """
    Runs the resolution query and returns a distinct ASIN set.
    De-duplication is enforced twice: once in SQL (DISTINCT p.ref_id)
    and once here (frozenset) as a defensive second layer, per the
    stage brief's requirement that "duplicated assignment rows do not
    duplicate report totals."
    """
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql, {"assigned_user": assigned_user, "channel_code": channel_code})
        rows = cur.fetchall()

    asins = frozenset(r[0] for r in rows)
    return AssignedSkuResult(
        assigned_user=assigned_user,
        channel_code=channel_code,
        asin_count=len(asins),
        asins=asins,
    )


def assert_no_cross_user_leakage(result: AssignedSkuResult, other_user_asins: frozenset) -> None:
    """
    Defensive check usable in tests/validation: proves the resolved set
    does not silently include ASINs known to belong only to another
    user's assignment set. Not called with any real other-user data in
    this project - see the isolation rule in every design document.
    """
    overlap_only_other = other_user_asins - result.asins
    assert len(overlap_only_other) == len(other_user_asins), (
        "Unexpected: resolver appears to have absorbed another user's exclusive ASINs."
    )
