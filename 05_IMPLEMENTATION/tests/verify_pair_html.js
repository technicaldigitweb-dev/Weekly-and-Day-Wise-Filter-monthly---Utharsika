/*
Verifies the exact ASIN B0FX2QT3B1 / SKU LSCYRO300GD2PK+RPR44WH2PK
using the HTML's own embedded data and engine code, for June 2025 and
June 2026.
*/
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

var TARGET_ASIN = "B0FX2QT3B1";
var TARGET_SKU = "LSCYRO300GD2PK+RPR44WH2PK";

var pmEntry = productMasterFull.find(function(p){ return p.asin === TARGET_ASIN; });
console.log("Product master entry for", TARGET_ASIN, ":", JSON.stringify(pmEntry));

var splitIndex = Engine.buildDailyIndexSplit(dailySplit);
var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);
var targetCanonical = canonicalRows.filter(function(r){ return r.asin === TARGET_ASIN; });
console.log("Canonical rows for this ASIN:", JSON.stringify(targetCanonical));

function totalsFor(start, end) {
  var split = Engine.sumRangeSplitByAsinSku(splitIndex, start, end);
  var vend = Engine.sumVendorRange(vendorPeriods, start, end);
  var rows = Engine.computeRowsV3(canonicalRows, split, {}, vend, {});
  return rows.filter(function(r){ return r.asin === TARGET_ASIN; });
}

var june2025rows = totalsFor("2025-06-01", "2025-06-30");
var june2026rows = totalsFor("2026-06-01", "2026-06-30");

console.log("\n=== June 2025 rows for", TARGET_ASIN, "===");
console.log(JSON.stringify(june2025rows, null, 2));

console.log("\n=== June 2026 rows for", TARGET_ASIN, "===");
console.log(JSON.stringify(june2026rows, null, 2));

var june2026target = june2026rows.find(function(r){ return r.sku === TARGET_SKU; });
console.log("\nExact SKU row June2026:", JSON.stringify(june2026target));
