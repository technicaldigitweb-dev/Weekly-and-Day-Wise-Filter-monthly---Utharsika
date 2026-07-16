"""
UAWSO calculation module: Sales Change, Order Change, Trend, 130%
achievement. Encodes 04_DESIGN/UAWSO_BUSINESS_RULES_SPEC.md Section 5-6,
as corrected by this execution stage's Trend zero-base rule:

    Previous = 0, Current > 0  -> Trend = UP   (was previously "open"; now resolved)
    Previous = 0, Current = 0  -> Trend = NO CHANGE, improvement_status = NOT IMPROVED

Achieve % remains UNDEFINED (None) whenever the target (Previous * 1.30)
is zero - this is never fabricated as a number, per the stage brief:
"do not fabricate a numeric achievement percentage" for the
Previous=0,Current>0 case. This is intentionally different from Trend,
which IS resolved for that case.
"""

from dataclasses import dataclass
from typing import Optional

ACHIEVEMENT_TARGET_MULTIPLIER = 1.30


@dataclass(frozen=True)
class CalculatedRow:
    asin: str
    sku: str
    previous_year_sales: float
    previous_year_orders: int
    this_year_sales: float
    this_year_orders: int
    sales_change: Optional[float]      # None when previous_year_sales == 0 (undefined growth base)
    order_change: Optional[float]
    trend: str                         # 'UP' | 'DOWN' | 'NO CHANGE'
    sales_target: float
    order_target: float
    achieve_sales_pct: Optional[float]   # None when sales_target == 0 (undefined)
    achieve_order_pct: Optional[float]
    improvement_status: Optional[str]    # 'NOT IMPROVED' when previous==0 and current==0, else None


def _safe_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return (current - previous) / previous


def _safe_achieve_pct(current: float, target: float) -> Optional[float]:
    if target == 0:
        return None
    return (current / target) * 100.0


def _trend(current_sales: float, previous_sales: float) -> str:
    if previous_sales == 0 and current_sales == 0:
        return "NO CHANGE"
    if previous_sales == 0 and current_sales > 0:
        return "UP"
    if current_sales > previous_sales:
        return "UP"
    if current_sales < previous_sales:
        return "DOWN"
    return "NO CHANGE"


def calculate_row(raw) -> CalculatedRow:
    sales_target = raw.previous_year_sales * ACHIEVEMENT_TARGET_MULTIPLIER
    order_target = raw.previous_year_orders * ACHIEVEMENT_TARGET_MULTIPLIER

    both_zero_sales = raw.previous_year_sales == 0 and raw.this_year_sales == 0

    return CalculatedRow(
        asin=raw.asin,
        sku=raw.sku,
        previous_year_sales=raw.previous_year_sales,
        previous_year_orders=raw.previous_year_orders,
        this_year_sales=raw.this_year_sales,
        this_year_orders=raw.this_year_orders,
        sales_change=_safe_change(raw.this_year_sales, raw.previous_year_sales),
        order_change=_safe_change(raw.this_year_orders, raw.previous_year_orders),
        trend=_trend(raw.this_year_sales, raw.previous_year_sales),
        sales_target=sales_target,
        order_target=order_target,
        achieve_sales_pct=_safe_achieve_pct(raw.this_year_sales, sales_target),
        achieve_order_pct=_safe_achieve_pct(raw.this_year_orders, order_target),
        improvement_status=("NOT IMPROVED" if both_zero_sales else None),
    )


@dataclass(frozen=True)
class TotalRow:
    total_previous_year_sales: float
    total_previous_year_orders: int
    total_this_year_sales: float
    total_this_year_orders: int
    total_sales_change: Optional[float]
    total_order_change: Optional[float]
    total_achieve_sales_pct: Optional[float]
    total_achieve_order_pct: Optional[float]


def calculate_total(rows) -> TotalRow:
    """
    Computed from AGGREGATE sums, never from averaging row-level
    percentages - per the explicit "do not average row-level
    percentages" rule.
    """
    total_py_sales = sum(r.previous_year_sales for r in rows)
    total_py_orders = sum(r.previous_year_orders for r in rows)
    total_ty_sales = sum(r.this_year_sales for r in rows)
    total_ty_orders = sum(r.this_year_orders for r in rows)

    return TotalRow(
        total_previous_year_sales=total_py_sales,
        total_previous_year_orders=total_py_orders,
        total_this_year_sales=total_ty_sales,
        total_this_year_orders=total_ty_orders,
        total_sales_change=_safe_change(total_ty_sales, total_py_sales),
        total_order_change=_safe_change(total_ty_orders, total_py_orders),
        total_achieve_sales_pct=_safe_achieve_pct(total_ty_sales, total_py_sales * ACHIEVEMENT_TARGET_MULTIPLIER),
        total_achieve_order_pct=_safe_achieve_pct(total_ty_orders, total_py_orders * ACHIEVEMENT_TARGET_MULTIPLIER),
    )
