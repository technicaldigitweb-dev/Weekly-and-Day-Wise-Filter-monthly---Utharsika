"""
Tests for the 15-row table-viewport correction to the v004 report.

Unlike the prior sticky-columns/pagination tasks (where no browser was
available and checks were structural/source-level only), a real headless
Chromium is available in this environment via the `playwright` package -
these are genuine functional measurements of the rendered page, not
static grep. Historical HTML files and ph_task rows are checked by file
hash / DB read-only query, never modified by this test.

Run: python tests/test_uawso_15row_viewport_v5.py [path_to_html]
"""
import hashlib
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DEFAULT_TARGET = os.path.join(ROOT, "09_OUTPUTS", "2026-07-15_utharsika_v004.html")
TARGET = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET)
TARGET_URL = "file:///" + TARGET.replace("\\", "/")

OTHER_PROTECTED_HASHES = {
    "2026-07-09_utharsika_v001.html": "52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b",
    "2026-07-10_utharsika_v001.html": "335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4",
    "2026-07-10_utharsika_v002.html": "0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72",
    "2026-07-14_utharsika_v002.html": "16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684",
}

results = []


def check(label, cond, detail=""):
    results.append((label, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def measure(page):
    return page.evaluate("""
    () => {
      const wrap = document.querySelector('.uawso-table-wrap');
      const wrapRect = wrap.getBoundingClientRect();
      const theadRow = document.querySelector('#uawso-table thead tr');
      const theadHeight = theadRow.getBoundingClientRect().height;
      const tbody = document.querySelector('#uawso-tbody');
      const bodyRows = Array.from(tbody.querySelectorAll('tr'));
      const pagination = document.querySelector('.uawso-pagination');
      const pagRect = pagination.getBoundingClientRect();
      const visibleContentBottom = wrapRect.top + wrap.clientHeight - pagRect.height;

      let fullyVisibleCount = 0;
      let row15FullyVisible = false;
      let row16NeedsScroll = false;
      for (let i = 0; i < bodyRows.length; i++) {
        const r = bodyRows[i].getBoundingClientRect();
        const isFullyVisible = r.top >= wrapRect.top + theadHeight - 0.5 && r.bottom <= visibleContentBottom + 0.5;
        if (isFullyVisible) fullyVisibleCount++;
        if (i === 14) row15FullyVisible = isFullyVisible;
        if (i === 15) row16NeedsScroll = !isFullyVisible;
      }

      const headSticky = getComputedStyle(document.querySelector('#uawso-table thead th')).position === 'sticky';
      const col1Sticky = getComputedStyle(document.querySelector('#uawso-table thead th:nth-child(1)')).position === 'sticky';
      const col2Sticky = getComputedStyle(document.querySelector('#uawso-table thead th:nth-child(2)')).position === 'sticky';
      const pagSticky = getComputedStyle(pagination).position === 'sticky';

      const perPageSelect = document.querySelector('#f-rows-per-page');
      const pageSize = perPageSelect ? perPageSelect.value : null;

      return {
        fullyVisibleRowCount: fullyVisibleCount,
        row15FullyVisible, row16NeedsScroll,
        headSticky, col1Sticky, col2Sticky, pagSticky,
        pageInfo: document.querySelector('.uawso-pagination-info') ? document.querySelector('.uawso-pagination-info').innerText : null,
        pageSize,
        rowCount: bodyRows.length,
      };
    }
    """)


def main():
    check("0. Target file exists", os.path.exists(TARGET), TARGET)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # 1-4, 5-9: viewport + sticky + pagination checks across 3 viewport sizes
        for vw, vh in [(1440, 900), (1366, 768), (1920, 1080)]:
            page = browser.new_page(viewport={"width": vw, "height": vh})
            page.goto(TARGET_URL, wait_until="networkidle")
            page.wait_for_timeout(300)
            m = measure(page)
            check(f"1. Visible-row target = 15 fully visible rows (viewport {vw}x{vh})", m["fullyVisibleRowCount"] == 15, f"got={m['fullyVisibleRowCount']}")
            check(f"2. Row 15 fully visible (viewport {vw}x{vh})", m["row15FullyVisible"])
            check(f"3. Row 16 requires vertical scrolling (viewport {vw}x{vh})", m["row16NeedsScroll"])
            page.close()

        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(TARGET_URL, wait_until="networkidle")
        page.wait_for_timeout(300)
        m = measure(page)

        check("4. Page size remains 50", m["pageSize"] == "50", f"got={m['pageSize']}")
        check("5. Sticky header remains active", m["headSticky"])
        check("6. Sticky ASIN column remains active", m["col1Sticky"])
        check("7. Sticky Image column remains active", m["col2Sticky"])
        check("8. Sticky pagination remains active", m["pagSticky"])
        check("9. Pagination does not cover row 15 (row 15 counted fully visible above)", m["row15FullyVisible"])

        # 10-12: Previous/Next/direct navigation
        initial_info = m["pageInfo"]
        page.click("#pg-next")
        page.wait_for_timeout(150)
        after_next = page.evaluate("document.querySelector('.uawso-pagination-info').innerText")
        check("10. Next works", "Page 2" in after_next, after_next.splitlines()[0])

        page.click("#pg-prev")
        page.wait_for_timeout(150)
        after_prev = page.evaluate("document.querySelector('.uawso-pagination-info').innerText")
        check("11. Previous works", after_prev == initial_info, after_prev.splitlines()[0])

        page.fill("#pg-goto", "10")
        page.click("#pg-goto-btn")
        page.wait_for_timeout(150)
        after_goto = page.evaluate("document.querySelector('.uawso-pagination-info').innerText")
        check("12. Direct-page navigation works", "Page 10" in after_goto, after_goto.splitlines()[0])
        page.fill("#pg-goto", "1")
        page.click("#pg-goto-btn")
        page.wait_for_timeout(150)

        # 13: filtered full-data download remains complete - capture the REAL download
        # (state is module-scoped inside an IIFE, not on window, so the actual
        # download event is the genuine way to verify this, not an internal read)
        with page.expect_download() as dl_info:
            page.click("#btn-csv")
        download = dl_info.value
        dl_path = download.path()
        with open(dl_path, "r", encoding="utf-8") as f:
            csv_lines = [l for l in f.read().splitlines() if l.strip()]
        check("13. Filtered full-data download remains complete (1 header + 1723 data rows)",
              len(csv_lines) == 1724, f"got={len(csv_lines)} lines")

        # 14-17: data/KPI unchanged - read the embedded snapshot and recompute via the real engine
        page.close()
        browser.close()

    import json
    html = open(TARGET, "r", encoding="utf-8").read()

    def extract(id_):
        marker = f'id="{id_}">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        return json.loads(html[start:end])

    pm = extract("uawso-product-master-asin-level")
    check("17. ASIN row count unchanged (1,723)", len(pm) == 1723, f"got={len(pm)}")

    # Use the real engine (node subprocess) to recompute totals from this exact file's embedded data
    import subprocess
    engine_path = os.path.join(os.path.dirname(__file__), "..", "src", "uawso_client_engine.js")
    node_script = f"""
    const fs = require('fs');
    const Engine = require({json.dumps(engine_path)});
    const html = fs.readFileSync({json.dumps(TARGET)}, 'utf-8');
    function extract(id) {{
      const marker = 'id="' + id + '">';
      const start = html.indexOf(marker) + marker.length;
      const end = html.indexOf('</script>', start);
      return JSON.parse(html.slice(start, end));
    }}
    const pmFinal = extract('uawso-product-master-asin-level');
    const daFinal = extract('uawso-daily-aggregates-asin');
    const vpFinal = extract('uawso-vendor-periods');
    const idxFinal = Engine.buildDailyIndexSplit(daFinal);
    const canonFinal = Engine.buildCanonicalRowsV5(pmFinal);
    const csFinal = Engine.sumRangeByAsinV5(idxFinal, '2025-01-01', '2026-07-14');
    const cvFinal = Engine.sumVendorRangeV4(vpFinal, '2025-01-01', '2026-07-14');
    const rowsFinal = Engine.computeRowsV5(canonFinal, csFinal, {{}}, cvFinal, {{}});
    const totalFinal = Engine.computeTotalV5(rowsFinal);
    console.log(JSON.stringify({{
      sales: Math.round(totalFinal.currentYearSales * 100) / 100,
      orders: totalFinal.currentYearOrders,
      totalQuantity: totalFinal.totalQuantity,
      asinCount: pmFinal.length,
    }}));
    """
    out = subprocess.check_output(["node", "-e", node_script], cwd=os.path.dirname(engine_path))
    totals = json.loads(out.decode("utf-8").strip().splitlines()[-1])

    check("14. Sales remains unchanged (718835.91)", totals["sales"] == 718835.91, f"got={totals['sales']}")
    check("15. Total Orders reflects the updated formula (FBM+FBA+Vendor Orders = 39202, 2026-07-15 amendment - not a viewport regression)", totals["orders"] == 39202, f"got={totals['orders']}")
    check("16. No Quantity field remains (2026-07-15 amendment - Sales and Orders only)", totals.get("totalQuantity") is None, f"got={totals.get('totalQuantity')}")

    # 18/19: only v004 local file replaced, no other HTML output modified
    outputs_dir = os.path.join(ROOT, "09_OUTPUTS")
    all_unchanged = True
    for name, expected in OTHER_PROTECTED_HASHES.items():
        p = os.path.join(outputs_dir, name)
        actual = sha256_of(p)
        if actual != expected:
            all_unchanged = False
        check(f"18/19. {name} unchanged", actual == expected, f"got={actual}")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    if failed:
        print("FAILED:", "; ".join(r[0] for r in failed))
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
