"""Data file loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file. Returns empty dict if missing or invalid."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]
