"""Status Effects v2 (ADR-0179).

Adds 4 new effects: Bleed, Fatigue, Confused, Terrified.
Each has a type, duration, and value.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StatusEffectV2:
    """A single status effect v2 instance."""

    id: str
    effect_type: str
    name: str
    duration_ms: int
    value: float


STATUS_V2_REGISTRY: dict[str, StatusEffectV2] = {
    "bleed": StatusEffectV2(
        id="bleed",
        effect_type="bleed",
        name="BLEED",
        duration_ms=5000,
        value=5.0,
    ),
    "fatigue": StatusEffectV2(
        id="fatigue",
        effect_type="fatigue",
        name="FATIGUE",
        duration_ms=8000,
        value=-0.5,
    ),
    "confused": StatusEffectV2(
        id="confused",
        effect_type="confused",
        name="CONFUSED",
        duration_ms=6000,
        value=0.25,
    ),
    "terrified": StatusEffectV2(
        id="terrified",
        effect_type="terrified",
        name="TERRIFIED",
        duration_ms=4000,
        value=0.25,
    ),
}


def get_status_v2(effect_id: str) -> StatusEffectV2 | None:
    """Return status effect v2 by id."""
    return STATUS_V2_REGISTRY.get(effect_id)


def list_status_v2() -> tuple[StatusEffectV2, ...]:
    """Return all status effects v2."""
    return tuple(STATUS_V2_REGISTRY.values())


def get_status_v2_by_type(effect_type: str) -> tuple[StatusEffectV2, ...]:
    """Return all status effects v2 of a given type."""
    return tuple(e for e in STATUS_V2_REGISTRY.values() if e.effect_type == effect_type)


def get_status_v2_count() -> int:
    """Return the number of status effects v2."""
    return len(STATUS_V2_REGISTRY)


def has_status_v2(effect_id: str) -> bool:
    """Return True if a status effect v2 exists."""
    return effect_id in STATUS_V2_REGISTRY


def make_status_v2(effect_type: str, duration_ms: int = 0, value: float = 0.0) -> StatusEffectV2:
    """Create a status effect v2 instance with overrides."""
    template = STATUS_V2_REGISTRY.get(effect_type)
    if template is None:
        raise ValueError(f"Unknown status effect type: {effect_type}")
    if duration_ms <= 0:
        duration_ms = template.duration_ms
    return StatusEffectV2(
        id=template.id,
        effect_type=template.effect_type,
        name=template.name,
        duration_ms=duration_ms,
        value=value if value != 0.0 else template.value,
    )


def apply_bleed(duration_ms: int = 5000) -> StatusEffectV2:
    """Create a bleed status effect."""
    return make_status_v2("bleed", duration_ms=duration_ms)


def apply_fatigue(duration_ms: int = 8000) -> StatusEffectV2:
    """Create a fatigue status effect."""
    return make_status_v2("fatigue", duration_ms=duration_ms)


def apply_confused(duration_ms: int = 6000) -> StatusEffectV2:
    """Create a confused status effect."""
    return make_status_v2("confused", duration_ms=duration_ms)


def apply_terrified(duration_ms: int = 4000) -> StatusEffectV2:
    """Create a terrified status effect."""
    return make_status_v2("terrified", duration_ms=duration_ms)


__all__ = [
    "STATUS_V2_REGISTRY",
    "StatusEffectV2",
    "apply_bleed",
    "apply_confused",
    "apply_fatigue",
    "apply_terrified",
    "get_status_v2",
    "get_status_v2_by_type",
    "get_status_v2_count",
    "has_status_v2",
    "list_status_v2",
    "make_status_v2",
]
