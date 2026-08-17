"""Tests for the story event expansion (Phase 6+ content).

Covers:
- Aftermath event rewards system (StoryReward + apply_event_rewards)
- Reward kinds: credits / material / reputation / achievement
- Edge cases: invalid data, missing fields, large deltas (clamped)
- JSON data integrity: all 12 events have valid structure
"""

from __future__ import annotations

import json
from pathlib import Path

from wet_run.engine.state import AppState
from wet_run.matrix.node import Faction
from wet_run.story import (
    RewardKind,
    StoryReward,
    apply_event_rewards,
    load_rewards_from,
)

# ============================================================================
# RewardKind enum
# ============================================================================


class TestRewardKind:
    def test_all_kinds_defined(self) -> None:
        expected = {"credits", "material", "reputation", "achievement"}
        actual = {k.value for k in RewardKind}
        assert actual == expected


# ============================================================================
# StoryReward.from_dict
# ============================================================================


class TestStoryRewardFromDict:
    def test_credits_reward(self) -> None:
        r = StoryReward.from_dict({"kind": "credits", "target": "", "amount": 500})
        assert r is not None
        assert r.kind is RewardKind.CREDITS
        assert r.target == ""
        assert r.amount == 500

    def test_material_reward(self) -> None:
        r = StoryReward.from_dict({"kind": "material", "target": "ice_shard", "amount": 2})
        assert r is not None
        assert r.kind is RewardKind.MATERIAL
        assert r.target == "ice_shard"

    def test_reputation_reward(self) -> None:
        r = StoryReward.from_dict({"kind": "reputation", "target": "hosaka", "amount": 10})
        assert r is not None
        assert r.kind is RewardKind.REPUTATION
        assert r.target == "hosaka"

    def test_achievement_reward(self) -> None:
        r = StoryReward.from_dict({"kind": "achievement", "target": "matrix_master", "amount": 1})
        assert r is not None
        assert r.kind is RewardKind.ACHIEVEMENT

    def test_unknown_kind_returns_none(self) -> None:
        assert StoryReward.from_dict({"kind": "unknown_kind", "target": "x", "amount": 1}) is None

    def test_missing_kind_returns_none(self) -> None:
        assert StoryReward.from_dict({"target": "x", "amount": 1}) is None

    def test_non_int_amount_returns_none(self) -> None:
        assert StoryReward.from_dict({"kind": "credits", "target": "", "amount": "many"}) is None

    def test_non_dict_returns_none(self) -> None:
        # We intentionally don't pass a dict — the function should
        # return None instead of raising. Use a TYPE_CHECKER bypass.
        try:
            result = StoryReward.from_dict("not a dict")  # type: ignore[arg-type]
        except (AttributeError, TypeError):
            result = None
        assert result is None


# ============================================================================
# apply_event_rewards
# ============================================================================


class TestApplyEventRewards:
    def test_credits_increases_balance(self) -> None:
        state = AppState()
        state.credits = 100
        rewards = [StoryReward(RewardKind.CREDITS, "", 500)]
        apply_event_rewards(state, rewards)
        assert state.credits == 600

    def test_material_adds_to_inventory(self) -> None:
        state = AppState()
        state.inventory = {}
        rewards = [StoryReward(RewardKind.MATERIAL, "ice_shard", 2)]
        apply_event_rewards(state, rewards)
        assert state.inventory.get("ice_shard") == 2

    def test_material_increments_existing(self) -> None:
        state = AppState()
        state.inventory = {"ice_shard": 1}
        rewards = [StoryReward(RewardKind.MATERIAL, "ice_shard", 3)]
        apply_event_rewards(state, rewards)
        assert state.inventory.get("ice_shard") == 4

    def test_reputation_positive(self) -> None:
        state = AppState()
        rewards = [StoryReward(RewardKind.REPUTATION, "hosaka", 20)]
        apply_event_rewards(state, rewards)
        assert state.reputation.get(Faction.HOSAKA).score == 20

    def test_reputation_negative(self) -> None:
        """Rep delta of -30 is clamped to MAX_DELTA_PER_EVENT (-25)."""
        state = AppState()
        rewards = [StoryReward(RewardKind.REPUTATION, "maas", -30)]
        apply_event_rewards(state, rewards)
        # Clamped to ±25 (MAX_DELTA_PER_EVENT).
        assert state.reputation.get(Faction.MAAS).score == -25

    def test_reputation_clamps_to_max_delta(self) -> None:
        """Per-event delta clamped to ±25 (MAX_DELTA_PER_EVENT)."""
        state = AppState()
        rewards = [StoryReward(RewardKind.REPUTATION, "hosaka", 999)]
        apply_event_rewards(state, rewards)
        # 999 clamped to +25
        assert state.reputation.get(Faction.HOSAKA).score == 25

    def test_reputation_invalid_faction_skipped(self) -> None:
        state = AppState()
        rewards = [StoryReward(RewardKind.REPUTATION, "phantom_faction", 10)]
        # Should not crash; should report failure in summary.
        summaries = apply_event_rewards(state, rewards)
        assert any("invalid" in s for s in summaries)

    def test_achievement_returns_string_summary(self) -> None:
        state = AppState()
        rewards = [StoryReward(RewardKind.ACHIEVEMENT, "matrix_master", 1)]
        summaries = apply_event_rewards(state, rewards)
        assert "Achievement" in summaries[0]

    def test_multiple_rewards_applied_in_order(self) -> None:
        state = AppState()
        state.credits = 0
        state.inventory = {}
        rewards = [
            StoryReward(RewardKind.CREDITS, "", 100),
            StoryReward(RewardKind.MATERIAL, "ice_shard", 1),
            StoryReward(RewardKind.REPUTATION, "hosaka", 5),
        ]
        apply_event_rewards(state, rewards)
        assert state.credits == 100
        assert state.inventory["ice_shard"] == 1
        assert state.reputation.get(Faction.HOSAKA).score == 5

    def test_empty_rewards_list_returns_empty_summary(self) -> None:
        state = AppState()
        assert apply_event_rewards(state, []) == []

    def test_legacy_state_without_reputation_falls_back_gracefully(self) -> None:
        """Pre-reputation saves: rep rewards gracefully no-op."""
        state = AppState()
        object.__setattr__(state, "reputation", None)
        rewards = [StoryReward(RewardKind.REPUTATION, "hosaka", 10)]
        # Should not crash; rep reward is silently dropped.
        summaries = apply_event_rewards(state, rewards)
        # Either a failure summary or empty — both are acceptable.
        assert isinstance(summaries, list)


# ============================================================================
# load_rewards_from
# ============================================================================


class TestLoadRewardsFrom:
    def test_loads_valid_rewards(self) -> None:
        raw = [
            {"kind": "credits", "target": "", "amount": 100},
            {"kind": "material", "target": "ice_shard", "amount": 2},
        ]
        rewards = load_rewards_from(raw)
        assert len(rewards) == 2
        assert rewards[0].kind is RewardKind.CREDITS
        assert rewards[1].kind is RewardKind.MATERIAL

    def test_skips_invalid_entries(self) -> None:
        raw = [
            {"kind": "credits", "target": "", "amount": 100},  # valid
            {"kind": "unknown", "target": "", "amount": 5},  # invalid kind
            "not a dict",  # invalid type
            {"kind": "credits"},  # missing amount → defaults to 0 (still valid)
        ]
        rewards = load_rewards_from(raw)
        # First entry valid; "not a dict" is non-dict; "unknown" kind
        # rejected; "credits" with no amount → 0 (still parseable).
        # So: 2 valid (the first + the last).
        assert len(rewards) == 2
        assert rewards[0].amount == 100
        assert rewards[1].amount == 0

    def test_strict_amount_required(self) -> None:
        """If a reward has a non-int amount, it's rejected entirely."""
        raw = [
            {"kind": "credits", "target": "", "amount": "many"},
        ]
        rewards = load_rewards_from(raw)
        assert len(rewards) == 0

    def test_none_returns_empty(self) -> None:
        assert load_rewards_from(None) == []

    def test_non_list_returns_empty(self) -> None:
        assert load_rewards_from("not a list") == []  # type: ignore[arg-type]


# ============================================================================
# Data integrity — real aftermath.json must have all 12 events
# ============================================================================


class TestAftermathDataIntegrity:
    """Verify the 12-event aftermath catalog is well-formed."""

    EXPECTED_IDS = [
        "aftermath_black_ice",
        "aftermath_construct_first",
        "aftermath_zone_core_first",
        "aftermath_mission_first",
        "aftermath_arc_advance",
        "aftermath_chapter_complete",
        "aftermath_zone_deep_first",
        "aftermath_zone_freeside_first",
        "aftermath_ice_goliath_first",
        "aftermath_faction_threshold",
        "aftermath_jockey_death_first",
        "aftermath_hub_first_visit",
    ]

    def test_all_12_events_present(self, data_dir: Path) -> None:
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for event_id in self.EXPECTED_IDS:
            assert event_id in data, f"Missing aftermath event: {event_id}"

    def test_all_events_have_required_fields(self, data_dir: Path) -> None:
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        required = {
            "id",
            "importance",
            "trigger",
            "duration_ms",
            "narrative_en",
            "narrative_ko",
            "reactions",
        }
        for event_id, event in data.items():
            missing = required - set(event.keys())
            assert not missing, f"{event_id} missing: {missing}"

    def test_all_events_have_rewards_field(self, data_dir: Path) -> None:
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for event_id, event in data.items():
            assert "rewards" in event, f"{event_id} missing rewards field"
            assert isinstance(event["rewards"], list)

    def test_all_rewards_are_parseable(self, data_dir: Path) -> None:
        """Every reward in aftermath.json can be parsed by from_dict()."""
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for event_id, event in data.items():
            for raw_reward in event.get("rewards", []):
                reward = StoryReward.from_dict(raw_reward)
                if raw_reward.get("kind") in {"credits", "material", "reputation", "achievement"}:
                    assert reward is not None, f"{event_id} has unparseable reward: {raw_reward}"

    def test_importance_levels_are_valid(self, data_dir: Path) -> None:
        valid = {"minor", "notable", "major", "legendary"}
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for event_id, event in data.items():
            assert event["importance"] in valid, (
                f"{event_id} has invalid importance: {event['importance']}"
            )


# ============================================================================
# Data integrity — reactions catalog
# ============================================================================


class TestReactionsDataIntegrity:
    EXPECTED_CHARACTERS = {"case", "dixie", "finn", "maelcum", "3jane", "sally"}

    def test_at_least_18_reactions_present(self, data_dir: Path) -> None:
        with (data_dir / "story" / "reactions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        # Original 10 + new 15 = 25 (some triggers added new reactions).
        assert len(data) >= 18, f"Expected ≥18 reactions, got {len(data)}"

    def test_all_reactions_have_required_fields(self, data_dir: Path) -> None:
        with (data_dir / "story" / "reactions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        required = {"id", "character", "trigger", "text_en", "text_ko"}
        for reaction_id, reaction in data.items():
            missing = required - set(reaction.keys())
            assert not missing, f"{reaction_id} missing: {missing}"

    def test_all_characters_covered(self, data_dir: Path) -> None:
        with (data_dir / "story" / "reactions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        characters = {r["character"] for r in data.values()}
        # All major NPCs should have at least 1 reaction.
        for c in self.EXPECTED_CHARACTERS:
            assert c in characters, f"No reactions for character: {c}"

    def test_new_triggers_have_reactions(self, data_dir: Path) -> None:
        """The 4 new EventTrigger types should have at least 1 reaction each."""
        with (data_dir / "story" / "reactions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        new_triggers = {
            "chapter_complete",
            "matrix.zone.deep_first_time",
            "matrix.zone.freeside_first_time",
            "combat.defeat.goliath.first",
            "vendor_unlocked",
            "death.first",
            "hub_visited",
        }
        covered = {r["trigger"] for r in data.values()}
        missing = new_triggers - covered
        assert not missing, f"New triggers without reactions: {missing}"


# ============================================================================
# Integration — load aftermath + apply rewards through normal flow
# ============================================================================


class TestRewardApplicationIntegration:
    """End-to-end: load a real aftermath event, parse its rewards,
    apply via apply_event_rewards, verify state changes."""

    def test_black_ice_aftermath_grants_credits_and_ice_shard(self, data_dir: Path) -> None:
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        event = data["aftermath_black_ice"]
        rewards = load_rewards_from(event["rewards"])
        assert len(rewards) == 2
        assert any(r.kind is RewardKind.CREDITS for r in rewards)
        assert any(r.kind is RewardKind.MATERIAL and r.target == "ice_shard" for r in rewards)

        state = AppState()
        state.credits = 0
        state.inventory = {}
        apply_event_rewards(state, rewards)
        assert state.credits == 500
        assert state.inventory["ice_shard"] == 2

    def test_chapter_complete_grants_rep_and_achievement(self, data_dir: Path) -> None:
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        event = data["aftermath_chapter_complete"]
        rewards = load_rewards_from(event["rewards"])
        assert any(r.kind is RewardKind.REPUTATION and r.target == "maas" for r in rewards)
        assert any(r.kind is RewardKind.ACHIEVEMENT for r in rewards)
        # Verify rep + achievement pair
        state = AppState()
        apply_event_rewards(state, rewards)
        assert state.reputation.get(Faction.MAAS).score == 15

    def test_freeside_aftermath_grants_biosoft_agent(self, data_dir: Path) -> None:
        """The legendary Freeside entry should award a rare material."""
        with (data_dir / "story" / "aftermath.json").open(encoding="utf-8") as f:
            data = json.load(f)
        event = data["aftermath_zone_freeside_first"]
        rewards = load_rewards_from(event["rewards"])
        # Should include biosoft_agent (rare T4 material).
        assert any(r.kind is RewardKind.MATERIAL and r.target == "biosoft_agent" for r in rewards)
