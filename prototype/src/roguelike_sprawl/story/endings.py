"""Endings choice handler (ADR-0192, Phase 14 integration).

Processes ending choices from endings.json, checks trigger conditions,
applies rewards, and locks/unlocks NG+ state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "story" / "endings.json"


@dataclass(frozen=True, slots=True)
class EndingResult:
    """Outcome of processing an ending choice."""

    ending_id: str
    title: str
    type: str
    achieved: bool
    reward_credits: int
    reputation_changes: dict[str, int]
    achievement: str | None
    permanent_death: bool
    ng_plus_unlocked: bool


def _load_endings() -> dict[str, Any]:
    """Load endings from endings.json."""
    with open(DATA_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


_ENDINGS_CACHE: dict[str, dict[str, Any]] | None = None


def _get_endings() -> dict[str, dict[str, Any]]:
    """Lazy-loaded endings cache."""
    global _ENDINGS_CACHE
    if _ENDINGS_CACHE is None:
        _ENDINGS_CACHE = _load_endings()
    return _ENDINGS_CACHE


def get_ending(ending_id: str) -> dict[str, Any] | None:
    """Return an ending definition by id."""
    return _get_endings().get(ending_id)


def get_endings_by_character(character_ref: str) -> list[dict[str, Any]]:
    """Return all endings for a specific character."""
    return [e for e in _get_endings().values() if e.get("character_ref") == character_ref]


def get_ng_plus_endings() -> list[dict[str, Any]]:
    """Return all NG+ (arc 6) endings."""
    return [e for e in _get_endings().values() if e.get("arc") == 6]


def get_endings_by_type(ending_type: str) -> list[dict[str, Any]]:
    """Return all endings of a given type (redemption, sacrifice, etc.)."""
    return [e for e in _get_endings().values() if e.get("type") == ending_type]


def _check_single_condition(condition: str, state: object) -> bool:
    """Check a single (non-compound) trigger condition."""
    condition = condition.strip()
    if condition == "salvation_complete":
        return getattr(state, "salvation_complete", False)
    if condition == "ngplus_active":
        return getattr(state, "ng_plus_active", False)
    if condition == "arc_5_progress >= 50":
        return getattr(state, "arc_5_progress", 0) >= 50
    if condition == "arc_4_progress >= 75":
        return getattr(state, "arc_4_progress", 0) >= 75
    if condition == "arc_4_progress >= 50":
        return getattr(state, "arc_4_progress", 0) >= 50
    if condition == "arc_1_progress >= 30":
        return getattr(state, "arc_1_progress", 0) >= 30
    if condition == "arc_1_complete" or condition == "chapter_complete:arc_1":
        return getattr(state, "arc_1_complete", False)
    if condition == "ta_vote_complete":
        return getattr(state, "ta_vote_complete", False)
    if condition == "neuromancer_word":
        return getattr(state, "neuromancer_word", False)
    if condition == "morrison_echo":
        return getattr(state, "morrison_echo", False)
    if condition == "neon_memory_complete":
        return getattr(state, "neon_memory_complete", False)
    if condition == "construct_awakening":
        return getattr(state, "construct_awakening", False)
    if condition.startswith("ally_with:"):
        faction = condition.split(":", 1)[1]
        return getattr(state, "ally_with", None) == faction
    if "credit" in condition and ">" in condition:
        return getattr(state, "credits", 0) > 1000
    if "hp_below" in condition:
        return getattr(state, "hp", 100) < getattr(state, "max_hp", 100) * 0.5
    if condition.startswith("complete_") or condition.startswith("defeat_"):
        return getattr(state, "quest_complete", False)
    if condition == "all_constructs_awakened":
        return getattr(state, "all_constructs_awakened", False)
    if condition == "all_constructs_merged":
        return getattr(state, "all_constructs_merged", False)
    if condition == "peripheral_defeated":
        return getattr(state, "peripheral_defeated", False)
    return False


def is_trigger_condition_met(ending: dict[str, Any], state: object) -> bool:
    """Check if an ending's trigger_condition is satisfied.

    Supports compound conditions (AND-joined with ``+``).

    Args:
        ending: Ending definition from endings.json.
        state: AppState (or dict[str, Any]-like) with player progression data.

    Returns:
        True if the trigger condition is met.
    """
    condition = ending.get("trigger_condition", "")
    if not condition:
        return False

    if "+" in condition:
        parts = [p.strip() for p in condition.split("+")]
        return all(_check_single_condition(p, state) for p in parts)

    return _check_single_condition(condition, state)


def check_ending_eligibility(ending_id: str, state: object) -> bool:
    """Check if player is eligible for a specific ending."""
    ending = get_ending(ending_id)
    if ending is None:
        return False
    return is_trigger_condition_met(ending, state)


def process_ending(ending_id: str, state: object) -> EndingResult:
    """Process an ending choice and apply its rewards.

    Args:
        ending_id: The ending chosen by the player.
        state: AppState to mutate.

    Returns:
        EndingResult with outcome details.
    """
    ending = get_ending(ending_id)
    if ending is None:
        return EndingResult(
            ending_id=ending_id,
            title="Unknown",
            type="unknown",
            achieved=False,
            reward_credits=0,
            reputation_changes={},
            achievement=None,
            permanent_death=False,
            ng_plus_unlocked=False,
        )

    reward = ending.get("reward", {})
    credit_amount = reward.get("credits", 0) if isinstance(reward, dict) else 0
    reputation = reward.get("reputation", {}) if isinstance(reward, dict) else {}
    permanent_death = reward.get("permanent_death", False) if isinstance(reward, dict) else False
    achievement = ending.get("achievement")
    arc = ending.get("arc", 1)

    if permanent_death:
        if hasattr(state, "alive"):
            state.alive = False

    if credit_amount and hasattr(state, "credits"):
        state.credits = getattr(state, "credits", 0) + credit_amount

    if hasattr(state, "reputation") and isinstance(reputation, dict):
        for faction, amount in reputation.items():
            current = state.reputation.get(faction, 0)
            state.reputation[faction] = current + amount

    if achievement and hasattr(state, "achievements"):
        if achievement not in state.achievements:
            state.achievements.append(achievement)

    if hasattr(state, "ending_choice"):
        state.ending_choice = ending_id

    ng_plus = arc == 6
    if ng_plus and hasattr(state, "ng_plus_unlocked"):
        state.ng_plus_unlocked = True

    return EndingResult(
        ending_id=ending_id,
        title=ending.get("title", ""),
        type=ending.get("type", ""),
        achieved=True,
        reward_credits=credit_amount,
        reputation_changes=reputation,
        achievement=achievement,
        permanent_death=permanent_death,
        ng_plus_unlocked=ng_plus,
    )


def get_total_endings() -> int:
    """Return total number of endings."""
    return len(_get_endings())


def get_ending_count_by_type() -> dict[str, int]:
    """Return count of endings by type."""
    counts: dict[str, int] = {}
    for ending in _get_endings().values():
        t = ending.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def get_ending_count_by_character() -> dict[str, int]:
    """Return count of endings by character."""
    counts: dict[str, int] = {}
    for ending in _get_endings().values():
        c = ending.get("character_ref", "unknown")
        counts[c] = counts.get(c, 0) + 1
    return counts
