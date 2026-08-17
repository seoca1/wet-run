"""Entry point for `python -m wet_run`."""

from __future__ import annotations

import sys

from wet_run.engine.app import main

if __name__ == "__main__":
    sys.exit(main())
