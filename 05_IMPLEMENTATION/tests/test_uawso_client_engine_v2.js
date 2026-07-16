/*
Real functional tests for the v2 (FBM/FBA/Vendor, full-ASIN-coverage)
engine functions, against the real extracted data.
Run: node tests/test_uawso_client_engine_v2.js
*/
"use strict";
var fs = require("fs");
var path = require("path");
var Engine = require("../src/uawso_client_engine.js");

var DATA_DIR = path.join(__dirname, "..", "..", "07_EVIDENCE", "generated_data");
var IDENTITY = "2026-07-10_utharsika_v001";

var productMasterFull = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_product_master_full.json"), "utf-8"));
var dailySplit = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_daily_aggregates_split.json"), "utf-8"));
var vendorPeriods = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_vendor_periods.json"), "utf-8"));
var assignedAsins = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_assigned_asins.json"), "utf-8"));

var splitIndex = Engine.buildDailyIndexSplit(dailySplit);

var results = [];
function check(label, cond, detail) {
  results.push({ label: label, pass: !!cond, detail: detail || "" });
  console.log("[" + (cond ? "PASS" : "FAIL") + "] " + label + (detail ? " -- " + detail : ""));
}

// 1. Full ASIN coverage
check("Product master full covers all 1723 assigned ASINs", productMasterFull.length === 1723, "count=" + productMasterFull.length);
var withSku = productMasterFull.filter(function(p){ return p.skus.length > 0; }).length;
var withoutSku = productMasterFull.filter(function(p){ return p.skus.length === 0; }).length;
check("1610 ASINs have at least one SKU", withSku === 1610, "got=" + withSku);
check("113 ASINs have zero SKUs (still present in master)", withoutSku === 113, "got=" + withoutSku);

// 2. FBM/FBA/Vendor totals over the FULL embedded window - cross-check
// against the exact values independently computed in
// 07_EVIDENCE/2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md and
// 07_EVIDENCE/2026-07-10_utharsika_VENDOR_SALES_VALIDATION.md
(function testFullWindowTotals() {
  var cur = Engine.sumRangeSplitByAsin(splitIndex, "2025-01-01", "2026-07-09");
  var vend = Engine.sumVendorRange(vendorPeriods, "2025-01-01", "2026-07-09");
  var rows = Engine.computeRowsV2(productMasterFull, cur, {}, vend, {});
  var total = Engine.computeTotalV2(rows);

  check("FBM sales matches prior validation (507631.04)", Math.abs(total.fbmSales - 507631.04) < 0.01, "got=" + total.fbmSales.toFixed(2));
  check("FBM orders matches prior validation (25448)", total.fbmOrders === 25448, "got=" + total.fbmOrders);
  check("FBA sales matches prior validation (170330.29)", Math.abs(total.fbaSales - 170330.29) < 0.01, "got=" + total.fbaSales.toFixed(2));
  check("FBA orders matches prior validation (7886)", total.fbaOrders === 7886, "got=" + total.fbaOrders);
  check("Vendor sales matches prior validation (46642.46)", Math.abs(total.vendorSales - 46642.46) < 0.02, "got=" + total.vendorSales.toFixed(2));
  check("Vendor units matches prior validation (4738)", total.vendorUnits === 4738, "got=" + total.vendorUnits);
  check("Total sales = FBM+FBA+Vendor = 724603.79", Math.abs(total.totalSales - (507631.04+170330.29+46642.46)) < 0.05, "got=" + total.totalSales.toFixed(2));
})();

// 3. Row count is always exactly 1723 (never hides a zero-activity or
//    no-SKU ASIN)
(function testRowCountAlways1723() {
  var cur = Engine.sumRangeSplitByAsin(splitIndex, "2026-07-01", "2026-07-09");
  var prev = Engine.sumRangeSplitByAsin(splitIndex, "2025-07-01", "2025-07-09");
  var curV = Engine.sumVendorRange(vendorPeriods, "2026-07-01", "2026-07-09");
  var prevV = Engine.sumVendorRange(vendorPeriods, "2025-07-01", "2025-07-09");
  var rows = Engine.computeRowsV2(productMasterFull, cur, prev, curV, prevV);
  check("MTD default view always has exactly 1723 rows", rows.length === 1723, "got=" + rows.length);

  var noSkuRows = rows.filter(function(r){ return !r.hasSku; });
  check("No-SKU rows are present and flagged hasSku=false", noSkuRows.length === 113, "got=" + noSkuRows.length);
  check("No-SKU rows still have valid zero/actual totals, not omitted", noSkuRows.every(function(r){ return typeof r.totalSales === "number"; }));
})();

// 4. Vendor overlap allocation correctness (period vs daily granularity)
(function testVendorOverlap() {
  // Pick a known monthly-bucketed vendor period and confirm it's included
  // when the query range overlaps it, and excluded when it doesn't.
  var monthly = vendorPeriods.find(function(v){
    var d1 = new Date(v.start_date), d2 = new Date(v.end_date);
    return (d2 - d1) / (1000*3600*24) > 20; // >20 days = a monthly-ish bucket
  });
  check("A monthly-granularity vendor period exists in the real data (confirms mixed granularity)", !!monthly, monthly ? JSON.stringify(monthly) : "none found");
  if (monthly) {
    var overlapping = Engine.periodsOverlap(monthly.start_date, monthly.end_date, monthly.start_date, monthly.end_date);
    check("Vendor period overlaps itself (sanity)", overlapping === true);
    var before = Engine.periodsOverlap(monthly.start_date, monthly.end_date, "1900-01-01", "1900-01-02");
    check("Vendor period does not overlap an unrelated date range", before === false);
  }
})();

// 5. Trend/Achieve% rules still apply correctly on the combined total
(function testTrendOnTotal() {
  var fakeMaster = [{ asin: "TESTASIN", skus: ["TESTSKU"] }];
  var curSplit = { TESTASIN: { fbmSales: 100, fbmOrders: 2, fbaSales: 50, fbaOrders: 1 } };
  var prevSplit = { TESTASIN: { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 } };
  var curVendor = { TESTASIN: { vendorSales: 20, vendorUnits: 3 } };
  var prevVendor = {};
  var rows = Engine.computeRowsV2(fakeMaster, curSplit, prevSplit, curVendor, prevVendor);
  check("Total sales combines FBM+FBA+Vendor (100+50+20=170)", rows[0].totalSales === 170, "got=" + rows[0].totalSales);
  check("Trend UP when previous total is zero and current > 0", rows[0].trend === "UP");
  check("Achieve% undefined when previous total is zero", rows[0].achieveSalesPct === null);
})();

var passed = results.filter(function(r){ return r.pass; }).length;
console.log("\n" + passed + "/" + results.length + " checks passed");
if (passed !== results.length) {
  console.log("\nFAILED CHECKS:");
  results.filter(function(r){ return !r.pass; }).forEach(function(r){ console.log(" - " + r.label + " :: " + r.detail); });
  process.exit(1);
}
