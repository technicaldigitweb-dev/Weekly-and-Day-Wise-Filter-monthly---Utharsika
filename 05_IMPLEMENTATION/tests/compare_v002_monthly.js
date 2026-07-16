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

var months = [
  ["2025-01","2025-01-01","2025-01-31"], ["2025-02","2025-02-01","2025-02-28"], ["2025-03","2025-03-01","2025-03-31"],
  ["2025-04","2025-04-01","2025-04-30"], ["2025-05","2025-05-01","2025-05-31"], ["2025-06","2025-06-01","2025-06-30"],
  ["2025-07","2025-07-01","2025-07-31"], ["2025-08","2025-08-01","2025-08-31"], ["2025-09","2025-09-01","2025-09-30"],
  ["2025-10","2025-10-01","2025-10-31"], ["2025-11","2025-11-01","2025-11-30"], ["2025-12","2025-12-01","2025-12-31"],
  ["2026-01","2026-01-01","2026-01-31"], ["2026-02","2026-02-01","2026-02-28"], ["2026-03","2026-03-01","2026-03-31"],
  ["2026-04","2026-04-01","2026-04-30"], ["2026-05","2026-05-01","2026-05-31"], ["2026-06","2026-06-01","2026-06-30"],
  ["2026-07","2026-07-01","2026-07-09"] // v002's current embedded history ends 2026-07-09
];

var out = [];
months.forEach(function (mm) {
  var label = mm[0], start = mm[1], end = mm[2];
  var curSplit = Engine.sumRangeSplitByAsinSkuV4(splitIndex, start, end);
  var curVendor = Engine.sumVendorRange(vendorPeriods, start, end);
  var rows = Engine.computeRowsV4(canonicalRows, curSplit, {}, curVendor, {});
  var t = Engine.computeTotalV4(rows);
  out.push({
    month: label, htmlAmazonSales: (t.fbmSales + t.fbaSales), htmlVendorSales: t.vendorSales,
    htmlTotalSales: t.totalSales, htmlTotalOrders: t.totalOrders, htmlTotalQuantity: t.totalQuantity,
  });
});

console.log(JSON.stringify(out, null, 2));
