"""
UAWSO execution logger.

Appends structured entries to the daily master execution log in the
exact field format mandated by the stage brief. Never accepts a raw
credential value - callers must pass config.redact()'d strings for
anything DB-connection-related.
"""

import os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Asia/Colombo")
except ImportError:
    _TZ = None

FIELDS = [
    "Timestamp", "Timezone", "Step ID", "Milestone", "Action", "Purpose",
    "Working directory", "Command or script", "Script/file path", "Input source",
    "Database object", "Operation type", "Output", "Rows returned or affected",
    "Validation result", "Error or warning", "Retry required", "Status", "Next action",
    "Performed by",
]


def _now_str():
    if _TZ is not None:
        return datetime.now(_TZ).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " (UTC, zoneinfo unavailable)"


class ExecutionLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("# UAWSO Execution Log\n\n")

    def log(self, **kwargs):
        kwargs.setdefault("Timestamp", _now_str())
        kwargs.setdefault("Timezone", "Asia/Colombo")
        kwargs.setdefault("Performed by", "Satheskanth")
        entry_lines = ["\n---\n"]
        for field in FIELDS:
            value = kwargs.get(field, "")
            entry_lines.append(f"**{field}:** {value}\n")
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.writelines(entry_lines)
