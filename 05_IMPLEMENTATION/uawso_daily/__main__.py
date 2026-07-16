"""
Entry point for `python -m uawso_daily <command>`. Must be invoked with the
current working directory set to 05_IMPLEMENTATION (or with 05_IMPLEMENTATION
on sys.path) so the `config` and `src` sibling packages resolve - see
commands/update_for_today.bat and .sh, which set the working directory
before invoking this.
"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
