"""
Staged-then-atomic HTML rendering for uawso_daily.

Imports and calls the existing, approved src/dashboard_renderer.render_dashboard_v5()
directly - no template-filling logic is duplicated here. Sequence:
  1. render in memory
  2. verify zero unresolved __UAWSO_X__ placeholders remain
  3. write to a run-scoped staging file (05_IMPLEMENTATION/runtime/uawso_daily/staging/<run_id>/)
  4. hash the staging file
  5. atomically promote to 09_OUTPUTS/<run_date>_<user>_v<NNN>.html via a
     temp-file-write + hash-verify + os.rename (never os.replace - rename
     fails outright if the target already exists, which is the desired
     OUTPUT_VERSION_ALREADY_EXISTS guard, not something to catch-and-ignore)
"""
import hashlib
import os
import sys

IMPL_ROOT = os.path.join(os.path.dirname(__file__), "..")
if IMPL_ROOT not in sys.path:
    sys.path.insert(0, IMPL_ROOT)

from src import dashboard_renderer  # noqa: E402

from . import config as automation_config
from . import versioning


class RenderValidationError(Exception):
    """Raised when the rendered HTML still contains unresolved placeholders."""


class OutputVersionAlreadyExistsError(Exception):
    """Raised when the target 09_OUTPUTS path already exists at promotion time."""


def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render_report_html(*, run_id, assigned_asin_count, product_master_asin_level,
                        daily_aggregates_asin, vendor_periods, image_covered_count,
                        no_image_count, multi_image_count, run_date, report_start, report_end,
                        version, generated_timestamp, project_name="Utharsika Amazon UK Daily, "
                        "Weekly and Month-to-Date Sales and Orders Report", project_code="UAWSO",
                        assigned_user="utharsika") -> str:
    html = dashboard_renderer.render_dashboard_v5(
        project_name=project_name, project_code=project_code, assigned_user=assigned_user,
        version=f"v{version:03d}", template_version="5.5.0-amazon-only-orders",
        generated_timestamp=generated_timestamp,
        latest_completed_date=report_end.isoformat(),
        history_start=report_start.isoformat(), history_end=report_end.isoformat(),
        selectable_start=f"{report_end.year}-01-01", selectable_end=report_end.isoformat(),
        assigned_asin_count=assigned_asin_count,
        product_master_asin_level=product_master_asin_level,
        daily_aggregates_asin=daily_aggregates_asin,
        vendor_periods=vendor_periods,
        image_covered_count=image_covered_count,
        no_image_count=no_image_count,
        multi_image_count=multi_image_count,
    )
    unresolved = dashboard_renderer.verify_no_placeholders(html)
    if unresolved:
        raise RenderValidationError(f"Unresolved placeholders after render: {unresolved}")
    return html


def write_staging_file(run_id: str, html_text: str) -> str:
    staging_dir = os.path.join(automation_config.STAGING_ROOT_DIR, run_id)
    os.makedirs(staging_dir, exist_ok=True)
    staging_path = os.path.join(staging_dir, "report.staging.html")
    with open(staging_path, "wb") as f:
        f.write(html_text.encode("utf-8"))
    return staging_path


def promote_to_output(staging_path: str, run_date, version: int, username: str = "utharsika") -> str:
    """
    Atomically promotes an already-validated staging file to its final,
    never-existed-before 09_OUTPUTS path. Raises OutputVersionAlreadyExistsError
    if the target already exists (idempotency case E / duplicate-guard).
    """
    target_path = versioning.output_path_for(run_date, version, username)
    if os.path.exists(target_path):
        raise OutputVersionAlreadyExistsError(target_path)

    staging_hash = sha256_of_file(staging_path)
    temp_path = target_path + ".tmp"
    with open(staging_path, "rb") as src, open(temp_path, "wb") as dst:
        dst.write(src.read())
    temp_hash = sha256_of_file(temp_path)
    if temp_hash != staging_hash:
        os.remove(temp_path)
        raise RenderValidationError(
            f"Temp file hash ({temp_hash}) does not match staging hash ({staging_hash}) - refusing to promote."
        )

    os.rename(temp_path, target_path)  # fails outright if target now exists (race-safe on top of the pre-check)

    final_hash = sha256_of_file(target_path)
    if final_hash != staging_hash:
        raise RenderValidationError(
            f"Final hash ({final_hash}) does not match staging hash ({staging_hash}) after promotion."
        )
    return target_path
