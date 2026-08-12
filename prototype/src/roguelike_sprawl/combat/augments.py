"""Wetware Augments (ADR-0173).

Passive cyberware augments. 6 slots, 20+ augments. Augments are TOOLS
(Pillar 4), not stat boosts. Each provides a passive effect.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_AUGMENT_SLOTS = 6


@dataclass(frozen=True, slots=True)
class WetwareAugment:
    """A passive cyberware augment equipped by the player."""

    id: str
    name: str
    description: str
    effect_type: str
    effect_value: float
    tier: int = 1


AUGMENT_REGISTRY: dict[str, WetwareAugment] = {
    aug.id: aug
    for aug in [
        WetwareAugment("adrenal_boost", "Adrenal Boost", "AP regen +1", "ap_regen", 1.0),
        WetwareAugment("reflex_boost", "Reflex Boost", "Speed +10%", "speed", 0.1),
        WetwareAugment("kerenzikov", "Kerenzikov", "Slow time on combat", "slow_time", 1.0),
        WetwareAugment("sandevistan", "Sandevistan", "Slow time on damage", "slow_time", 1.0),
        WetwareAugment("berserk_core", "Berserk Core", "Crit +10% at low HP", "crit", 0.1),
        WetwareAugment("optical_camo", "Optical Camo", "Dodge +15%", "dodge", 0.15),
        WetwareAugment(
            "pain_editor", "Pain Editor", "Damage threshold -10%", "damage_threshold", -0.1
        ),
        WetwareAugment("bioconductor", "Bioconductor", "Healing +25%", "healing", 0.25),
        WetwareAugment("titanium_bones", "Titanium Bones", "Max HP +20", "max_hp", 20.0),
        WetwareAugment(
            "subdermal_armor", "Subdermal Armor", "Shield +1/hit", "shield_per_hit", 1.0
        ),
        WetwareAugment("gorilla_fists", "Gorilla Fists", "Melee +30%", "melee", 0.3),
        WetwareAugment("projectile_launcher", "Projectile Launcher", "Range +20%", "range", 0.2),
        WetwareAugment("cyberdeck_boost", "Cyberdeck Boost", "AP +2 max", "max_ap", 2.0),
        WetwareAugment("quickhack_boost", "Quickhack Boost", "Hack speed +20%", "hack_speed", 0.2),
        WetwareAugment("stealth_oxide", "Stealth Oxide", "Stealth +25%", "stealth", 0.25),
        WetwareAugment("nanowire", "Nanowire", "Crit +5%", "crit", 0.05),
        WetwareAugment("biowire", "Biowire", "AP regen +2", "ap_regen", 2.0),
        WetwareAugment("missile_launcher", "Missile Launcher", "AoE +20%", "aoe", 0.2),
        WetwareAugment(
            "optical_camouflage", "Optical Camouflage", "Detection -30%", "detection", -0.3
        ),
        WetwareAugment("reinforced_skin", "Reinforced Skin", "Bleed resist", "bleed_resist", 1.0),
        WetwareAugment(
            "adaptive_immunity", "Adaptive Immunity", "Slow immunity", "slow_immune", 1.0
        ),
    ]
}


def get_augment(augment_id: str) -> WetwareAugment | None:
    """Return augment by id, or None."""
    return AUGMENT_REGISTRY.get(augment_id)


def list_augments() -> tuple[WetwareAugment, ...]:
    """Return all augments in the registry."""
    return tuple(AUGMENT_REGISTRY.values())


def get_augment_count() -> int:
    """Return the number of registered augments."""
    return len(AUGMENT_REGISTRY)


def augment_exists(augment_id: str) -> bool:
    """Return True if augment exists in registry."""
    return augment_id in AUGMENT_REGISTRY


def get_augments_by_effect(effect_type: str) -> tuple[WetwareAugment, ...]:
    """Return all augments with the given effect type."""
    return tuple(a for a in AUGMENT_REGISTRY.values() if a.effect_type == effect_type)


def get_augments_by_tier(tier: int) -> tuple[WetwareAugment, ...]:
    """Return all augments at the given tier."""
    return tuple(a for a in AUGMENT_REGISTRY.values() if a.tier == tier)


def apply_augment_effect(augment: WetwareAugment, attr: str) -> float:
    """Apply augment effect to an attribute value. Returns modified value."""
    if augment.effect_type == attr:
        return augment.effect_value
    return 0.0


__all__ = [
    "AUGMENT_REGISTRY",
    "DEFAULT_AUGMENT_SLOTS",
    "WetwareAugment",
    "apply_augment_effect",
    "augment_exists",
    "get_augment",
    "get_augment_count",
    "get_augments_by_effect",
    "get_augments_by_tier",
    "list_augments",
]
