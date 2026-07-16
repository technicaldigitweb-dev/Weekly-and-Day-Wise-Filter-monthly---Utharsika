/*
Tests for the sticky-header/sticky-columns/single-download/Row-Type-removal/
Column-Definitions UI update to the v5 (ASIN-level) template and the
actual updated 09_OUTPUTS\2026-07-15_utharsika_v004.html.

This environment has no browser-automation tool available (no Playwright/
Puppeteer/jsdom), so these are structural/source-level checks - the CSS
sticky pattern used (bounded-height scroll container + position:sticky on
th/td, with left offsets driven by --uawso-col1-width) is the standard,
well-established technique for combined sticky-header + frozen-column
tables and is verified present and internally consistent here. True
interactive scroll/overlap verification could not be performed and is
disclosed as a limitation in the evidence file, not silently skipped.

Run: node tests/test_uawso_sticky_columns_and_export_v5.js
*/
"use strict";
var fs = require("fs");
var path = require("path");

var TEMPLATE_PATH = path.join(__dirname, "..", "templates", "uawso_report_template_v5_asin_level.html");
var FINAL_HTML_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-15_utharsika_v004.html");
var OLD_HTML_HASHES_PATH_1 = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v001.html");

var template = fs.readFileSync(TEMPLATE_PATH, "utf-8");
var finalHtml = fs.readFileSync(FINAL_HTML_PATH, "utf-8");

var results = [];
function check(label, cond, detail) {
  results.push({ label: label, pass: !!cond, detail: detail || "" });
  console.log("[" + (cond ? "PASS" : "FAIL") + "] " + label + (detail ? " -- " + detail : ""));
}

// ---------------------------------------------------------------------
// 1. Table header uses sticky positioning
// ---------------------------------------------------------------------
check("1. thead th has position: sticky; top: 0",
  /table\.uawso-table thead th\s*\{[^}]*position:\s*sticky;[^}]*top:\s*0;/.test(template));

// ---------------------------------------------------------------------
// 2/3. First and second visible columns are sticky
// ---------------------------------------------------------------------
check("2. Column 1 (nth-child(1)) has position: sticky; left: 0",
  /th:nth-child\(1\),\s*\n?\s*table\.uawso-table td:nth-child\(1\)\s*\{[^}]*position:\s*sticky;[^}]*left:\s*0;/.test(template));
check("3. Column 2 (nth-child(2)) has position: sticky with a left offset variable",
  /th:nth-child\(2\),\s*\n?\s*table\.uawso-table td:nth-child\(2\)\s*\{[^}]*position:\s*sticky;[^}]*left:\s*var\(--uawso-col1-width/.test(template));

// ---------------------------------------------------------------------
// 4. Second-column left offset matches first-column width (measured, not
//    hardcoded) - verify the JS measures column 1's REAL rendered width
//    and writes it to the exact custom property column 2's CSS reads.
// ---------------------------------------------------------------------
var measuresWidth = /firstHeaderCell\.getBoundingClientRect\(\)\.width/.test(template);
var setsProperty = /setProperty\("--uawso-col1-width"/.test(template);
var readsProperty = /left:\s*var\(--uawso-col1-width,\s*90px\)/.test(template);
check("4. Column 2's left offset is driven by column 1's measured width (not a hardcoded guess)",
  measuresWidth && setsProperty && readsProperty,
  "measures=" + measuresWidth + " sets=" + setsProperty + " reads=" + readsProperty);
check("4b. updateStickyColumnOffsets() is called after every table render (stays correct across filters/sorts)",
  /function renderTable[\s\S]*updateStickyColumnOffsets\(\);\s*\n\s*\}/.test(template));

// ---------------------------------------------------------------------
// 5. Safe z-index layering: frozen header cells (both row+column frozen)
//    must have a HIGHER z-index than both the plain sticky header and the
//    frozen body columns, so they render on top at the intersection.
// ---------------------------------------------------------------------
// Split the <style> block into individual rule blocks and find the
// z-index declared in the rule whose selector matches each fragment -
// avoids fragile whitespace-sensitive regex reconstruction of the CSS.
var styleBlock = template.match(/<style>([\s\S]*?)<\/style>/)[1];
var ruleBlocks = styleBlock.split("}").map(function (b) { return b.trim(); }).filter(Boolean);
function zIndexForSelectorContaining(needle) {
  var rule = ruleBlocks.find(function (b) { return b.indexOf(needle) !== -1 && b.indexOf("z-index") !== -1; });
  if (!rule) return null;
  var m = rule.match(/z-index:\s*(\d+)/);
  return m ? parseInt(m[1], 10) : null;
}
var zHeaderPlain = zIndexForSelectorContaining("table.uawso-table thead th {");
var zBodyCol1 = zIndexForSelectorContaining("table.uawso-table td:nth-child(1)");
var zHeaderFrozenCols = zIndexForSelectorContaining("table.uawso-table thead th:nth-child(2)");
check("5. Frozen header-column cells have a higher z-index than plain sticky header and frozen body columns",
  zHeaderFrozenCols !== null && zHeaderPlain !== null && zBodyCol1 !== null &&
  zHeaderFrozenCols > zHeaderPlain && zHeaderFrozenCols > zBodyCol1,
  "plain_header=" + zHeaderPlain + " body_col=" + zBodyCol1 + " frozen_header_col=" + zHeaderFrozenCols);

// ---------------------------------------------------------------------
// 6/7/8. Exactly one download action; exports all currently filtered rows,
// not just the visible page.
// ---------------------------------------------------------------------
var downloadButtonMatches = template.match(/id="btn-csv[^"]*"/g) || [];
check("6. Exactly one download button/action exists", downloadButtonMatches.length === 1, "found=" + JSON.stringify(downloadButtonMatches));
check("7. The remaining download exports state.lastFilteredRows (the full filtered set, not a page slice)",
  /downloadCsv\(state\.lastFilteredRows, "filtered"\)/.test(template));
check("8. state.lastFilteredRows is assigned the FULL sorted array (not pageRows/a paginated slice) at the end of renderTable",
  /state\.lastFilteredRows = sorted;/.test(template) && !/state\.lastFilteredRows = pageRows;/.test(template));

// ---------------------------------------------------------------------
// 9/10/11. Row Type absent from header/body/CSV; Image URL remains in CSV
// ---------------------------------------------------------------------
check("9. No \"Row Type\" text or data-field=\"rowType\" header remains in the template", !/Row Type/i.test(template) && !/data-field="rowType"/.test(template));
check("10. CSV headers array contains no \"Row Type\" entry",
  /var headers = \["ASIN","Image URL",/.test(template) && !/headers = \[[^\]]*"Row Type"/.test(template));
check("11. CSV still includes \"Image URL\" as a column", /"Image URL"/.test(template));

// ---------------------------------------------------------------------
// 12. One row per ASIN unchanged (engine/data model untouched by this task)
// ---------------------------------------------------------------------
var engineSource = fs.readFileSync(path.join(__dirname, "..", "src", "uawso_client_engine.js"), "utf-8");
check("12. buildCanonicalRowsV5/computeRowsV5/computeTotalV5 (KPI logic) untouched by this task - still present, unmodified signatures",
  /function buildCanonicalRowsV5\(productMasterAsinLevel\)/.test(engineSource) &&
  /function computeRowsV5\(canonicalRows, curSplit, prevSplit, curVendor, prevVendor\)/.test(engineSource) &&
  /function computeTotalV5\(rows\)/.test(engineSource));

// ---------------------------------------------------------------------
// 13/14. Column Definitions section exists and explains all visible columns
// ---------------------------------------------------------------------
check("13. \"Column Definitions\" section exists in the template", /<h2>Column Definitions<\/h2>/.test(template));
var visibleColumnLabels = (template.match(/<th data-field="[a-zA-Z]+">([^<]+)<\/th>/g) || [])
  .map(function (s) { return s.match(/>([^<]+)</)[1]; });
// Anchor on the specific panel id (not a plain string search for "Column
// Definitions", which can also appear in unrelated comments elsewhere in
// the file) and take everything up to that panel's OWN closing </div>.
var panelStart = template.indexOf('id="uawso-column-definitions"');
var panelEnd = template.indexOf("</div>", template.indexOf("</table>", panelStart));
var definitionsSection = template.slice(panelStart, panelEnd);
var allExplained = visibleColumnLabels.every(function (label) {
  return definitionsSection.indexOf("<strong>" + label + "</strong>") !== -1;
});
check("14. Every visible table column has a matching <strong>Label</strong> entry in Column Definitions",
  allExplained, "columns=" + JSON.stringify(visibleColumnLabels));

// ---------------------------------------------------------------------
// 15. KPI totals unchanged (same embedded data used to regenerate) -
// cross-checked against the pre-recorded v004 baseline.
// ---------------------------------------------------------------------
function extractJsonScript(html, id) {
  var re = new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>');
  var m = html.match(re);
  return JSON.parse(m[1]);
}
var Engine = require(path.join(__dirname, "..", "src", "uawso_client_engine.js"));
var pmFinal = extractJsonScript(finalHtml, "uawso-product-master-asin-level");
var daFinal = extractJsonScript(finalHtml, "uawso-daily-aggregates-asin");
var vpFinal = extractJsonScript(finalHtml, "uawso-vendor-periods");
var idxFinal = Engine.buildDailyIndexSplit(daFinal);
var canonFinal = Engine.buildCanonicalRowsV5(pmFinal);
var csFinal = Engine.sumRangeByAsinV5(idxFinal, "2025-01-01", "2026-07-14");
var cvFinal = Engine.sumVendorRangeV4(vpFinal, "2025-01-01", "2026-07-14");
var rowsFinal = Engine.computeRowsV5(canonFinal, csFinal, {}, cvFinal, {});
var totalFinal = Engine.computeTotalV5(rowsFinal);
check("15. Sales total unchanged (718,835.91)", Math.round(totalFinal.currentYearSales * 100) === 71883591, "got=" + totalFinal.currentYearSales.toFixed(2));
check("15b. Total Orders reflects the updated formula (FBM+FBA+Vendor Orders = 39,202, 2026-07-15 amendment)", totalFinal.currentYearOrders === 39202, "got=" + totalFinal.currentYearOrders);
check("15c. No Quantity field remains on the computed total (2026-07-15 amendment - Sales and Orders only)", totalFinal.totalQuantity === undefined && totalFinal.fbmQuantity === undefined, "got totalQuantity=" + totalFinal.totalQuantity);
check("15d. ASIN row count unchanged (1,723)", pmFinal.length === 1723, "got=" + pmFinal.length);

// ---------------------------------------------------------------------
// 16. Historical HTML outputs remain unchanged
// ---------------------------------------------------------------------
var crypto = require("crypto");
function sha256(buf) { return crypto.createHash("sha256").update(buf).digest("hex"); }
var v001Hash = sha256(fs.readFileSync(OLD_HTML_HASHES_PATH_1));
check("16. 2026-07-10_utharsika_v001.html hash matches its long-standing baseline",
  v001Hash === "335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4", "got=" + v001Hash);

// ---------------------------------------------------------------------
// 17. Existing ph_task rows remain unchanged - this task's scripts never
// touch tech_team_outputs.ph_task at all.
// ---------------------------------------------------------------------
var updateScriptSource = fs.readFileSync(path.join(__dirname, "..", "src", "update_uawso_v004_sticky_and_export.py"), "utf-8");
var genScriptSource = fs.readFileSync(path.join(__dirname, "..", "src", "generate_uawso_v5_2026_07_15_sticky_update_staging.py"), "utf-8");
var writesPhTask = /(INSERT INTO|UPDATE)\s+tech_team_outputs\.ph_task/i;
check("17. Update/regeneration scripts contain no ph_task INSERT/UPDATE statement",
  !writesPhTask.test(updateScriptSource) && !writesPhTask.test(genScriptSource));

// ---------------------------------------------------------------------
var failed = results.filter(function (r) { return !r.pass; });
console.log("\n" + (results.length - failed.length) + "/" + results.length + " checks passed.");
if (failed.length) {
  console.log("FAILED: " + failed.map(function (r) { return r.label; }).join("; "));
  process.exit(1);
}
console.log("ALL PASS");
