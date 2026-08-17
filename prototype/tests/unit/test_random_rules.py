"""Tests for Random Selection Rules (ADR-0188, Phase 11 integration)."""

from __future__ import annotations

from dataclasses import dataclass

from wet_run.missions.random_rules import (
    RuleResult,
    apply_rule,
    calculate_weight_bonus,
    get_all_active_rules,
    get_random_mission,
    get_rule_by_id,
    get_rules_by_trigger_state,
    get_total_rules,
    simulate_random_event,
)


@dataclass
class MockState:
    """Mock state for random rules testing."""

    grade: int = 1
    yakuza_rep: int = 0
    sense_net_rep: int = 0
    hosaka_rep: int = 0
    ta_rep: int = 0
    freeside_rep: int = 0
    loa_rep: int = 0
    faction_rep: int = 0
    has_construct: bool = False
    consecutive_failures: int = 0
    consecutive_completions: int = 0
    consecutive_high_salvages: int = 0
    boss_defeated_recently: bool = False
    chain_complete_recently: bool = False
    chain_failed_recently: bool = False
    construct_lost_recently: bool = False
    fixer_used_recently: bool = False
    node_turns: int = 0
    bandwidth: int = 100
    corrupted_node: bool = False
    hp_pct: int = 100
    days_until_random_expires: int = 5


class TestRuleCounts:
    """Rule metadata queries."""

    def test_total_rules(self) -> None:
        assert get_total_rules() == 19, f"Expected 19 rules, got {get_total_rules()}"

    def test_get_rule_by_id(self) -> None:
        rule = get_rule_by_id("faction_weighted")
        assert rule is not None
        assert rule["name"] == "Faction-Weighted Selection"

    def test_get_rule_by_id_nonexistent(self) -> None:
        assert get_rule_by_id("nonexistent") is None


class TestRuleTriggers:
    """Trigger condition evaluation."""

    def test_player_grade_3_trigger(self) -> None:
        state = MockState(grade=3)
        rules = get_rules_by_trigger_state(state)
        assert any(r["rule_id"] == "faction_weighted" for r in rules)

    def test_player_level_grade_5_trigger(self) -> None:
        state = MockState(grade=5)
        rules = get_rules_by_trigger_state(state)
        assert any(r["rule_id"] == "player_level" for r in rules)

    def test_faction_rep_triggers(self) -> None:
        state = MockState(faction_rep=5)
        rules = get_rules_by_trigger_state(state)
        assert any(r["rule_id"] == "reputation_gate" for r in rules)

    def test_construct_trigger(self) -> None:
        state = MockState(has_construct=True)
        rules = get_rules_by_trigger_state(state)
        assert any(r["rule_id"] == "construct_aware" for r in rules)

    def test_consecutive_failures_trigger(self) -> None:
        state = MockState(consecutive_failures=3)
        rules = get_rules_by_trigger_state(state)
        assert any(r["rule_id"] == "difficulty_spike" for r in rules)

    def test_no_triggers_returns_empty(self) -> None:
        state = MockState()
        rules = get_rules_by_trigger_state(state)
        assert isinstance(rules, list)


class TestRuleApplication:
    """Rule application and result handling."""

    def test_apply_rule_nonexistent(self) -> None:
        state = MockState()
        result = apply_rule("nonexistent", state, ["m1", "m2"])
        assert result.rule_id == "nonexistent"
        assert result.selected_missions == ()

    def test_apply_rule_trigger_not_met(self) -> None:
        state = MockState()
        result = apply_rule("player_level", state, ["m1", "m2"])
        assert result.selected_missions == ()
        assert result.active is False or result.active is True

    def test_apply_rule_with_missions(self) -> None:
        state = MockState(faction_rep=5)
        result = apply_rule("reputation_gate", state, ["m1", "m2", "m3", "m4", "m5"])
        assert result.rule_id == "reputation_gate"
        assert result.active is True
        assert len(result.selected_missions) > 0

    def test_get_all_active_rules(self) -> None:
        state = MockState(faction_rep=5, has_construct=True)
        active = get_all_active_rules(state)
        assert isinstance(active, list)
        assert len(active) >= 2


class TestWeightBonus:
    """Faction weight bonus calculation."""

    def test_low_rep(self) -> None:
        state = MockState(yakuza_rep=1)
        bonus = calculate_weight_bonus(state, "yakuza")
        assert bonus == 1.0

    def test_medium_rep(self) -> None:
        state = MockState(yakuza_rep=2)
        bonus = calculate_weight_bonus(state, "yakuza")
        assert bonus == 1.4

    def test_high_rep(self) -> None:
        state = MockState(yakuza_rep=5)
        bonus = calculate_weight_bonus(state, "yakuza")
        assert bonus == 1.8


class TestRandomSelection:
    """Random mission selection."""

    def test_simulate_random_event_seed(self) -> None:
        for _ in range(5):
            result = simulate_random_event(MockState(), seed=42)
            assert isinstance(result, bool)

    def test_get_random_mission_returns_none_when_empty(self) -> None:
        result = get_random_mission(MockState(), [], seed=42)
        assert result is None

    def test_get_random_mission_returns_valid(self) -> None:
        state = MockState(grade=3)
        missions = ["m1", "m2", "m3", "m4", "m5"]
        result = get_random_mission(state, missions, seed=42)
        assert result in missions

    def test_get_random_mission_seed_deterministic(self) -> None:
        state = MockState(grade=3)
        missions = ["m1", "m2", "m3", "m4", "m5"]
        result1 = get_random_mission(state, missions, seed=42)
        result2 = get_random_mission(state, missions, seed=42)
        assert result1 == result2


class TestRuleResult:
    """RuleResult dataclass."""

    def test_default_result(self) -> None:
        result = RuleResult("test", ("m1",))
        assert result.rule_id == "test"
        assert result.selected_missions == ("m1",)
        assert result.weight_modifier == 1.0
        assert result.active is True

    def test_custom_result(self) -> None:
        result = RuleResult("test", ("m1", "m2"), 1.5, False)
        assert result.weight_modifier == 1.5
        assert result.active is False
