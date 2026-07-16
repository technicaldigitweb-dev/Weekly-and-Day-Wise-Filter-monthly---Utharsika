"use strict";
var fs = require("fs");
var path = require("path");
var vm = require("vm");

var HTML_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-14_utharsika_v002.html");
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
var sandbox = { module: { exports: {} }, self: {} };
vm.createContext(sandbox);
vm.runInContext(scripts[0], sandbox);
var Engine = sandbox.module.exports;

var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);
var splitIndex = Engine.buildDailyIndexSplit(dailySplit);

function totalsFor(start, end) {
  var curSplit = Engine.sumRangeSplitByAsinSkuV4(splitIndex, start, end);
  var curVendor = Engine.sumVendorRangeV4(vendorPeriods, start, end);
  var rows = Engine.computeRowsV4(canonicalRows, curSplit, {}, curVendor, {});
  return Engine.computeTotalV4(rows);
}

var months = [
  ["2025-01","2025-01-01","2025-01-31"], ["2025-02","2025-02-01","2025-02-28"], ["2025-03","2025-03-01","2025-03-31"],
  ["2025-04","2025-04-01","2025-04-30"], ["2025-05","2025-05-01","2025-05-31"], ["2025-06","2025-06-01","2025-06-30"],
  ["2025-07","2025-07-01","2025-07-31"], ["2025-08","2025-08-01","2025-08-31"], ["2025-09","2025-09-01","2025-09-30"],
  ["2025-10","2025-10-01","2025-10-31"], ["2025-11","2025-11-01","2025-11-30"], ["2025-12","2025-12-01","2025-12-31"],
  ["2026-01","2026-01-01","2026-01-31"], ["2026-02","2026-02-01","2026-02-28"], ["2026-03","2026-03-01","2026-03-31"],
  ["2026-04","2026-04-01","2026-04-30"], ["2026-05","2026-05-01","2026-05-31"], ["2026-06","2026-06-01","2026-06-30"],
  ["2026-07","2026-07-01","2026-07-13"]
];

var out = [];
months.forEach(function (mm) {
  var t = totalsFor(mm[1], mm[2]);
  out.push({
    month: mm[0],
    htmlAmazonSales: Number((t.fbmSales + t.fbaSales).toFixed(2)),
    htmlVendorSales: Number(t.vendorSales.toFixed(2)),
    htmlTotalSales: Number(t.totalSales.toFixed(2)),
    htmlTotalOrders: t.totalOrders,
    htmlTotalQuantity: t.totalQuantity,
  });
});
console.log(JSON.stringify(out, null, 2));

// Full-period total
var fullTotal = totalsFor("2025-01-01", "2026-07-13");
console.log("\n=== FULL PERIOD TOTAL ===");
console.log(JSON.stringify(fullTotal, null, 2));

// Exact ASIN regression
var TARGET_ASIN = "B0FX2QT3B1";
var june2026rows = (function () {
  var curSplit = Engine.sumRangeSplitByAsinSkuV4(splitIndex, "2026-06-01", "2026-06-30");
  var curVendor = Engine.sumVendorRangeV4(vendorPeriods, "2026-06-01", "2026-06-30");
  return Engine.computeRowsV4(canonicalRows, curSplit, {}, curVendor, {}).filter(function (r) { return r.asin === TARGET_ASIN; });
})();
console.log("\n=== B0FX2QT3B1 June 2026 rows (new 7-status rule) ===");
console.log(JSON.stringify(june2026rows, null, 2));
var asinSales = june2026rows.reduce(function (a, r) { return a + r.totalSales; }, 0);
var asinOrders = june2026rows.reduce(function (a, r) { return a + r.totalOrders; }, 0);
var asinQty = june2026rows.reduce(function (a, r) { return a + r.totalQuantity; }, 0);
console.log("ASIN totals: Sales=" + asinSales.toFixed(2) + " Orders=" + asinOrders + " Quantity=" + asinQty);

// Grain checks
var pairSet = {}, dupPairs = 0, multiSku = 0;
canonicalRows.forEach(function (r) {
  var key = r.asin + "|" + r.sku;
  if (pairSet[key]) dupPairs++;
  pairSet[key] = true;
  if (r.sku && r.sku.indexOf(",") !== -1) multiSku++;
});
console.log("\nTotal canonical rows:", canonicalRows.length, "Duplicate ASIN-SKU pairs:", dupPairs, "Multi-SKU rows:", multiSku);
