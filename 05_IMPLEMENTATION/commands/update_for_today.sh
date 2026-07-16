#!/usr/bin/env bash
# UAWSO daily automation - Linux/cron entry point wrapper.
# Invokes the uawso_daily package as a module; contains no business logic
# of its own. Sets the working directory to 05_IMPLEMENTATION so the
# `config` and `src` sibling packages resolve correctly - required because
# cron runs with a minimal environment and an unpredictable starting cwd.
#
# Usage:
#   commands/update_for_today.sh
#   commands/update_for_today.sh --dry-run --verbose
#   commands/update_for_today.sh --no-publish --verbose
#
# Exit code: 0 on any success-family outcome (SUCCESS, ALREADY_COMPLETE,
# DRY_RUN_COMPLETE, NO_PUBLISH_COMPLETE); 1 on any failure code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${IMPL_ROOT}"
exec python3 -m uawso_daily update-for-today "$@"
