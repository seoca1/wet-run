"""Translation manager (ADR-0010).

English is primary. Korean is supplementary translation.
Display mode: Off (English only, default) / Subtitle / Replace.
"""

from __future__ import annotations

import json
import string
from pathlib import Path
from typing import Any

from typing_extensions import override


def _format_template(template: str, kwargs: dict[str, Any]) -> str:
    """Format ``template`` with ``kwargs``; missing fields render as ``<name>``.

    Unlike ``str.format()``, this never raises — instead unfilled
    placeholders are surfaced as ``<name>`` so the player sees an
    obvious marker rather than a raw ``{name}`` substring. This makes
    missing-translation bugs visible at runtime instead of leaking into
    UI text.
    """
    formatter = string.Formatter()
    parts: list[str] = []
    for literal_text, field_name, format_spec, conversion in formatter.parse(template):
        parts.append(literal_text)
        if field_name is None:
            continue
        # Field reference (e.g. "0" for positional, "name" for kwarg,
        # "obj.attr" for dotted lookup).
        if field_name.isdigit():
            # Positional argument — we don't support positional args here.
            parts.append(f"<{field_name}>")
            continue
        if field_name in kwargs:
            value = kwargs[field_name]
        else:
            parts.append(f"<{field_name}>")
            continue
        # Apply format spec / conversion if present
        try:
            if conversion:
                value = formatter.convert_field(value, conversion)
            if format_spec:
                value = format(value, format_spec)
        except (ValueError, TypeError):
            parts.append(f"<{field_name}>")
            continue
        parts.append(str(value))
    return "".join(parts)


class Translator:
    """Manages translations for a specific language.

    Loads a JSON file (e.g. `en.json`) and provides dotted-key lookup
    with optional format arguments.
    """

    __slots__ = ("lang", "_data")

    def __init__(self, lang: str, data_dir: Path | None = None) -> None:
        """Create a Translator for ``lang``; loads from ``data_dir/{lang}.json`` if given."""
        self.lang = lang
        self._data: dict[str, Any] = {}
        if data_dir is not None:
            self._load(data_dir)

    def _load(self, data_dir: Path) -> None:
        """Load ``{data_dir}/{self.lang}.json`` into ``self._data``.

        Silent no-op if the file is absent (the Translator keeps an
        empty dict and ``t()`` falls back to returning the key itself).
        """
        path = data_dir / f"{self.lang}.json"
        if not path.exists():
            return
        with path.open(encoding="utf-8") as f:
            self._data = json.load(f)

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a dotted key with optional format arguments.

        Falls back to the key itself if not found. Missing format
        arguments render as ``<name>`` (P2 #14) rather than raising
        or leaking raw ``{name}`` placeholders into UI text.
        """
        value: Any = self._data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return key
            value = value[part]
        if not isinstance(value, str):
            return key
        # Always run through _format_template so unfilled placeholders
        # become ``<name>`` markers (visible at runtime) instead of
        # leaking raw ``{name}`` syntax into UI text.
        if "{" in value or "}" in value:
            return _format_template(value, kwargs)
        return value

    def set_locale(self, lang: str, data_dir: Path | None = None) -> None:
        """Switch to a different language. Reloads from ``data_dir`` if given."""
        self.lang = lang
        self._data = {}
        if data_dir is not None:
            self._load(data_dir)

    def __call__(self, key: str, **kwargs: Any) -> str:
        """Shorthand for `t(key, **kwargs)`. Allows `translator("key")`."""
        return self.t(key, **kwargs)

    def has(self, key: str) -> bool:
        """Return True if the key exists in this language."""
        value: Any = self._data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return False
            value = value[part]
        return isinstance(value, str)

    @override
    def __repr__(self) -> str:
        return f"Translator(lang={self.lang!r}, keys={len(self._data)})"
