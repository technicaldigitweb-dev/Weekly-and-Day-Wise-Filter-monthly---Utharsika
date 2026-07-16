/*
Data-layer tests for the fresh 2026-07-16_utharsika_v001 report
(AMAZON-only Orders business-rule update).
Run: node tests/test_uawso_2026_07_16_amazon_only_orders_v001.js [path_to_html]
*/
"use strict";
var fs = require("fs");
var path = require("path");
var Engine = require("../src/uawso_client_engine.js");

var ROOT = path.join(__dirname, "..", "..");
var TARGET = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(ROOT, "09_OUTPUTS", "2026-07-16_utharsika_v001.html");

var results = [];
function check(label, cond, detail) {
  results.push({ label: label, pass: !!cond, detail: detail || "" });
  console.log("[" + (cond ? "PASS" : "FAIL") + "] " + label + (detail ? " -- " + detail : ""));
}

var html = fs.readFileSync(TARGET, "utf-8");
function extract(id) {
  var marker = 'id="' + id + '">';
  var start = html.indexOf(marker) + marker.length;
  var end = html.indexOf("</script>", start);
  return JSON.parse(html.slice(start, end));
}
var pm = extract("uawso-product-master-asin-level");
var da = extract("uawso-daily-aggregates-asin");
var vp = extract("uawso-vendor-periods");
var extractScriptSource = fs.readFileSync(path.join(__dirname, "..", "src", "extract_uawso_v5_asin_level.py"), "utf-8");
var templateSource = fs.readFileSync(path.join(__dirname, "..", "templates", "uawso_report_template_v5_asin_level.html"), "utf-8");

// ---------------------------------------------------------------------
// 1/2. AMAZON Orders included, REPLACEMENT Orders excluded - structural
// proof: the extraction script's Orders query WHERE clause is exactly
// source_name='AMAZON', not IN ('AMAZON','REPLACEMENT').
// ---------------------------------------------------------------------
var ordersQueryMatch = extractScriptSource.match(/FROM public\.order_transaction ot[\s\S]*?GROUP BY ot\.order_date::date, ot\.asin/);
var ordersQueryText = ordersQueryMatch ? ordersQueryMatch[0] : "";
check("0. Orders query block located in extract_uawso_v5_asin_level.py", ordersQueryText.length > 0, "found=" + (ordersQueryText.length > 0));
check("1. Orders query scopes source_name to 'AMAZON' only", /source_name = 'AMAZON'/.test(ordersQueryText) && !/source_name = 'AMAZON'\s*,/.test(ordersQueryText));
check("2. Orders query does NOT use source_name IN ('AMAZON', 'REPLACEMENT')", !/source_name IN \('AMAZON',\s*'REPLACEMENT'\)/.test(ordersQueryText), "query=" + ordersQueryText.replace(/\s+/g, " ").slice(0, 300));

// ---------------------------------------------------------------------
// 3/4. Cancelled/Canceled excluded - the shared STATUS_FILTER_SQL fragment
// (reused by the same query) is unchanged.
// ---------------------------------------------------------------------
check("3/4. Status filter excludes Cancelled and Canceled (unchanged)",
  /NOT IN \('Cancelled', 'Canceled'\)/.test(extractScriptSource));

// ---------------------------------------------------------------------
// 5. B0FX2XDLT5 June 2026 Amazon Orders = 16 (14 FBM + 2 FBA), reproduced
// directly from this report's own embedded data.
// ---------------------------------------------------------------------
var junRows = da.filter(function (r) { return r.asin === "B0FX2XDLT5" && r.calendar_date >= "2026-06-01" && r.calendar_date < "2026-07-01"; });
var junFbm = 0, junFba = 0;
junRows.forEach(function (r) { junFbm += r.fbm_orders; junFba += r.fba_orders; });
check("5. B0FX2XDLT5 June 2026 Amazon Orders = 16 (14 FBM + 2 FBA)",
  junFbm === 14 && junFba === 2 && (junFbm + junFba) === 16,
  "fbm=" + junFbm + " fba=" + junFba + " total=" + (junFbm + junFba));

// ---------------------------------------------------------------------
// 6/7. FBM/FBA Orders correct - structural: computed via sumRangeByAsinV5
// pass-through of the embedded (already AMAZON-only) daily aggregates.
// ---------------------------------------------------------------------
var idx = Engine.buildDailyIndexSplit(da);
var canon = Engine.buildCanonicalRowsV5(pm);
var cs = Engine.sumRangeByAsinV5(idx, "2025-01-01", "2026-07-15");
var cv = Engine.sumVendorRangeV4(vp, "2025-01-01", "2026-07-15");
var rows = Engine.computeRowsV5(canon, cs, {}, cv, {});
var total = Engine.computeTotalV5(rows);
check("6. FBM Orders total is a positive integer, computed from embedded data", Number.isInteger(total.fbmOrders) && total.fbmOrders > 0, "got=" + total.fbmOrders);
check("7. FBA Orders total is a positive integer, computed from embedded data", Number.isInteger(total.fbaOrders) && total.fbaOrders > 0, "got=" + total.fbaOrders);

// ---------------------------------------------------------------------
// 8/9. Vendor Orders equal ordered_units; Total Orders include Vendor Orders
// ---------------------------------------------------------------------
var vendorUnitsDirect = 0;
Object.keys(cv).forEach(function (a) { vendorUnitsDirect += cv[a].vendorUnits; });
check("8. Vendor Orders equal direct ordered_units sum", total.vendorOrders === vendorUnitsDirect, "engine=" + total.vendorOrders + " direct=" + vendorUnitsDirect);
check("9. Total Orders = FBM Orders + FBA Orders + Vendor Orders",
  total.fbmOrders + total.fbaOrders + total.vendorOrders === total.currentYearOrders,
  "fbm=" + total.fbmOrders + " fba=" + total.fbaOrders + " vendor=" + total.vendorOrders + " total=" + total.currentYearOrders);

// ---------------------------------------------------------------------
// 10-13. Quantity absent from KPI/table/CSV/definitions (structural)
// ---------------------------------------------------------------------
check("10. No Quantity KPI card in template", !/Previous-Year Total Quantity|Current-Year Total Quantity|Quantity Change %.*fmtPct\(total\.quantityChange\)/.test(templateSource));
check("11. No Quantity table header/column in template", !/data-field="(fbmQuantity|fbaQuantity|vendorUnits|totalQuantity|previousYearQuantity|currentYearQuantity|quantityChange)"/.test(templateSource));
check("12. No Quantity CSV header field", !/headers = \[[^\]]*Quantity/.test(templateSource));
check("13. No Quantity entry in Column Definitions", !/<strong>(FBM|FBA|Total|PY|CY) Quantity<\/strong>|<strong>Quantity Change %<\/strong>/.test(templateSource));
check("13b. No Quantity field on computed rows/total", total.totalQuantity === undefined && rows.every(function (r) { return r.fbmQuantity === undefined; }));

// ---------------------------------------------------------------------
// 14. Sales logic unchanged - still source_name='AMAZON' inside the Sales CASE
// ---------------------------------------------------------------------
check("14. Sales CASE still restricted to source_name='AMAZON' (unchanged by this task)",
  (extractScriptSource.match(/source_name = 'AMAZON'/g) || []).length >= 2, "occurrences=" + (extractScriptSource.match(/source_name = 'AMAZON'/g) || []).length);

// ---------------------------------------------------------------------
// 15. One row per ASIN
// ---------------------------------------------------------------------
check("15. One canonical row per ASIN, no duplicates", rows.length === pm.length && new Set(rows.map(function (r) { return r.asin; })).size === rows.length, "rows=" + rows.length);

// ---------------------------------------------------------------------
// 20. Historical requirement and output files unchanged (hash check)
// ---------------------------------------------------------------------
var crypto = require("crypto");
function sha256(buf) { return crypto.createHash("sha256").update(buf).digest("hex"); }
var reqPath = path.join(ROOT, "01_REQUIREMENTS", "Requirement", "2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md");
var reqHash = sha256(fs.readFileSync(reqPath));
check("20a. Original requirement file hash matches the recorded protected baseline",
  reqHash === "f652d51fb6c77e3b1512a8078c86afe6e1726a86f7c43f5ca58259d2dfb14ea5", "got=" + reqHash);
var v004Path = path.join(ROOT, "09_OUTPUTS", "2026-07-15_utharsika_v004.html");
var v004Hash = sha256(fs.readFileSync(v004Path));
check("20b. 2026-07-15_utharsika_v004.html hash matches the recorded protected baseline",
  v004Hash === "d8ab5b255619bf188acfa7044679e7c60bff0cef4d8d52717483e49ef1f4999d", "got=" + v004Hash);

var OTHER_PROTECTED_HASHES = {
  "2026-07-09_utharsika_v001.html": "52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b",
  "2026-07-10_utharsika_v001.html": "335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4",
  "2026-07-10_utharsika_v002.html": "0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72",
  "2026-07-14_utharsika_v002.html": "16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684",
};
Object.keys(OTHER_PROTECTED_HASHES).forEach(function (name) {
  var p = path.join(ROOT, "09_OUTPUTS", name);
  var h = sha256(fs.readFileSync(p));
  check("20c. " + name + " unchanged", h === OTHER_PROTECTED_HASHES[name], "got=" + h);
});

// ---------------------------------------------------------------------
console.log("\nTotals for this report: FBM Orders=" + total.fbmOrders + " FBA Orders=" + total.fbaOrders +
  " Vendor Orders=" + total.vendorOrders + " Total Orders=" + total.currentYearOrders +
  " Total Sales=" + total.currentYearSales.toFixed(2) + " ASIN rows=" + rows.length);

var failed = results.filter(function (r) { return !r.pass; });
console.log("\n" + (results.length - failed.length) + "/" + results.length + " checks passed.");
if (failed.length) {
  console.log("FAILED: " + failed.map(function (r) { return r.label; }).join("; "));
  process.exit(1);
}
console.log("ALL PASS");
