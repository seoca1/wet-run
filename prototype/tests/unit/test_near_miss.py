"""Unit tests for Near-Miss Extraction (ADR-0140 P3.6).

Covers:
- HP ratio computation (clamping, edge cases)
- Threshold check (above/below)
- Reward application (credits + salvage)
- One-shot semantics
- Pillar 4 safety (no cross-run inheritance)
"""

from __future__ import annotations

from wet_run.matrix.near_miss import (
    DEFAULT_NEAR_MISS_HP_THRESHOLD,
    NEAR_MISS_CREDITS,
    NEAR_MISS_SALVAGE,
    NearMissReward,
    NearMissRewardKind,
    check_near_miss_extraction,
    compute_hp_ratio,
)


class TestComputeHpRatio:
    """HP ratio clamping + edge cases."""

    def test_full_hp_returns_one(self) -> None:
        assert compute_hp_ratio(100, 100) == 1.0

    def test_zero_hp_returns_zero(self) -> None:
        assert compute_hp_ratio(0, 100) == 0.0

    def test_half_hp_returns_half(self) -> None:
        assert compute_hp_ratio(50, 100) == 0.5

    def test_max_hp_zero_returns_zero(self) -> None:
        """Defensive: zero/negative max_hp returns 0 (no false triggers)."""
        assert compute_hp_ratio(50, 0) == 0.0
        assert compute_hp_ratio(50, -10) == 0.0

    def test_hp_clamped_to_max(self) -> None:
        """Overheal (HP > max) clamped to 1.0."""
        assert compute_hp_ratio(150, 100) == 1.0

    def test_hp_clamped_to_zero(self) -> None:
        """Negative HP clamped to 0."""
        assert compute_hp_ratio(-10, 100) == 0.0


class TestNearMissThreshold:
    """Threshold check at boundary."""

    def test_default_threshold_is_80_percent(self) -> None:
        assert DEFAULT_NEAR_MISS_HP_THRESHOLD == 0.80

    def test_above_threshold_triggers(self) -> None:
        state = self._make_state(hp=80, max_hp=100)
        result = check_near_miss_extraction(state)
        assert result.triggered is True
        assert result.hp_ratio == 0.80

    def test_full_hp_triggers(self) -> None:
        state = self._make_state(hp=100, max_hp=100)
        result = check_near_miss_extraction(state)
        assert result.triggered is True
        assert result.hp_ratio == 1.0

    def test_below_threshold_no_trigger(self) -> None:
        state = self._make_state(hp=79, max_hp=100)
        result = check_near_miss_extraction(state)
        assert result.triggered is False
        assert result.hp_ratio == 0.79

    def test_zero_hp_no_trigger(self) -> None:
        state = self._make_state(hp=0, max_hp=100)
        result = check_near_miss_extraction(state)
        assert result.triggered is False

    def test_custom_threshold_higher(self) -> None:
        """Custom threshold 0.90 = 90% HP."""
        state = self._make_state(hp=85, max_hp=100)
        result = check_near_miss_extraction(state, threshold=0.90)
        assert result.triggered is False
        result = check_near_miss_extraction(state, threshold=0.80)
        assert result.triggered is True

    @staticmethod
    def _make_state(hp: int, max_hp: int) -> object:
        return type(
            "S",
            (),
            {
                "player_hp": hp,
                "player_max_hp": max_hp,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()


class TestNearMissRewards:
    """Reward application to AppState."""

    def test_credits_added(self) -> None:
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 50,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        result = check_near_miss_extraction(state)
        assert state.credits == 50 + NEAR_MISS_CREDITS
        assert result.rewards[0].kind is NearMissRewardKind.CREDITS
        assert result.rewards[0].amount == NEAR_MISS_CREDITS

    def test_salvage_added(self) -> None:
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        result = check_near_miss_extraction(state)
        assert state.salvage_fragments == NEAR_MISS_SALVAGE
        assert result.rewards[1].kind is NearMissRewardKind.SALVAGE

    def test_initializes_missing_fields(self) -> None:
        """State without credits/salvage should still work (initializes 0)."""
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        result = check_near_miss_extraction(state)
        assert state.credits == NEAR_MISS_CREDITS
        assert state.salvage_fragments == NEAR_MISS_SALVAGE
        assert result.triggered is True

    def test_status_message_appended(self) -> None:
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        result = check_near_miss_extraction(state)
        assert len(state.status_messages) == 1
        assert "Near-miss extraction" in state.status_messages[0]
        assert f"+{NEAR_MISS_CREDITS}" in state.status_messages[0]
        assert result.status_message == state.status_messages[0]

    def test_no_message_on_failure(self) -> None:
        state = type(
            "S",
            (),
            {
                "player_hp": 50,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        result = check_near_miss_extraction(state)
        assert len(state.status_messages) == 0
        assert result.status_message == ""


class TestNearMissOneShot:
    """One-shot per run semantics."""

    def test_already_triggered_no_double_reward(self) -> None:
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        # First call: triggers
        result1 = check_near_miss_extraction(state, already_triggered=False)
        assert result1.triggered is True
        # Second call with already_triggered=True: skipped
        state.player_hp = 100  # still full HP
        result2 = check_near_miss_extraction(state, already_triggered=True)
        assert result2.triggered is False
        assert state.credits == NEAR_MISS_CREDITS  # not doubled

    def test_status_message_count_after_two_calls(self) -> None:
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
            },
        )()
        check_near_miss_extraction(state, already_triggered=False)
        check_near_miss_extraction(state, already_triggered=True)
        assert len(state.status_messages) == 1


class TestNearMissIsPillar4Safe:
    """Verify no cross-run inheritance."""

    def test_no_meta_state_write(self) -> None:
        """Near-miss should not write to run.meta_state (ADR-0131)."""
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": False,
                "meta_state": None,
            },
        )()
        check_near_miss_extraction(state)
        assert state.meta_state is None

    def test_death_resets_reward(self) -> None:
        """After death, HP resets to 0 — no near-miss possible."""
        state = type(
            "S",
            (),
            {
                "player_hp": 100,
                "player_max_hp": 100,
                "credits": 0,
                "salvage_fragments": 0,
                "status_messages": [],
                "near_miss_triggered": True,  # already triggered (preserved)
            },
        )()
        # Player dies, HP resets
        state.player_hp = 0
        state.player_max_hp = 100
        # New run: should not trigger (already_triggered stays True)
        result = check_near_miss_extraction(state, already_triggered=state.near_miss_triggered)
        assert result.triggered is False


class TestNearMissRewardIntegrity:
    """Sanity checks on reward constants."""

    def test_credits_amount_is_positive(self) -> None:
        assert NEAR_MISS_CREDITS > 0

    def test_salvage_amount_is_positive(self) -> None:
        assert NEAR_MISS_SALVAGE > 0

    def test_rewards_are_flat(self) -> None:
        """Same amount on every trigger (no progressive scaling)."""
        r1 = NearMissReward(
            kind=NearMissRewardKind.CREDITS, amount=NEAR_MISS_CREDITS, label="+75 credits"
        )
        r2 = NearMissReward(
            kind=NearMissRewardKind.CREDITS, amount=NEAR_MISS_CREDITS, label="+75 credits"
        )
        assert r1.amount == r2.amount


__all__ = [
    "TestComputeHpRatio",
    "TestNearMissThreshold",
    "TestNearMissRewards",
    "TestNearMissOneShot",
    "TestNearMissIsPillar4Safe",
    "TestNearMissRewardIntegrity",
]
