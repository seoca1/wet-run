"""Boss Expansion (ADR-0180).

3 new boss profiles: Neuromancer, Loa Baron, Black Baron.
Each has distinct theme, HP, damage, and phase structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from .state import DEFAULT_ALARM_SPEED, Combatant


@dataclass(frozen=True, slots=True)
class BossPhase:
    """A single boss phase."""

    phase: int
    hp_threshold: float
    damage_multiplier: float
    color: tuple[int, int, int]
    glyph: str
    intro_text: str


@dataclass(frozen=True, slots=True)
class BossProfile:
    """A complete boss profile."""

    id: str
    name: str
    description: str
    hp_base: int
    damage_base: int
    defense: int
    tier: int
    phases: tuple[BossPhase, ...]


# Neuromancer — final merger entity (6 phases)
NEUROMANCER_PROFILE = BossProfile(
    id="neuromancer",
    name="Neuromancer",
    description="The merger. The final entity.",
    hp_base=400,
    damage_base=18,
    defense=10,
    tier=5,
    phases=(
        BossPhase(1, 1.0, 1.0, (255, 0, 100), "*", "NEUROMANCER — emerging"),
        BossPhase(2, 0.8, 1.3, (255, 50, 120), "@", "NEUROMANCER — integrating"),
        BossPhase(3, 0.6, 1.6, (255, 100, 140), "#", "NEUROMANCER — spreading"),
        BossPhase(4, 0.4, 2.0, (255, 150, 160), "!", "NEUROMANCER — converging"),
        BossPhase(5, 0.2, 2.5, (255, 200, 180), "?", "NEUROMANCER — final"),
        BossPhase(6, 0.1, 3.0, (255, 255, 255), "#", "NEUROMANCER — LAST STAND"),
    ),
)


# Loa Baron — voodoo-themed (4 phases)
LOA_BARON_PROFILE = BossProfile(
    id="loa_baron",
    name="Loa Baron",
    description="The voodoo boss. ZION-adjacent.",
    hp_base=300,
    damage_base=14,
    defense=7,
    tier=4,
    phases=(
        BossPhase(1, 1.0, 1.0, (180, 100, 50), "L", "LOA BARON — summoning"),
        BossPhase(2, 0.6, 1.4, (200, 100, 60), "X", "LOA BARON — binding"),
        BossPhase(3, 0.3, 1.8, (220, 100, 70), "Y", "LOA BARON — possessing"),
        BossPhase(4, 0.1, 2.4, (255, 100, 80), "Z", "LOA BARON — dissolving"),
    ),
)


# Black Baron — corruption boss (4 phases)
BLACK_BARON_PROFILE = BossProfile(
    id="black_baron",
    name="Black Baron",
    description="The corruption boss. Glitch-themed.",
    hp_base=250,
    damage_base=12,
    defense=6,
    tier=3,
    phases=(
        BossPhase(1, 1.0, 1.0, (50, 0, 100), "@", "BLACK BARON — corrupting"),
        BossPhase(2, 0.6, 1.3, (80, 0, 130), "?", "BLACK BARON — corrupting"),
        BossPhase(3, 0.3, 1.7, (120, 0, 160), "!", "BLACK BARON — corrupting"),
        BossPhase(4, 0.1, 2.2, (180, 0, 200), "#", "BLACK BARON — LAST STAND"),
    ),
)


BOSS_EXPANSION_REGISTRY: dict[str, BossProfile] = {
    "neuromancer": NEUROMANCER_PROFILE,
    "loa_baron": LOA_BARON_PROFILE,
    "black_baron": BLACK_BARON_PROFILE,
}


def get_boss_profile(boss_id: str) -> BossProfile | None:
    """Return boss profile by id."""
    return BOSS_EXPANSION_REGISTRY.get(boss_id)


def get_all_bosses() -> tuple[BossProfile, ...]:
    """Return all boss profiles."""
    return tuple(BOSS_EXPANSION_REGISTRY.values())


def get_boss_by_tier(tier: int) -> BossProfile | None:
    """Return boss profile for a given tier."""
    for boss in BOSS_EXPANSION_REGISTRY.values():
        if boss.tier == tier:
            return boss
    return None


def get_boss_count() -> int:
    """Return the number of boss profiles."""
    return len(BOSS_EXPANSION_REGISTRY)


def get_boss_ids() -> tuple[str, ...]:
    """Return all boss ids."""
    return tuple(BOSS_EXPANSION_REGISTRY.keys())


def boss_exists(boss_id: str) -> bool:
    """Return True if boss exists."""
    return boss_id in BOSS_EXPANSION_REGISTRY


def get_boss_phase_count(boss_id: str) -> int:
    """Return the number of phases for a boss."""
    boss = get_boss_profile(boss_id)
    if boss is None:
        return 0
    return len(boss.phases)


def get_boss_max_hp(boss_id: str) -> int:
    """Return the base HP for a boss."""
    boss = get_boss_profile(boss_id)
    if boss is None:
        return 0
    return boss.hp_base


def build_boss_combatant(
    boss: BossProfile,
    *,
    player_grade: int | None = None,
) -> Combatant:
    """Convert BossProfile to Combatant for combat dispatch (F.4 integration).

    Maps the boss expansion registry (Neuromancer/Loa Baron/Black Baron)
    into the Combatant dataclass used by build_ice_enemy and combat dispatch.

    Args:
        boss: BossProfile from BOSS_EXPANSION_REGISTRY.
        player_grade: If provided, scale boss HP and damage to match player
            grade (matches build_ice_enemy scaling behavior).

    Returns:
        Combatant ready for combat dispatch.
    """
    if player_grade is not None:
        scale = 1.0 + (player_grade - 1) * 0.15
        hp = int(boss.hp_base * scale)
        dmg = int(boss.damage_base * scale)
    else:
        hp = boss.hp_base
        dmg = boss.damage_base

    if boss.phases:
        first_phase = boss.phases[0]
        portrait_glyph = first_phase.glyph
        color = first_phase.color
    else:
        portrait_glyph = "*"
        color = (255, 0, 255)

    return Combatant(
        id=boss.id,
        name=boss.name,
        portrait=portrait_glyph,
        color=color,
        hp=hp,
        max_hp=hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=dmg,
        skills=(),
        team="enemy",
        ice_kind=f"boss_{boss.id}",
        ice_resistance=0.5,
        alarm_speed=DEFAULT_ALARM_SPEED,
    )


__all__ = [
    "BLACK_BARON_PROFILE",
    "BOSS_EXPANSION_REGISTRY",
    "BossPhase",
    "BossProfile",
    "LOA_BARON_PROFILE",
    "NEUROMANCER_PROFILE",
    "boss_exists",
    "build_boss_combatant",
    "get_all_bosses",
    "get_boss_by_tier",
    "get_boss_count",
    "get_boss_ids",
    "get_boss_max_hp",
    "get_boss_phase_count",
    "get_boss_profile",
]
