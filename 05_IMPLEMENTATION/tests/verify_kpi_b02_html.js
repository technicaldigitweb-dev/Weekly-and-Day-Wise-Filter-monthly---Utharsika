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
var sandbox = { module: { exports: {} }, self: {} };
vm.createContext(sandbox);
vm.runInContext(scripts[0], sandbox);
var Engine = sandbox.module.exports;

var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);
var splitIndex = Engine.buildDailyIndexSplit(dailySplit);

var ROWS = [
  { asin: "B084RC5DQG", sku: "LASGSABL+LSFRYBS", mapped: "LSGD280AR+SCRN70YB" },
  { asin: "B0GY3G4S1F", sku: "LSGL7512CL3PK+RPM40WH3PK", mapped: "LSGL1275CL3PK+RPM40WH3PK" },
  { asin: "B0GY423LQJ", sku: "LSGL9015CL2PK+RPM40WH2PK", mapped: null },
  { asin: "B0H38YJTN8", sku: "LSGL9015GY2PK+RPM40WH2PK", mapped: null },
  { asin: "B0H393YSKV", sku: "LSGL9015GY3PK+RPM40WH3PK", mapped: null },
  { asin: "B0H3918NPV", sku: "LSGL9015GY5PK+RPM40WH5PK", mapped: null },
  { asin: "B0D9Q142ZZ", sku: "LSGLBC150CO2PK", mapped: "LSGLBG145AR+RPM40WH" },
];

function rowsForPeriod(start, end) {
  var curSplit = Engine.sumRangeSplitByAsinSkuV4(splitIndex, start, end);
  var curVendor = Engine.sumVendorRangeV4(vendorPeriods, start, end);
  return Engine.computeRowsV4(canonicalRows, curSplit, {}, curVendor, {});
}

var rows2025 = rowsForPeriod("2025-06-01", "2025-06-30");
var rows2026 = rowsForPeriod("2026-06-01", "2026-06-30");

function findRow(rows, asin, sku) {
  return rows.find(function (r) { return r.asin === asin && r.sku === sku; });
}

ROWS.forEach(function (ref) {
  console.log("\nASIN=" + ref.asin + " sku=" + ref.sku + " mapped=" + ref.mapped);
  var r25 = findRow(rows2025, ref.asin, ref.sku);
  var r26 = findRow(rows2026, ref.asin, ref.sku);
  console.log("  2025 exact-SKU HTML:", r25 ? ("sales=" + r25.totalSales.toFixed(2) + " orders=" + r25.totalOrders) : "ROW NOT FOUND IN PRODUCT MASTER");
  console.log("  2026 exact-SKU HTML:", r26 ? ("sales=" + r26.totalSales.toFixed(2) + " orders=" + r26.totalOrders) : "ROW NOT FOUND IN PRODUCT MASTER");
  if (ref.mapped) {
    var m25 = findRow(rows2025, ref.asin, ref.mapped);
    var m26 = findRow(rows2026, ref.asin, ref.mapped);
    console.log("  2025 mapped-SKU HTML:", m25 ? ("sales=" + m25.totalSales.toFixed(2) + " orders=" + m25.totalOrders) : "ROW NOT FOUND IN PRODUCT MASTER");
    console.log("  2026 mapped-SKU HTML:", m26 ? ("sales=" + m26.totalSales.toFixed(2) + " orders=" + m26.totalOrders) : "ROW NOT FOUND IN PRODUCT MASTER");
  }
  // ASIN-level total (all SKU rows for this asin)
  var asinRows25 = rows2025.filter(function (r) { return r.asin === ref.asin; });
  var asinRows26 = rows2026.filter(function (r) { return r.asin === ref.asin; });
  var asinSales25 = asinRows25.reduce(function (a, r) { return a + r.totalSales; }, 0);
  var asinOrders25 = asinRows25.reduce(function (a, r) { return a + r.totalOrders; }, 0);
  var asinSales26 = asinRows26.reduce(function (a, r) { return a + r.totalSales; }, 0);
  var asinOrders26 = asinRows26.reduce(function (a, r) { return a + r.totalOrders; }, 0);
  console.log("  2025 ASIN-level (all SKUs) HTML: sales=" + asinSales25.toFixed(2) + " orders=" + asinOrders25);
  console.log("  2026 ASIN-level (all SKUs) HTML: sales=" + asinSales26.toFixed(2) + " orders=" + asinOrders26);
});
