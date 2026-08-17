"""Edge case tests for data/loader.py (ADR-0060 Edge case 분석).

Covers all branches of load_json(path):
- File missing → returns empty dict (defensive)
- File exists + valid JSON → returns parsed dict
- File exists + nested JSON → returns nested dict
- File exists + invalid JSON → raises JSONDecodeError
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.data.loader import load_json


class TestLoadJson:
    """load_json(path) — JSON file loader with defensive missing-file handling."""

    def test_returns_empty_dict_when_file_missing(self, tmp_path: Path) -> None:
        """Missing file → empty dict (defensive, no exception raised)."""
        missing_path = tmp_path / "does_not_exist.json"
        assert not missing_path.exists()
        assert load_json(missing_path) == {}

    def test_loads_valid_flat_json(self, tmp_path: Path) -> None:
        """Valid JSON file → parsed dict."""
        path = tmp_path / "data.json"
        path.write_text('{"key": "value", "number": 42}', encoding="utf-8")
        result = load_json(path)
        assert result == {"key": "value", "number": 42}

    def test_loads_nested_json(self, tmp_path: Path) -> None:
        """Nested JSON (dict containing list) → fully parsed structure preserved."""
        path = tmp_path / "nested.json"
        path.write_text(
            '{"items": [1, 2, 3], "nested": {"inner": "value"}}',
            encoding="utf-8",
        )
        result = load_json(path)
        assert result == {"items": [1, 2, 3], "nested": {"inner": "value"}}

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON → raises JSONDecodeError (NOT silent fallback to {})."""
        path = tmp_path / "broken.json"
        path.write_text("{invalid json, no closing brace", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_json(path)

    def test_loads_empty_json_object(self, tmp_path: Path) -> None:
        """Empty JSON object {} → returns empty dict (not None, not error)."""
        path = tmp_path / "empty.json"
        path.write_text("{}", encoding="utf-8")
        result = load_json(path)
        assert result == {}

    def test_loads_empty_json_array(self, tmp_path: Path) -> None:
        """Empty JSON array [] → returns empty list (note: function signature is dict but json.load accepts arrays)."""
        path = tmp_path / "array.json"
        path.write_text("[]", encoding="utf-8")
        result = load_json(path)
        assert result == []
