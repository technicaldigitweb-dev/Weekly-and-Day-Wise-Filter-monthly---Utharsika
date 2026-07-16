"""
Structured run result and machine-readable failure codes for uawso_daily.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


class Code:
    SUCCESS = "SUCCESS"
    ALREADY_COMPLETE = "ALREADY_COMPLETE"
    SOURCE_NOT_READY = "SOURCE_NOT_READY"
    RUN_ALREADY_IN_PROGRESS = "RUN_ALREADY_IN_PROGRESS"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    OUTPUT_VERSION_ALREADY_EXISTS = "OUTPUT_VERSION_ALREADY_EXISTS"
    DUPLICATE_ACTIVE_OUTPUT = "DUPLICATE_ACTIVE_OUTPUT"
    LOCAL_HTML_VALIDATION_FAILED = "LOCAL_HTML_VALIDATION_FAILED"
    PUBLICATION_FAILED = "PUBLICATION_FAILED"
    POST_PUBLICATION_HASH_MISMATCH = "POST_PUBLICATION_HASH_MISMATCH"
    CRITICAL_POST_COMMIT_MISMATCH = "CRITICAL_POST_COMMIT_MISMATCH"
    DRY_RUN_COMPLETE = "DRY_RUN_COMPLETE"
    NO_PUBLISH_COMPLETE = "NO_PUBLISH_COMPLETE"


# Exit codes: 0 = success-family (SUCCESS, ALREADY_COMPLETE, DRY_RUN_COMPLETE,
# NO_PUBLISH_COMPLETE); 1 = any failure code below.
SUCCESS_CODES = {Code.SUCCESS, Code.ALREADY_COMPLETE, Code.DRY_RUN_COMPLETE, Code.NO_PUBLISH_COMPLETE}


@dataclass
class RunResult:
    run_id: str
    command: str
    started_at: str
    finished_at: Optional[str] = None
    timezone: str = "Asia/Colombo"
    run_date: Optional[str] = None
    report_start_date: Optional[str] = None
    report_end_date: Optional[str] = None
    version: Optional[int] = None
    output_path: Optional[str] = None
    source_max_date: Optional[str] = None
    assigned_asin_count: Optional[int] = None
    extraction_counts: dict = field(default_factory=dict)
    kpi_totals: dict = field(default_factory=dict)
    html_sha256: Optional[str] = None
    publication_action: Optional[str] = None
    ph_task_row_id: Optional[int] = None
    final_status: str = Code.CONFIGURATION_ERROR
    failure_code: Optional[str] = None
    failure_detail: Optional[str] = None
    evidence_path: Optional[str] = None

    def exit_code(self) -> int:
        return 0 if self.final_status in SUCCESS_CODES else 1

    def to_dict(self) -> dict:
        return asdict(self)

    def summary_lines(self):
        lines = [
            f"run_id: {self.run_id}",
            f"command: {self.command}",
            f"final_status: {self.final_status}",
        ]
        if self.report_start_date and self.report_end_date:
            lines.append(f"report_period: {self.report_start_date} -> {self.report_end_date}")
        if self.version is not None:
            lines.append(f"version: v{self.version:03d}")
        if self.output_path:
            lines.append(f"output_path: {self.output_path}")
        if self.assigned_asin_count is not None:
            lines.append(f"assigned_asin_count: {self.assigned_asin_count}")
        if self.kpi_totals:
            lines.append(
                f"totals: Sales={self.kpi_totals.get('total_sales')} "
                f"FBM_Orders={self.kpi_totals.get('fbm_orders')} "
                f"FBA_Orders={self.kpi_totals.get('fba_orders')} "
                f"Vendor_Orders={self.kpi_totals.get('vendor_orders')} "
                f"Total_Orders={self.kpi_totals.get('total_orders')}"
            )
        if self.publication_action:
            lines.append(f"publication_action: {self.publication_action}")
        if self.ph_task_row_id is not None:
            lines.append(f"ph_task_row_id: {self.ph_task_row_id}")
        if self.evidence_path:
            lines.append(f"evidence_path: {self.evidence_path}")
        if self.failure_code:
            lines.append(f"failure_code: {self.failure_code}")
        if self.failure_detail:
            lines.append(f"failure_detail: {self.failure_detail}")
        lines.append("PASS" if self.final_status in SUCCESS_CODES else "FAIL")
        return lines
