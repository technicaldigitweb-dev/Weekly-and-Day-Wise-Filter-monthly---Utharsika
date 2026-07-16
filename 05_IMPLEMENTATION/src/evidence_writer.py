"""
UAWSO evidence writer.

Writes the structured Markdown evidence files required by the stage
brief (dry-run evidence, publication evidence) under 07_EVIDENCE\\.
Never writes raw source-data dumps - only counts, ranges, and summaries.
"""

import os

EVIDENCE_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE")


def write_dry_run_evidence(*, path, execution_date, report_date, period_sets,
                            assigned_asin_count, matched_asin_counts,
                            row_counts, totals, validation_report):
    lines = []
    lines.append("# UAWSO Dry-Run Data Evidence\n")
    lines.append(f"**Execution date (Asia/Colombo):** {execution_date}\n")
    lines.append(f"**Report date:** {report_date}\n\n")

    lines.append("## Reporting Period Ranges\n")
    for ps in period_sets:
        lines.append(f"- **{ps.period_name}** — current: `{ps.current_year.start}` to `{ps.current_year.end}` | "
                      f"previous: `{ps.previous_year.start}` to `{ps.previous_year.end}`\n")

    lines.append(f"\n## Scope\n")
    lines.append(f"- Utharsika assigned-ASIN count: **{assigned_asin_count}**\n")
    for period_name, count in matched_asin_counts.items():
        lines.append(f"- Matched ASINs with transactions in {period_name}: **{count}**\n")

    lines.append(f"\n## Row Counts\n")
    for period_name, count in row_counts.items():
        lines.append(f"- {period_name} rows: **{count}**\n")

    lines.append(f"\n## Totals\n")
    for period_name, t in totals.items():
        lines.append(
            f"- **{period_name}** — Prev Sales: {t.total_previous_year_sales:.2f}, "
            f"This Sales: {t.total_this_year_sales:.2f}, Prev Orders: {t.total_previous_year_orders}, "
            f"This Orders: {t.total_this_year_orders}\n"
        )

    lines.append(f"\n## Validation Outcomes\n")
    lines.append(f"**All checks passed: {validation_report.all_passed}**\n\n")
    lines.append("| Check ID | Description | Result | Detail |\n|---|---|---|---|\n")
    for c in validation_report.checks:
        result = "PASS" if c.passed else "FAIL"
        lines.append(f"| {c.check_id} | {c.description} | {result} | {c.detail} |\n")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path
