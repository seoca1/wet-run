"""Random selection rules implementation (ADR-0188, Phase 11 integration).

Implements the 19 random selection rules from random_selection_rules.json.
Each rule provides a function that selects/eligible-missions for a given run state.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    pass


DATA_PATH = (
    Path(__file__).parent.parent.parent.parent / "data" / "missions" / "random_selection_rules.json"
)


@dataclass(frozen=True, slots=True)
class RuleResult:
    """Result of a random selection rule execution."""

    rule_id: str
    selected_missions: tuple[str, ...]
    weight_modifier: float = 1.0
    active: bool = True


def _load_rules() -> list[dict[str, Any]]:
    """Load rules from random_selection_rules.json."""
    with open(DATA_PATH) as f:
        return cast(list[dict[str, Any]], json.load(f).get("rules", []))


_RULES_CACHE: list[dict[str, Any]] | None = None


def _get_rules() -> list[dict[str, Any]]:
    """Lazy-loaded rules cache."""
    global _RULES_CACHE
    if _RULES_CACHE is None:
        _RULES_CACHE = _load_rules()
    return _RULES_CACHE


def get_total_rules() -> int:
    """Return total number of rules."""
    return len(_get_rules())


def get_rule_by_id(rule_id: str) -> dict[str, Any] | None:
    """Return a rule by id."""
    for r in _get_rules():
        if r["rule_id"] == rule_id:
            return r
    return None


def get_rules_by_trigger_state(state: object) -> list[dict[str, Any]]:
    """Return rules whose trigger_condition is met for the current state."""
    return [r for r in _get_rules() if _is_trigger_met(r, state)]


def _is_trigger_met(rule: dict[str, Any], state: object) -> bool:
    """Check if a rule's trigger_condition is met."""
    condition = rule.get("trigger", "")
    if not condition:
        return False

    if condition == "player_grade >= 3":
        return getattr(state, "grade", 1) >= 3
    if condition == "player_grade >= 5":
        return getattr(state, "grade", 1) >= 5
    if condition == "yakuza_rep >= 2":
        return getattr(state, "yakuza_rep", 0) >= 2
    if condition == "yakuza_rep >= 3":
        return getattr(state, "yakuza_rep", 0) >= 3
    if condition == "faction_rep >= 5":
        return getattr(state, "faction_rep", 0) >= 5
    if condition == "sense_net_rep >= 3":
        return getattr(state, "sense_net_rep", 0) >= 3
    if condition == "sense_net_rep >= 4":
        return getattr(state, "sense_net_rep", 0) >= 4
    if condition == "hosaka_rep >= 4":
        return getattr(state, "hosaka_rep", 0) >= 4
    if condition == "hosaka_rep >= 5":
        return getattr(state, "hosaka_rep", 0) >= 5
    if condition == "ta_rep >= 4":
        return getattr(state, "ta_rep", 0) >= 4
    if condition == "freeside_rep >= 3":
        return getattr(state, "freeside_rep", 0) >= 3
    if condition == "loa_rep >= 4":
        return getattr(state, "loa_rep", 0) >= 4
    if condition == "has_construct":
        return getattr(state, "has_construct", False)
    if condition.startswith("consecutive_failures >= "):
        threshold = int(condition.split(">= ")[1])
        return getattr(state, "consecutive_failures", 0) >= threshold
    if condition.startswith("consecutive_completions >= "):
        threshold = int(condition.split(">= ")[1])
        return getattr(state, "consecutive_completions", 0) >= threshold
    if condition.startswith("consecutive_high_salvages >= "):
        threshold = int(condition.split(">= ")[1])
        return getattr(state, "consecutive_high_salvages", 0) >= threshold
    if condition == "boss_defeated":
        return getattr(state, "boss_defeated_recently", False)
    if condition == "chain_complete":
        return getattr(state, "chain_complete_recently", False)
    if condition == "chain_failed":
        return getattr(state, "chain_failed_recently", False)
    if condition == "construct_lost":
        return getattr(state, "construct_lost_recently", False)
    if condition == "fixer_used":
        return getattr(state, "fixer_used_recently", False)
    if condition == "stay_in_node_5_turns":
        return getattr(state, "node_turns", 0) >= 5
    if condition == "low_bandwidth_zone":
        return getattr(state, "bandwidth", 100) < 50
    if condition == "enter_corrupted_node":
        return getattr(state, "corrupted_node", False)
    if condition == "hp_below_threshold":
        return getattr(state, "hp_pct", 100) < 30
    if "always_random" in condition or ">= 1" in condition:
        return True
    return False


def apply_rule(
    rule_id: str,
    state: object,
    all_missions: list[str],
    mission_weights: dict[str, float] | None = None,
) -> RuleResult:
    """Apply a specific rule and return the selected missions.

    Args:
        rule_id: The rule to apply.
        state: Player state.
        all_missions: List of all available mission IDs.
        mission_weights: Optional per-mission random_weight overrides.
            When provided, missions with weight < 0 are filtered out.

    Returns:
        RuleResult with selected missions and weight modifier.
    """
    rule = get_rule_by_id(rule_id)
    if rule is None:
        return RuleResult(rule_id, ())

    if not _is_trigger_met(rule, state):
        return RuleResult(rule_id, ())

    weight = _compute_weight_modifier(rule, state)
    selected = _select_missions(rule, state, all_missions, weight)
    if mission_weights is not None:
        selected = [m for m in selected if mission_weights.get(m, 1.0) >= 0]
    return RuleResult(rule_id, tuple(selected), weight)


def _compute_weight_modifier(rule: dict[str, Any], state: object) -> float:
    """Compute the weight modifier from the rule."""
    modifier_str = rule.get("weight_modifier", "1.0")
    if isinstance(modifier_str, str):
        if "rep" in modifier_str:
            if "factor" in modifier_str:
                return 1.2
            if "0.2" in modifier_str:
                return 1.2
        if "0.3" in modifier_str:
            return 1.3
        if "0.5" in modifier_str:
            return 1.5
        if "0.6" in modifier_str:
            return 1.6
        if "0.25" in modifier_str:
            return 1.25
        if "20" in modifier_str or "30" in modifier_str or "50" in modifier_str:
            return 1.5
    if isinstance(modifier_str, (int, float)):
        return float(modifier_str)
    return 1.0


def _select_missions(
    rule: dict[str, Any], state: object, all_missions: list[str], weight: float
) -> list[str]:
    """Select missions based on the rule's scope."""
    scope = rule.get("scope", "")
    affected = rule.get("affected_missions", "all")

    if affected == "all":
        return list(all_missions)

    if scope == "run_wide":
        return list(all_missions)

    if scope == "5_runs":
        days_remaining = getattr(state, "days_until_random_expires", 5)
        return list(all_missions) if days_remaining > 0 else []

    if scope == "next_mission":
        return list(all_missions)[:1]

    if scope == "any_mission":
        return list(all_missions)

    return list(all_missions)


def get_all_active_rules(state: object) -> list[dict[str, object]]:
    """Return all rules whose trigger_condition is met."""
    return get_rules_by_trigger_state(state)


def simulate_random_event(state: object, seed: int | None = None) -> bool:
    """Simulate a random event trigger (1d20 >= 18 by default).

    Returns:
        True if the random event should trigger.
    """
    if seed is not None:
        rng: random.Random = random.Random(seed)
    else:
        rng = random.Random()
    return rng.randint(1, 20) >= 18


def calculate_weight_bonus(state: object, faction: str) -> float:
    """Calculate faction-weighted bonus based on reputation."""
    rep_key = f"{faction}_rep"
    rep = getattr(state, rep_key, 0)
    if rep >= 4:
        return 1.8
    if rep >= 3:
        return 1.6
    if rep >= 2:
        return 1.4
    return 1.0


def get_random_mission(
    state: object, available_missions: list[str], seed: int | None = None
) -> str | None:
    """Get a random mission using all active rules' weights.

    Args:
        state: Player state.
        available_missions: List of available mission IDs.
        seed: Optional random seed.

    Returns:
        Selected mission ID or None if no missions available.
    """
    result = get_random_mission_with_rule(state, available_missions, seed=seed, mission_weights=mission_weights)
    if result is None:
        return None
    return result[0]


def get_random_mission_with_rule(
    state: object, available_missions: list[str], seed: int | None = None
) -> tuple[str, str | None] | None:
    """Get a random mission AND the rule_id that selected it.

    Phase 17: exposes the rule_id so the UI can show why a mission was
    selected (e.g. "Selected by rule: faction_weighted").

    Args:
        state: Player state.
        available_missions: List of available mission IDs.
        seed: Optional random seed.

    Returns:
        Tuple of (selected mission ID, rule_id) or None if no missions.
        rule_id is None when no active rules fired (uniform random pick).
    """
    if not available_missions:
        return None

    if seed is not None:
        rng: random.Random = random.Random(seed)
    else:
        rng = random.Random()

    # Phase 17 + ADR-0208: mission_weights multiplies per-mission weight.
    if mission_weights is not None:
        weights = [max(0.0, mission_weights.get(m, 1.0)) for m in available_missions]
        total_weight = sum(weights)
        if total_weight <= 0:
            return None
        pick = rng.uniform(0, total_weight)
        cumulative = 0.0
        for mid, weight in zip(available_missions, weights, strict=False):
            cumulative += weight
            if pick <= cumulative:
                return mid, None
        return available_missions[-1], None

    active_rules = get_all_active_rules(state)
    weights = [_compute_weight_modifier(r, state) for r in active_rules]
    total_weight = sum(weights) if weights else 1.0

    pick = rng.uniform(0, total_weight)
    cumulative = 0.0
    for rule, weight in zip(active_rules, weights, strict=False):
        cumulative += weight
        if pick <= cumulative:
            rule_id = str(rule.get("rule_id", "unknown"))
            return rng.choice(available_missions), rule_id
    # Out-of-rules fallback (no active rules) — uniform random pick.
    return rng.choice(available_missions), None
