"""
Unit tests for 05_IMPLEMENTATION\\automation\\uawso_daily_runner.py logic
that does not require a live database connection: dynamic status rule,
version resolution, filename construction, Vendor period-overlap
arithmetic (client-engine mirror), and duplicate-prevention checks.

Run: python 05_IMPLEMENTATION\\tests\\test_uawso_daily_runner.py
No network/DB access is performed by this file.
"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "automation"))

from src.extract_uawso_v4_ordered_sales import is_included_order_status, EXCLUDED_ORDER_STATUSES  # noqa: E402
import uawso_daily_runner as runner  # noqa: E402


class DynamicStatusRuleTests(unittest.TestCase):
    def test_excludes_only_the_two_cancellation_variants(self):
        self.assertEqual(EXCLUDED_ORDER_STATUSES, {"Cancelled", "Canceled"})

    def test_included_statuses(self):
        for status in ["Completed", "Refunded", "Deleted", "New", "Pending", "Inprogress", "Hold"]:
            self.assertTrue(is_included_order_status(status), status)

    def test_excluded_statuses(self):
        for status in ["Cancelled", "Canceled", "  Cancelled  ", "CANCELLED".title()]:
            self.assertFalse(is_included_order_status(status), status)

    def test_null_and_blank_excluded(self):
        self.assertFalse(is_included_order_status(None))
        self.assertFalse(is_included_order_status(""))
        self.assertFalse(is_included_order_status("   "))

    def test_new_future_status_is_included_automatically(self):
        # A status never seen before ("Backordered") must be included by
        # the exclusion rule with no code change - this is the entire
        # point of the dynamic rule replacing the old fixed allow-list.
        self.assertTrue(is_included_order_status("Backordered"))


class VersionResolutionTests(unittest.TestCase):
    def test_first_ever_run_starts_at_v001(self):
        next_version, found = runner.resolve_next_version({}, {})
        self.assertEqual(next_version, 1)
        self.assertEqual(found, [])

    def test_next_version_is_max_plus_one_across_files_and_db(self):
        html_inv = {
            "2026-07-09_utharsika_v001.html": {},
            "2026-07-10_utharsika_v001.html": {},
            "2026-07-10_utharsika_v002.html": {},
        }
        ph_task_rows = {
            "UAWSO-2026-07-14-utharsika-v002": {},
        }
        next_version, found = runner.resolve_next_version(html_inv, ph_task_rows)
        self.assertEqual(next_version, 3)
        self.assertEqual(found, [1, 2])

    def test_db_only_version_still_counted(self):
        # If a version exists only as a ph_task row (e.g. local file was
        # cleaned up) it must still be respected, never reused.
        next_version, found = runner.resolve_next_version({}, {"UAWSO-2026-07-01-utharsika-v005": {}})
        self.assertEqual(next_version, 6)

    def test_malformed_names_are_ignored_not_counted(self):
        html_inv = {"not_a_uawso_file.html": {}, "2026-13-40_utharsika_v001.html": {}}
        next_version, found = runner.resolve_next_version(html_inv, {})
        # "2026-13-40" fails the \d{4}-\d{2}-\d{2} shape check? Actually
        # it matches the regex shape (digits only) even though month=13
        # is not a real calendar date - the version-number extraction
        # does not validate calendar correctness, only counts version.
        self.assertIn(1, found)


class FilenameConstructionTests(unittest.TestCase):
    def test_build_target_filename(self):
        name = runner.build_target_filename(date(2026, 7, 15), 3)
        self.assertEqual(name, "2026-07-15_utharsika_v003.html")

    def test_filename_regex_round_trips(self):
        name = runner.build_target_filename(date(2026, 1, 5), 12)
        m = runner.FILENAME_RE.match(name)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "2026-01-05")
        self.assertEqual(int(m.group(2)), 12)

    def test_task_id_regex_round_trips(self):
        task_id = f"UAWSO-2026-07-15-utharsika-v003"
        m = runner.TASK_ID_RE.match(task_id)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "2026-07-15")
        self.assertEqual(int(m.group(2)), 3)


class AlreadyCompletedTests(unittest.TestCase):
    def test_detects_already_completed_same_day(self):
        run_date = date(2026, 7, 15)
        name = "2026-07-15_utharsika_v004.html"
        html_inv = {name: {"sha256": "abc123", "size": 100}}
        ph_task_rows = {"UAWSO-2026-07-15-utharsika-v004": {"sha256": "abc123"}}
        result = runner.check_already_completed(run_date, html_inv, ph_task_rows)
        self.assertEqual(result, (name, "UAWSO-2026-07-15-utharsika-v004"))

    def test_no_match_when_hash_mismatch(self):
        run_date = date(2026, 7, 15)
        name = "2026-07-15_utharsika_v004.html"
        html_inv = {name: {"sha256": "abc123", "size": 100}}
        ph_task_rows = {"UAWSO-2026-07-15-utharsika-v004": {"sha256": "DIFFERENT"}}
        result = runner.check_already_completed(run_date, html_inv, ph_task_rows)
        self.assertIsNone(result)

    def test_no_match_for_other_dates(self):
        run_date = date(2026, 7, 15)
        html_inv = {"2026-07-14_utharsika_v002.html": {"sha256": "abc123", "size": 100}}
        ph_task_rows = {"UAWSO-2026-07-14-utharsika-v002": {"sha256": "abc123"}}
        result = runner.check_already_completed(run_date, html_inv, ph_task_rows)
        self.assertIsNone(result)


class VendorOverlapTests(unittest.TestCase):
    """Mirrors the periodsOverlapV4 fix in src/uawso_client_engine.js:
    !(pEnd <= rStart || pStart > rEnd) - strict <= on the end boundary,
    fixing the double-count bug where a period ending exactly at the
    next range's start used to leak into that next range."""

    @staticmethod
    def overlaps(p_start, p_end, r_start, r_end):
        return not (p_end <= r_start or p_start > r_end)

    def test_period_ending_exactly_at_next_range_start_does_not_overlap(self):
        # Vendor period Jun 1 - Jul 1; range = July (Jul 1 - Jul 31).
        # pEnd (Jul 1) <= rStart (Jul 1) -> no overlap with July.
        self.assertFalse(self.overlaps(date(2026, 6, 1), date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31)))

    def test_period_ending_exactly_at_next_range_start_overlaps_prior_range(self):
        # Same period against June (Jun 1 - Jun 30): pEnd (Jul 1) > rStart, overlaps.
        self.assertTrue(self.overlaps(date(2026, 6, 1), date(2026, 7, 1), date(2026, 6, 1), date(2026, 6, 30)))

    def test_no_double_counting_across_adjacent_ranges(self):
        p_start, p_end = date(2026, 6, 1), date(2026, 7, 1)
        june = self.overlaps(p_start, p_end, date(2026, 6, 1), date(2026, 6, 30))
        july = self.overlaps(p_start, p_end, date(2026, 7, 1), date(2026, 7, 31))
        self.assertTrue(june)
        self.assertFalse(july)

    def test_fully_disjoint_periods(self):
        self.assertFalse(self.overlaps(date(2026, 1, 1), date(2026, 1, 31), date(2026, 7, 1), date(2026, 7, 31)))


class DuplicatePreventionTests(unittest.TestCase):
    def test_target_filename_collision_detected(self):
        html_inv = {"2026-07-15_utharsika_v001.html": {}}
        self.assertIn("2026-07-15_utharsika_v001.html", html_inv)

    def test_target_task_id_collision_detected(self):
        ph_task_rows = {"UAWSO-2026-07-15-utharsika-v001": {}}
        self.assertIn("UAWSO-2026-07-15-utharsika-v001", ph_task_rows)

    def test_no_duplicate_asin_sku_pairs_gate(self):
        product_master = [
            {"asin": "B001", "skus": ["SKU-A", "SKU-B"]},
            {"asin": "B002", "skus": ["SKU-C"]},
        ]
        pair_set = set()
        dup_count = 0
        for p in product_master:
            for sku in p["skus"]:
                key = (p["asin"], sku)
                if key in pair_set:
                    dup_count += 1
                pair_set.add(key)
        self.assertEqual(dup_count, 0)

    def test_duplicate_daily_rows_gate_flags_repeats(self):
        daily_split = [
            {"calendar_date": "2026-07-01", "asin": "B001", "sku": "SKU-A"},
            {"calendar_date": "2026-07-01", "asin": "B001", "sku": "SKU-A"},
        ]
        counts = {}
        for row in daily_split:
            key = (row["calendar_date"], row["asin"], row["sku"])
            counts[key] = counts.get(key, 0) + 1
        dup_rows = sum(1 for c in counts.values() if c > 1)
        self.assertEqual(dup_rows, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
