"""
Per-run evidence and structured run-state writers for uawso_daily.

Run-state JSON (05_IMPLEMENTATION/runtime/uawso_daily/state/<run_id>.json)
is written from RunResult.to_dict() only - that dataclass has no field for
any credential/connection-string value, so there is nothing to redact here;
the guarantee is structural (by field absence), not by a filter applied at
write time.
"""
import json
import os

from . import config as automation_config


def write_run_state(result) -> str:
    automation_config.ensure_runtime_dirs()
    path = os.path.join(automation_config.STATE_DIR, f"{result.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    return path


def write_run_evidence(result, validation_report=None, extra_sections=None) -> str:
    lines = [f"# UAWSO Daily Automation Run Evidence — {result.run_id}", ""]
    for label, value in [
        ("run_id", result.run_id), ("command", result.command),
        ("started_at", result.started_at), ("finished_at", result.finished_at),
        ("timezone", result.timezone), ("run_date", result.run_date),
        ("report_start_date", result.report_start_date), ("report_end_date", result.report_end_date),
        ("version", result.version), ("output_path", result.output_path),
        ("source_max_date", result.source_max_date), ("assigned_asin_count", result.assigned_asin_count),
        ("extraction_counts", result.extraction_counts), ("kpi_totals", result.kpi_totals),
        ("html_sha256", result.html_sha256), ("publication_action", result.publication_action),
        ("ph_task_row_id", result.ph_task_row_id), ("final_status", result.final_status),
    ]:
        lines.append(f"- {label}: {value}")
    if result.failure_code:
        lines.append(f"- failure_code: {result.failure_code}")
        lines.append(f"- failure_detail: {result.failure_detail}")
    lines.append("")

    if validation_report is not None:
        lines.append("## Validation gate results")
        lines.append("")
        for l in validation_report.to_lines():
            lines.append(f"- {l}")
        lines.append("")
        lines.append(f"Overall validation: {'PASS' if validation_report.passed else 'FAIL'}")
        lines.append("")

    if extra_sections:
        for title, content in extra_sections.items():
            lines.append(f"## {title}")
            lines.append("")
            lines.append(content)
            lines.append("")

    lines.append("## Verdict")
    lines.append("")
    lines.append("PASS" if result.exit_code() == 0 else "FAIL")

    os.makedirs(automation_config.EVIDENCE_DIR, exist_ok=True)
    path = os.path.join(automation_config.EVIDENCE_DIR, f"{result.run_date}_uawso_daily_{result.run_id}.md")
    if os.path.exists(path):
        raise RuntimeError(f"STOP: evidence file already exists, refusing to overwrite: {path}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
