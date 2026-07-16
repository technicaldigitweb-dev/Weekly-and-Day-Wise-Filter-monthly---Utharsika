"""
Sanity tests for the uawso_daily automation package (05_IMPLEMENTATION/uawso_daily/).
No test-framework dependency, per the project's minimal-dependency stance -
run directly: python tests/test_uawso_daily_automation_package.py

None of these tests touch the live database or write to 09_OUTPUTS/ph_task -
they exercise pure logic (dates, versioning, locking, transformation,
result, config, validation aggregation, CLI parsing) against a temporary
scratch directory, never the real project folders.
"""
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from uawso_daily import cli, config, dates, locking, publication, result as result_mod, transformation, validation, versioning  # noqa: E402


def check(label, actual, expected):
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {label}: got {actual!r}, expected {expected!r}")
    return status == "PASS"


def check_true(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}{(': ' + detail) if detail else ''}")
    return status == "PASS"


def main():
    results = []

    # --- dates.py ---
    results.append(check_true("dates.TZ_SOURCE is a known value", dates.TZ_SOURCE in ("zoneinfo", "fixed-offset-fallback")))
    rs, re_ = dates.report_window(date(2026, 7, 16), date(2025, 1, 1))
    results.append(check("report_window default rule (run_date - 1 day)", re_, date(2026, 7, 15)))
    results.append(check("report_window preserves report_start", rs, date(2025, 1, 1)))
    rs2, re2 = dates.report_window(date(2026, 7, 16), date(2025, 1, 1), report_end_override=date(2026, 6, 30))
    results.append(check("report_window honors override", re2, date(2026, 6, 30)))
    raised = False
    try:
        dates.report_window(date(2025, 1, 1), date(2025, 6, 1))
    except ValueError:
        raised = True
    results.append(check_true("report_window raises ValueError on negative window", raised))
    results.append(check("output_identity format", dates.output_identity(date(2026, 7, 16), 1), "2026-07-16_utharsika_v001"))

    # --- versioning.py (temp output dir, never the real 09_OUTPUTS) ---
    tmp_out = tempfile.mkdtemp(prefix="uawso_daily_test_outputs_")
    try:
        results.append(check("existing_versions_for_date empty dir", versioning.existing_versions_for_date(date(2026, 7, 16), output_dir=tmp_out), []))
        results.append(check("next_version_for_date fresh date", versioning.next_version_for_date(date(2026, 7, 16), output_dir=tmp_out), 1))
        open(os.path.join(tmp_out, "2026-07-16_utharsika_v001.html"), "w").close()
        open(os.path.join(tmp_out, "2026-07-16_utharsika_v002.html"), "w").close()
        open(os.path.join(tmp_out, "2026-07-15_utharsika_v004.html"), "w").close()  # different date, must not count
        results.append(check("existing_versions_for_date finds only matching date", versioning.existing_versions_for_date(date(2026, 7, 16), output_dir=tmp_out), [1, 2]))
        results.append(check("next_version_for_date increments from max", versioning.next_version_for_date(date(2026, 7, 16), output_dir=tmp_out), 3))
        results.append(check_true("output_exists true for v001", versioning.output_exists(date(2026, 7, 16), 1, output_dir=tmp_out)))
        results.append(check_true("output_exists false for v099", not versioning.output_exists(date(2026, 7, 16), 99, output_dir=tmp_out)))
    finally:
        shutil.rmtree(tmp_out, ignore_errors=True)

    # --- locking.py (temp lock dir, never the real runtime lock) ---
    tmp_lock_dir = tempfile.mkdtemp(prefix="uawso_daily_test_locks_")
    try:
        lock_path = os.path.join(tmp_lock_dir, "test.lock")
        lock_a = locking.RunLock(lock_path, run_id="run_a")
        lock_a.acquire()
        results.append(check_true("lock file created on acquire", os.path.exists(lock_path)))

        lock_b = locking.RunLock(lock_path, run_id="run_b")
        held_error = False
        try:
            lock_b.acquire()
        except locking.LockHeldError:
            held_error = True
        results.append(check_true("second acquire raises LockHeldError while first is live", held_error))

        lock_a.release()
        results.append(check_true("lock file removed on release", not os.path.exists(lock_path)))

        # Stale lock: dead PID (very unlikely to be a real running process) + old timestamp
        import json
        stale_payload = {"pid": 999999, "run_id": "dead_run", "started_at": "2020-01-01T00:00:00",
                          "started_at_epoch": time.time() - (7 * 60 * 60)}
        with open(lock_path, "w", encoding="utf-8") as f:
            json.dump(stale_payload, f)
        lock_c = locking.RunLock(lock_path, run_id="run_c")
        stale_reclaimed = True
        try:
            lock_c.acquire()
        except locking.LockHeldError:
            stale_reclaimed = False
        results.append(check_true("stale lock (dead pid + old timestamp) is reclaimed", stale_reclaimed))
        lock_c.release()

        # Context manager releases even on exception
        cm_released = False
        try:
            with locking.RunLock(lock_path, run_id="run_d"):
                raise RuntimeError("simulated failure inside lock")
        except RuntimeError:
            cm_released = not os.path.exists(lock_path)
        results.append(check_true("RunLock context manager releases on exception", cm_released))
    finally:
        shutil.rmtree(tmp_lock_dir, ignore_errors=True)

    # --- transformation.py ---
    daily = [
        {"calendar_date": "2026-07-01", "asin": "A1", "fbm_sales": 10.0, "fbm_orders": 1, "fba_sales": 5.0, "fba_orders": 1},
        {"calendar_date": "2026-07-02", "asin": "A2", "fbm_sales": 20.0, "fbm_orders": 2, "fba_sales": 0.0, "fba_orders": 0},
    ]
    vendor = [
        {"asin": "A1", "start_date": "2026-06-01", "end_date": "2026-07-02", "revenue": 100.0, "units": 4},  # overlaps (end_date > report_start)
        {"asin": "A2", "start_date": "2026-07-20", "end_date": "2026-07-25", "revenue": 999.0, "units": 99},  # entirely after window, excluded
        {"asin": "A3", "start_date": "2026-06-30", "end_date": "2026-07-01", "revenue": 50.0, "units": 2},   # end_date == report_start, excluded (rule is strictly-greater)
    ]
    totals = transformation.compute_kpi_totals(daily, vendor, date(2026, 7, 1), date(2026, 7, 2))
    results.append(check("compute_kpi_totals fbm_sales", totals["fbm_sales"], 30.0))
    results.append(check("compute_kpi_totals fba_orders", totals["fba_orders"], 1))
    results.append(check("compute_kpi_totals vendor_sales includes only overlapping period", totals["vendor_sales"], 100.0))
    results.append(check("compute_kpi_totals vendor_orders (units, 1:1)", totals["vendor_orders"], 4))
    results.append(check("compute_kpi_totals total_orders = fbm+fba+vendor", totals["total_orders"], 1 + 2 + 1 + 0 + 4))

    product_master = [{"asin": "A1", "image_url": "http://x/1.jpg"}, {"asin": "A2", "image_url": None}, {"asin": "A3", "image_url": ""}]
    cov = transformation.compute_image_coverage(product_master)
    results.append(check("compute_image_coverage assigned_asin_count", cov["assigned_asin_count"], 3))
    results.append(check("compute_image_coverage image_covered_count", cov["image_covered_count"], 1))
    results.append(check("compute_image_coverage no_image_count", cov["no_image_count"], 2))

    # --- result.py ---
    r = result_mod.RunResult(run_id="uawso_test", command="update-for-today", started_at="x", final_status=result_mod.Code.SUCCESS)
    results.append(check("RunResult.exit_code SUCCESS -> 0", r.exit_code(), 0))
    r.final_status = result_mod.Code.VALIDATION_FAILED
    results.append(check("RunResult.exit_code failure -> 1", r.exit_code(), 1))
    r.final_status = result_mod.Code.ALREADY_COMPLETE
    results.append(check_true("ALREADY_COMPLETE is in SUCCESS_CODES", result_mod.Code.ALREADY_COMPLETE in result_mod.SUCCESS_CODES))
    d = r.to_dict()
    secret_like = [k for k in d if re.search(r"pass|pwd|secret|token", k, re.IGNORECASE)]
    results.append(check_true("RunResult.to_dict() has no credential-like field names", not secret_like, f"found={secret_like}"))
    results.append(check_true("summary_lines ends with PASS/FAIL", r.summary_lines()[-1] in ("PASS", "FAIL")))

    # --- config.py ---
    os.environ["UAWSO_FRESHNESS_TOLERANCE_DAYS"] = "5"
    cfg = config.load_automation_config()
    results.append(check("load_automation_config reads env override", cfg.freshness_tolerance_days, 5))
    del os.environ["UAWSO_FRESHNESS_TOLERANCE_DAYS"]
    cfg_default = config.load_automation_config()
    results.append(check("load_automation_config default freshness tolerance", cfg_default.freshness_tolerance_days, 0))
    results.append(check("load_automation_config default report_start_date", cfg_default.report_start_date, date(2025, 1, 1)))

    # --- validation.py aggregation logic (no DB calls) ---
    vr = validation.ValidationReport()
    vr.add("check_a", True, "ok")
    vr.add("check_b", True, "ok")
    results.append(check_true("ValidationReport.passed True when all checks pass", vr.passed))
    vr.add("check_c", False, "boom")
    results.append(check_true("ValidationReport.passed False when any check fails", not vr.passed))
    results.append(check("ValidationReport.failures() returns only failing checks", [c.name for c in vr.failures()], ["check_c"]))

    # --- cli.py argument parsing ---
    a1 = cli.parse_args(["update-for-today"])
    results.append(check_true("parse_args defaults: no flags set", not a1.dry_run and not a1.no_publish and not a1.force_rerun))
    a2 = cli.parse_args(["update-for-today", "--dry-run", "--verbose"])
    results.append(check_true("parse_args --dry-run --verbose", a2.dry_run and a2.verbose))
    a3 = cli.parse_args(["update-for-today", "--no-publish", "--report-end-date", "2026-06-30"])
    results.append(check("parse_args --report-end-date value", a3.report_end_date, "2026-06-30"))
    run_id = cli._new_run_id()
    results.append(check_true("run_id matches uawso_YYYYMMDD_HHMMSS pattern", bool(re.match(r"^uawso_\d{8}_\d{6}$", run_id)), run_id))

    # --- publication.py ---
    results.append(check("build_task_id format", publication.build_task_id(date(2026, 7, 16), 1), "UAWSO-2026-07-16-utharsika-v001"))

    # --- no-secrets source audit ---
    package_dir = os.path.join(os.path.dirname(__file__), "..", "uawso_daily")
    offending = []
    for fname in os.listdir(package_dir):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(package_dir, fname), "r", encoding="utf-8") as f:
            text = f.read()
        if re.search(r'PGPASSWORD\s*=\s*["\']', text) or re.search(r'password\s*=\s*["\'][^"\']+["\']', text, re.IGNORECASE):
            offending.append(fname)
    results.append(check_true("no uawso_daily/*.py file contains a literal hardcoded credential assignment", not offending, f"offending={offending}"))

    passed = sum(1 for r_ in results if r_)
    total = len(results)
    print(f"\n{passed}/{total} checks passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
