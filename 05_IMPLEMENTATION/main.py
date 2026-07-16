"""
UAWSO main orchestration entry point.

Usage:
    python main.py --dry-run       Resolve scope, run queries, calculate,
                                    render HTML, validate. No DB write.
                                    No promotion to 09_OUTPUTS by default
                                    (pass --promote to write the staged
                                    HTML file once validation passes).
    python main.py --publish       Full pipeline, and on validation
                                    success, publish the row to
                                    tech_team_outputs.ph_task. Requires
                                    the operator to also pass
                                    --i-understand-this-writes-to-production
                                    as an explicit confirmation flag - a
                                    bare --publish is refused.

Every run computes report_date = (Sri Lanka today) - 1 day and appends
to the day's execution log under 07_EVIDENCE/execution_logs/.
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from config import config
from src import period_calculator as pc
from src import db, sku_resolver, report_query, calculations, html_renderer, validator, version_resolver, evidence_writer
from src.logger import ExecutionLogger


def sri_lanka_now_str():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Colombo")).strftime("%Y-%m-%d %H:%M:%S")
    except ImportError:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " UTC"


def run_pipeline(logger: ExecutionLogger, readonly: bool):
    step = 0

    def next_step():
        nonlocal step
        step += 1
        return f"S{step:03d}"

    execution_date = pc.sri_lanka_today()
    report_date = pc.compute_report_date(execution_date)
    version = version_resolver.resolve_planned_version(report_date)
    output_identity = version_resolver.format_output_identity(report_date, version)

    logger.log(
        **{
            "Step ID": next_step(), "Milestone": "Pipeline start",
            "Action": "Compute execution_date/report_date/planned version",
            "Purpose": "Establish the reporting scope for this run",
            "Working directory": os.getcwd(),
            "Output": f"execution_date={execution_date} report_date={report_date} version=v{version:03d} identity={output_identity}",
            "Status": "PASS",
        }
    )

    with db.get_connection(readonly=readonly) as conn:
        # --- Assigned-SKU resolution ---
        assigned = sku_resolver.resolve_assigned_asins(conn, config.ASSIGNED_USER, config.AMAZON_CHANNEL_CODE)
        logger.log(
            **{
                "Step ID": next_step(), "Milestone": "Assigned-SKU resolution",
                "Action": "Resolve Utharsika's assigned Amazon ASINs",
                "Purpose": "Scope every downstream query to only Utharsika-assigned SKUs",
                "Script/file path": "src/sku_resolver.py, sql/01_resolve_assigned_asins.sql",
                "Input source": "public.user, public.ph_categories, public.ph_cate_products",
                "Database object": "public.ph_cate_products",
                "Operation type": "READ",
                "Output": f"assigned_asin_count={assigned.asin_count}",
                "Rows returned or affected": str(assigned.asin_count),
                "Validation result": "PASS" if assigned.asin_count > 0 else "FAIL - empty assignment set",
                "Status": "PASS" if assigned.asin_count > 0 else "FAIL",
            }
        )

        # --- Period boundaries ---
        period_sets = pc.all_periods(report_date)

        # --- Report queries + calculations per period ---
        period_rows = {}
        period_totals = {}
        matched_asin_counts = {}
        row_counts = {}
        validation_report = validator.ValidationReport()
        validator.validate_date_ranges(validation_report, period_sets, report_date)
        validator.validate_assignment_scope(validation_report, assigned)

        for ps in period_sets:
            raw_rows = report_query.run_report_query(conn, assigned.asins, ps)
            calc_rows = [calculations.calculate_row(r) for r in raw_rows]
            total = calculations.calculate_total(calc_rows)

            period_rows[ps.period_name] = calc_rows
            period_totals[ps.period_name] = total
            matched_asin_counts[ps.period_name] = len({r.asin for r in calc_rows})
            row_counts[ps.period_name] = len(calc_rows)

            validator.validate_period(validation_report, ps.period_name, calc_rows, total, assigned.asins)

            logger.log(
                **{
                    "Step ID": next_step(), "Milestone": f"{ps.period_name} report query + calculation",
                    "Action": f"Run report query and compute metrics for {ps.period_name}",
                    "Purpose": "Produce Sales/Orders/Change/Trend/Achieve% for the period",
                    "Script/file path": "src/report_query.py, sql/02_report_query.sql, src/calculations.py",
                    "Input source": "public.order_transaction",
                    "Database object": "public.order_transaction",
                    "Operation type": "READ",
                    "Output": f"rows={len(calc_rows)} matched_asins={matched_asin_counts[ps.period_name]}",
                    "Rows returned or affected": str(len(calc_rows)),
                    "Validation result": "see validation report",
                    "Status": "PASS",
                }
            )

    logger.log(
        **{
            "Step ID": next_step(), "Milestone": "Validation gate",
            "Action": "Evaluate all validation checks",
            "Purpose": "Block promotion/publication if any check fails",
            "Script/file path": "src/validator.py",
            "Output": f"checks={len(validation_report.checks)} all_passed={validation_report.all_passed}",
            "Validation result": "PASS" if validation_report.all_passed else "FAIL",
            "Status": "PASS" if validation_report.all_passed else "FAIL",
        }
    )

    # --- HTML rendering (staging) ---
    html = html_renderer.render_report(
        project_code=config.PROJECT_CODE,
        assigned_user=config.ASSIGNED_USER,
        version=f"v{version:03d}",
        generated_timestamp=sri_lanka_now_str(),
        report_cutoff_date=report_date,
        daily_rows=period_rows["DAILY"], daily_total=period_totals["DAILY"],
        weekly_rows=period_rows["WEEKLY"], weekly_total=period_totals["WEEKLY"],
        mtd_rows=period_rows["MTD"], mtd_total=period_totals["MTD"],
    )
    # NOTE: no "final" SHA-256 is computed here. The authoritative hash is
    # only ever computed from the bytes actually written to disk (see
    # html_renderer.write_html_and_hash), because a text-mode write can
    # translate line endings and silently change the byte content.

    logger.log(
        **{
            "Step ID": next_step(), "Milestone": "HTML rendering (staging)",
            "Action": "Render original UAWSO HTML report",
            "Purpose": "Produce the report artifact prior to promotion",
            "Script/file path": "src/html_renderer.py, templates/report_template.html",
            "Output": "HTML rendered in memory; hash to be computed on write",
            "Status": "PASS",
        }
    )

    return {
        "execution_date": execution_date, "report_date": report_date, "version": version,
        "output_identity": output_identity, "assigned": assigned, "period_sets": period_sets,
        "period_rows": period_rows, "period_totals": period_totals,
        "matched_asin_counts": matched_asin_counts, "row_counts": row_counts,
        "validation_report": validation_report, "html": html,
    }


def main():
    parser = argparse.ArgumentParser(description="UAWSO report pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Read-only run, no DB write, no promotion by default")
    parser.add_argument("--publish", action="store_true", help="Full pipeline including ph_task publication")
    parser.add_argument("--promote", action="store_true", help="Promote staged HTML to 09_OUTPUTS on validation success")
    parser.add_argument("--i-understand-this-writes-to-production", action="store_true", dest="confirm_write")
    args = parser.parse_args()

    if not args.dry_run and not args.publish:
        parser.error("Specify --dry-run or --publish")
    if args.publish and not args.confirm_write:
        parser.error("--publish requires --i-understand-this-writes-to-production")

    execution_date_for_log = pc.sri_lanka_today()
    report_date_for_log = pc.compute_report_date(execution_date_for_log)
    version_for_log = version_resolver.resolve_planned_version(report_date_for_log)
    identity = version_resolver.format_output_identity(report_date_for_log, version_for_log)

    log_dir = os.path.join(os.path.dirname(__file__), "..", "07_EVIDENCE", "execution_logs")
    log_path = os.path.join(log_dir, f"{identity}_EXECUTION_LOG.md")
    logger = ExecutionLogger(log_path)

    result = run_pipeline(logger, readonly=not args.publish)

    if not result["validation_report"].all_passed:
        print("VALIDATION FAILED - see execution log. No promotion, no publication.")
        sys.exit(1)

    html_sha256 = None
    if args.promote or args.publish:
        out_dir = os.path.join(os.path.dirname(__file__), "..", "09_OUTPUTS")
        out_path = os.path.join(out_dir, f"{result['output_identity']}.html")
        html_sha256 = html_renderer.write_html_and_hash(out_path, result["html"])
        print(f"Promoted HTML to {out_path} (sha256={html_sha256})")

    if args.publish:
        # Deliberately not implemented as a live call in this session -
        # see src/ph_task_publisher.py and 10_HANDOVER/UAWSO_HANDOVER.md
        # for the confirmed gate status before this path is exercised.
        raise NotImplementedError(
            "Live publication is gated pending explicit go-ahead - see handover doc. "
            "src/ph_task_publisher.publish_report() is implemented and ready to call "
            "once the gate is cleared."
        )

    print(f"Dry run complete. Validation all_passed={result['validation_report'].all_passed}. "
          f"HTML SHA-256={html_sha256 if html_sha256 else '(not promoted - pass --promote to write+hash the file)'}")


if __name__ == "__main__":
    main()
