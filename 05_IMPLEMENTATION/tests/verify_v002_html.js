"use strict";
var fs = require("fs");
var path = require("path");
var vm = require("vm");

var HTML_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v002.html");
var html = fs.readFileSync(HTML_PATH, "utf-8");

function extractJson(id) {
  var re = new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>');
  var m = html.match(re);
  return JSON.parse(m[1]);
}

var productMasterFull = extractJson("uawso-product-master-full");
var dailySplit = extractJson("uawso-daily-aggregates-split");
var vendorPeriods = extractJson("uawso-vendor-periods");

var scripts = [];
var re = /<script>([\s\S]*?)<\/script>/g;
var m;
while ((m = re.exec(html)) !== null) scripts.push(m[1]);
var engineSource = scripts[0];
var sandbox = { module: { exports: {} }, self: {} };
vm.createContext(sandbox);
vm.runInContext(engineSource, sandbox);
var Engine = sandbox.module.exports;

// ---- Grain checks -------------------------------------------------
var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);
console.log("Total canonical rows:", canonicalRows.length);
console.log("Assigned ASIN count (product master):", productMasterFull.length);

var pairSet = {};
var dupPairs = 0, multiSkuRows = 0;
canonicalRows.forEach(function (r) {
  var key = r.asin + "|" + r.sku;
  if (pairSet[key]) dupPairs++;
  pairSet[key] = true;
  if (r.sku && r.sku.indexOf(",") !== -1) multiSkuRows++;
});
console.log("Duplicate ASIN-SKU pairs:", dupPairs);
console.log("Rows containing multiple SKUs (comma):", multiSkuRows);

var vendorRowCount = canonicalRows.filter(function (r) { return r.isVendorRow; }).length;
console.log("Vendor rows:", vendorRowCount);

// ---- Exact ASIN validation -----------------------------------------
var splitIndex = Engine.buildDailyIndexSplit(dailySplit);

function totalsForAsin(asin, start, end) {
  var curSplit = Engine.sumRangeSplitByAsinSkuV4(splitIndex, start, end);
  var curVendor = Engine.sumVendorRange(vendorPeriods, start, end);
  var rows = Engine.computeRowsV4(canonicalRows, curSplit, {}, curVendor, {});
  return rows.filter(function (r) { return r.asin === asin; });
}

var TARGET_ASIN = "B0FX2QT3B1";
var june2025 = totalsForAsin(TARGET_ASIN, "2025-06-01", "2025-06-30");
var june2026 = totalsForAsin(TARGET_ASIN, "2026-06-01", "2026-06-30");

console.log("\n=== " + TARGET_ASIN + " June 2025 rows ===");
console.log(JSON.stringify(june2025, null, 2));
console.log("\n=== " + TARGET_ASIN + " June 2026 rows ===");
console.log(JSON.stringify(june2026, null, 2));

function sumRows(rows, field) { return rows.reduce(function (a, r) { return a + r[field]; }, 0); }
console.log("\nJune 2025 ASIN totals: Sales=" + sumRows(june2025, "totalSales").toFixed(2) + " Orders=" + sumRows(june2025, "totalOrders") + " Quantity=" + sumRows(june2025, "totalQuantity"));
console.log("June 2026 ASIN totals: Sales=" + sumRows(june2026, "totalSales").toFixed(2) + " Orders=" + sumRows(june2026, "totalOrders") + " Quantity=" + sumRows(june2026, "totalQuantity"));

// ---- Full-scope June 2025 / June 2026 (all 1723 ASINs) --------------
function fullScopeTotals(start, end) {
  var curSplit = Engine.sumRangeSplitByAsinSkuV4(splitIndex, start, end);
  var curVendor = Engine.sumVendorRange(vendorPeriods, start, end);
  var rows = Engine.computeRowsV4(canonicalRows, curSplit, {}, curVendor, {});
  var t = Engine.computeTotalV4(rows);
  return t;
}

var full2025 = fullScopeTotals("2025-06-01", "2025-06-30");
var full2026 = fullScopeTotals("2026-06-01", "2026-06-30");

console.log("\n=== FULL SCOPE June 2025 (v4 rules, all 1723 ASINs) ===");
console.log(JSON.stringify(full2025, null, 2));
console.log("\n=== FULL SCOPE June 2026 (v4 rules, all 1723 ASINs) ===");
console.log(JSON.stringify(full2026, null, 2));
