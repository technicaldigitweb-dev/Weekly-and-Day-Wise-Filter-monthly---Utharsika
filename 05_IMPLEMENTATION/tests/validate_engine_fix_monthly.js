"use strict";
var fs = require("fs");
var path = require("path");

var DATA_DIR = path.join(__dirname, "..", "..", "07_EVIDENCE", "generated_data");
var IDENTITY = "2026-07-10_utharsika_v002";

function load(name) {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_" + name + ".json"), "utf-8"));
}

var productMasterFull = load("product_master_full");
var dailySplit = load("daily_aggregates_split");
var vendorPeriods = load("vendor_periods");

var Engine = require(path.join(__dirname, "..", "src", "uawso_client_engine.js"));

var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);
var splitIndex = Engine.buildDailyIndexSplit(dailySplit);

var months = [
  ["2025-01","2025-01-01","2025-01-31"], ["2025-02","2025-02-01","2025-02-28"], ["2025-03","2025-03-01","2025-03-31"],
  ["2025-04","2025-04-01","2025-04-30"], ["2025-05","2025-05-01","2025-05-31"], ["2025-06","2025-06-01","2025-06-30"],
  ["2025-07","2025-07-01","2025-07-31"], ["2025-08","2025-08-01","2025-08-31"], ["2025-09","2025-09-01","2025-09-30"],
  ["2025-10","2025-10-01","2025-10-31"], ["2025-11","2025-11-01","2025-11-30"], ["2025-12","2025-12-01","2025-12-31"],
  ["2026-01","2026-01-01","2026-01-31"], ["2026-02","2026-02-01","2026-02-28"], ["2026-03","2026-03-01","2026-03-31"],
  ["2026-04","2026-04-01","2026-04-30"], ["2026-05","2026-05-01","2026-05-31"], ["2026-06","2026-06-01","2026-06-30"],
  ["2026-07","2026-07-01","2026-07-13"]
];

console.log("month       vendorSales(FIXED)   vendorUnits");
months.forEach(function (mm) {
  var label = mm[0], start = mm[1], end = mm[2];
  var v = Engine.sumVendorRangeV4(vendorPeriods, start, end);
  var totalSales = 0, totalUnits = 0;
  Object.keys(v).forEach(function (a) { totalSales += v[a].vendorSales; totalUnits += v[a].vendorUnits; });
  console.log(label.padEnd(10) + totalSales.toFixed(2).padStart(18) + String(totalUnits).padStart(14));
});
