"""Portrait manager (ADR-0011).

ASCII / Unicode symbols + colors, loaded from JSON.
Pillar 2: cyberspace-only — meatspace persons are NOT shown.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typing_extensions import override

from ..combat.palette import (
    CYAN_PURE,
    GLITCH_COLOR,
    GRAY_MID_LIGHT,
    GREEN_PURE,
    HIT_FLASH_COLOR,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
)

# Color name to RGB tuple mapping
COLOR_NAMES: dict[str, tuple[int, int, int]] = {
    "red": (255, 0, 64),
    "green": GREEN_PURE,
    "blue": (0, 128, 255),
    "yellow": ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    "magenta": GLITCH_COLOR,
    "cyan": CYAN_PURE,
    "white": HIT_FLASH_COLOR,
    "gray": GRAY_MID_LIGHT,
    "dark_red": (128, 0, 32),
}


def parse_color(value: str | tuple[int, int, int]) -> tuple[int, int, int]:
    """Convert a color name or tuple to an RGB tuple."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    if isinstance(value, str):
        return COLOR_NAMES.get(value.lower(), HIT_FLASH_COLOR)
    return HIT_FLASH_COLOR


class PortraitManager:
    """Manages ASCII portraits for entities.

    Loads from `portraits.json` and provides lookups by entity id.
    Cyberspace-only — see ADR-0011 Pillar 2 compliance.
    """

    __slots__ = ("_portraits",)

    def __init__(self, data_dir: Path | None = None) -> None:
        """Create a PortraitManager; load from ``data_dir/portraits.json`` if given."""
        self._portraits: dict[str, dict[str, Any]] = {}
        if data_dir is not None:
            self._load(data_dir)

    def _load(self, data_dir: Path) -> None:
        """Load portraits from ``data_dir/portraits.json`` (silent no-op if missing).

        Each portrait entry is normalised so the ``color`` field becomes
        an RGB tuple via :func:`parse_color`.
        """
        path = data_dir / "portraits.json"
        if not path.exists():
            return
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
        for key, portrait in raw.items():
            portrait = dict(portrait)
            if "color" in portrait:
                portrait["color"] = parse_color(portrait["color"])
            self._portraits[key] = portrait

    def get(self, entity_id: str) -> dict[str, Any]:
        """Get a portrait by entity id. Returns a default if not found."""
        return self._portraits.get(
            entity_id,
            {
                "ascii": "????",
                "color": HIT_FLASH_COLOR,
                "name": entity_id,
            },
        )

    def has(self, entity_id: str) -> bool:
        """Return True if a portrait is registered for this id."""
        return entity_id in self._portraits

    def __len__(self) -> int:
        """Return the count of registered portraits."""
        return len(self._portraits)

    @override
    def __repr__(self) -> str:
        """Return a debug representation including portrait count."""
        return f"PortraitManager({len(self._portraits)} portraits)"
