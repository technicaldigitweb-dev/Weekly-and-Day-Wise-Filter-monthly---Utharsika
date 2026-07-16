"""
UAWSO interactive-dashboard renderer.

Fills templates/uawso_report_template.html (the canonical, reusable,
filterable single-page dashboard template - original UAWSO design, no
data hardcoded into the template itself) with per-run metadata and two
safely-serialized JSON payloads (product master, daily aggregates).

Template history (2026-07-15 automation build):
As of this build, templates/uawso_report_template.html holds the v4
template content (Ordered Product Sales / Total Orders / Total Quantity,
dynamic status rule support) - this is now the single canonical template
used by BOTH render_dashboard() and render_dashboard_v4(). The prior v3
template that used to live at this exact path (used only to regenerate
the frozen 09_OUTPUTS\\2026-07-10_utharsika_v001.html byte-identically)
was moved to 12_ARCHIVE\\automation_cleanup\\2026-07-15\\templates\\
uawso_report_template_v3_legacy.html - see LEGACY_V3_TEMPLATE_PATH below.
v001 regeneration continues to work unchanged via that archived path.

Safety rules enforced here:
- All HTML-context text values are HTML-escaped (html.escape) before
  substitution, so no injected value can break the surrounding markup.
- JSON payloads are serialized with json.dumps and additionally have
  the substring "</" replaced with "<\\/" so a value that happened to
  contain "</script>" cannot prematurely close the embedding
  <script type="application/json"> tag.
- Placeholders are unique, unambiguous tokens (__UAWSO_X__) that cannot
  collide with real report content (ASINs/SKUs never contain "__").
- After substitution, the caller MUST verify zero placeholders remain
  (see verify_no_placeholders below) before treating the output as final.
"""

import html
import json
import os
import re

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "uawso_report_template.html")
TEMPLATE_PATH_V4 = os.path.join(os.path.dirname(__file__), "..", "templates", "uawso_report_template.html")
TEMPLATE_PATH_V5 = os.path.join(os.path.dirname(__file__), "..", "templates", "uawso_report_template_v5_asin_level.html")
LEGACY_V3_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "12_ARCHIVE", "automation_cleanup", "2026-07-15",
    "templates", "uawso_report_template_v3_legacy.html",
)
ENGINE_JS_PATH = os.path.join(os.path.dirname(__file__), "uawso_client_engine.js")

PLACEHOLDER_PATTERN = re.compile(r"__UAWSO_[A-Z_]+__")


def _safe_json_for_script_tag(value) -> str:
    return json.dumps(value, separators=(",", ":")).replace("</", "<\\/")


def render_dashboard(*, project_name, project_code, assigned_user, version, template_version,
                      generated_timestamp, latest_completed_date, history_start, history_end,
                      selectable_start, selectable_end, assigned_asin_count, assigned_sku_count,
                      product_master_full, daily_aggregates_split, vendor_periods,
                      no_sku_count, total_row_count, sku_row_count, vendor_row_count) -> str:
    # Uses the archived v3 template, not the canonical (now v4-content)
    # TEMPLATE_PATH, so v001 regeneration stays byte-identical - see the
    # module docstring's "Template history" note.
    with open(LEGACY_V3_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    with open(ENGINE_JS_PATH, "r", encoding="utf-8") as f:
        engine_js = f.read()

    head_title = f"UAWSO — {assigned_user} Amazon UK Sales & Orders Dashboard — {latest_completed_date}"

    text_replacements = {
        "__UAWSO_HEAD_TITLE__": html.escape(head_title),
        "__UAWSO_PROJECT_CODE__": html.escape(project_code),
        "__UAWSO_ASSIGNED_USER__": html.escape(assigned_user),
        "__UAWSO_VERSION__": html.escape(version),
        "__UAWSO_TEMPLATE_VERSION__": html.escape(template_version),
        "__UAWSO_GENERATED_TS__": html.escape(generated_timestamp),
        "__UAWSO_LATEST_COMPLETED_DATE__": html.escape(str(latest_completed_date)),
        "__UAWSO_HISTORY_START__": html.escape(str(history_start)),
        "__UAWSO_HISTORY_END__": html.escape(str(history_end)),
        "__UAWSO_SELECTABLE_START__": html.escape(str(selectable_start)),
        "__UAWSO_SELECTABLE_END__": html.escape(str(selectable_end)),
        "__UAWSO_ASSIGNED_ASIN_COUNT__": html.escape(str(assigned_asin_count)),
        "__UAWSO_ASSIGNED_SKU_COUNT__": html.escape(str(assigned_sku_count)),
        "__UAWSO_NO_SKU_COUNT__": html.escape(str(no_sku_count)),
        "__UAWSO_TOTAL_ROW_COUNT__": html.escape(str(total_row_count)),
        "__UAWSO_SKU_ROW_COUNT__": html.escape(str(sku_row_count)),
        "__UAWSO_VENDOR_ROW_COUNT__": html.escape(str(vendor_row_count)),
    }

    json_replacements = {
        "__UAWSO_PRODUCT_MASTER_FULL_JSON__": _safe_json_for_script_tag(product_master_full),
        "__UAWSO_DAILY_AGGREGATES_SPLIT_JSON__": _safe_json_for_script_tag(daily_aggregates_split),
        "__UAWSO_VENDOR_PERIODS_JSON__": _safe_json_for_script_tag(vendor_periods),
    }

    # Raw code injection (not HTML-escaped - this is trusted, project-authored
    # JS source, not user/DB-derived text). Verified separately to contain no
    # literal "</script>" sequence - see render_dashboard's caller-side checks.
    code_replacements = {
        "__UAWSO_ENGINE_JS__": engine_js,
    }

    out = template
    for placeholder, value in {**text_replacements, **json_replacements, **code_replacements}.items():
        out = out.replace(placeholder, value)

    return out


def render_dashboard_v5(*, project_name, project_code, assigned_user, version, template_version,
                         generated_timestamp, latest_completed_date, history_start, history_end,
                         selectable_start, selectable_end, assigned_asin_count,
                         product_master_asin_level, daily_aggregates_asin, vendor_periods,
                         image_covered_count, no_image_count, multi_image_count) -> str:
    """
    v5 renderer (REQ-02-D01) - fills templates/uawso_report_template_v5_asin_level.html
    with the true ASIN-level product master (one row per ASIN, deterministic
    image), ASIN-grain daily aggregates, and vendor periods. Uses the SAME
    engine JS file as render_dashboard_v4() (src/uawso_client_engine.js),
    which carries the v5 functions additively alongside v1-v4 - does not
    require, and does not use, a second engine file. Does not touch
    render_dashboard()/render_dashboard_v4() or their template paths.
    """
    with open(TEMPLATE_PATH_V5, "r", encoding="utf-8") as f:
        template = f.read()
    with open(ENGINE_JS_PATH, "r", encoding="utf-8") as f:
        engine_js = f.read()

    head_title = f"UAWSO — {assigned_user} Amazon UK Sales & Orders Dashboard (ASIN-Level) — {latest_completed_date}"

    text_replacements = {
        "__UAWSO_HEAD_TITLE__": html.escape(head_title),
        "__UAWSO_PROJECT_CODE__": html.escape(project_code),
        "__UAWSO_ASSIGNED_USER__": html.escape(assigned_user),
        "__UAWSO_VERSION__": html.escape(version),
        "__UAWSO_TEMPLATE_VERSION__": html.escape(template_version),
        "__UAWSO_GENERATED_TS__": html.escape(generated_timestamp),
        "__UAWSO_LATEST_COMPLETED_DATE__": html.escape(str(latest_completed_date)),
        "__UAWSO_HISTORY_START__": html.escape(str(history_start)),
        "__UAWSO_HISTORY_END__": html.escape(str(history_end)),
        "__UAWSO_SELECTABLE_START__": html.escape(str(selectable_start)),
        "__UAWSO_SELECTABLE_END__": html.escape(str(selectable_end)),
        "__UAWSO_ASSIGNED_ASIN_COUNT__": html.escape(str(assigned_asin_count)),
        "__UAWSO_IMAGE_COVERED_COUNT__": html.escape(str(image_covered_count)),
        "__UAWSO_NO_IMAGE_COUNT__": html.escape(str(no_image_count)),
        "__UAWSO_MULTI_IMAGE_COUNT__": html.escape(str(multi_image_count)),
    }

    json_replacements = {
        "__UAWSO_PRODUCT_MASTER_ASIN_LEVEL_JSON__": _safe_json_for_script_tag(product_master_asin_level),
        "__UAWSO_DAILY_AGGREGATES_ASIN_JSON__": _safe_json_for_script_tag(daily_aggregates_asin),
        "__UAWSO_VENDOR_PERIODS_JSON__": _safe_json_for_script_tag(vendor_periods),
    }

    code_replacements = {
        "__UAWSO_ENGINE_JS__": engine_js,
    }

    out = template
    for placeholder, value in {**text_replacements, **json_replacements, **code_replacements}.items():
        out = out.replace(placeholder, value)

    return out


def verify_no_placeholders(html_text: str):
    """Returns the list of unresolved __UAWSO_X__ tokens still present (empty list = clean)."""
    return sorted(set(PLACEHOLDER_PATTERN.findall(html_text)))


def render_dashboard_v4(*, project_name, project_code, assigned_user, version, template_version,
                         generated_timestamp, latest_completed_date, history_start, history_end,
                         selectable_start, selectable_end, assigned_asin_count, assigned_sku_count,
                         product_master_full, daily_aggregates_split, vendor_periods,
                         no_sku_count, total_row_count, sku_row_count, vendor_row_count) -> str:
    """
    v002 renderer - fills templates/uawso_report_template_v4.html (Ordered
    Product Sales / Total Orders / Total Quantity rules) with the SAME
    engine JS file as render_dashboard() (src/uawso_client_engine.js),
    which carries the v4 functions additively alongside v1/v2/v3 - so
    this does not require, and does not use, a second engine file.
    Does not touch render_dashboard() or TEMPLATE_PATH (v001's path).
    """
    with open(TEMPLATE_PATH_V4, "r", encoding="utf-8") as f:
        template = f.read()
    with open(ENGINE_JS_PATH, "r", encoding="utf-8") as f:
        engine_js = f.read()

    head_title = f"UAWSO — {assigned_user} Amazon UK Sales, Orders & Quantity Dashboard — {latest_completed_date}"

    text_replacements = {
        "__UAWSO_HEAD_TITLE__": html.escape(head_title),
        "__UAWSO_PROJECT_CODE__": html.escape(project_code),
        "__UAWSO_ASSIGNED_USER__": html.escape(assigned_user),
        "__UAWSO_VERSION__": html.escape(version),
        "__UAWSO_TEMPLATE_VERSION__": html.escape(template_version),
        "__UAWSO_GENERATED_TS__": html.escape(generated_timestamp),
        "__UAWSO_LATEST_COMPLETED_DATE__": html.escape(str(latest_completed_date)),
        "__UAWSO_HISTORY_START__": html.escape(str(history_start)),
        "__UAWSO_HISTORY_END__": html.escape(str(history_end)),
        "__UAWSO_SELECTABLE_START__": html.escape(str(selectable_start)),
        "__UAWSO_SELECTABLE_END__": html.escape(str(selectable_end)),
        "__UAWSO_ASSIGNED_ASIN_COUNT__": html.escape(str(assigned_asin_count)),
        "__UAWSO_ASSIGNED_SKU_COUNT__": html.escape(str(assigned_sku_count)),
        "__UAWSO_NO_SKU_COUNT__": html.escape(str(no_sku_count)),
        "__UAWSO_TOTAL_ROW_COUNT__": html.escape(str(total_row_count)),
        "__UAWSO_SKU_ROW_COUNT__": html.escape(str(sku_row_count)),
        "__UAWSO_VENDOR_ROW_COUNT__": html.escape(str(vendor_row_count)),
    }

    json_replacements = {
        "__UAWSO_PRODUCT_MASTER_FULL_JSON__": _safe_json_for_script_tag(product_master_full),
        "__UAWSO_DAILY_AGGREGATES_SPLIT_JSON__": _safe_json_for_script_tag(daily_aggregates_split),
        "__UAWSO_VENDOR_PERIODS_JSON__": _safe_json_for_script_tag(vendor_periods),
    }

    code_replacements = {
        "__UAWSO_ENGINE_JS__": engine_js,
    }

    out = template
    for placeholder, value in {**text_replacements, **json_replacements, **code_replacements}.items():
        out = out.replace(placeholder, value)

    return out
