"""Tests for Endings Choice Handler (ADR-0192)."""

from __future__ import annotations

from dataclasses import dataclass, field

from roguelike_sprawl.story.endings import (
    EndingResult,
    check_ending_eligibility,
    get_ending,
    get_ending_count_by_character,
    get_ending_count_by_type,
    get_endings_by_character,
    get_endings_by_type,
    get_ng_plus_endings,
    get_total_endings,
    is_trigger_condition_met,
    process_ending,
)


@dataclass
class MockState:
    """Mock AppState for testing."""

    credits: int = 1000
    hp: int = 50
    max_hp: int = 100
    alive: bool = True
    salvation_complete: bool = False
    ng_plus_active: bool = False
    arc_5_progress: int = 0
    arc_4_progress: int = 0
    arc_1_progress: int = 0
    arc_1_complete: bool = False
    ally_with: str | None = None
    reputation: dict = field(default_factory=dict)
    achievements: list = field(default_factory=list)
    ending_choice: str = ""
    ng_plus_unlocked: bool = False
    all_constructs_awakened: bool = False
    all_constructs_merged: bool = False
    peripheral_defeated: bool = False
    neuromancer_word: bool = False
    morrison_echo: bool = False
    neon_memory_complete: bool = False
    construct_awakening: bool = False
    ta_vote_complete: bool = False


class TestEndingCounts:
    """Total ending counts and distribution."""

    def test_total_endings(self) -> None:
        assert get_total_endings() >= 22, f"Expected 22+ endings, got {get_total_endings()}"

    def test_ending_types(self) -> None:
        counts = get_ending_count_by_type()
        required = [
            "redemption",
            "sacrifice",
            "transcendence",
            "betrayal",
            "absolution",
            "integration",
        ]
        for t in required:
            assert t in counts, f"Missing ending type: {t}"

    def test_ending_character_distribution(self) -> None:
        counts = get_ending_count_by_character()
        assert "case" in counts
        assert counts["case"] >= 6, f"Case should have 6+ endings, got {counts['case']}"

    def test_ng_plus_endings(self) -> None:
        ng_plus = get_ng_plus_endings()
        assert len(ng_plus) == 3, f"Expected 3 NG+ endings, got {len(ng_plus)}"


class TestEndingQueries:
    """Ending lookup functions."""

    def test_get_ending_existing(self) -> None:
        ending = get_ending("ending_case_redemption")
        assert ending is not None
        assert ending["title"] == "Case's Redemption"

    def test_get_ending_nonexistent(self) -> None:
        assert get_ending("nonexistent") is None

    def test_get_endings_by_character(self) -> None:
        case_endings = get_endings_by_character("case")
        assert len(case_endings) >= 6
        for e in case_endings:
            assert e["character_ref"] == "case"

    def test_get_endings_by_type(self) -> None:
        trans = get_endings_by_type("transcendence")
        assert len(trans) >= 3
        for e in trans:
            assert e["type"] == "transcendence"


class TestTriggerConditions:
    """Trigger condition evaluation."""

    def test_arc_5_progress_trigger(self) -> None:
        ending = get_ending("ending_neuromancer_merge")
        state = MockState(salvation_complete=True, neuromancer_word=True)
        assert "salvation_complete" in ending["trigger_condition"]
        assert is_trigger_condition_met(ending, state) is True

    def test_arc_5_progress_not_met(self) -> None:
        ending = get_ending("ending_neuromancer_merge")
        state = MockState(salvation_complete=False)
        assert is_trigger_condition_met(ending, state) is False

    def test_arc_4_progress_trigger(self) -> None:
        ending = get_ending("ending_3jane_family")
        state = MockState(arc_4_progress=80)
        assert "ta_vote_complete" in ending["trigger_condition"]
        assert is_trigger_condition_met(ending, state) is False

    def test_arc_1_progress_trigger(self) -> None:
        ending = get_ending("ending_case_sacrifice")
        state = MockState(hp=10, max_hp=100)
        assert "hp_below" in ending["trigger_condition"]
        assert is_trigger_condition_met(ending, state) is False

    def test_ng_plus_trigger(self) -> None:
        ending = get_ending("ending_ngplus_network")
        state = MockState(
            salvation_complete=True,
            ng_plus_active=True,
            all_constructs_awakened=True,
        )
        assert is_trigger_condition_met(ending, state) is True

    def test_ally_with_faction_trigger(self) -> None:
        ending = get_ending("ending_case_redemption")
        state = MockState(ally_with="wintermute")
        assert "ally_with:wintermute" in ending["trigger_condition"]
        assert is_trigger_condition_met(ending, state) is False

    def test_unknown_trigger_returns_false(self) -> None:
        ending = {"trigger_condition": "unknown_condition_xyz"}
        state = MockState()
        assert is_trigger_condition_met(ending, state) is False


class TestEndingProcessing:
    """Process ending and apply rewards."""

    def test_process_ending_applies_credits(self) -> None:
        state = MockState(credits=1000)
        result = process_ending("ending_case_redemption", state)
        assert result.achieved is True
        assert result.reward_credits == 5000
        assert state.credits == 6000

    def test_process_ending_applies_reputation(self) -> None:
        state = MockState()
        result = process_ending("ending_3jane_betrayal", state)
        assert result.reputation_changes.get("wintermute") == 30
        assert state.reputation.get("wintermute") == 30

    def test_process_ending_records_achievement(self) -> None:
        state = MockState()
        result = process_ending("ending_case_redemption", state)
        assert result.achievement == "case_redemption"
        assert "case_redemption" in state.achievements

    def test_process_ending_permanent_death(self) -> None:
        state = MockState(alive=True)
        result = process_ending("ending_case_sacrifice", state)
        assert result.permanent_death is True
        assert state.alive is False

    def test_process_ending_ng_plus_unlocks(self) -> None:
        state = MockState(ng_plus_unlocked=False)
        result = process_ending("ending_ngplus_network", state)
        assert result.ng_plus_unlocked is True
        assert state.ng_plus_unlocked is True

    def test_process_ending_sets_choice(self) -> None:
        state = MockState()
        process_ending("ending_case_redemption", state)
        assert state.ending_choice == "ending_case_redemption"

    def test_process_ending_nonexistent(self) -> None:
        state = MockState()
        result = process_ending("nonexistent_ending", state)
        assert result.achieved is False
        assert result.reward_credits == 0


class TestEndingEligibility:
    """Check eligibility for specific endings."""

    def test_eligible(self) -> None:
        state = MockState(salvation_complete=True, neuromancer_word=True)
        assert check_ending_eligibility("ending_neuromancer_merge", state) is True

    def test_not_eligible(self) -> None:
        state = MockState()
        assert check_ending_eligibility("ending_neuromancer_merge", state) is False

    def test_nonexistent_ending_not_eligible(self) -> None:
        state = MockState()
        assert check_ending_eligibility("nonexistent", state) is False


class TestEndingResult:
    """EndingResult dataclass."""

    def test_result_basic(self) -> None:
        result = EndingResult(
            ending_id="test",
            title="Test",
            type="redemption",
            achieved=True,
            reward_credits=1000,
            reputation_changes={"faction": 10},
            achievement="test_achievement",
            permanent_death=False,
            ng_plus_unlocked=False,
        )
        assert result.ending_id == "test"
        assert result.reward_credits == 1000
        assert result.reputation_changes["faction"] == 10
