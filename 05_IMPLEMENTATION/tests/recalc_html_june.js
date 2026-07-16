/*
Recalculates June 2025 and June 2026 totals DIRECTLY from the current
09_OUTPUTS/2026-07-10_utharsika_v001.html file - extracting both the
embedded data AND the embedded engine code from the HTML itself (not
assuming the on-disk src/uawso_client_engine.js matches), so this is a
true "recalculate from the current file" check.
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
  if (!m) throw new Error("Could not find embedded JSON block: " + id);
  return JSON.parse(m[1]);
}

var productMasterFull = extractJson("uawso-product-master-full");
var dailySplit = extractJson("uawso-daily-aggregates-split");
var vendorPeriods = extractJson("uawso-vendor-periods");

// Extract the engine JS verbatim from inside the HTML (the FIRST <script> block after the JSON blocks, before the UI-wiring script)
var scripts = [];
var re = /<script>([\s\S]*?)<\/script>/g;
var m;
while ((m = re.exec(html)) !== null) scripts.push(m[1]);
if (scripts.length < 1) throw new Error("No inline <script> blocks found");
var engineSource = scripts[0];

var sandbox = { module: { exports: {} }, self: {} };
vm.createContext(sandbox);
vm.runInContext(engineSource, sandbox);
var Engine = sandbox.module.exports;
console.log("Engine loaded from HTML, functions available:", Object.keys(Engine).length);

var splitIndex = Engine.buildDailyIndexSplit(dailySplit);
var canonicalRows = Engine.buildCanonicalRows(productMasterFull, vendorPeriods);

function totalsFor(start, end) {
  var split = Engine.sumRangeSplitByAsinSku(splitIndex, start, end);
  var vend = Engine.sumVendorRange(vendorPeriods, start, end);
  var rows = Engine.computeRowsV3(canonicalRows, split, {}, vend, {});
  var t = Engine.computeTotalV3(rows);
  return t;
}

var june2025 = totalsFor("2025-06-01", "2025-06-30");
var june2026 = totalsFor("2026-06-01", "2026-06-30");

console.log("\n=== HTML-recalculated June 2025 ===");
console.log("FBM Sales:", june2025.fbmSales.toFixed(2), "FBM Orders:", june2025.fbmOrders);
console.log("FBA Sales:", june2025.fbaSales.toFixed(2), "FBA Orders:", june2025.fbaOrders);
console.log("Vendor Sales:", june2025.vendorSales.toFixed(2), "Vendor Units:", june2025.vendorUnits);
console.log("Total Sales:", (june2025.fbmSales+june2025.fbaSales+june2025.vendorSales).toFixed(2));

console.log("\n=== HTML-recalculated June 2026 ===");
console.log("FBM Sales:", june2026.fbmSales.toFixed(2), "FBM Orders:", june2026.fbmOrders);
console.log("FBA Sales:", june2026.fbaSales.toFixed(2), "FBA Orders:", june2026.fbaOrders);
console.log("Vendor Sales:", june2026.vendorSales.toFixed(2), "Vendor Units:", june2026.vendorUnits);
console.log("Total Sales:", (june2026.fbmSales+june2026.fbaSales+june2026.vendorSales).toFixed(2));

// Confirm the HTML's own default view / filter mode by inspecting the UI script
var uiScript = scripts[scripts.length - 1];
console.log("\nDefault comparison mode in HTML (search for 'value=\"MTD\" selected'):", html.indexOf('value="MTD" selected') !== -1);
console.log("Pagination computed before totals? (Total row uses 'total' object, not paginated rows):", uiScript.indexOf("computeTotalV3(rows)") !== -1 && uiScript.indexOf("renderTable(rows, total)") !== -1);
