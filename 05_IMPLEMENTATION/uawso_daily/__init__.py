"""
UAWSO Daily Automation System.

Complete, reusable, unattended daily pipeline for the Utharsika Amazon UK
Daily, Weekly and Month-to-Date Sales and Orders Report (UAWSO):
fresh PostgreSQL extraction -> validation -> HTML generation -> ph_task
publication, callable as a single stable command:

    python -m uawso_daily update-for-today

See uawso_daily/README.md for full documentation. This package is
prepared and locally tested only - no cron/systemd job is installed or
enabled by this package itself (see 05_IMPLEMENTATION/deployment/).
"""

__version__ = "1.0.0"
