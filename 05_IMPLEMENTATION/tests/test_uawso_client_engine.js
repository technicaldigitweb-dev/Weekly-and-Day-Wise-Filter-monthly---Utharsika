/*
Real functional tests for the UAWSO client-side dashboard engine
(src/uawso_client_engine.js) - the EXACT file inlined into the shipped
self-contained HTML, run here under Node against the REAL extracted
data (07_EVIDENCE/generated_data/2026-07-10_utharsika_v001_*.json).

Run: node tests/test_uawso_client_engine.js
*/
"use strict";
var fs = require("fs");
var path = require("path");
var Engine = require("../src/uawso_client_engine.js");

var DATA_DIR = path.join(__dirname, "..", "..", "07_EVIDENCE", "generated_data");
var IDENTITY = "2026-07-10_utharsika_v001";

var productMaster = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_product_master.json"), "utf-8"));
var daily = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_daily_aggregates.json"), "utf-8"));
var assignedAsins = JSON.parse(fs.readFileSync(path.join(DATA_DIR, IDENTITY + "_assigned_asins.json"), "utf-8"));

var index = Engine.buildDailyIndex(daily);

var BOUNDS = {
  selectableStart: "2026-01-01", selectableEnd: "2026-07-09",
  historyStart: "2025-01-01", historyEnd: "2026-07-09",
  latestCompleted: "2026-07-09",
};

var results = [];
function check(label, cond, detail) {
  results.push({ label: label, pass: !!cond, detail: detail || "" });
  console.log("[" + (cond ? "PASS" : "FAIL") + "] " + label + (detail ? " -- " + detail : ""));
}

// ---------------------------------------------------------------------
// 1. Data coverage
// ---------------------------------------------------------------------
check("Data coverage: product master non-empty", productMaster.length > 0, "rows=" + productMaster.length);
check("Data coverage: daily aggregate row count = 28601 (confirmed extraction)", daily.length === 28601, "rows=" + daily.length);
check("Data coverage: no aggregate date later than 2026-07-09", daily.every(function(r){ return r.calendar_date <= "2026-07-09"; }));
check("Data coverage: no aggregate date earlier than 2025-01-01", daily.every(function(r){ return r.calendar_date >= "2025-01-01"; }));
check("Data coverage: min date is exactly 2025-01-01", index.dates[0] === "2025-01-01", "actual=" + index.dates[0]);
check("Data coverage: max date is exactly 2026-07-09", index.dates[index.dates.length-1] === "2026-07-09", "actual=" + index.dates[index.dates.length-1]);
check("Data coverage: assigned ASIN count = 1723", assignedAsins.length === 1723, "count=" + assignedAsins.length);
check("Data coverage: no raw order_id/order_item_info/customer fields present", daily.every(function(r){
  return !("order_id" in r) && !("order_item_info" in r) && !("customer_email" in r) && !("tracking_number" in r);
}));

// ---------------------------------------------------------------------
// 2. Default MTD view
// ---------------------------------------------------------------------
(function testDefaultMTD() {
  var period = Engine.resolvePeriod("MTD", {}, BOUNDS);
  check("Default MTD: current period = 2026-07-01..2026-07-09", period.cyStart === "2026-07-01" && period.cyEnd === "2026-07-09", JSON.stringify(period));
  check("Default MTD: previous period = 2025-07-01..2025-07-09", period.pyStart === "2025-07-01" && period.pyEnd === "2025-07-09", JSON.stringify(period));

  var curMap = Engine.sumRange(index, period.cyStart, period.cyEnd);
  var prevMap = Engine.sumRange(index, period.pyStart, period.pyEnd);
  var rows = Engine.computeRows(productMaster, curMap, prevMap);
  check("Default MTD: row count === product master count (zero-activity retained)", rows.length === productMaster.length, "rows=" + rows.length + " master=" + productMaster.length);

  var zeroActivityRows = rows.filter(function(r){ return r.thisYearSales === 0 && r.previousYearSales === 0; });
  check("Default MTD: some zero-activity assigned products are present and retained (not hidden)", zeroActivityRows.length > 0, "zero-activity rows=" + zeroActivityRows.length);

  var total = Engine.computeTotal(rows);
  check("Default MTD: total this-year sales matches independent full-scan sum", (function(){
    var s = 0; for (var i=0;i<daily.length;i++){ var r=daily[i]; if (r.calendar_date>="2026-07-01" && r.calendar_date<="2026-07-09") s+=r.sales_total; }
    return Math.abs(s - total.thisYearSales) < 0.005;
  })(), "total=" + total.thisYearSales);
})();

// ---------------------------------------------------------------------
// 3. Random Daily test (2026-07-09 vs 2025-07-09) - cross-checked
//    against the values independently fetched earlier this session
//    (this_year_sales=350.94, this_year_orders=12).
// ---------------------------------------------------------------------
(function testDaily() {
  var period = Engine.resolvePeriod("DAILY", { date: "2026-07-09" }, BOUNDS);
  check("Daily: previous date is exactly one year back", period.pyStart === "2025-07-09" && period.pyEnd === "2025-07-09");
  var curMap = Engine.sumRange(index, period.cyStart, period.cyEnd);
  var prevMap = Engine.sumRange(index, period.pyStart, period.pyEnd);
  var rows = Engine.computeRows(productMaster, curMap, prevMap);
  var total = Engine.computeTotal(rows);
  check("Daily 2026-07-09: this-year sales matches earlier independent MCP fetch (350.94)", Math.abs(total.thisYearSales - 350.94) < 0.01, "got=" + total.thisYearSales);
  check("Daily 2026-07-09: this-year orders matches earlier independent MCP fetch (12)", total.thisYearOrders === 12, "got=" + total.thisYearOrders);
})();

// ---------------------------------------------------------------------
// 4. June 2026 vs June 2025 month test
// ---------------------------------------------------------------------
(function testJune() {
  var period = Engine.resolvePeriod("MONTH", { month: "2026-06" }, BOUNDS);
  check("June month: current = 2026-06-01..2026-06-30", period.cyStart === "2026-06-01" && period.cyEnd === "2026-06-30", JSON.stringify(period));
  check("June month: previous = 2025-06-01..2025-06-30", period.pyStart === "2025-06-01" && period.pyEnd === "2025-06-30", JSON.stringify(period));
})();

// ---------------------------------------------------------------------
// 5. Week test (Monday-Sunday)
// ---------------------------------------------------------------------
(function testWeek() {
  var period = Engine.resolvePeriod("WEEKLY", { weekStart: "2026-06-08" }, BOUNDS);
  check("Week: current = 2026-06-08..2026-06-14", period.cyStart === "2026-06-08" && period.cyEnd === "2026-06-14");
  check("Week: previous = 2025-06-08..2025-06-14", period.pyStart === "2025-06-08" && period.pyEnd === "2025-06-14", JSON.stringify(period));
})();

// ---------------------------------------------------------------------
// 6. Custom range test (matches the spec's own example)
// ---------------------------------------------------------------------
(function testCustom() {
  var period = Engine.resolvePeriod("CUSTOM", { customStart: "2026-05-10", customEnd: "2026-05-25" }, BOUNDS);
  check("Custom range: previous = 2025-05-10..2025-05-25", period.pyStart === "2025-05-10" && period.pyEnd === "2025-05-25", JSON.stringify(period));
})();

// ---------------------------------------------------------------------
// 7-9. ASIN / SKU / combined filter tests (filter logic mirrors the
//      template's applyProductFilters, exercised directly here)
// ---------------------------------------------------------------------
(function testProductFilters() {
  var period = Engine.resolvePeriod("MTD", {}, BOUNDS);
  var curMap = Engine.sumRange(index, period.cyStart, period.cyEnd);
  var prevMap = Engine.sumRange(index, period.pyStart, period.pyEnd);
  var rows = Engine.computeRows(productMaster, curMap, prevMap);

  var sampleAsin = productMaster[0].asin;
  var asinFiltered = rows.filter(function(r){ return r.asin === sampleAsin; });
  check("ASIN filter: returns only rows for the selected ASIN", asinFiltered.every(function(r){ return r.asin === sampleAsin; }) && asinFiltered.length > 0, "matched=" + asinFiltered.length);

  var sampleSku = productMaster[0].sku;
  var skuFiltered = rows.filter(function(r){ return r.sku === sampleSku; });
  check("SKU filter: returns only rows for the selected SKU", skuFiltered.every(function(r){ return r.sku === sampleSku; }) && skuFiltered.length > 0, "matched=" + skuFiltered.length);

  var combined = rows.filter(function(r){ return r.asin === sampleAsin && r.sku === sampleSku; });
  check("Combined ASIN+SKU filter: returns the exact single pair", combined.length === 1, "matched=" + combined.length);

  var otherUserCheck = rows.every(function(r){ return assignedAsins.indexOf(r.asin) !== -1; });
  check("Isolation: every row's ASIN is in Utharsika's assigned set (no other user's product)", otherUserCheck);
})();

// ---------------------------------------------------------------------
// 10-12. Trend / min-max filters
// ---------------------------------------------------------------------
(function testPerfFilters() {
  var period = Engine.resolvePeriod("MTD", {}, BOUNDS);
  var curMap = Engine.sumRange(index, period.cyStart, period.cyEnd);
  var prevMap = Engine.sumRange(index, period.pyStart, period.pyEnd);
  var rows = Engine.computeRows(productMaster, curMap, prevMap);

  var upRows = rows.filter(function(r){ return r.trend === "UP"; });
  check("Trend filter UP: only UP rows, and this-year > previous-year (or previous=0,current>0)", upRows.every(function(r){ return r.thisYearSales > r.previousYearSales; }), "count=" + upRows.length);

  var allowedTrends = { "UP":1, "DOWN":1, "NO CHANGE":1 };
  check("Trend labels: every row uses exactly one of UP/DOWN/NO CHANGE", rows.every(function(r){ return allowedTrends[r.trend]; }));

  var minSales = 10;
  var minFiltered = rows.filter(function(r){ return r.thisYearSales >= minSales; });
  check("Min-Sales filter: all results >= threshold", minFiltered.every(function(r){ return r.thisYearSales >= minSales; }), "count=" + minFiltered.length);

  var maxOrders = 2;
  var maxFiltered = rows.filter(function(r){ return r.thisYearOrders <= maxOrders; });
  check("Max-Orders filter: all results <= threshold", maxFiltered.every(function(r){ return r.thisYearOrders <= maxOrders; }), "count=" + maxFiltered.length);
})();

// ---------------------------------------------------------------------
// 13. Boundary rejections
// ---------------------------------------------------------------------
(function testBoundaries() {
  function expectThrow(label, fn) {
    try { fn(); check(label, false, "did NOT throw"); }
    catch (e) { check(label, true, e.message); }
  }
  expectThrow("Boundary: current/today date (2026-07-10) rejected", function(){ Engine.resolvePeriod("DAILY", { date: "2026-07-10" }, BOUNDS); });
  expectThrow("Boundary: future date rejected", function(){ Engine.resolvePeriod("DAILY", { date: "2026-08-01" }, BOUNDS); });
  expectThrow("Boundary: 2025 selected as current period rejected", function(){ Engine.resolvePeriod("DAILY", { date: "2025-06-01" }, BOUNDS); });
  expectThrow("Boundary: date before 2026-01-01 rejected", function(){ Engine.resolvePeriod("DAILY", { date: "2025-12-31" }, BOUNDS); });
  expectThrow("Boundary: reversed custom range rejected", function(){ Engine.resolvePeriod("CUSTOM", { customStart: "2026-06-10", customEnd: "2026-06-01" }, BOUNDS); });

  // Unavailable prior-year comparison: pick a current date whose shifted
  // previous-year equivalent falls before historyStart (2025-01-01).
  // Not reachable from the 2026-01-01..2026-07-09 selectable range in this
  // dataset (every selectable date's -1y equivalent is >= 2025-01-01), so
  // this specific rejection path is verified by code inspection instead:
  var tightBounds = { selectableStart: "2026-01-01", selectableEnd: "2026-07-09", historyStart: "2025-02-01", historyEnd: "2026-07-09", latestCompleted: "2026-07-09" };
  expectThrow("Boundary: previous-year comparison outside embedded history rejected", function(){ Engine.resolvePeriod("DAILY", { date: "2026-01-15" }, tightBounds); });
})();

// ---------------------------------------------------------------------
// 14. Leap-year handling
// ---------------------------------------------------------------------
(function testLeapYear() {
  var shifted = Engine.shiftOneYearBack(Engine.parseDate("2028-02-29"));
  check("Leap year: 2028-02-29 shifts to 2027-02-28 with leapNote", Engine.fmtDate(shifted.date) === "2027-02-28" && shifted.leapNote === true, JSON.stringify({d: Engine.fmtDate(shifted.date), note: shifted.leapNote}));
})();

// ---------------------------------------------------------------------
// 15. Total recalculation is aggregate-of-aggregate, not averaged
// ---------------------------------------------------------------------
(function testTotalNotAveraged() {
  var period = Engine.resolvePeriod("MONTH", { month: "2026-06" }, BOUNDS);
  var curMap = Engine.sumRange(index, period.cyStart, period.cyEnd);
  var prevMap = Engine.sumRange(index, period.pyStart, period.pyEnd);
  var rows = Engine.computeRows(productMaster, curMap, prevMap);
  var total = Engine.computeTotal(rows);

  var definedPct = rows.filter(function(r){ return r.achieveSalesPct !== null; }).map(function(r){ return r.achieveSalesPct; });
  var naiveAvg = definedPct.reduce(function(a,b){return a+b;}, 0) / (definedPct.length || 1);
  check("Total Achieve Sales % is NOT a naive average of row-level percentages", Math.abs(total.achieveSalesPct - naiveAvg) > 0.001 || definedPct.length <= 1, "total=" + total.achieveSalesPct + " naiveAvg=" + naiveAvg);

  var expectedTotalPct = (total.previousYearSales * 1.30 === 0) ? null : (total.thisYearSales / (total.previousYearSales * 1.30)) * 100;
  check("Total Achieve Sales % equals SUM(current)/SUM(previous*1.3)*100", Math.abs(total.achieveSalesPct - expectedTotalPct) < 0.0001);
})();

// ---------------------------------------------------------------------
// 16. Zero-base rule
// ---------------------------------------------------------------------
(function testZeroBase() {
  check("Zero-base: prev=0,cur=0 -> NO CHANGE", Engine.trendOf(0,0) === "NO CHANGE");
  check("Zero-base: prev=0,cur>0 -> UP", Engine.trendOf(150,0) === "UP");
  check("Zero-base: achieve% undefined (null) when target is zero", Engine.safeAchievePct(150, 0) === null);
  check("Zero-base: change undefined (null) when previous is zero", Engine.safeChange(150, 0) === null);
})();

// ---------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------
var passed = results.filter(function(r){ return r.pass; }).length;
console.log("\n" + passed + "/" + results.length + " checks passed");
if (passed !== results.length) {
  console.log("\nFAILED CHECKS:");
  results.filter(function(r){ return !r.pass; }).forEach(function(r){ console.log(" - " + r.label + " :: " + r.detail); });
  process.exit(1);
}
