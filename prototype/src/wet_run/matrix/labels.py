"""Zone label helper (i18n-aware)."""

from __future__ import annotations

from ..i18n import Translator
from .node import ZoneDepth

_ZONE_KEY: dict[ZoneDepth, str] = {
    ZoneDepth.SURFACE: "zone.surface",
    ZoneDepth.MID: "zone.mid",
    ZoneDepth.CORE: "zone.core",
    ZoneDepth.TA: "zone.ta",
}


def zone_label(t: Translator, zone: ZoneDepth) -> str:
    """Return a translated label for a zone (falls back to the zone value)."""
    key = _ZONE_KEY.get(zone, "zone.unknown")
    label = t(key)
    return label if label != key else zone.value.capitalize()
