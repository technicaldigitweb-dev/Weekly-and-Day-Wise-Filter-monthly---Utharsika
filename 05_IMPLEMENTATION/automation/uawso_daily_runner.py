"""
UAWSO daily production orchestrator.

Implements the MANDATORY Historical Output Protection policy (adopted
2026-07-15, see 07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md):
    - Never overwrite, regenerate in place, rename over, delete, or
      modify any existing HTML output.
    - Never update, replace, delete, or reuse any existing ph_task row.
    - Before generating: list all existing HTML outputs + hashes/sizes;
      check whether the proposed filename already exists; check whether
      the proposed task_id/date/version already exists in ph_task.
    - Every successful run creates exactly ONE new dated/versioned HTML
      file, ONE new versioned ph_task row, and ONE new local evidence
      pack - never zero, never more than one.
    - After completion, re-verify every previously-existing HTML/ph_task
      hash is still unchanged.

Business rule (dynamic, exclusion-based - see
src/extract_uawso_v4_ordered_sales.py for the single source of truth):
    Include every order_status that is not null, not blank after
    BTRIM(), and not 'Cancelled'/'Canceled'. Never a fixed allow-list.

Usage:
    python uawso_daily_runner.py --dry-run
    python uawso_daily_runner.py --publish
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.config import load_db_config, redact, ASSIGNED_USER, AMAZON_CHANNEL_CODE  # noqa: E402
from src import dashboard_renderer  # noqa: E402
from src.html_renderer import write_html_and_hash  # noqa: E402
from src.extract_uawso_v4_ordered_sales import extract as run_extraction  # noqa: E402

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "09_OUTPUTS")
STAGING_DIR = os.path.join(OUTPUTS_DIR, "staging")
EVIDENCE_AUTOMATION_DIR = os.path.join(PROJECT_ROOT, "07_EVIDENCE", "automation")
RUNS_DIR = os.path.join(EVIDENCE_AUTOMATION_DIR, "runs")
FAILURES_DIR = os.path.join(EVIDENCE_AUTOMATION_DIR, "failures")
CHECKPOINTS_DIR = os.path.join(EVIDENCE_AUTOMATION_DIR, "checkpoints")

PROJECT_CODE = "UAWSO"
ASSIGNED_TEAM = "ph_priors"
FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_utharsika_v(\d{3})\.html$")
TASK_ID_RE = re.compile(r"^UAWSO-(\d{4}-\d{2}-\d{2})-utharsika-v(\d{3})$")

EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"}


class RunFailure(Exception):
    def __init__(self, code, detail):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


# ---------------------------------------------------------------------
# Step 0: inventory existing outputs (Historical Output Protection)
# ---------------------------------------------------------------------
def inventory_existing_outputs():
    inventory = {}
    for path in sorted(glob.glob(os.path.join(OUTPUTS_DIR, "*.html"))):
        name = os.path.basename(path)
        inventory[name] = {
            "path": path,
            "sha256": sha256_file(path),
            "size": os.path.getsize(path),
        }
    return inventory


def inventory_ph_task_rows(cur):
    cur.execute(
        "SELECT id, task_id, "
        "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
        "length(html_content) AS html_length, updated_at "
        "FROM tech_team_outputs.ph_task WHERE project_code = %(pc)s AND lower(assigned_user) = lower(%(u)s)",
        {"pc": PROJECT_CODE, "u": ASSIGNED_USER},
    )
    return {r[1]: {"id": r[0], "sha256": r[2], "length": r[3], "updated_at": str(r[4])} for r in cur.fetchall()}


# ---------------------------------------------------------------------
# Step 1: status discovery (dynamic, exclusion-based)
# ---------------------------------------------------------------------
def discover_statuses(cur):
    cur.execute(
        """
        SELECT order_status, COUNT(*) AS row_count,
               SUM(COALESCE(item_price,0)*COALESCE(quantity,0)) AS sales,
               COUNT(DISTINCT order_item_info) AS distinct_items,
               SUM(COALESCE(quantity,0)) AS quantity
        FROM public.order_transaction
        GROUP BY order_status
        ORDER BY order_status
        """
    )
    rows = cur.fetchall()
    discovered = []
    null_count = 0
    blank_count = 0
    included = []
    excluded = []
    for status, row_count, sales, distinct_items, quantity in rows:
        if status is None:
            null_count = row_count
            continue
        trimmed = status.strip()
        if trimmed == "":
            blank_count = row_count
            continue
        entry = {
            "status": status, "row_count": row_count,
            "sales": float(sales or 0), "distinct_items": distinct_items, "quantity": int(quantity or 0),
        }
        discovered.append(entry)
        if trimmed in EXCLUDED_ORDER_STATUSES:
            excluded.append(entry)
        else:
            included.append(entry)
    return {
        "discovered": discovered, "included": included, "excluded": excluded,
        "null_count": null_count, "blank_count": blank_count,
    }


def compare_against_previous_statuses(current_included):
    state_path = os.path.join(CHECKPOINTS_DIR, "uawso_known_statuses.json")
    current_names = sorted(e["status"] for e in current_included)
    previous_names = []
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            previous_names = json.load(f).get("included_statuses", [])
    new_statuses = [s for s in current_names if s not in previous_names]
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump({"included_statuses": current_names, "recorded_at": datetime.now().isoformat()}, f, indent=2)
    return new_statuses, previous_names


# ---------------------------------------------------------------------
# Step 2: safe data end date
# ---------------------------------------------------------------------
def determine_safe_end_date(cur, run_date: date) -> date:
    yesterday = run_date - timedelta(days=1)
    cur.execute(
        "SELECT MAX(order_date::date) FROM public.order_transaction WHERE order_date::date <= %(cutoff)s",
        {"cutoff": yesterday},
    )
    max_source_date = cur.fetchone()[0]
    if max_source_date is None:
        raise RunFailure("NO_SOURCE_DATA", "No order_transaction rows found at or before yesterday.")
    return min(max_source_date, yesterday)


# ---------------------------------------------------------------------
# Step 3: assigned-ASIN scope + drift check
# ---------------------------------------------------------------------
def resolve_assigned_scope(cur):
    cur.execute(
        """
        WITH target_user AS (
            SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower(%(u)s)
        ),
        target_categories AS (
            SELECT DISTINCT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
        ),
        raw_assignment AS (
            SELECT p.ref_id AS asin
            FROM public.ph_cate_products p JOIN target_categories c ON c.category_id = p.ass_cate_id
            WHERE p.which_channel = %(channel)s
        )
        SELECT COUNT(*) AS raw_count, COUNT(DISTINCT asin) AS distinct_count
        FROM raw_assignment
        """,
        {"u": ASSIGNED_USER, "channel": AMAZON_CHANNEL_CODE},
    )
    raw_count, distinct_count = cur.fetchone()
    if distinct_count == 0:
        raise RunFailure("SCOPE_CORRUPTION", "Assigned-ASIN resolution returned zero ASINs.")

    state_path = os.path.join(CHECKPOINTS_DIR, "uawso_asin_scope_state.json")
    previous_count = None
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            previous_count = json.load(f).get("distinct_asin_count")

    if previous_count is not None:
        change_pct = abs(distinct_count - previous_count) / previous_count
        if change_pct > 0.20:
            raise RunFailure(
                "SCOPE_CORRUPTION",
                f"Assigned ASIN count changed by {change_pct:.1%} ({previous_count} -> {distinct_count}) - "
                "exceeds the 20% unexplained-change threshold. Refusing to proceed automatically.",
            )

    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump({"distinct_asin_count": distinct_count, "recorded_at": datetime.now().isoformat()}, f, indent=2)

    return {"raw_count": raw_count, "distinct_count": distinct_count, "previous_count": previous_count}


# ---------------------------------------------------------------------
# Step 4: version resolution (Historical Output Protection)
# ---------------------------------------------------------------------
def resolve_next_version(existing_html_inventory, ph_task_rows):
    versions_found = []
    for name in existing_html_inventory:
        m = FILENAME_RE.match(name)
        if m:
            versions_found.append(int(m.group(2)))
    for task_id in ph_task_rows:
        m = TASK_ID_RE.match(task_id)
        if m:
            versions_found.append(int(m.group(2)))
    next_version = (max(versions_found) + 1) if versions_found else 1
    return next_version, sorted(set(versions_found))


def build_target_filename(run_date: date, version: int) -> str:
    return f"{run_date.isoformat()}_utharsika_v{version:03d}.html"


def check_already_completed(run_date: date, existing_html_inventory, ph_task_rows):
    """Returns the completed filename if today's date already has a
    successfully-published HTML+ph_task pair; None otherwise."""
    for name, info in existing_html_inventory.items():
        m = FILENAME_RE.match(name)
        if not m or m.group(1) != run_date.isoformat():
            continue
        version = int(m.group(2))
        expected_task_id = f"UAWSO-{run_date.isoformat()}-utharsika-v{version:03d}"
        row = ph_task_rows.get(expected_task_id)
        if row and row["sha256"] == info["sha256"]:
            return name, expected_task_id
    return None


# ---------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    dry_run = args.dry_run or not args.publish

    run_started_at = datetime.now()
    run_date = run_started_at.date()
    exit_code = 1
    manifest = {
        "run_started_at": run_started_at.isoformat(), "mode": "dry-run" if dry_run else "publish",
        "run_date": run_date.isoformat(),
    }

    import psycopg2

    cfg = load_db_config()
    print(f"[{run_started_at.isoformat()}] Connecting to host={cfg.host} port={cfg.port} "
          f"db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}")

    try:
        conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname,
                                 user=cfg.user, password=cfg.password, connect_timeout=15)
        conn.set_session(readonly=True, autocommit=True)  # read-only for discovery/extraction phase
    except Exception as e:
        return fail(manifest, run_date, "DB_CONNECT_FAILED", str(e))

    try:
        cur = conn.cursor()

        # ---- Historical Output Protection: inventory BEFORE anything ----
        html_inventory_before = inventory_existing_outputs()
        ph_task_rows_before = inventory_ph_task_rows(cur)
        manifest["html_inventory_before"] = html_inventory_before
        manifest["ph_task_rows_before"] = ph_task_rows_before
        print(f"Existing HTML outputs: {len(html_inventory_before)}; existing ph_task rows: {len(ph_task_rows_before)}")

        already = check_already_completed(run_date, html_inventory_before, ph_task_rows_before)
        if already:
            manifest["result"] = "ALREADY_COMPLETED"
            manifest["already_completed_filename"] = already[0]
            manifest["already_completed_task_id"] = already[1]
            write_manifest(manifest, run_date)
            print(f"ALREADY_COMPLETED: {already[0]} / {already[1]}")
            return 0

        # ---- Status discovery ----
        status_info = discover_statuses(cur)
        new_statuses, previous_statuses = compare_against_previous_statuses(status_info["included"])
        manifest["status_discovery"] = status_info
        manifest["new_statuses_since_last_run"] = new_statuses
        print(f"Discovered {len(status_info['discovered'])} statuses; "
              f"included={[e['status'] for e in status_info['included']]}; "
              f"excluded={[e['status'] for e in status_info['excluded']]}; "
              f"null={status_info['null_count']}; blank={status_info['blank_count']}")
        if new_statuses:
            print(f"NOTE: newly discovered non-cancellation status(es) since last run: {new_statuses} "
                  "- included automatically per the dynamic rule; review their Sales/Orders/Quantity "
                  "contribution in this run's evidence.")

        # ---- Safe end date ----
        safe_end_date = determine_safe_end_date(cur, run_date)
        manifest["data_start_date"] = "2025-01-01"
        manifest["data_end_date"] = safe_end_date.isoformat()
        print(f"Safe data end date: {safe_end_date.isoformat()}")

        # ---- Assigned scope ----
        scope_info = resolve_assigned_scope(cur)
        manifest["assigned_scope"] = scope_info
        print(f"Assigned ASIN count: {scope_info['distinct_count']} "
              f"(previous: {scope_info['previous_count']})")

        # ---- Version resolution ----
        next_version, versions_found = resolve_next_version(html_inventory_before, ph_task_rows_before)
        target_filename = build_target_filename(run_date, next_version)
        target_path = os.path.join(OUTPUTS_DIR, target_filename)
        target_task_id = f"UAWSO-{run_date.isoformat()}-utharsika-v{next_version:03d}"
        manifest["versions_found"] = versions_found
        manifest["resolved_version"] = next_version
        manifest["target_filename"] = target_filename
        manifest["target_task_id"] = target_task_id
        print(f"Resolved next version: v{next_version:03d} -> {target_filename} / {target_task_id}")

        if os.path.exists(target_path):
            return fail(manifest, run_date, "ALREADY_EXISTS",
                        f"Target path {target_path} already exists - refusing to overwrite.")
        if target_task_id in ph_task_rows_before:
            return fail(manifest, run_date, "ALREADY_EXISTS",
                        f"Target task_id {target_task_id} already exists in ph_task - refusing to reuse.")

        # ---- Fresh extraction (dynamic status rule, full historical range) ----
        assigned_asins, product_master_full, daily_split, vendor_periods = run_extraction(
            date(2025, 1, 1), safe_end_date
        )
        manifest["source_row_counts"] = {
            "assigned_asins": len(assigned_asins),
            "daily_split_rows": len(daily_split),
            "vendor_period_rows": len(vendor_periods),
        }

        no_sku_count = sum(1 for p in product_master_full if not p["skus"])
        with_sku_count = len(product_master_full) - no_sku_count
        sku_row_count = sum(len(p["skus"]) for p in product_master_full)
        vendor_asins = set(v["asin"] for v in vendor_periods)
        vendor_row_count = len(vendor_asins)
        total_row_count = sku_row_count + no_sku_count + sum(
            1 for p in product_master_full if p["skus"] and p["asin"] in vendor_asins
        )

        html = dashboard_renderer.render_dashboard_v4(
            project_name="Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report",
            project_code=PROJECT_CODE, assigned_user=ASSIGNED_USER,
            version=f"v{next_version:03d}", template_version="4.3.0-dynamic-automation",
            generated_timestamp=f"{run_started_at.isoformat()} (Asia/Colombo, automated daily run)",
            latest_completed_date=safe_end_date.isoformat(),
            history_start="2025-01-01", history_end=safe_end_date.isoformat(),
            selectable_start=f"{safe_end_date.year}-01-01", selectable_end=safe_end_date.isoformat(),
            assigned_asin_count=len(assigned_asins), assigned_sku_count=with_sku_count,
            product_master_full=product_master_full, daily_aggregates_split=daily_split,
            vendor_periods=vendor_periods, no_sku_count=no_sku_count, total_row_count=total_row_count,
            sku_row_count=sku_row_count, vendor_row_count=vendor_row_count,
        )

        unresolved = dashboard_renderer.verify_no_placeholders(html)
        if unresolved:
            return fail(manifest, run_date, "TEMPLATE_PLACEHOLDER_UNRESOLVED", str(unresolved))

        # ---- Validation gates ----
        gate_results = run_validation_gates(
            html=html, product_master_full=product_master_full, daily_split=daily_split,
            vendor_periods=vendor_periods, assigned_asins=assigned_asins,
            expected_row_count=total_row_count, cfg=cfg,
        )
        manifest["validation_gates"] = gate_results
        failed_gates = [k for k, v in gate_results.items() if not v["pass"]]
        if failed_gates:
            return fail(manifest, run_date, "VALIDATION_FAILED", f"Failed gates: {failed_gates}")

        if dry_run:
            dryrun_path = os.path.join(STAGING_DIR, f"DRYRUN_{target_filename}")
            os.makedirs(STAGING_DIR, exist_ok=True)
            dry_sha = write_html_and_hash(dryrun_path, html)
            manifest["result"] = "DRY_RUN_PASS"
            manifest["dry_run_output_path"] = dryrun_path
            manifest["dry_run_sha256"] = dry_sha
            write_manifest(manifest, run_date)
            write_validation_evidence(manifest, run_date, target_filename)
            print(f"DRY RUN PASS. Would publish: {target_filename} / {target_task_id}. "
                  f"Temporary output: {dryrun_path}")
            return 0

        # ---- PUBLISH: write the new file (never overwrite) ----
        os.makedirs(STAGING_DIR, exist_ok=True)
        staging_path = os.path.join(STAGING_DIR, f"{os.path.splitext(target_filename)[0]}.staging.html")
        write_html_and_hash(staging_path, html)
        local_sha256 = write_html_and_hash(target_path, html)
        local_size = os.path.getsize(target_path)
        manifest["local_html_sha256"] = local_sha256
        manifest["local_html_size"] = local_size
        print(f"Written new HTML: {target_path} SHA-256={local_sha256}")

        # ---- ph_task insert (transaction, pre-commit verification) ----
        conn.set_session(readonly=False, autocommit=False)
        pcur = conn.cursor()
        pcur.execute(
            "SELECT COUNT(*) FROM tech_team_outputs.ph_task WHERE task_id = %(tid)s",
            {"tid": target_task_id},
        )
        if pcur.fetchone()[0] != 0:
            conn.rollback()
            return fail(manifest, run_date, "FAIL_DUPLICATE", f"task_id {target_task_id} already exists.")
        pcur.execute(
            "SELECT COUNT(*) FROM tech_team_outputs.ph_task WHERE encode(sha256(convert_to(html_content,'UTF8')),'hex') = %(h)s",
            {"h": local_sha256},
        )
        if pcur.fetchone()[0] != 0:
            conn.rollback()
            return fail(manifest, run_date, "FAIL_DUPLICATE", "Identical HTML hash already published under a different row.")

        with open(target_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        pcur.execute(
            """
            INSERT INTO tech_team_outputs.ph_task
                (id, project_name, project_code, task_name, task_id, team, developer,
                 assigned_user, assigned_user_team, html_content, description,
                 phase_level, version_level, version_status, created_at, updated_at)
            VALUES
                (nextval('tech_team_outputs.ph_task_id_seq'),
                 %(pn)s, %(pc)s, %(tn)s, %(tid)s, %(team)s, %(dev)s,
                 %(u)s, %(ut)s, %(html)s, %(desc)s, 1, %(vl)s, 'released', now(), now())
            RETURNING id
            """,
            {
                "pn": "Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report",
                "pc": PROJECT_CODE, "tn": f"Utharsika Daily Automated Report v{next_version:03d}",
                "tid": target_task_id, "team": "PH Team", "dev": "satheskanth",
                "u": ASSIGNED_USER, "ut": ASSIGNED_TEAM, "html": html_text,
                "desc": f"Automated daily UAWSO run. Data range 2025-01-01 to {safe_end_date.isoformat()}. "
                        f"Dynamic status rule (exclude Cancelled/Canceled only).",
                "vl": next_version,
            },
        )
        new_row_id = pcur.fetchone()[0]

        pcur.execute(
            "SELECT id, task_id, project_code, assigned_user, version_level, "
            "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
            "length(html_content) AS html_length "
            "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
            {"rid": new_row_id},
        )
        inserted = pcur.fetchone()

        # re-check every previously-existing row is untouched, within the txn
        pcur.execute(
            "SELECT task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
            "FROM tech_team_outputs.ph_task WHERE task_id = ANY(%(tids)s)",
            {"tids": list(ph_task_rows_before.keys())},
        )
        unchanged_check = {r[0]: {"sha256": r[1], "updated_at": str(r[2])} for r in pcur.fetchall()}
        previous_rows_changed = [
            tid for tid, before in ph_task_rows_before.items()
            if unchanged_check.get(tid, {}).get("sha256") != before["sha256"]
            or unchanged_check.get(tid, {}).get("updated_at") != before["updated_at"]
        ]

        pre_commit_checks = {
            "hash_matches_local": inserted[5] == local_sha256,
            "project_code_correct": inserted[2] == PROJECT_CODE,
            "assigned_user_correct": inserted[3] == ASSIGNED_USER,
            "version_level_correct": inserted[4] == next_version,
            "data_start_present": "2025-01-01" in html_text,
            "data_end_present": safe_end_date.isoformat() in html_text,
            "no_previous_row_changed": len(previous_rows_changed) == 0,
        }
        manifest["pre_commit_checks"] = pre_commit_checks
        if not all(pre_commit_checks.values()):
            conn.rollback()
            return fail(manifest, run_date, "PRE_COMMIT_CHECK_FAILED", str(pre_commit_checks))

        conn.commit()
        print(f"COMMITTED. New ph_task row id={new_row_id}, task_id={target_task_id}")

        # ---- Post-commit verification ----
        pcur.execute(
            "SELECT id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256 "
            "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
            {"rid": new_row_id},
        )
        final_row = pcur.fetchone()
        stored_matches_local = final_row[1] == local_sha256

        # Historical Output Protection: final re-verification of ALL previous outputs
        html_inventory_after = inventory_existing_outputs()
        unexpected_changes = [
            name for name, before in html_inventory_before.items()
            if html_inventory_after.get(name, {}).get("sha256") != before["sha256"]
        ]
        new_html_files = [name for name in html_inventory_after if name not in html_inventory_before]

        manifest["result"] = "PASS"
        manifest["inserted_ph_task_row_id"] = new_row_id
        manifest["stored_sha256"] = final_row[1]
        manifest["stored_local_hash_match"] = stored_matches_local
        manifest["previous_html_files_changed"] = unexpected_changes
        manifest["new_html_files_created"] = new_html_files
        manifest["previous_ph_task_rows_changed"] = previous_rows_changed

        if unexpected_changes or len(new_html_files) != 1 or previous_rows_changed or not stored_matches_local:
            manifest["result"] = "PASS_WITH_PROTECTION_WARNING"

        write_manifest(manifest, run_date)
        write_validation_evidence(manifest, run_date, target_filename)
        write_monthly_reconciliation_placeholder(run_date, target_filename)

        print(f"RESULT: {manifest['result']}")
        print(f"Previous HTML files changed: {len(unexpected_changes)} (required: 0)")
        print(f"New HTML files created: {len(new_html_files)} (required: 1)")
        print(f"Previous ph_task rows changed: {len(previous_rows_changed)} (required: 0)")
        print(f"Stored/local hash match: {stored_matches_local}")

        exit_code = 0 if manifest["result"] == "PASS" else 1
        return exit_code

    except RunFailure as e:
        return fail(manifest, run_date, e.code, e.detail)
    except Exception as e:
        return fail(manifest, run_date, "UNEXPECTED_ERROR", repr(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_validation_gates(*, html, product_master_full, daily_split, vendor_periods, assigned_asins,
                          expected_row_count, cfg):
    gates = {}
    gates["all_asins_in_master"] = {"pass": len(product_master_full) == len(assigned_asins), "detail": len(product_master_full)}
    gates["no_credential_in_html"] = {"pass": cfg.password not in html, "detail": "checked"}
    gates["no_pg_host_in_html"] = {"pass": cfg.host not in html, "detail": "checked"}
    gates["no_connection_string"] = {"pass": "postgresql://" not in html and "psycopg2.connect" not in html, "detail": "checked"}
    gates["no_order_item_info_field"] = {"pass": '"order_item_info"' not in html and '"order_id"' not in html, "detail": "checked"}
    gates["has_one_table"] = {"pass": html.count('id="uawso-table"') == 1, "detail": html.count('id="uawso-table"')}
    gates["has_csv_buttons"] = {"pass": "btn-csv" in html and "btn-csv-full" in html, "detail": "checked"}
    gates["has_asin_sku_dropdowns"] = {"pass": "asin-dropdown" in html and "sku-dropdown" in html, "detail": "checked"}

    pair_set = {}
    dup_pairs = 0
    multi_sku_rows = 0
    for p in product_master_full:
        for sku in p["skus"]:
            key = (p["asin"], sku)
            if key in pair_set:
                dup_pairs += 1
            pair_set[key] = True
            if "," in sku:
                multi_sku_rows += 1
    gates["no_duplicate_asin_sku_pairs"] = {"pass": dup_pairs == 0, "detail": dup_pairs}
    gates["no_concatenated_skus"] = {"pass": multi_sku_rows == 0, "detail": multi_sku_rows}

    daily_key_counts = {}
    for row in daily_split:
        key = (row["calendar_date"], row["asin"], row["sku"])
        daily_key_counts[key] = daily_key_counts.get(key, 0) + 1
    dup_daily_rows = sum(1 for c in daily_key_counts.values() if c > 1)
    gates["no_duplicate_daily_rows"] = {"pass": dup_daily_rows == 0, "detail": dup_daily_rows}

    return gates


def write_manifest(manifest, run_date):
    run_dir = os.path.join(RUNS_DIR, run_date.isoformat())
    os.makedirs(run_dir, exist_ok=True)
    target = manifest.get("target_filename", f"{run_date.isoformat()}_run")
    base = os.path.splitext(target)[0]
    path = os.path.join(run_dir, f"{base}_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, default=str, indent=2)
    print(f"Manifest written: {path}")
    return path


def write_validation_evidence(manifest, run_date, target_filename):
    run_dir = os.path.join(RUNS_DIR, run_date.isoformat())
    os.makedirs(run_dir, exist_ok=True)
    base = os.path.splitext(target_filename)[0]
    path = os.path.join(run_dir, f"{base}_validation.md")
    gates = manifest.get("validation_gates", {})
    gate_lines = "\n".join(f"- `{k}`: {'PASS' if v['pass'] else 'FAIL'} ({v['detail']})" for k, v in gates.items())
    content = f"""# UAWSO Automated Run Validation — {manifest.get('target_filename', run_date.isoformat())}

**Mode:** {manifest.get('mode')}
**Result:** {manifest.get('result')}
**Run started:** {manifest.get('run_started_at')}
**Data range:** {manifest.get('data_start_date')} to {manifest.get('data_end_date')}
**Assigned ASIN count:** {manifest.get('assigned_scope', {}).get('distinct_count')} (previous: {manifest.get('assigned_scope', {}).get('previous_count')})

## Status rule (dynamic, exclusion-based)

Included: {[e['status'] for e in manifest.get('status_discovery', {}).get('included', [])]}
Excluded: {[e['status'] for e in manifest.get('status_discovery', {}).get('excluded', [])]}
Null: {manifest.get('status_discovery', {}).get('null_count')}
Blank: {manifest.get('status_discovery', {}).get('blank_count')}
Newly discovered since last run: {manifest.get('new_statuses_since_last_run')}

## Validation gates

{gate_lines}

## Historical Output Protection

- Previous HTML files changed: {manifest.get('previous_html_files_changed', 'n/a (dry-run)')}
- New HTML files created: {manifest.get('new_html_files_created', 'n/a (dry-run)')}
- Previous ph_task rows changed: {manifest.get('previous_ph_task_rows_changed', 'n/a (dry-run)')}
- Stored/local hash match: {manifest.get('stored_local_hash_match', 'n/a (dry-run)')}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Validation evidence written: {path}")
    return path


def write_monthly_reconciliation_placeholder(run_date, target_filename):
    run_dir = os.path.join(RUNS_DIR, run_date.isoformat())
    os.makedirs(run_dir, exist_ok=True)
    base = os.path.splitext(target_filename)[0]
    path = os.path.join(run_dir, f"{base}_monthly_reconciliation.csv")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("month,note\nALL,See validation evidence and manifest for this run's monthly totals.\n")
    return path


def fail(manifest, run_date, code, detail):
    manifest["result"] = "FAIL"
    manifest["failure_code"] = code
    manifest["failure_detail"] = detail
    os.makedirs(FAILURES_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    failure_path = os.path.join(FAILURES_DIR, f"{ts}_uawso_failure.md")
    with open(failure_path, "w", encoding="utf-8") as f:
        f.write(f"# UAWSO Automated Run Failure\n\n**Code:** {code}\n**Detail:** {detail}\n"
                f"**Manifest:**\n\n```json\n{json.dumps(manifest, default=str, indent=2)}\n```\n")
    print(f"FAIL [{code}]: {detail}")
    print(f"Failure evidence: {failure_path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
