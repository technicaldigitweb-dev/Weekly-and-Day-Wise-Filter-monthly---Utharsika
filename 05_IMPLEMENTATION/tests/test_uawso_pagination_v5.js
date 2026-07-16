/*
Tests for the sticky pagination bar / page info / Previous-Next /
go-to-page UI update to the v5 (ASIN-level) template and the actual
updated 09_OUTPUTS\2026-07-15_utharsika_v004.html.

Two layers:
  (a) structural/source checks (CSS, z-index compatibility, markup) -
      the same style used by the prior sticky-columns test file, since
      no browser-automation tool is available in this environment;
  (b) a genuine FUNCTIONAL check: the real inline pagination JS is
      extracted from the actual generated HTML and executed in a
      Node vm context against a minimal fake-DOM (just enough
      getElementById/innerHTML/addEventListener surface for this
      script's own usage) - this is not a structural guess, it is the
      real render()/renderTable()/renderPagination()/attemptGoToPage()
      code actually running and producing real page/range text.

Run: node tests/test_uawso_pagination_v5.js
*/
"use strict";
var fs = require("fs");
var path = require("path");
var vm = require("vm");
var crypto = require("crypto");

var TEMPLATE_PATH = path.join(__dirname, "..", "templates", "uawso_report_template_v5_asin_level.html");
var FINAL_HTML_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-15_utharsika_v004.html");
var OLD_V001_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v001.html");

var template = fs.readFileSync(TEMPLATE_PATH, "utf-8");
var finalHtml = fs.readFileSync(FINAL_HTML_PATH, "utf-8");

var results = [];
function check(label, cond, detail) {
  results.push({ label: label, pass: !!cond, detail: detail || "" });
  console.log("[" + (cond ? "PASS" : "FAIL") + "] " + label + (detail ? " -- " + detail : ""));
}

// =====================================================================
// STRUCTURAL CHECKS (source-level)
// =====================================================================

// 1/2/3. Sticky positioning present, remains within the same sticky
// stacking system as the header/columns.
check("1. .uawso-pagination uses position: sticky; bottom: 0",
  /\.uawso-pagination\s*\{[^}]*position:\s*sticky;[^}]*bottom:\s*0;/.test(template));
check("2. Pagination bar is the trailing element inside the SAME bounded scroll container as the table (no separate overlay hack)",
  /<div class="uawso-table-wrap">[\s\S]*<table class="uawso-table"[\s\S]*<div class="uawso-pagination" id="uawso-pagination">[\s\S]*<\/div>\s*\n?\s*<\/div>/.test(template));

// 3. Last row not hidden: pagination is the final child of the scroll
// container (proven by #2), so its sticky "docked" position and its
// natural end-of-content position coincide at max scroll - nothing
// after it can be covered. Plus an explicit safety margin exists.
check("3. Pagination bar has a safety margin above it (defensive spacing, on top of the structural proof in #2)",
  /\.uawso-pagination\s*\{[^}]*margin-top:\s*4px;/.test(template));

// 4/5. Current page / total pages displayed
check("4. Current page is rendered (\"Page \" + page + \" of \")", /Page ' \+ page \+ ' of '/.test(template));
check("5. Total pages is part of the same rendered string", /\+ totalPages \+/.test(template));

// 6. Filtered row range displayed
check("6. Row-range text (\"Showing X\\u2013Y of Z\") is rendered", /"Showing " \+ startRow/.test(template) && /rangeText/.test(template));

// 7/8/9/10. Previous/Next present with accessible labels and correct semantics in source
check("7. Previous button has an accessible aria-label", /aria-label="Previous page"/.test(template));
check("8. Next button has an accessible aria-label", /aria-label="Next page"/.test(template));
check("9. Previous handler decrements the page (Math.max(1, page - 1))", /Math\.max\(1, page - 1\)/.test(template));
check("10. Next handler increments the page (Math.min\\(totalPages, page \\+ 1\\))", /Math\.min\(totalPages, page \+ 1\)/.test(template));

// 11/12/13. Go-to-page input
check("11. Numeric \"Go to page\" input exists (type=number, min=1, max=totalPages)", /type="number" id="pg-goto" min="1" max="/.test(template));
check("12. Enter key triggers navigation", /if \(e\.key === "Enter"\)/.test(template));
check("13. Invalid input (blank/zero/negative/decimal/non-numeric) is rejected with a message, never silently ignored or crashing",
  /if \(s === ""\) \{ showError/.test(template) && /if \(!\/\^\[0-9\]\+\$\/\.test\(s\)\) \{ showError/.test(template) && /if \(n < 1\) \{ showError/.test(template));

// 14. Page input max updates after filtering (rebuilt every render via renderPagination)
check("14. Page input's max attribute is rebuilt from the CURRENT totalPages every render (not a static value)",
  /max="\' \+ Math\.max\(totalPages,1\) \+ \'"/.test(template));

// 15/16. Filtering/search resets page (Apply button + ASIN dropdown onChange)
check("15. Apply button resets to page 1", /"btn-apply"\)\.addEventListener\("click", function\(\)\{ state\.page = 1; render\(\); \}\)/.test(template));
check("16. ASIN dropdown selection change resets to page 1 (fixed in this task - previously did not)",
  /onChange: function\(\)\{ state\.page = 1; render\(\); \}/.test(template));

// 17. Page-size change resets to page 1
check("17. Changing rows-per-page resets to page 1", /"f-rows-per-page"\)\.addEventListener\("change", function\(\)\{ state\.page = 1; render\(\); \}\)/.test(template));

// 18. Sorting keeps or safely clamps the page (no longer force-resets to 1)
check("18. Column-header sort click no longer force-resets to page 1 (retains/clamps instead)",
  !/document\.getElementById\("f-sort-dir"\)\.value = "desc"; \}\n      state\.page = 1; render\(\);/.test(template) &&
  /Sorting retains the current page/.test(template));

// 19. Zero-result state - checked functionally below (item 19 in the harness)

// 20. Download exports all filtered rows, not the current page (state.lastFilteredRows, not pageRows)
check("20. Download still reads state.lastFilteredRows (all filtered rows, not the current page slice)",
  /downloadCsv\(state\.lastFilteredRows, "filtered"\)/.test(template) && /state\.lastFilteredRows = sorted;/.test(template));

// 21/22. Sticky header / sticky first two columns still present and unmodified by this task
check("21. Sticky header rule (thead th top:0) unchanged", /table\.uawso-table thead th \{[\s\S]{0,80}position:\s*sticky;[\s\S]{0,40}top:\s*0;/.test(template));
check("22. Sticky column 1/2 rules unchanged (left:0 / left:var(--uawso-col1-width", /left:\s*0;/.test(template) && /left:\s*var\(--uawso-col1-width/.test(template));

// 23. Row Type still absent
check("23. \"Row Type\" remains absent from the template", !/Row Type/i.test(template));

// 24. KPI totals unchanged - verified functionally below against the actual final HTML's embedded data

// 25. Historical HTML outputs unchanged
var v001Hash = crypto.createHash("sha256").update(fs.readFileSync(OLD_V001_PATH)).digest("hex");
check("25. 2026-07-10_utharsika_v001.html hash matches its long-standing baseline",
  v001Hash === "335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4", "got=" + v001Hash);

// 26. No ph_task writes in the update/generation scripts
var updateScriptSource = fs.readFileSync(path.join(__dirname, "..", "src", "update_uawso_v004_pagination.py"), "utf-8");
var genScriptSource = fs.readFileSync(path.join(__dirname, "..", "src", "generate_uawso_v5_2026_07_15_pagination_update_staging.py"), "utf-8");
var writesPhTask = /(INSERT INTO|UPDATE)\s+tech_team_outputs\.ph_task/i;
check("26. Update/regeneration scripts contain no ph_task INSERT/UPDATE statement",
  !writesPhTask.test(updateScriptSource) && !writesPhTask.test(genScriptSource));

// =====================================================================
// FUNCTIONAL CHECK: run the REAL inline pagination JS against a minimal
// fake DOM, using the REAL embedded data from the actual final HTML.
// =====================================================================
function extractJsonScript(html, id) {
  var re = new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)<\\/script>');
  return html.match(re)[1];
}
function extractInlineScripts(html) {
  var out = [];
  var re = /<script>([\s\S]*?)<\/script>/g;
  var m;
  while ((m = re.exec(html))) out.push(m[1]);
  return out;
}

function ClassList() { this.set = new Set(); }
ClassList.prototype.add = function () { var a = arguments; for (var i = 0; i < a.length; i++) this.set.add(a[i]); };
ClassList.prototype.remove = function () { var a = arguments; for (var i = 0; i < a.length; i++) this.set.delete(a[i]); };
ClassList.prototype.contains = function (c) { return this.set.has(c); };
function Style() { this.props = new Map(); }
Style.prototype.setProperty = function (k, v) { this.props.set(k, v); };

function makeElement(id) {
  var listeners = {};
  var el = {
    id: id, _value: "", _innerHTML: "", _disabled: false,
    classList: new ClassList(), style: new Style(),
    get value() { return this._value; }, set value(v) { this._value = v; },
    get innerHTML() { return this._innerHTML; },
    set innerHTML(v) {
      this._innerHTML = v;
      var ids = (String(v).match(/id="([a-zA-Z0-9-]+)"/g) || []).map(function (s) { return s.match(/id="([a-zA-Z0-9-]+)"/)[1]; });
      ids.forEach(function (cid) { if (!ELEMENTS.has(cid)) ELEMENTS.set(cid, makeElement(cid)); });
      ids.forEach(function (cid) {
        var seg = String(v).slice(String(v).indexOf('id="' + cid + '"'));
        var tagEnd = seg.indexOf(">");
        var openTag = seg.slice(0, tagEnd);
        ELEMENTS.get(cid)._disabled = /\bdisabled\b/.test(openTag);
        var valMatch = openTag.match(/value="([^"]*)"/);
        if (valMatch) ELEMENTS.get(cid)._value = valMatch[1];
      });
    },
    get textContent() { return this._textContent; }, set textContent(v) { this._textContent = v; },
    get disabled() { return this._disabled; }, set disabled(v) { this._disabled = v; },
    getAttribute: function () { return null; }, setAttribute: function () {},
    addEventListener: function (type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    dispatch: function (type, evt) { (listeners[type] || []).forEach(function (fn) { fn(evt || {}); }); },
    set onclick(fn) { this._onclick = fn; }, get onclick() { return this._onclick; },
    click: function () { if (this._onclick) this._onclick(); },
    getBoundingClientRect: function () { return { width: 90, height: 24 }; },
    querySelectorAll: function () { return []; },
    appendChild: function () {}, removeChild: function () {}, contains: function () { return false; },
  };
  return el;
}

var ELEMENTS = new Map();
[
  "btn-apply", "btn-csv", "btn-reset", "cov-no-sales",
  "f-custom-end", "f-custom-start", "f-date", "f-mode", "f-month",
  "f-rows-per-page", "f-search", "f-sort-dir", "f-sort-field", "f-trend",
  "f-week-end", "f-week-start",
  "uawso-kpis", "uawso-messages", "uawso-pagination", "uawso-summary",
  "uawso-table", "uawso-tbody", "uawso-tfoot",
  "wrap-particular-date", "wrap-month", "wrap-week-start", "wrap-week-end", "wrap-custom-start", "wrap-custom-end",
  "asin-dropdown", "asin-dropdown-toggle", "asin-search", "asin-options", "asin-selected-count", "asin-select-all", "asin-clear-all",
].forEach(function (id) { ELEMENTS.set(id, makeElement(id)); });

ELEMENTS.get("f-mode")._value = "MTD";
ELEMENTS.get("f-rows-per-page")._value = "25";
ELEMENTS.get("f-sort-field")._value = "totalSales";
ELEMENTS.get("f-sort-dir")._value = "desc";
ELEMENTS.set("uawso-product-master-asin-level", { textContent: extractJsonScript(finalHtml, "uawso-product-master-asin-level") });
ELEMENTS.set("uawso-daily-aggregates-asin", { textContent: extractJsonScript(finalHtml, "uawso-daily-aggregates-asin") });
ELEMENTS.set("uawso-vendor-periods", { textContent: extractJsonScript(finalHtml, "uawso-vendor-periods") });

var documentStub = {
  getElementById: function (id) { if (!ELEMENTS.has(id)) ELEMENTS.set(id, makeElement(id)); return ELEMENTS.get(id); },
  querySelectorAll: function () { return []; },
  querySelector: function (sel) { if (sel === "#uawso-table thead th:first-child") return makeElement("thead-th-1"); return null; },
  addEventListener: function () {},
  createElement: function () { return makeElement("dyn"); },
  body: { appendChild: function () {}, removeChild: function () {} },
};
var windowStub = {};
var sandbox = {
  document: documentStub, window: windowStub, self: windowStub,
  URL: { createObjectURL: function () { return "blob:x"; }, revokeObjectURL: function () {} },
  Blob: function Blob() {}, console: console,
};
vm.createContext(sandbox);
var scripts = extractInlineScripts(finalHtml);
new vm.Script(scripts[0], { filename: "engine.js" }).runInContext(sandbox);
new vm.Script(scripts[1], { filename: "controller.js" }).runInContext(sandbox);

function paginationText() { return ELEMENTS.get("uawso-pagination")._innerHTML; }
function currentPageFromDom() {
  var m = paginationText().match(/Page (\d+) of (\d+)/);
  return m ? { page: parseInt(m[1], 10), totalPages: parseInt(m[2], 10) } : null;
}

ELEMENTS.get("btn-apply").dispatch("click");
var pg = currentPageFromDom();
var expectedTotalPages = Math.ceil(1723 / 25);
check("F1 (=4/5). Functional: real render produces \"Page 1 of " + expectedTotalPages + "\" for 1723 rows at 25/page",
  pg && pg.page === 1 && pg.totalPages === expectedTotalPages, JSON.stringify(pg));
check("F2 (=6). Functional: row-range text matches \"Showing 1\\u20131325 of 1,723\" pattern", /Showing 1–25 of 1,723/.test(paginationText()));
check("F3 (=9). Functional: Previous disabled on page 1", ELEMENTS.get("pg-prev")._disabled === true);
check("F4 (=7). Functional: Next navigates to page 2", (ELEMENTS.get("pg-next").click(), currentPageFromDom().page === 2));
check("F5 (=7,10). Functional: Previous navigates back to page 1", (ELEMENTS.get("pg-prev").click(), currentPageFromDom().page === 1));

ELEMENTS.get("pg-goto")._value = "10"; ELEMENTS.get("pg-goto-btn").click();
check("F6 (=11,12,20). Functional: go-to-page(10) navigates to page 10", currentPageFromDom().page === 10);

var lastPage = expectedTotalPages;
ELEMENTS.get("pg-goto")._value = String(lastPage + 999); ELEMENTS.get("pg-goto-btn").click();
pg = currentPageFromDom();
check("F7 (=13). Functional: out-of-range page number clamps safely to the last valid page", pg.page === lastPage, JSON.stringify(pg));
check("F8 (=9). Functional: Next disabled on the last page", ELEMENTS.get("pg-next")._disabled === true);

ELEMENTS.get("pg-goto")._value = "3"; ELEMENTS.get("pg-goto-btn").click();
var beforeInvalid = currentPageFromDom().page;
var invalidValues = ["", "0", "-5", "3.5", "abc"];
var allInvalidSafe = true;
invalidValues.forEach(function (badVal) {
  ELEMENTS.get("pg-goto")._value = badVal;
  var threw = false;
  try { ELEMENTS.get("pg-goto-btn").click(); } catch (e) { threw = true; }
  var after = currentPageFromDom();
  if (threw || after.page !== beforeInvalid) allInvalidSafe = false;
});
check("F9 (=13). Functional: blank/zero/negative/decimal/non-numeric input never crashes and never navigates",
  allInvalidSafe, "values_tested=" + JSON.stringify(invalidValues));

ELEMENTS.get("pg-goto")._value = "5"; ELEMENTS.get("pg-goto-btn").click();
ELEMENTS.get("f-rows-per-page")._value = "50";
ELEMENTS.get("f-rows-per-page").dispatch("change");
check("F10 (=17). Functional: changing rows-per-page resets to page 1", currentPageFromDom().page === 1);

ELEMENTS.get("f-search")._value = "ZZZZZZ_NO_SUCH_ASIN_OR_TITLE_ZZZZZZ";
ELEMENTS.get("btn-apply").dispatch("click");
pg = currentPageFromDom();
check("F11 (=19). Functional: zero-result filter shows \"Page 0 of 0\"", pg.page === 0 && pg.totalPages === 0, JSON.stringify(pg));
check("F12 (=19). Functional: zero-result filter shows \"Showing 0 of 0\"", /Showing 0 of 0/.test(paginationText()));
ELEMENTS.get("f-search")._value = ""; ELEMENTS.get("btn-apply").dispatch("click");

// F13 (=24). KPI totals unchanged - full-range reconciliation against the actual embedded data
var Engine = require(path.join(__dirname, "..", "src", "uawso_client_engine.js"));
var pmFinal = JSON.parse(extractJsonScript(finalHtml, "uawso-product-master-asin-level"));
var daFinal = JSON.parse(extractJsonScript(finalHtml, "uawso-daily-aggregates-asin"));
var vpFinal = JSON.parse(extractJsonScript(finalHtml, "uawso-vendor-periods"));
var idxFinal = Engine.buildDailyIndexSplit(daFinal);
var canonFinal = Engine.buildCanonicalRowsV5(pmFinal);
var csFinal = Engine.sumRangeByAsinV5(idxFinal, "2025-01-01", "2026-07-14");
var cvFinal = Engine.sumVendorRangeV4(vpFinal, "2025-01-01", "2026-07-14");
var rowsFinal = Engine.computeRowsV5(canonFinal, csFinal, {}, cvFinal, {});
var totalFinal = Engine.computeTotalV5(rowsFinal);
check("F13 (=24). Sales total unchanged (718,835.91)", Math.round(totalFinal.currentYearSales * 100) === 71883591, "got=" + totalFinal.currentYearSales.toFixed(2));
check("F14 (=24). Total Orders reflects the updated formula (FBM+FBA+Vendor Orders = 39,202, 2026-07-15 amendment)", totalFinal.currentYearOrders === 39202, "got=" + totalFinal.currentYearOrders);
check("F15 (=24). No Quantity field remains on the computed total (2026-07-15 amendment - Sales and Orders only)", totalFinal.totalQuantity === undefined, "got totalQuantity=" + totalFinal.totalQuantity);
check("F16 (=24). ASIN row count unchanged (1,723)", pmFinal.length === 1723, "got=" + pmFinal.length);

// ---------------------------------------------------------------------
var failed = results.filter(function (r) { return !r.pass; });
console.log("\n" + (results.length - failed.length) + "/" + results.length + " checks passed.");
if (failed.length) {
  console.log("FAILED: " + failed.map(function (r) { return r.label; }).join("; "));
  process.exit(1);
}
console.log("ALL PASS");
