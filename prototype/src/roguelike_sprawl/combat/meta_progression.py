"""Meta-Progression (ADR-0174).

Persistent unlocks across runs. Unlocks are TOOLS (Pillar 4), not
stat boosts. Each unlock has a condition checked against run stats.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetaUnlock:
    """A persistent unlock earned across runs."""

    id: str
    name: str
    description: str
    category: str
    unlock_condition: str
    progress: int = 0
    goal: int = 1


# Initial unlock catalog
META_UNLOCKS: dict[str, MetaUnlock] = {
    "tier6_program_1": MetaUnlock(
        id="tier6_program_1",
        name="Neural Whip",
        description="Tier 6 program — finish with 0 deaths",
        category="program",
        unlock_condition="finish_with_0_deaths",
    ),
    "military_augment": MetaUnlock(
        id="military_augment",
        name="Military Augment Set",
        description="4 new augments — reach Grade 5",
        category="augment",
        unlock_condition="reach_grade_5",
    ),
    "ghost_deck": MetaUnlock(
        id="ghost_deck",
        name="Ghost Deck",
        description="Stealth preset deck — win 5 stealth runs",
        category="deck",
        unlock_condition="win_5_stealth_runs",
        goal=5,
    ),
    "wintermute_skin": MetaUnlock(
        id="wintermute_skin",
        name="Wintermute Skin",
        description="ASCII portrait — kill 100 Wintermute",
        category="cosmetic",
        unlock_condition="kill_100_wintermute",
        goal=100,
    ),
    "berserker_deck": MetaUnlock(
        id="berserker_deck",
        name="Berserker Deck",
        description="Aggressive preset — win 5 aggressive runs",
        category="deck",
        unlock_condition="win_5_aggressive_runs",
        goal=5,
    ),
    "stealth_deck": MetaUnlock(
        id="stealth_deck",
        name="Stealth Deck",
        description="Stealth preset — win 5 stealth runs",
        category="deck",
        unlock_condition="win_5_stealth_runs",
        goal=5,
    ),
    "hacker_deck": MetaUnlock(
        id="hacker_deck",
        name="Hacker Deck",
        description="Hacker preset — win 5 hack runs",
        category="deck",
        unlock_condition="win_5_hack_runs",
        goal=5,
    ),
    "adrenal_boost_mk2": MetaUnlock(
        id="adrenal_boost_mk2",
        name="Adrenal Boost Mk2",
        description="AP regen +2 — reach NG+ Grade 3",
        category="augment",
        unlock_condition="ng_plus_grade_3",
    ),
    "ta_skin": MetaUnlock(
        id="ta_skin",
        name="T-A Skin",
        description="T-A Construct Prime ASCII portrait",
        category="cosmetic",
        unlock_condition="kill_50_ta_prime",
        goal=50,
    ),
    "neuromancer_unlock": MetaUnlock(
        id="neuromancer_unlock",
        name="Neuromancer Boss",
        description="Post-game boss — finish all Phase 6 missions",
        category="boss",
        unlock_condition="complete_phase_6",
    ),
    "perfected_deck": MetaUnlock(
        id="perfected_deck",
        name="Perfected Deck",
        description="Master preset — win 20 runs",
        category="deck",
        unlock_condition="win_20_runs",
        goal=20,
    ),
    "codex_unlock": MetaUnlock(
        id="codex_unlock",
        name="Codex Collection",
        description="Bestiary entries — encounter 50 unique ICE types",
        category="cosmetic",
        unlock_condition="encounter_50_unique_ice",
        goal=50,
    ),
}


def get_meta_unlocks() -> tuple[MetaUnlock, ...]:
    """Return all meta unlocks."""
    return tuple(META_UNLOCKS.values())


def get_unlocked_ids() -> set[str]:
    """Return set of unlocked ids (unlocks with progress >= goal)."""
    return {uid for uid, unlock in META_UNLOCKS.items() if unlock.progress >= unlock.goal}


def get_locked_ids() -> set[str]:
    """Return set of unlocked ids (unlocks with progress < goal)."""
    return {uid for uid, unlock in META_UNLOCKS.items() if unlock.progress < unlock.goal}


def get_meta_progress(unlock_id: str) -> MetaUnlock | None:
    """Return the unlock record for a given id."""
    return META_UNLOCKS.get(unlock_id)


def record_meta_progress(unlock_id: str, amount: int = 1) -> MetaUnlock:
    """Record progress toward an unlock. Returns updated unlock."""
    unlock = META_UNLOCKS.get(unlock_id)
    if unlock is None:
        raise ValueError(f"Unknown unlock: {unlock_id}")
    new_unlock = MetaUnlock(
        id=unlock.id,
        name=unlock.name,
        description=unlock.description,
        category=unlock.category,
        unlock_condition=unlock.unlock_condition,
        progress=unlock.progress + amount,
        goal=unlock.goal,
    )
    META_UNLOCKS[unlock_id] = new_unlock
    return new_unlock


def check_unlock_condition(condition: str, run_stats: dict[str, int]) -> bool:
    """Check if an unlock condition is satisfied given run stats."""
    value = run_stats.get(condition, 0)
    return value > 0


def get_unlocks_by_category(category: str) -> tuple[MetaUnlock, ...]:
    """Return all unlocks in a given category."""
    return tuple(u for u in META_UNLOCKS.values() if u.category == category)


def get_unlock_progress_ratio(unlock_id: str) -> float:
    """Return unlock progress as a ratio (0.0 to 1.0)."""
    unlock = META_UNLOCKS.get(unlock_id)
    if unlock is None or unlock.goal == 0:
        return 0.0
    return min(1.0, unlock.progress / unlock.goal)


__all__ = [
    "META_UNLOCKS",
    "MetaUnlock",
    "check_unlock_condition",
    "get_locked_ids",
    "get_meta_progress",
    "get_meta_unlocks",
    "get_unlock_progress_ratio",
    "get_unlocked_ids",
    "get_unlocks_by_category",
    "record_meta_progress",
]
