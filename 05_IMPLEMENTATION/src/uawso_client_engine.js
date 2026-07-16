/*
UAWSO client-side calculation engine.

Single source of truth for the date/period math and Sales/Orders/
Change/Trend/Achieve% formulas used by the interactive dashboard HTML.
This exact file is:
  (a) inlined verbatim into the shipped self-contained HTML by
      src/dashboard_renderer.py (via its engine-injection placeholder), and
  (b) required() directly by tests/test_uawso_client_engine.js under Node.js.
There is no second, hand-duplicated copy of this logic anywhere - the
tested code and the shipped code are byte-identical.

Mirrors, deliberately, the same formulas as src/period_calculator.py
and src/calculations.py (Python, server-side/production path). Client-
side JS re-implementation is unavoidable because the dashboard has no
backend to call (static self-contained HTML) - see the runtime guide's
"Filter architecture used" note for the explicit tradeoff.
*/
(function (root, factory) {
  var engine = factory();
  if (typeof module !== "undefined" && module.exports) { module.exports = engine; }
  else { root.UAWSOEngine = engine; }
}(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var TARGET_MULT = 1.30;

  // ---- Dynamic order-status inclusion rule (final business rule) -----
  // Mirrors the SQL-side exclusion rule in
  // src/extract_uawso_v4_ordered_sales.py (STATUS_FILTER_SQL): every
  // non-null, non-blank order status is included EXCEPT the two
  // cancellation variants. The included set is never hardcoded here -
  // the pre-aggregated daily_split JSON embedded in the HTML already
  // reflects this rule (applied server-side, in SQL, at extraction
  // time), so this helper is not on the hot path for Sales/Orders/
  // Quantity totals today. It is exposed for any future client-side
  // status filter (e.g. a status dropdown) so that filter would use the
  // exact same rule as the server-side extraction, not a second,
  // independently-maintained list.
  var EXCLUDED_ORDER_STATUSES = new Set(["Cancelled", "Canceled"]);

  function isIncludedOrderStatus(value) {
    if (value === null || value === undefined) {
      return false;
    }
    var status = String(value).trim();
    return status !== "" && !EXCLUDED_ORDER_STATUSES.has(status);
  }

  // ---- Date helpers (mirrors src/period_calculator.py) ---------------
  function parseDate(s) { var p = s.split("-").map(Number); return new Date(Date.UTC(p[0], p[1]-1, p[2])); }
  function fmtDate(d) { return d.toISOString().slice(0,10); }
  function addDays(d, n) { var r = new Date(d.getTime()); r.setUTCDate(r.getUTCDate()+n); return r; }
  function isLeapDay(d) { return d.getUTCMonth() === 1 && d.getUTCDate() === 29; }
  function shiftOneYearBack(d) {
    var y = d.getUTCFullYear()-1, m = d.getUTCMonth(), day = d.getUTCDate();
    var leapNote = false;
    if (isLeapDay(d)) {
      var isLeapYear = (y%4===0 && y%100!==0) || y%400===0;
      if (!isLeapYear) { day = 28; leapNote = true; }
    }
    return { date: new Date(Date.UTC(y, m, day)), leapNote: leapNote };
  }
  function mondayOfWeek(d) { var dow = (d.getUTCDay()+6)%7; return addDays(d, -dow); }
  function firstOfMonth(d) { return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1)); }
  function lastOfMonth(d) { return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth()+1, 0)); }

  // ---- Aggregation over a date range (expects a DAILY_BY_DATE index) -
  function buildDailyIndex(dailyRows) {
    var byDate = {};
    for (var i = 0; i < dailyRows.length; i++) {
      var row = dailyRows[i];
      if (!byDate[row.calendar_date]) byDate[row.calendar_date] = [];
      byDate[row.calendar_date].push(row);
    }
    return { byDate: byDate, dates: Object.keys(byDate).sort() };
  }

  function sumRange(index, startStr, endStr) {
    var map = {};
    for (var i = 0; i < index.dates.length; i++) {
      var d = index.dates[i];
      if (d < startStr || d > endStr) continue;
      var rows = index.byDate[d];
      for (var j = 0; j < rows.length; j++) {
        var r = rows[j], key = r.asin + "|" + r.sku;
        if (!map[key]) map[key] = { sales: 0, orders: 0 };
        map[key].sales += r.sales_total;
        map[key].orders += r.orders_total;
      }
    }
    return map;
  }

  // ---- Calculation engine (mirrors src/calculations.py exactly) ------
  function safeChange(cur, prev) { if (prev === 0) return null; return (cur - prev) / prev; }
  function safeAchievePct(cur, target) { if (target === 0) return null; return (cur / target) * 100; }
  function trendOf(cur, prev) {
    if (prev === 0 && cur === 0) return "NO CHANGE";
    if (prev === 0 && cur > 0) return "UP";
    if (cur > prev) return "UP";
    if (cur < prev) return "DOWN";
    return "NO CHANGE";
  }

  function computeRows(productMaster, currentMap, previousMap) {
    var rows = [];
    for (var i = 0; i < productMaster.length; i++) {
      var p = productMaster[i], key = p.asin + "|" + p.sku;
      var cur = currentMap[key] || { sales: 0, orders: 0 };
      var prev = previousMap[key] || { sales: 0, orders: 0 };
      var salesTarget = prev.sales * TARGET_MULT, orderTarget = prev.orders * TARGET_MULT;
      var bothZero = prev.sales === 0 && cur.sales === 0;
      rows.push({
        asin: p.asin, sku: p.sku,
        previousYearSales: prev.sales, previousYearOrders: prev.orders,
        thisYearSales: cur.sales, thisYearOrders: cur.orders,
        salesChange: safeChange(cur.sales, prev.sales),
        orderChange: safeChange(cur.orders, prev.orders),
        trend: trendOf(cur.sales, prev.sales),
        achieveSalesPct: safeAchievePct(cur.sales, salesTarget),
        achieveOrderPct: safeAchievePct(cur.orders, orderTarget),
        improvementStatus: bothZero ? "NOT IMPROVED" : null,
      });
    }
    return rows;
  }

  function computeTotal(rows) {
    var tPY = 0, tPO = 0, tTY = 0, tTO = 0;
    for (var i = 0; i < rows.length; i++) {
      tPY += rows[i].previousYearSales; tPO += rows[i].previousYearOrders;
      tTY += rows[i].thisYearSales; tTO += rows[i].thisYearOrders;
    }
    return {
      previousYearSales: tPY, previousYearOrders: tPO, thisYearSales: tTY, thisYearOrders: tTO,
      salesChange: safeChange(tTY, tPY), orderChange: safeChange(tTO, tPO),
      achieveSalesPct: safeAchievePct(tTY, tPY * TARGET_MULT),
      achieveOrderPct: safeAchievePct(tTO, tPO * TARGET_MULT),
    };
  }

  // ---- Period resolution per comparison mode --------------------------
  function resolvePeriod(mode, params, bounds) {
    var selStart = parseDate(bounds.selectableStart), selEnd = parseDate(bounds.selectableEnd);
    var histStart = parseDate(bounds.historyStart), histEnd = parseDate(bounds.historyEnd);
    var leapNote = null, cyStart, cyEnd, pyStart, pyEnd;

    function within(d) { return d >= selStart && d <= selEnd; }

    if (mode === "DAILY") {
      cyStart = cyEnd = parseDate(params.date);
    } else if (mode === "MONTH") {
      var m = parseDate(params.month + "-01");
      cyStart = firstOfMonth(m);
      cyEnd = lastOfMonth(m);
      var latest = parseDate(bounds.latestCompleted);
      if (cyEnd > latest) cyEnd = latest;
    } else if (mode === "MTD") {
      var latestD = parseDate(bounds.latestCompleted);
      cyStart = firstOfMonth(latestD);
      cyEnd = latestD;
    } else if (mode === "WEEKLY") {
      cyStart = parseDate(params.weekStart);
      cyEnd = addDays(cyStart, 6);
    } else if (mode === "CUSTOM") {
      cyStart = parseDate(params.customStart);
      cyEnd = parseDate(params.customEnd);
    } else {
      throw new Error("Unknown comparison mode: " + mode);
    }

    if (cyStart > cyEnd) throw new Error("Start date is after end date.");
    if (!within(cyStart) || !within(cyEnd)) {
      throw new Error("Selected period is outside the selectable current-period range (" + bounds.selectableStart + " to " + bounds.selectableEnd + ").");
    }

    var shiftedStart = shiftOneYearBack(cyStart), shiftedEnd = shiftOneYearBack(cyEnd);
    if (shiftedStart.leapNote || shiftedEnd.leapNote) leapNote = "A selected boundary was February 29; the previous-year equivalent was mapped to February 28.";

    if (mode === "MONTH") {
      pyStart = firstOfMonth(shiftedStart.date);
      pyEnd = lastOfMonth(shiftedStart.date);
      if (fmtDate(cyEnd) !== fmtDate(lastOfMonth(cyStart))) {
        // incomplete-month case: mirror the same cutoff shortening previous year
        pyEnd = shiftedEnd.date;
      }
    } else {
      pyStart = shiftedStart.date;
      pyEnd = shiftedEnd.date;
    }

    var pyStartStr = fmtDate(pyStart), pyEndStr = fmtDate(pyEnd);
    if (pyStart < histStart || pyEnd > histEnd) {
      throw new Error("Previous-year comparison data is not available for the selected period.");
    }

    return {
      cyStart: fmtDate(cyStart), cyEnd: fmtDate(cyEnd),
      pyStart: pyStartStr, pyEnd: pyEndStr,
      leapNote: leapNote,
    };
  }

  // =====================================================================
  // v2: FBM/FBA/Vendor coverage, ASIN-level grain (full 1723-ASIN master)
  // Added for the "complete ASIN coverage + FBM/FBA/Vendor" requirement.
  // Does not remove or alter any v1 function above (still used by v1
  // tests/paths) - v2 is additive.
  // =====================================================================

  // ---- Daily FBM/FBA split index (from daily_aggregates_split.json) ---
  function buildDailyIndexSplit(dailyRows) {
    var byDate = {};
    for (var i = 0; i < dailyRows.length; i++) {
      var row = dailyRows[i];
      if (!byDate[row.calendar_date]) byDate[row.calendar_date] = [];
      byDate[row.calendar_date].push(row);
    }
    return { byDate: byDate, dates: Object.keys(byDate).sort() };
  }

  // Sums FBM/FBA sales+orders per ASIN (SKU-level detail is not needed
  // for the totals - SKU is carried separately via the product master's
  // per-ASIN SKU list) over [startStr, endStr] inclusive.
  function sumRangeSplitByAsin(index, startStr, endStr) {
    var map = {}; // asin -> {fbmSales, fbmOrders, fbaSales, fbaOrders}
    for (var i = 0; i < index.dates.length; i++) {
      var d = index.dates[i];
      if (d < startStr || d > endStr) continue;
      var rows = index.byDate[d];
      for (var j = 0; j < rows.length; j++) {
        var r = rows[j];
        if (!map[r.asin]) map[r.asin] = { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
        map[r.asin].fbmSales += r.fbm_sales;
        map[r.asin].fbmOrders += r.fbm_orders;
        map[r.asin].fbaSales += r.fba_sales;
        map[r.asin].fbaOrders += r.fba_orders;
      }
    }
    return map;
  }

  // ---- Vendor period overlap allocation --------------------------------
  // vendor_sales rows are PERIODS (start_date..end_date), not daily
  // buckets - some are ~1-day, some are full-month (confirmed on the
  // source data; see extract_uawso_full_coverage.py's module docstring).
  // A period's full revenue/units is attributed to a selected range if
  // the period OVERLAPS the range at all (no proration) - this can over-
  // or under-attribute at month-boundary edges for monthly-bucketed
  // periods; that is a source-data granularity limitation, documented
  // here and in the HTML's Data Coverage Notes, not silently hidden.
  function periodsOverlap(pStart, pEnd, rStart, rEnd) {
    return !(pEnd < rStart || pStart > rEnd);
  }

  function sumVendorRange(vendorPeriods, startStr, endStr) {
    var map = {}; // asin -> {vendorSales, vendorUnits}
    for (var i = 0; i < vendorPeriods.length; i++) {
      var v = vendorPeriods[i];
      if (!periodsOverlap(v.start_date, v.end_date, startStr, endStr)) continue;
      if (!map[v.asin]) map[v.asin] = { vendorSales: 0, vendorUnits: 0 };
      map[v.asin].vendorSales += v.revenue;
      map[v.asin].vendorUnits += v.units;
    }
    return map;
  }

  // ---- Row computation: ASIN-level grain, all 1723 assigned ASINs ------
  // productMasterFull: [{asin, skus: [sku, ...]}, ...] - one row per ASIN,
  // regardless of whether it has ever sold (skus may be an empty array).
  function computeRowsV2(productMasterFull, curSplit, prevSplit, curVendor, prevVendor) {
    var rows = [];
    for (var i = 0; i < productMasterFull.length; i++) {
      var p = productMasterFull[i];
      var cs = curSplit[p.asin] || { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
      var ps = prevSplit[p.asin] || { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
      var cv = curVendor[p.asin] || { vendorSales: 0, vendorUnits: 0 };
      var pv = prevVendor[p.asin] || { vendorSales: 0, vendorUnits: 0 };

      var curTotalSales = cs.fbmSales + cs.fbaSales + cv.vendorSales;
      var prevTotalSales = ps.fbmSales + ps.fbaSales + pv.vendorSales;
      var curTotalOrdersUnits = cs.fbmOrders + cs.fbaOrders + cv.vendorUnits;
      var prevTotalOrdersUnits = ps.fbmOrders + ps.fbaOrders + pv.vendorUnits;

      var salesTarget = prevTotalSales * TARGET_MULT;
      var bothZero = prevTotalSales === 0 && curTotalSales === 0;

      rows.push({
        asin: p.asin,
        sku: p.skus.join(", "),
        skus: p.skus,
        skuCount: p.skus.length,
        fbmSales: cs.fbmSales, fbmOrders: cs.fbmOrders,
        fbaSales: cs.fbaSales, fbaOrders: cs.fbaOrders,
        vendorSales: cv.vendorSales, vendorUnits: cv.vendorUnits,
        totalSales: curTotalSales, totalOrdersUnits: curTotalOrdersUnits,
        previousYearSales: prevTotalSales,
        currentYearSales: curTotalSales,
        previousYearOrdersUnits: prevTotalOrdersUnits,
        salesChange: safeChange(curTotalSales, prevTotalSales),
        orderChange: safeChange(curTotalOrdersUnits, prevTotalOrdersUnits),
        trend: trendOf(curTotalSales, prevTotalSales),
        achieveSalesPct: safeAchievePct(curTotalSales, salesTarget),
        achieveOrderPct: safeAchievePct(curTotalOrdersUnits, prevTotalOrdersUnits * TARGET_MULT),
        improvementStatus: bothZero ? "NOT IMPROVED" : null,
        hasSku: p.skus.length > 0,
        hasAnySales: curTotalSales > 0 || prevTotalSales > 0,
      });
    }
    return rows;
  }

  // =====================================================================
  // v3: CORRECTED grain - one row = one ASIN + one SKU (or one ASIN with
  // a blank SKU for no-mapping / Vendor-only rows). Fixes v2's incorrect
  // comma-joined-SKU-per-ASIN grain, per the corrected requirement.
  // v1/v2 functions are left untouched above (still used by their own
  // tests as a historical record) - v3 is what the shipped HTML now uses.
  // =====================================================================

  // ---- Static row identity, computed once regardless of filters --------
  // Row structure never changes as the user changes date/period filters -
  // only the metric VALUES on each row change. This keeps "one row = one
  // ASIN + one SKU" a stable structural property, not a per-period
  // side-effect of which SKUs happened to sell in a given window.
  function buildCanonicalRows(productMasterFull, vendorPeriods) {
    var vendorAsinSet = {};
    for (var i = 0; i < vendorPeriods.length; i++) vendorAsinSet[vendorPeriods[i].asin] = true;

    var rows = [];
    for (var i = 0; i < productMasterFull.length; i++) {
      var p = productMasterFull[i];
      var hasVendor = !!vendorAsinSet[p.asin];
      if (p.skus.length > 0) {
        for (var j = 0; j < p.skus.length; j++) {
          rows.push({ asin: p.asin, sku: p.skus[j], rowType: "ASIN_SKU", isVendorRow: false, mappingStatus: "SKU_MAPPED" });
        }
        if (hasVendor) {
          // ASIN already has SKU row(s) - Vendor gets its OWN separate
          // blank-SKU row, never attached to any SKU-specific row.
          rows.push({ asin: p.asin, sku: "", rowType: "VENDOR_ASIN_LEVEL", isVendorRow: true, mappingStatus: "SKU_MAPPED" });
        }
      } else {
        // No SKU mapping at all. If this ASIN also has Vendor data, this
        // single blank row carries BOTH the no-SKU-mapping status AND the
        // Vendor metrics - never create a second blank row for the same ASIN.
        rows.push({
          asin: p.asin, sku: "", rowType: hasVendor ? "NO_SKU_MAPPING_VENDOR" : "NO_SKU_MAPPING",
          isVendorRow: hasVendor, mappingStatus: "NO_SKU_MAPPING",
        });
      }
    }
    return rows;
  }

  // ---- FBM/FBA sums at (asin, sku) grain - NOT collapsed to asin only --
  function sumRangeSplitByAsinSku(index, startStr, endStr) {
    var map = {}; // "asin|sku" -> {fbmSales, fbmOrders, fbaSales, fbaOrders}
    for (var i = 0; i < index.dates.length; i++) {
      var d = index.dates[i];
      if (d < startStr || d > endStr) continue;
      var rows = index.byDate[d];
      for (var j = 0; j < rows.length; j++) {
        var r = rows[j], key = r.asin + "|" + r.sku;
        if (!map[key]) map[key] = { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
        map[key].fbmSales += r.fbm_sales;
        map[key].fbmOrders += r.fbm_orders;
        map[key].fbaSales += r.fba_sales;
        map[key].fbaOrders += r.fba_orders;
      }
    }
    return map;
  }

  // ---- Row computation: correct grain, Vendor never duplicated ---------
  function computeRowsV3(canonicalRows, curSplit, prevSplit, curVendor, prevVendor) {
    var rows = [];
    for (var i = 0; i < canonicalRows.length; i++) {
      var c = canonicalRows[i];
      var key = c.asin + "|" + c.sku;
      // FBM/FBA only apply to real (asin,sku) rows - a blank-SKU Vendor
      // row (sku="") never matches a real key, so this is naturally zero
      // for Vendor-only rows without needing a special case.
      var cs = curSplit[key] || { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
      var ps = prevSplit[key] || { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
      // Vendor is explicitly gated by isVendorRow - attached to exactly
      // one row per ASIN, never to a SKU-specific row.
      var cv = c.isVendorRow ? (curVendor[c.asin] || { vendorSales: 0, vendorUnits: 0 }) : { vendorSales: 0, vendorUnits: 0 };
      var pv = c.isVendorRow ? (prevVendor[c.asin] || { vendorSales: 0, vendorUnits: 0 }) : { vendorSales: 0, vendorUnits: 0 };

      var cySales = cs.fbmSales + cs.fbaSales + cv.vendorSales;
      var pySales = ps.fbmSales + ps.fbaSales + pv.vendorSales;
      var salesTarget = pySales * TARGET_MULT;
      var bothZero = pySales === 0 && cySales === 0;

      rows.push({
        asin: c.asin, sku: c.sku, rowType: c.rowType, mappingStatus: c.mappingStatus,
        fbmSales: cs.fbmSales, fbmOrders: cs.fbmOrders,
        fbaSales: cs.fbaSales, fbaOrders: cs.fbaOrders,
        vendorSales: cv.vendorSales, vendorUnits: cv.vendorUnits,
        previousYearSales: pySales, currentYearSales: cySales,
        salesChange: safeChange(cySales, pySales),
        trend: trendOf(cySales, pySales),
        achievementPct: safeAchievePct(cySales, salesTarget),
        improvementStatus: bothZero ? "NOT IMPROVED" : null,
      });
    }
    return rows;
  }

  function computeTotalV3(rows) {
    var tPY = 0, tCY = 0, tFbmS = 0, tFbmO = 0, tFbaS = 0, tFbaO = 0, tVS = 0, tVU = 0;
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      tPY += r.previousYearSales; tCY += r.currentYearSales;
      tFbmS += r.fbmSales; tFbmO += r.fbmOrders;
      tFbaS += r.fbaSales; tFbaO += r.fbaOrders;
      tVS += r.vendorSales; tVU += r.vendorUnits;
    }
    return {
      previousYearSales: tPY, currentYearSales: tCY,
      fbmSales: tFbmS, fbmOrders: tFbmO, fbaSales: tFbaS, fbaOrders: tFbaO,
      vendorSales: tVS, vendorUnits: tVU,
      salesChange: safeChange(tCY, tPY),
      achievementPct: safeAchievePct(tCY, tPY * TARGET_MULT),
    };
  }

  function computeTotalV2(rows) {
    var tPY = 0, tTY = 0, tFbmS = 0, tFbmO = 0, tFbaS = 0, tFbaO = 0, tVS = 0, tVU = 0, tOU = 0, tPOU = 0;
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      tPY += r.previousYearSales; tTY += r.currentYearSales;
      tFbmS += r.fbmSales; tFbmO += r.fbmOrders;
      tFbaS += r.fbaSales; tFbaO += r.fbaOrders;
      tVS += r.vendorSales; tVU += r.vendorUnits;
      tOU += r.totalOrdersUnits; tPOU += r.previousYearOrdersUnits;
    }
    return {
      previousYearSales: tPY, currentYearSales: tTY,
      fbmSales: tFbmS, fbmOrders: tFbmO, fbaSales: tFbaS, fbaOrders: tFbaO,
      vendorSales: tVS, vendorUnits: tVU, totalSales: tTY, totalOrdersUnits: tOU,
      previousYearOrdersUnits: tPOU,
      salesChange: safeChange(tTY, tPY),
      orderChange: safeChange(tOU, tPOU),
      achieveSalesPct: safeAchievePct(tTY, tPY * TARGET_MULT),
      achieveOrderPct: safeAchievePct(tOU, tPOU * TARGET_MULT),
    };
  }

  // =====================================================================
  // v4: Ordered Product Sales / Total Orders / Total Quantity rules
  // (v002 requirement). Additive only - does not alter any v1/v2/v3
  // function above, so the already-shipped v001 HTML (which has v3
  // baked in verbatim) is completely unaffected by this addition.
  //
  // Business rules (see 07_EVIDENCE v002 validation doc for full
  // reasoning and evidence):
  //   Ordered Product Sales = SUM(item_price * quantity) for
  //     source_name='AMAZON' AND order_status IN ('Completed','Refunded').
  //     A same/later-month refund does NOT remove the original Sales
  //     from the month the order was placed.
  //   Total Orders = COUNT(DISTINCT order_item_info) for
  //     order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT').
  //     Refunded rows contribute to Sales but NOT to Total Orders (the
  //     item was not, in the end, retained/fulfilled to the customer).
  //     A zero-value Completed REPLACEMENT row contributes exactly one
  //     order item and zero Sales. Cancelled/Canceled rows are excluded
  //     entirely from both Sales and Orders.
  //   Total Quantity = FBM Quantity + FBA Quantity + Vendor Units, using
  //     the SAME row-inclusion scope as Total Orders (Completed,
  //     AMAZON+REPLACEMENT) for FBM/FBA Quantity.
  //   Vendor Orders = N/A always - no valid Vendor order key exists in
  //     the source database (public.vendor_sales has no order/PO
  //     column); Vendor Units are never counted as, or added to,
  //     Total Orders.
  // =====================================================================

  // ---- Corrected Vendor period-overlap test (v002 Phase 7 bug fix) ----
  // vendor_sales periods are stored half-open: [start_date, end_date) -
  // end_date is literally the first day of the NEXT period, not the
  // last day of this one (confirmed: exact-calendar-month Vendor rows
  // consistently show e.g. start_date="2025-06-01", end_date="2025-07-01").
  // The original periodsOverlap() test used `pEnd < rStart` (non-strict
  // on the touching boundary), which meant a period ending EXACTLY on a
  // queried range's start date (e.g. a June period touching a July
  // query) was incorrectly counted as overlapping BOTH months - found
  // during v002 Phase 7 cross-validation against PostgreSQL (e.g. July
  // 2025 Vendor Sales was 8871.77 via the old test vs a confirmed-
  // correct 4568.81 via direct SQL - the difference, 4302.96, is
  // exactly June 2025's Vendor Sales leaking forward into July).
  // periodsOverlapV4 fixes this with a strict `pEnd <= rStart` exclusion
  // on the half-open side; the other boundary (pStart > rEnd) needs no
  // change since start_date is inclusive already. Additive only - does
  // not alter periodsOverlap/sumVendorRange, which v001's already-baked
  // HTML uses verbatim and must not change.
  function periodsOverlapV4(pStart, pEnd, rStart, rEnd) {
    return !(pEnd <= rStart || pStart > rEnd);
  }

  function sumVendorRangeV4(vendorPeriods, startStr, endStr) {
    var map = {}; // asin -> {vendorSales, vendorUnits}
    for (var i = 0; i < vendorPeriods.length; i++) {
      var v = vendorPeriods[i];
      if (!periodsOverlapV4(v.start_date, v.end_date, startStr, endStr)) continue;
      if (!map[v.asin]) map[v.asin] = { vendorSales: 0, vendorUnits: 0 };
      map[v.asin].vendorSales += v.revenue;
      map[v.asin].vendorUnits += v.units;
    }
    return map;
  }

  function sumRangeSplitByAsinSkuV4(index, startStr, endStr) {
    var map = {}; // "asin|sku" -> {fbmSales,fbmOrders,fbmQuantity,fbaSales,fbaOrders,fbaQuantity}
    for (var i = 0; i < index.dates.length; i++) {
      var d = index.dates[i];
      if (d < startStr || d > endStr) continue;
      var rows = index.byDate[d];
      for (var j = 0; j < rows.length; j++) {
        var r = rows[j], key = r.asin + "|" + r.sku;
        if (!map[key]) map[key] = { fbmSales: 0, fbmOrders: 0, fbmQuantity: 0, fbaSales: 0, fbaOrders: 0, fbaQuantity: 0 };
        map[key].fbmSales += r.fbm_sales;
        map[key].fbmOrders += r.fbm_orders;
        map[key].fbmQuantity += r.fbm_quantity;
        map[key].fbaSales += r.fba_sales;
        map[key].fbaOrders += r.fba_orders;
        map[key].fbaQuantity += r.fba_quantity;
      }
    }
    return map;
  }

  var EMPTY_SPLIT_V4 = { fbmSales: 0, fbmOrders: 0, fbmQuantity: 0, fbaSales: 0, fbaOrders: 0, fbaQuantity: 0 };
  var EMPTY_VENDOR_V4 = { vendorSales: 0, vendorUnits: 0 };

  function computeRowsV4(canonicalRows, curSplit, prevSplit, curVendor, prevVendor) {
    var rows = [];
    for (var i = 0; i < canonicalRows.length; i++) {
      var c = canonicalRows[i];
      var key = c.asin + "|" + c.sku;
      var cs = curSplit[key] || EMPTY_SPLIT_V4;
      var ps = prevSplit[key] || EMPTY_SPLIT_V4;
      var cv = c.isVendorRow ? (curVendor[c.asin] || EMPTY_VENDOR_V4) : EMPTY_VENDOR_V4;
      var pv = c.isVendorRow ? (prevVendor[c.asin] || EMPTY_VENDOR_V4) : EMPTY_VENDOR_V4;

      var cyOrders = cs.fbmOrders + cs.fbaOrders; // Vendor Units never added to Total Orders
      var pyOrders = ps.fbmOrders + ps.fbaOrders;
      var cySales = cs.fbmSales + cs.fbaSales + cv.vendorSales;
      var pySales = ps.fbmSales + ps.fbaSales + pv.vendorSales;
      var cyQuantity = cs.fbmQuantity + cs.fbaQuantity + cv.vendorUnits;
      var pyQuantity = ps.fbmQuantity + ps.fbaQuantity + pv.vendorUnits;

      var salesTarget = pySales * TARGET_MULT;
      var orderTarget = pyOrders * TARGET_MULT;
      var quantityTarget = pyQuantity * TARGET_MULT;
      var bothZero = pySales === 0 && cySales === 0;

      rows.push({
        asin: c.asin, sku: c.sku, rowType: c.rowType, mappingStatus: c.mappingStatus,
        fbmSales: cs.fbmSales, fbmOrders: cs.fbmOrders, fbmQuantity: cs.fbmQuantity,
        fbaSales: cs.fbaSales, fbaOrders: cs.fbaOrders, fbaQuantity: cs.fbaQuantity,
        vendorSales: cv.vendorSales, vendorUnits: cv.vendorUnits, vendorOrders: null,
        totalSales: cySales, totalOrders: cyOrders, totalQuantity: cyQuantity,
        previousYearSales: pySales, currentYearSales: cySales,
        previousYearOrders: pyOrders, currentYearOrders: cyOrders,
        previousYearQuantity: pyQuantity, currentYearQuantity: cyQuantity,
        salesChange: safeChange(cySales, pySales),
        orderChange: safeChange(cyOrders, pyOrders),
        quantityChange: safeChange(cyQuantity, pyQuantity),
        trend: trendOf(cySales, pySales),
        achievementPct: safeAchievePct(cySales, salesTarget),
        achievementOrdersPct: safeAchievePct(cyOrders, orderTarget),
        achievementQuantityPct: safeAchievePct(cyQuantity, quantityTarget),
        improvementStatus: bothZero ? "NOT IMPROVED" : null,
      });
    }
    return rows;
  }

  function computeTotalV4(rows) {
    var t = {
      fbmSales: 0, fbmOrders: 0, fbmQuantity: 0, fbaSales: 0, fbaOrders: 0, fbaQuantity: 0,
      vendorSales: 0, vendorUnits: 0,
      previousYearSales: 0, currentYearSales: 0,
      previousYearOrders: 0, currentYearOrders: 0,
      previousYearQuantity: 0, currentYearQuantity: 0,
    };
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      t.fbmSales += r.fbmSales; t.fbmOrders += r.fbmOrders; t.fbmQuantity += r.fbmQuantity;
      t.fbaSales += r.fbaSales; t.fbaOrders += r.fbaOrders; t.fbaQuantity += r.fbaQuantity;
      t.vendorSales += r.vendorSales; t.vendorUnits += r.vendorUnits;
      t.previousYearSales += r.previousYearSales; t.currentYearSales += r.currentYearSales;
      t.previousYearOrders += r.previousYearOrders; t.currentYearOrders += r.currentYearOrders;
      t.previousYearQuantity += r.previousYearQuantity; t.currentYearQuantity += r.currentYearQuantity;
    }
    t.totalSales = t.currentYearSales;
    t.totalOrders = t.currentYearOrders; // FBM+FBA only - Vendor Orders is N/A, never added
    t.totalQuantity = t.currentYearQuantity; // FBM+FBA Quantity + Vendor Units
    t.vendorOrders = null; // N/A - no valid Vendor order key exists in the source database
    t.salesChange = safeChange(t.currentYearSales, t.previousYearSales);
    t.orderChange = safeChange(t.currentYearOrders, t.previousYearOrders);
    t.quantityChange = safeChange(t.currentYearQuantity, t.previousYearQuantity);
    t.achievementPct = safeAchievePct(t.currentYearSales, t.previousYearSales * TARGET_MULT);
    t.achievementOrdersPct = safeAchievePct(t.currentYearOrders, t.previousYearOrders * TARGET_MULT);
    t.achievementQuantityPct = safeAchievePct(t.currentYearQuantity, t.previousYearQuantity * TARGET_MULT);
    return t;
  }

  // =====================================================================
  // v5: TRUE ASIN-LEVEL grain (REQ-02-D01). One row per ASIN - SKU is not
  // part of the row key, the grouping, or any output field. Orders/Sales
  // are summed directly from a daily_aggregates_asin index that was
  // already grouped by (date, ASIN) at the SQL layer (see
  // extract_uawso_v5_asin_level.py) - NOT summed up from (date,ASIN,SKU)
  // partitions. This is a structural fix, not just a display change: see
  // 03_DISCOVERY\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md
  // Section 8 for why the two are not equivalent. Vendor values need no
  // special dedup logic here (unlike v3/v4's isVendorRow gate) because
  // there is exactly one row per ASIN already, so Vendor simply adds into
  // that row. Additive only - does not alter any v1/v2/v3/v4 function
  // above, so v001/v002 HTML (which have v3/v4 baked in verbatim) are
  // completely unaffected by this addition.
  //
  // 2026-07-15 SAME-DAY AMENDMENT (REQ-02-D01 Section 3.2): the report now
  // shows Sales and Orders only - Quantity is removed from this v5 model.
  // Vendor Orders = ordered_units directly (one Vendor Unit = one Vendor
  // Order, NOT a COUNT(DISTINCT order_item_info) calculation - Vendor has
  // no order-item key) and IS included in Total Orders. This changes
  // computeRowsV5/computeTotalV5 and sumRangeByAsinV5 only; v1-v4 functions
  // above remain untouched, so historical v001/v002 HTML is unaffected.
  // =====================================================================

  // ---- Static row identity: one row per assigned ASIN, with a
  // deterministically-selected image (see extract_uawso_v5_asin_level.py -
  // lowest listing_data.id, chosen in SQL, never re-chosen here). --------
  function buildCanonicalRowsV5(productMasterAsinLevel) {
    var rows = [];
    for (var i = 0; i < productMasterAsinLevel.length; i++) {
      var p = productMasterAsinLevel[i];
      rows.push({
        asin: p.asin,
        imageUrl: p.image_url || null,
        productTitle: p.product_title || null,
        rowType: "ASIN",
      });
    }
    return rows;
  }

  // ---- FBM/FBA sums at ASIN grain - index rows are ALREADY (date,asin)
  // grouped (not date,asin,sku then summed here). Quantity fields from the
  // source rows (fbm_quantity/fba_quantity) are intentionally not summed
  // here - Quantity is not part of the v5 report model (2026-07-15
  // amendment, REQ-02-D01 Section 3.2). --------------------------------
  function sumRangeByAsinV5(index, startStr, endStr) {
    var map = {}; // asin -> {fbmSales,fbmOrders,fbaSales,fbaOrders}
    for (var i = 0; i < index.dates.length; i++) {
      var d = index.dates[i];
      if (d < startStr || d > endStr) continue;
      var rows = index.byDate[d];
      for (var j = 0; j < rows.length; j++) {
        var r = rows[j], key = r.asin;
        if (!map[key]) map[key] = { fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0 };
        map[key].fbmSales += r.fbm_sales;
        map[key].fbmOrders += r.fbm_orders;
        map[key].fbaSales += r.fba_sales;
        map[key].fbaOrders += r.fba_orders;
      }
    }
    return map;
  }

  function computeRowsV5(canonicalRows, curSplit, prevSplit, curVendor, prevVendor) {
    var rows = [];
    for (var i = 0; i < canonicalRows.length; i++) {
      var c = canonicalRows[i];
      var cs = curSplit[c.asin] || EMPTY_SPLIT_V4;
      var ps = prevSplit[c.asin] || EMPTY_SPLIT_V4;
      // No isVendorRow gate needed - exactly one row per ASIN, so Vendor
      // is attached directly and is structurally impossible to duplicate.
      var cv = curVendor[c.asin] || EMPTY_VENDOR_V4;
      var pv = prevVendor[c.asin] || EMPTY_VENDOR_V4;

      // Vendor Orders = Vendor ordered_units directly (one Vendor Unit =
      // one Vendor Order) - 2026-07-15 same-day amendment, REQ-02-D01
      // Section 3.2. Not a COUNT(DISTINCT order_item_info) calculation -
      // Vendor has no order-item key, so this is a direct 1:1 mapping, not
      // an equivalent count. Vendor Orders ARE now included in Total Orders.
      var cyVendorOrders = cv.vendorUnits;
      var pyVendorOrders = pv.vendorUnits;

      var cyOrders = cs.fbmOrders + cs.fbaOrders + cyVendorOrders;
      var pyOrders = ps.fbmOrders + ps.fbaOrders + pyVendorOrders;
      var cySales = cs.fbmSales + cs.fbaSales + cv.vendorSales;
      var pySales = ps.fbmSales + ps.fbaSales + pv.vendorSales;

      var salesTarget = pySales * TARGET_MULT;
      var orderTarget = pyOrders * TARGET_MULT;
      var bothZero = pySales === 0 && cySales === 0;

      rows.push({
        asin: c.asin, imageUrl: c.imageUrl, productTitle: c.productTitle, rowType: c.rowType,
        fbmSales: cs.fbmSales, fbmOrders: cs.fbmOrders,
        fbaSales: cs.fbaSales, fbaOrders: cs.fbaOrders,
        vendorSales: cv.vendorSales, vendorOrders: cyVendorOrders,
        totalSales: cySales, totalOrders: cyOrders,
        previousYearSales: pySales, currentYearSales: cySales,
        previousYearOrders: pyOrders, currentYearOrders: cyOrders,
        salesChange: safeChange(cySales, pySales),
        orderChange: safeChange(cyOrders, pyOrders),
        trend: trendOf(cySales, pySales),
        achievementPct: safeAchievePct(cySales, salesTarget),
        achievementOrdersPct: safeAchievePct(cyOrders, orderTarget),
        improvementStatus: bothZero ? "NOT IMPROVED" : null,
      });
    }
    return rows;
  }

  function computeTotalV5(rows) {
    var t = {
      fbmSales: 0, fbmOrders: 0, fbaSales: 0, fbaOrders: 0,
      vendorSales: 0, vendorOrders: 0,
      previousYearSales: 0, currentYearSales: 0,
      previousYearOrders: 0, currentYearOrders: 0,
    };
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      t.fbmSales += r.fbmSales; t.fbmOrders += r.fbmOrders;
      t.fbaSales += r.fbaSales; t.fbaOrders += r.fbaOrders;
      t.vendorSales += r.vendorSales; t.vendorOrders += r.vendorOrders;
      t.previousYearSales += r.previousYearSales; t.currentYearSales += r.currentYearSales;
      t.previousYearOrders += r.previousYearOrders; t.currentYearOrders += r.currentYearOrders;
    }
    t.totalSales = t.currentYearSales;
    t.totalOrders = t.currentYearOrders;
    t.salesChange = safeChange(t.currentYearSales, t.previousYearSales);
    t.orderChange = safeChange(t.currentYearOrders, t.previousYearOrders);
    t.achievementPct = safeAchievePct(t.currentYearSales, t.previousYearSales * TARGET_MULT);
    t.achievementOrdersPct = safeAchievePct(t.currentYearOrders, t.previousYearOrders * TARGET_MULT);
    return t;
  }

  return {
    parseDate: parseDate, fmtDate: fmtDate, addDays: addDays, shiftOneYearBack: shiftOneYearBack,
    mondayOfWeek: mondayOfWeek, firstOfMonth: firstOfMonth, lastOfMonth: lastOfMonth,
    buildDailyIndex: buildDailyIndex, sumRange: sumRange,
    safeChange: safeChange, safeAchievePct: safeAchievePct, trendOf: trendOf,
    computeRows: computeRows, computeTotal: computeTotal, resolvePeriod: resolvePeriod,
    isIncludedOrderStatus: isIncludedOrderStatus,
    // v2
    buildDailyIndexSplit: buildDailyIndexSplit, sumRangeSplitByAsin: sumRangeSplitByAsin,
    periodsOverlap: periodsOverlap, sumVendorRange: sumVendorRange,
    computeRowsV2: computeRowsV2, computeTotalV2: computeTotalV2,
    // v3 - corrected ASIN+SKU grain (used by the shipped v001 HTML)
    buildCanonicalRows: buildCanonicalRows, sumRangeSplitByAsinSku: sumRangeSplitByAsinSku,
    computeRowsV3: computeRowsV3, computeTotalV3: computeTotalV3,
    // v4 - Ordered Product Sales / Total Orders / Total Quantity (v002)
    periodsOverlapV4: periodsOverlapV4, sumVendorRangeV4: sumVendorRangeV4,
    sumRangeSplitByAsinSkuV4: sumRangeSplitByAsinSkuV4,
    computeRowsV4: computeRowsV4, computeTotalV4: computeTotalV4,
    // v5 - true ASIN-level grain, Image column (REQ-02-D01)
    buildCanonicalRowsV5: buildCanonicalRowsV5, sumRangeByAsinV5: sumRangeByAsinV5,
    computeRowsV5: computeRowsV5, computeTotalV5: computeTotalV5,
  };
}));
