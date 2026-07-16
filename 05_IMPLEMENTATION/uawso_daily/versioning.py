"""
Filesystem-based version inspection for uawso_daily.

Per the task's explicit instruction, version selection is based on
INSPECTING EXISTING FILES on disk, not on 05_IMPLEMENTATION/state/version_state.json
(that file only tracks the manual-publish scripts' own history and has not
reliably reflected every version actually published across this project -
see the automation-system evidence file for the specific gaps found).
"""
import glob
import os
import re
from datetime import date

from . import config as automation_config

_OUTPUT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_([a-zA-Z0-9]+)_v(\d{3})\.html$")


def existing_versions_for_date(run_date: date, username: str = "utharsika", output_dir: str = None) -> list:
    """Returns the sorted list of version ints already present in 09_OUTPUTS for this run_date, any status."""
    output_dir = output_dir or automation_config.OUTPUTS_DIR
    prefix = f"{run_date.isoformat()}_{username}_v"
    versions = []
    for path in glob.glob(os.path.join(output_dir, f"{prefix}*.html")):
        m = _OUTPUT_RE.match(os.path.basename(path))
        if m and m.group(1) == run_date.isoformat() and m.group(2) == username:
            versions.append(int(m.group(3)))
    return sorted(versions)


def next_version_for_date(run_date: date, username: str = "utharsika", output_dir: str = None) -> int:
    existing = existing_versions_for_date(run_date, username, output_dir)
    return (max(existing) + 1) if existing else 1


def output_path_for(run_date: date, version: int, username: str = "utharsika", output_dir: str = None) -> str:
    output_dir = output_dir or automation_config.OUTPUTS_DIR
    return os.path.join(output_dir, f"{run_date.isoformat()}_{username}_v{version:03d}.html")


def output_exists(run_date: date, version: int, username: str = "utharsika", output_dir: str = None) -> bool:
    return os.path.exists(output_path_for(run_date, version, username, output_dir))
