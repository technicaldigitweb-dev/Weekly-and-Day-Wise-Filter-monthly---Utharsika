"""
uawso_daily CLI orchestrator - the single entry point behind
`python -m uawso_daily update-for-today`.

Sequence: acquire lock -> resolve run/report dates -> idempotency decision
(cases A-E) -> source-freshness gate -> extract -> transform -> render
(staged) -> validate -> promote to 09_OUTPUTS (unless --dry-run) ->
publish to ph_task (unless --dry-run or --no-publish or config disables
publication) -> post-commit hash verification -> write run-state JSON and
evidence markdown -> release lock -> return RunResult.

Every exit path (success, expected stop, or exception) goes through
_finish() so run-state/evidence are always written and the lock is always
released - see the try/finally structure in cmd_update_for_today().
"""
import argparse
import sys
import traceback
from datetime import date

from . import config as automation_config
from . import dates
from . import evidence
from . import extraction
from . import locking
from . import publication
from . import rendering
from . import transformation
from . import validation
from . import versioning
from .result import Code, RunResult


def _new_run_id() -> str:
    return "uawso_" + dates.now_colombo().strftime("%Y%m%d_%H%M%S")


def _iso(d):
    return d.isoformat() if d is not None else None


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="python -m uawso_daily")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("update-for-today", help="Run the full unattended daily UAWSO pipeline.")
    p.add_argument("--dry-run", action="store_true",
                    help="Extract, render, and validate only - writes nothing to 09_OUTPUTS or ph_task.")
    p.add_argument("--no-publish", action="store_true",
                    help="Extract, render, validate, and promote to 09_OUTPUTS - skips ph_task publication.")
    p.add_argument("--report-end-date", default=None,
                    help="Manual testing override for report_end_date (YYYY-MM-DD). Never used by the scheduled run.")
    p.add_argument("--force-rerun", action="store_true",
                    help="Bypass the ALREADY_COMPLETE short-circuit and produce a new corrected version even if today's report already matches ph_task.")
    p.add_argument("--verbose", action="store_true", help="Print step-by-step progress to stdout.")

    return parser.parse_args(argv)


def _log(verbose, message):
    if verbose:
        print(message, flush=True)


def cmd_update_for_today(args) -> RunResult:
    automation_config.ensure_runtime_dirs()
    cfg = automation_config.load_automation_config()
    run_id = _new_run_id()
    started_at = dates.now_colombo().isoformat()

    result = RunResult(run_id=run_id, command="update-for-today", started_at=started_at,
                        timezone=cfg.timezone_name, final_status=Code.CONFIGURATION_ERROR)

    lock = locking.RunLock(
        lock_path=__import__("os").path.join(automation_config.LOCKS_DIR, "update_for_today.lock"),
        run_id=run_id,
    )

    try:
        lock.acquire()
    except locking.LockHeldError as exc:
        result.final_status = Code.RUN_ALREADY_IN_PROGRESS
        result.failure_code = Code.RUN_ALREADY_IN_PROGRESS
        result.failure_detail = str(exc)
        return _finish(result, None)

    validation_report = None
    try:
        run_date = dates.today_colombo()
        report_end_override = date.fromisoformat(args.report_end_date) if args.report_end_date else None
        try:
            report_start, report_end = dates.report_window(run_date, cfg.report_start_date, report_end_override)
        except ValueError as exc:
            result.final_status = Code.CONFIGURATION_ERROR
            result.failure_code = Code.CONFIGURATION_ERROR
            result.failure_detail = str(exc)
            return _finish(result, validation_report)

        result.run_date = _iso(run_date)
        result.report_start_date = _iso(report_start)
        result.report_end_date = _iso(report_end)
        _log(args.verbose, f"[1/9] run_date={run_date} report_window={report_start}..{report_end}")

        # --- Idempotency decision (cases A-E) ---
        _log(args.verbose, "[2/9] Checking existing local output versions and ph_task state...")
        existing_versions = versioning.existing_versions_for_date(run_date)
        try:
            active_count = publication.count_active_rows_for_date(run_date)
        except Exception as exc:
            result.final_status = Code.DATABASE_CONNECTION_FAILED
            result.failure_code = Code.DATABASE_CONNECTION_FAILED
            result.failure_detail = f"Could not query ph_task for duplicate-active check: {exc}"
            return _finish(result, validation_report)

        if active_count > 1:
            result.final_status = Code.DUPLICATE_ACTIVE_OUTPUT
            result.failure_code = Code.DUPLICATE_ACTIVE_OUTPUT
            result.failure_detail = f"{active_count} active ph_task rows found for {run_date} - refusing to act."
            return _finish(result, validation_report)

        active_row = publication.find_active_row_for_date(run_date)  # (id, task_id, version_level) | None

        if active_row is not None and not args.force_rerun and not args.dry_run:
            existing_version_level = active_row[2]
            local_output_path = versioning.output_path_for(run_date, existing_version_level)
            if versioning.output_exists(run_date, existing_version_level):
                with open(local_output_path, "rb") as f:
                    local_hash = rendering.sha256_of_text(f.read().decode("utf-8"))
                try:
                    matches = _ph_task_hash_matches(active_row[0], local_hash)
                except Exception:
                    matches = False
                if matches:
                    result.final_status = Code.ALREADY_COMPLETE
                    result.version = existing_version_level
                    result.output_path = local_output_path
                    result.html_sha256 = local_hash
                    result.ph_task_row_id = active_row[0]
                    result.publication_action = "none_already_matches"
                    _log(args.verbose, f"[3/9] ALREADY_COMPLETE: version v{existing_version_level:03d} already matches ph_task row {active_row[0]}.")
                    return _finish(result, validation_report)

        is_correction = active_row is not None
        version = versioning.next_version_for_date(run_date)
        result.version = version
        _log(args.verbose, f"[3/9] Proceeding: version=v{version:03d} is_correction={is_correction}")

        # --- Source-freshness gate ---
        _log(args.verbose, "[4/9] Checking source freshness...")
        try:
            is_ready, source_max_date = extraction.check_source_freshness(report_end, cfg.freshness_tolerance_days)
        except Exception as exc:
            result.final_status = Code.DATABASE_CONNECTION_FAILED
            result.failure_code = Code.DATABASE_CONNECTION_FAILED
            result.failure_detail = f"Freshness probe failed: {exc}"
            return _finish(result, validation_report)
        result.source_max_date = _iso(source_max_date)
        if not is_ready:
            result.final_status = Code.SOURCE_NOT_READY
            result.failure_code = Code.SOURCE_NOT_READY
            result.failure_detail = f"source_max_date={source_max_date} does not reach report_end_date={report_end} within tolerance_days={cfg.freshness_tolerance_days}"
            return _finish(result, validation_report)

        # --- Extraction ---
        _log(args.verbose, "[5/9] Extracting from PostgreSQL (read-only)...")
        try:
            assigned_asins, product_master, daily_asin, vendor_periods = extraction.extract_report_data(report_start, report_end)
            multi_image_count = extraction.get_multi_image_count(assigned_asins)
        except Exception as exc:
            result.final_status = Code.EXTRACTION_FAILED
            result.failure_code = Code.EXTRACTION_FAILED
            result.failure_detail = f"{exc}"
            return _finish(result, validation_report)

        image_cov = transformation.compute_image_coverage(product_master)
        kpi_totals = transformation.compute_kpi_totals(daily_asin, vendor_periods, report_start, report_end)
        result.assigned_asin_count = image_cov["assigned_asin_count"]
        result.kpi_totals = kpi_totals
        result.extraction_counts = {
            "daily_aggregate_rows": len(daily_asin),
            "vendor_period_rows": len(vendor_periods),
            "image_covered_count": image_cov["image_covered_count"],
            "no_image_count": image_cov["no_image_count"],
            "multi_image_count": multi_image_count,
        }
        _log(args.verbose, f"[5/9] Extracted: {result.assigned_asin_count} ASINs, {len(daily_asin)} daily rows, totals={kpi_totals}")

        # --- Render (staged) ---
        _log(args.verbose, "[6/9] Rendering HTML (staged)...")
        generated_ts = dates.now_colombo().strftime("%Y-%m-%d %H:%M:%S (Asia/Colombo)")
        try:
            html_text = rendering.render_report_html(
                run_id=run_id, assigned_asin_count=result.assigned_asin_count,
                product_master_asin_level=product_master, daily_aggregates_asin=daily_asin,
                vendor_periods=vendor_periods, image_covered_count=image_cov["image_covered_count"],
                no_image_count=image_cov["no_image_count"], multi_image_count=multi_image_count,
                run_date=run_date, report_start=report_start, report_end=report_end,
                version=version, generated_timestamp=generated_ts,
            )
            staging_path = rendering.write_staging_file(run_id, html_text)
        except rendering.RenderValidationError as exc:
            result.final_status = Code.LOCAL_HTML_VALIDATION_FAILED
            result.failure_code = Code.LOCAL_HTML_VALIDATION_FAILED
            result.failure_detail = str(exc)
            return _finish(result, validation_report)
        result.html_sha256 = rendering.sha256_of_text(html_text)
        _log(args.verbose, f"[6/9] Staged: {staging_path} sha256={result.html_sha256}")

        # --- Validation gate ---
        _log(args.verbose, "[7/9] Running full validation gate...")
        try:
            validation_report = validation.run_full_validation_gate(
                assigned_asins=assigned_asins, product_master_asin_level=product_master,
                daily_aggregates_asin=daily_asin, report_start=report_start, report_end=report_end,
                computed_totals=kpi_totals, html_text=html_text,
            )
        except Exception as exc:
            result.final_status = Code.VALIDATION_FAILED
            result.failure_code = Code.VALIDATION_FAILED
            result.failure_detail = f"Validation gate raised: {exc}"
            return _finish(result, validation_report)

        if not validation_report.passed:
            result.final_status = Code.VALIDATION_FAILED
            result.failure_code = Code.VALIDATION_FAILED
            result.failure_detail = "; ".join(f"{c.name}: {c.detail}" for c in validation_report.failures())
            return _finish(result, validation_report)
        _log(args.verbose, f"[7/9] Validation PASSED ({len(validation_report.checks)} checks)")

        if args.dry_run:
            result.final_status = Code.DRY_RUN_COMPLETE
            result.output_path = staging_path
            _log(args.verbose, "[8/9] --dry-run: skipping promotion and publication.")
            return _finish(result, validation_report)

        # --- Promote to 09_OUTPUTS ---
        _log(args.verbose, "[8/9] Promoting staged HTML to 09_OUTPUTS...")
        try:
            output_path = rendering.promote_to_output(staging_path, run_date, version)
        except rendering.OutputVersionAlreadyExistsError as exc:
            result.final_status = Code.OUTPUT_VERSION_ALREADY_EXISTS
            result.failure_code = Code.OUTPUT_VERSION_ALREADY_EXISTS
            result.failure_detail = str(exc)
            return _finish(result, validation_report)
        result.output_path = output_path
        _log(args.verbose, f"[8/9] Promoted: {output_path}")

        if args.no_publish or not cfg.publication_enabled:
            result.final_status = Code.NO_PUBLISH_COMPLETE
            _log(args.verbose, "[9/9] --no-publish (or publication disabled): skipping ph_task publish.")
            return _finish(result, validation_report)

        # --- Publish to ph_task ---
        _log(args.verbose, "[9/9] Publishing to ph_task...")
        task_name = "Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report"
        description = (
            f"Automated daily UAWSO report (uawso_daily {run_id}), report window "
            f"{report_start.isoformat()} to {report_end.isoformat()}, version v{version:03d}."
        )
        try:
            outcome = publication.publish(
                report_date=run_date, version=version, task_name=task_name,
                html_content=html_text, description=description, is_correction=is_correction,
            )
        except Exception as exc:
            result.final_status = Code.PUBLICATION_FAILED
            result.failure_code = Code.PUBLICATION_FAILED
            result.failure_detail = str(exc)
            return _finish(result, validation_report)

        result.publication_action = outcome.action
        if outcome.action != "inserted" or outcome.row_id is None:
            result.final_status = Code.PUBLICATION_FAILED
            result.failure_code = Code.PUBLICATION_FAILED
            result.failure_detail = outcome.detail
            return _finish(result, validation_report)

        result.ph_task_row_id = outcome.row_id

        try:
            publication.verify_post_commit_hash(outcome.row_id, html_text)
        except publication.CriticalPostCommitMismatchError as exc:
            result.final_status = Code.CRITICAL_POST_COMMIT_MISMATCH
            result.failure_code = Code.CRITICAL_POST_COMMIT_MISMATCH
            result.failure_detail = str(exc)
            return _finish(result, validation_report)

        result.final_status = Code.SUCCESS
        _log(args.verbose, f"[9/9] Published: ph_task id={outcome.row_id} task_id={outcome.task_id}")
        return _finish(result, validation_report)

    except Exception:
        result.final_status = Code.CONFIGURATION_ERROR
        result.failure_code = "UNHANDLED_EXCEPTION"
        result.failure_detail = traceback.format_exc()
        return _finish(result, validation_report)
    finally:
        lock.release()


def _ph_task_hash_matches(row_id: int, local_hash: str) -> bool:
    import os
    import sys
    impl_root = os.path.join(os.path.dirname(__file__), "..")
    if impl_root not in sys.path:
        sys.path.insert(0, impl_root)
    from config.config import load_db_config
    import psycopg2

    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname,
                             user=cfg.user, password=cfg.password, connect_timeout=15)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT html_content FROM tech_team_outputs.ph_task WHERE id = %(id)s", {"id": row_id})
            row = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()
    if row is None:
        return False
    return rendering.sha256_of_text(row[0]) == local_hash


def _finish(result: RunResult, validation_report) -> RunResult:
    result.finished_at = dates.now_colombo().isoformat()
    try:
        evidence.write_run_state(result)
        result.evidence_path = evidence.write_run_evidence(result, validation_report)
        evidence.write_run_state(result)  # re-write once more so evidence_path itself is captured in the state file
    except Exception:
        pass  # never let evidence/state writing hide the real run outcome
    return result


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.command == "update-for-today":
        result = cmd_update_for_today(args)
        for line in result.summary_lines():
            print(line)
        return result.exit_code()
    return 2
