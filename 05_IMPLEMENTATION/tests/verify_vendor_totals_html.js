"use strict";
var fs = require("fs");
var path = require("path");
var vm = require("vm");

var HTML_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v001.html");
var html = fs.readFileSync(HTML_PATH, "utf-8");

function extractJson(id) {
  var re = new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>');
  var m = html.match(re);
  return JSON.parse(m[1]);
}

var vendorPeriods = extractJson("uawso-vendor-periods");
var productMasterFull = extractJson("uawso-product-master-full");

var scripts = [];
var re = /<script>([\s\S]*?)<\/script>/g;
var m;
while ((m = re.exec(html)) !== null) scripts.push(m[1]);
var engineSource = scripts[0];
var sandbox = { module: { exports: {} }, self: {} };
vm.createContext(sandbox);
vm.runInContext(engineSource, sandbox);
var Engine = sandbox.module.exports;

console.log("Total vendor period rows embedded:", vendorPeriods.length);
console.log("Total assigned ASINs embedded (product master):", productMasterFull.length);

var assignedAsinSet = {};
productMasterFull.forEach(function (p) { assignedAsinSet[p.asin] = true; });

var vendorAsinsNotAssigned = vendorPeriods.filter(function (v) { return !assignedAsinSet[v.asin]; });
console.log("Vendor period rows whose ASIN is NOT in assigned product master:", vendorAsinsNotAssigned.length);

function report(label, start, end) {
  var map = Engine.sumVendorRange(vendorPeriods, start, end);
  var asins = Object.keys(map);
  var totalSales = 0, totalUnits = 0;
  asins.forEach(function (a) {
    totalSales += map[a].vendorSales;
    totalUnits += map[a].vendorUnits;
  });
  console.log("\n=== " + label + " (" + start + " to " + end + ") ===");
  console.log("Distinct ASINs with Vendor activity:", asins.length);
  console.log("Total Vendor Sales:", totalSales.toFixed(2));
  console.log("Total Vendor Units:", totalUnits);

  // count how many raw period rows contributed (overlap count, not distinct ASIN)
  var contributingRows = vendorPeriods.filter(function (v) {
    return !(v.end_date < start || v.start_date > end);
  });
  console.log("Contributing raw period rows (overlap):", contributingRows.length);
  return { asins: asins.length, sales: totalSales, units: totalUnits, rows: contributingRows.length };
}

var j25 = report("June 2025", "2025-06-01", "2025-06-30");
var j26 = report("June 2026", "2026-06-01", "2026-06-30");

console.log("\nSample vendor period row:", JSON.stringify(vendorPeriods[0]));
