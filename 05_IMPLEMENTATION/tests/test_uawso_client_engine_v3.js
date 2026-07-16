/*
Real functional tests for the v3 (corrected ASIN+SKU grain) engine
functions, against the real extracted data.
Run: node tests/test_uawso_client_engine_v3.js
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
var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);

var results = [];
function check(label, cond, detail) {
  results.push({ label: label, pass: !!cond, detail: detail || "" });
  console.log("[" + (cond ? "PASS" : "FAIL") + "] " + label + (detail ? " -- " + detail : ""));
}

// ---------------------------------------------------------------------
// GRAIN CHECKS
// ---------------------------------------------------------------------
check("1723 distinct assigned ASINs represented", new Set(canonicalRows.map(function(r){return r.asin;})).size === 1723,
  "distinct asins=" + new Set(canonicalRows.map(function(r){return r.asin;})).size);

check("Total canonical row count = 2388 (1947 SKU + 113 no-SKU + 328 extra vendor)",
  canonicalRows.length === 2388, "got=" + canonicalRows.length);

var multiSkuValues = canonicalRows.filter(function(r){ return r.sku.indexOf(",") !== -1; });
check("No row contains a comma-joined SKU value", multiSkuValues.length === 0, "offenders=" + multiSkuValues.length);

var pairKeys = canonicalRows.map(function(r){ return r.asin + "|" + r.sku + "|" + r.rowType; });
check("No duplicated ASIN-SKU-rowType triple", new Set(pairKeys).size === pairKeys.length,
  "rows=" + pairKeys.length + " distinct=" + new Set(pairKeys).size);

var noSkuRows = canonicalRows.filter(function(r){ return r.mappingStatus === "NO_SKU_MAPPING"; });
check("Every no-SKU ASIN appears at least once (113 expected)", noSkuRows.length === 113, "got=" + noSkuRows.length);
check("Every no-SKU row has blank SKU", noSkuRows.every(function(r){ return r.sku === ""; }));

var vendorRows = canonicalRows.filter(function(r){ return r.isVendorRow; });
check("Vendor data appears in exactly 329 rows (one per vendor ASIN, never more)",
  vendorRows.length === 329, "got=" + vendorRows.length);
var vendorAsinCounts = {};
vendorRows.forEach(function(r){ vendorAsinCounts[r.asin] = (vendorAsinCounts[r.asin]||0) + 1; });
var multiVendorRowAsins = Object.keys(vendorAsinCounts).filter(function(a){ return vendorAsinCounts[a] > 1; });
check("No ASIN has more than one Vendor row", multiVendorRowAsins.length === 0, "offenders=" + JSON.stringify(multiVendorRowAsins));

var skuRows = canonicalRows.filter(function(r){ return r.rowType === "ASIN_SKU"; });
check("1947 ASIN_SKU rows, one SKU each, no ASIN-level totals repeated blindly", skuRows.length === 1947, "got=" + skuRows.length);

// ---------------------------------------------------------------------
// RECONCILIATION CHECKS (full embedded window)
// ---------------------------------------------------------------------
(function testFullWindowReconciliation() {
  var cur = Engine.sumRangeSplitByAsinSku(splitIndex, "2025-01-01", "2026-07-09");
  var vend = Engine.sumVendorRange(vendorPeriods, "2025-01-01", "2026-07-09");
  var rows = Engine.computeRowsV3(canonicalRows, cur, {}, vend, {});
  var total = Engine.computeTotalV3(rows);

  check("FBM Sales row-sum reconciles to source total (507631.04)", Math.abs(total.fbmSales - 507631.04) < 0.01, "got=" + total.fbmSales.toFixed(2));
  check("FBM Orders row-sum reconciles (25448)", total.fbmOrders === 25448, "got=" + total.fbmOrders);
  check("FBA Sales row-sum reconciles (170330.29)", Math.abs(total.fbaSales - 170330.29) < 0.01, "got=" + total.fbaSales.toFixed(2));
  check("FBA Orders row-sum reconciles (7886)", total.fbaOrders === 7886, "got=" + total.fbaOrders);
  check("Vendor Sales row-sum reconciles (46642.46) - NOT duplicated across SKU rows", Math.abs(total.vendorSales - 46642.46) < 0.02, "got=" + total.vendorSales.toFixed(2));
  check("Vendor Units row-sum reconciles (4738) - NOT duplicated across SKU rows", total.vendorUnits === 4738, "got=" + total.vendorUnits);
  check("CY Sales total = FBM+FBA+Vendor", Math.abs(total.currentYearSales - (total.fbmSales+total.fbaSales+total.vendorSales)) < 0.01);

  // Prove vendor is NOT duplicated: sum vendorSales only on SKU-specific
  // rows must be exactly zero (vendor should never attach to those).
  var vendorOnSkuRows = rows.filter(function(r){ return r.rowType === "ASIN_SKU"; })
    .reduce(function(a,r){ return a + r.vendorSales; }, 0);
  check("Zero Vendor Sales leaked onto ASIN_SKU rows", vendorOnSkuRows === 0, "leaked=" + vendorOnSkuRows);
})();

// ---------------------------------------------------------------------
// Multi-SKU ASIN produces separate rows, not comma-joined
// ---------------------------------------------------------------------
(function testMultiSkuAsinRows() {
  var multiSkuAsin = productMasterFull.find(function(p){ return p.skus.length > 1; });
  var itsRows = canonicalRows.filter(function(r){ return r.asin === multiSkuAsin.asin && r.rowType === "ASIN_SKU"; });
  check("Multi-SKU ASIN " + multiSkuAsin.asin + " produces " + multiSkuAsin.skus.length + " separate rows",
    itsRows.length === multiSkuAsin.skus.length, "got=" + itsRows.length);
  check("Each of those rows has exactly one SKU value (no comma)", itsRows.every(function(r){ return r.sku.indexOf(",") === -1 && multiSkuAsin.skus.indexOf(r.sku) !== -1; }));
})();

// ---------------------------------------------------------------------
// No-SKU-but-Vendor ASIN uses ONE row, not two
// ---------------------------------------------------------------------
(function testNoSkuVendorAsin() {
  var target = "B0DTKCSD1R"; // confirmed: no SKU mapping AND has vendor data
  var itsRows = canonicalRows.filter(function(r){ return r.asin === target; });
  check("ASIN " + target + " (no-SKU + Vendor) has exactly ONE row, not two", itsRows.length === 1, "got=" + itsRows.length);
  check("That row is flagged as both no-SKU-mapping and Vendor", itsRows[0].rowType === "NO_SKU_MAPPING_VENDOR");
})();

var passed = results.filter(function(r){ return r.pass; }).length;
console.log("\n" + passed + "/" + results.length + " checks passed");
if (passed !== results.length) {
  console.log("\nFAILED CHECKS:");
  results.filter(function(r){ return !r.pass; }).forEach(function(r){ console.log(" - " + r.label + " :: " + r.detail); });
  process.exit(1);
}
