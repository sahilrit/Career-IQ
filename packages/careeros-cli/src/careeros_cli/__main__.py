"""Allows `python -m careeros_cli` as an alternative to the `careeros` script."""

from __future__ import annotations

import sys

from careeros_cli.main import main

if __name__ == "__main__":
    sys.exit(main())
