"""Tests for achievement system (achievements.py).

Validates:
- 28 achievement definitions
- 5 categories × tier distribution
- Achievement data structure (frozen, slots)
- AchievementState: unlock, progress, notifications
- Event-based check helpers (combat, exploration, story, mastery)
- Display helpers (render, summary)
- Hidden achievement behavior
"""

from __future__ import annotations

import pytest

from wet_run.achievements import (
    ACH_CENTURION,
    ACH_FIRST_BLOOD,
    ACH_GHOST_PROTOCOL,
    ACH_PHOENIX,
    ACH_TRUE_HACKER,
    ACH_VOID_WALKER,
    ACHIEVEMENT_BY_ID,
    ALL_ACHIEVEMENTS,
    AchievementCategory,
    AchievementState,
    AchievementTier,
    check_combat_event,
    check_exploration_event,
    check_mastery_event,
    check_story_event,
    get_achievement,
    get_achievements_by_category,
    get_achievements_summary,
    render_achievement,
)

# ----------------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------------


class TestRegistry:
    def test_total_count(self) -> None:
        # 7 combat + 6 exploration + 5 story + 6 mastery + 4 hidden = 28
        assert len(ALL_ACHIEVEMENTS) == 28

    def test_by_id_count_matches(self) -> None:
        assert len(ACHIEVEMENT_BY_ID) == len(ALL_ACHIEVEMENTS)

    def test_unique_ids(self) -> None:
        ids = [a.id for a in ALL_ACHIEVEMENTS]
        assert len(set(ids)) == len(ids)

    def test_all_have_required_fields(self) -> None:
        for ach in ALL_ACHIEVEMENTS:
            assert ach.id
            assert ach.name
            assert ach.name_ko
            assert ach.description
            assert ach.icon
            assert isinstance(ach.category, AchievementCategory)
            assert isinstance(ach.tier, AchievementTier)


# ----------------------------------------------------------------------------
# Category distribution
# ----------------------------------------------------------------------------


CATEGORY_COUNTS: list[tuple[AchievementCategory, int]] = [
    (AchievementCategory.COMBAT, 7),
    (AchievementCategory.EXPLORATION, 6),
    (AchievementCategory.STORY, 5),
    (AchievementCategory.MASTERY, 6),
    (AchievementCategory.HIDDEN, 4),
]


class TestCategoryDistribution:
    @pytest.mark.parametrize("case_idx", list(range(len(CATEGORY_COUNTS))))
    def test_count_per_category(self, case_idx: int) -> None:
        cat, expected = CATEGORY_COUNTS[case_idx]
        achs = get_achievements_by_category(cat, include_hidden=True)
        assert len(achs) == expected

    def test_hidden_excluded_by_default(self) -> None:
        hidden_achs = get_achievements_by_category(AchievementCategory.HIDDEN)
        assert len(hidden_achs) == 0

    def test_hidden_included_with_flag(self) -> None:
        hidden_achs = get_achievements_by_category(AchievementCategory.HIDDEN, include_hidden=True)
        assert len(hidden_achs) == 4

    def test_all_4_hidden_achievements_exist(self) -> None:
        assert ACH_GHOST_PROTOCOL.hidden is True
        assert ACH_PHOENIX.hidden is True
        assert ACH_VOID_WALKER.hidden is True
        assert ACH_TRUE_HACKER.hidden is True


# ----------------------------------------------------------------------------
# Tier distribution
# ----------------------------------------------------------------------------


TIER_MINS: list[tuple[AchievementTier, int]] = [
    (AchievementTier.BRONZE, 3),
    (AchievementTier.SILVER, 4),
    (AchievementTier.GOLD, 5),
    (AchievementTier.PLATINUM, 4),
]


class TestTierDistribution:
    @pytest.mark.parametrize("case_idx", list(range(len(TIER_MINS))))
    def test_tier_has_achievements(self, case_idx: int) -> None:
        tier, expected_min = TIER_MINS[case_idx]
        achs = [a for a in ALL_ACHIEVEMENTS if a.tier == tier]
        assert len(achs) >= expected_min


# ----------------------------------------------------------------------------
# Achievement dataclass
# ----------------------------------------------------------------------------


class TestAchievementDataclass:
    def test_frozen(self) -> None:
        import dataclasses

        with pytest.raises(dataclasses.FrozenInstanceError):
            ACH_FIRST_BLOOD.id = "hacked"  # type: ignore[misc]

    def test_slots(self) -> None:
        # Should be able to access all fields
        ach = ACH_FIRST_BLOOD
        assert ach.id == "first_blood"
        assert ach.name == "First Blood"
        assert ach.name_ko == "첫 피"


# ----------------------------------------------------------------------------
# get_achievement
# ----------------------------------------------------------------------------


class TestGetAchievement:
    def test_existing(self) -> None:
        assert get_achievement("first_blood") == ACH_FIRST_BLOOD

    def test_nonexistent(self) -> None:
        assert get_achievement("xyz_nonexistent") is None


# ----------------------------------------------------------------------------
# AchievementState
# ----------------------------------------------------------------------------


class TestAchievementState:
    def test_default_state(self) -> None:
        s = AchievementState()
        assert s.unlocked_ids == set()
        assert s.progress == {}
        assert s.notification_queue == []
        assert s.total_credits_earned == 0
        assert s.last_unlocked is None

    def test_unlock_first_time(self) -> None:
        s = AchievementState()
        ach = s.unlock("first_blood", current_ms=1000)
        assert ach is not None
        assert s.is_unlocked("first_blood")
        assert s.total_credits_earned == 50  # first_blood reward
        assert s.last_unlocked == ach

    def test_unlock_already_unlocked(self) -> None:
        s = AchievementState()
        s.unlock("first_blood")
        result = s.unlock("first_blood")
        assert result is None  # Already unlocked

    def test_unlock_nonexistent(self) -> None:
        s = AchievementState()
        result = s.unlock("xyz_nonexistent")
        assert result is None

    def test_set_progress(self) -> None:
        s = AchievementState()
        s.set_progress("ppl_progress", 25)
        assert s.get_progress("ppl_progress") == 25

    def test_unlock_progress_achievement(self) -> None:
        s = AchievementState()
        # ppl_10 unlocks at PPL >= 10
        result = s.unlock_progress_achievement("ppl_10", current_value=10, threshold=10)
        assert result is not None
        assert s.is_unlocked("ppl_10")

    def test_unlock_progress_below_threshold(self) -> None:
        s = AchievementState()
        result = s.unlock_progress_achievement("ppl_10", current_value=5, threshold=10)
        assert result is None
        assert not s.is_unlocked("ppl_10")
        assert s.get_progress("ppl_10") == 5

    def test_notification_queue(self) -> None:
        s = AchievementState()
        s.unlock("first_blood")
        s.unlock("first_jackin")
        notif = s.consume_notification()
        assert notif is not None
        notif2 = s.consume_notification()
        assert notif2 is not None
        notif3 = s.consume_notification()
        assert notif3 is None  # Queue empty

    def test_completion_stats(self) -> None:
        s = AchievementState()
        s.unlock("first_blood")
        s.unlock("case_journey")
        stats = s.get_completion_stats()
        assert stats["combat"] == 1
        assert stats["story"] == 1

    def test_total_unlocked(self) -> None:
        s = AchievementState()
        s.unlock("first_blood")
        s.unlock("case_journey")
        assert s.get_total_unlocked() == 2

    def test_completion_pct(self) -> None:
        s = AchievementState()
        s.unlock("first_blood")
        s.unlock("case_journey")
        # 2 / 28 ≈ 7.1%
        pct = s.get_completion_pct()
        assert 7.0 < pct < 7.5


# ----------------------------------------------------------------------------
# check_combat_event
# ----------------------------------------------------------------------------


class TestCheckCombatEvent:
    def test_first_ice_kill_unlocks_first_blood(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "ice_killed", value=1)
        assert any(a.id == "first_blood" for a in unlocked)

    def test_100_kills_unlocks_centurion(self) -> None:
        s = AchievementState()
        s.set_progress("centurion_progress", 99)
        # 99 + 1 = 100
        unlocked = check_combat_event(s, "ice_killed", value=1)
        assert any(a.id == "centurion" for a in unlocked)

    def test_10_crits_unlocks_sharpshooter(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "crit_hit", value=10)
        assert any(a.id == "sharpshooter" for a in unlocked)

    def test_max_combo_6_unlocks_combo_master(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "max_combo", value=6)
        assert any(a.id == "combo_master" for a in unlocked)

    def test_max_combo_50_unlocks_combo_quant(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "max_combo", value=50)
        assert any(a.id == "combo_master" for a in unlocked)
        assert any(a.id == "combo_quant" for a in unlocked)

    def test_boss_killed_unlocks_boss_slayer(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "boss_killed", value=1)
        assert any(a.id == "boss_slayer" for a in unlocked)

    def test_goliath_killed_unlocks_goliath_slayer(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "boss_killed", value="goliath_prime")
        assert any(a.id == "goliath_slayer" for a in unlocked)

    def test_black_ice_lord_unlocks_void_walker(self) -> None:
        s = AchievementState()
        unlocked = check_combat_event(s, "boss_killed", value="black_ice_lord")
        assert any(a.id == "void_walker" for a in unlocked)

    def test_10_wins_unlocks_undefeated(self) -> None:
        s = AchievementState()
        s.set_progress("undefeated_progress", 9)
        unlocked = check_combat_event(s, "won_fight", value=1)
        assert any(a.id == "undefeated" for a in unlocked)


# ----------------------------------------------------------------------------
# check_exploration_event
# ----------------------------------------------------------------------------


class TestCheckExplorationEvent:
    def test_jack_in_unlocks_first_jackin(self) -> None:
        s = AchievementState()
        unlocked = check_exploration_event(s, "jack_in", value=1)
        assert any(a.id == "first_jackin" for a in unlocked)

    def test_both_worlds_unlocks_world_walker(self) -> None:
        s = AchievementState()
        check_exploration_event(s, "visited_world", value=1)  # chiba
        unlocked = check_exploration_event(s, "visited_world", value=2)  # night city
        assert any(a.id == "world_walker" for a in unlocked)

    def test_all_servers_unlocks_domination(self) -> None:
        s = AchievementState()
        for i in range(6):
            check_exploration_event(s, "visited_server", value=i)
        assert s.is_unlocked("server_domination")

    def test_10_data_unlocks_extractor(self) -> None:
        s = AchievementState()
        unlocked = check_exploration_event(s, "data_extracted", value=10)
        assert any(a.id == "data_extractor" for a in unlocked)

    def test_10_jackouts_unlocks_survivor(self) -> None:
        s = AchievementState()
        s.set_progress("jackouts", 9)
        unlocked = check_exploration_event(s, "jack_out", value=1)
        assert any(a.id == "jackout_survivor" for a in unlocked)

    def test_50_nodes_unlocks_explorer(self) -> None:
        s = AchievementState()
        s.set_progress("nodes_visited", 49)
        unlocked = check_exploration_event(s, "node_visited", value=1)
        assert any(a.id == "matrix_explorer" for a in unlocked)


# ----------------------------------------------------------------------------
# check_story_event
# ----------------------------------------------------------------------------


PROLOGUE_CASES: list[tuple[str, str]] = [
    ("novice", "case_journey"),
    ("case", "case_journey"),
    ("veteran", "sil_awakening"),
    ("sil", "sil_awakening"),
    ("heretic", "kas_rise"),
    ("kas", "kas_rise"),
]


class TestCheckStoryEvent:
    @pytest.mark.parametrize("case_idx", list(range(len(PROLOGUE_CASES))))
    def test_prologues(self, case_idx: int) -> None:
        char_id, ach_id = PROLOGUE_CASES[case_idx]
        s = AchievementState()
        unlocked = check_story_event(s, "prologue_complete", value=char_id)
        assert any(a.id == ach_id for a in unlocked)

    def test_5_stories_unlocks_five_tales(self) -> None:
        s = AchievementState()
        # Use 5 different story IDs
        for i in range(5):
            check_story_event(s, "story_read", value=f"story_{i}")
        assert s.is_unlocked("five_tales")

    def test_3_endings_unlocks_truth(self) -> None:
        s = AchievementState()
        check_story_event(s, "ending_unlocked", value="success")
        check_story_event(s, "ending_unlocked", value="failure")
        unlocked = check_story_event(s, "ending_unlocked", value="hidden")
        assert any(a.id == "the_truth" for a in unlocked)


# ----------------------------------------------------------------------------
# check_mastery_event
# ----------------------------------------------------------------------------


PPL_CASES: list[tuple[int, str]] = [
    (10, "ppl_10"),
    (20, "ppl_20"),
    (30, "ppl_30"),
]


class TestCheckMasteryEvent:
    @pytest.mark.parametrize("case_idx", list(range(len(PPL_CASES))))
    def test_ppl_milestones(self, case_idx: int) -> None:
        ppl, expected_ach = PPL_CASES[case_idx]
        s = AchievementState()
        unlocked = check_mastery_event(s, "ppl_reached", value=ppl)
        assert any(a.id == expected_ach for a in unlocked)

    def test_ppl_30_unlocks_all_lower_tiers(self) -> None:
        s = AchievementState()
        unlocked = check_mastery_event(s, "ppl_reached", value=30)
        unlocked_ids = {a.id for a in unlocked}
        assert "ppl_10" in unlocked_ids
        assert "ppl_20" in unlocked_ids
        assert "ppl_30" in unlocked_ids

    def test_matrix_master_ppl_zdr_combined(self) -> None:
        """PPL + ZDR >= 60 (one fight) unlocks matrix_master."""
        from wet_run.achievements import (
            ACH_MATRIX_MASTER,
            check_mastery_event,
            check_matrix_master,
        )

        # Insufficient: 25 + 25 = 50 < 60
        assert check_matrix_master(AchievementState(), 25, 25) is None
        # Exact: 30 + 30 = 60 → unlocks
        ach = check_matrix_master(AchievementState(), 30, 30)
        assert ach is not None
        assert ach.id == ACH_MATRIX_MASTER.id
        # Via the event-style API:
        ach2 = check_mastery_event(AchievementState(), "ppl_zdr_combined", value=60)
        assert any(a.id == "matrix_master" for a in ach2)

    def test_true_hacker_unlocks_when_all_others_unlocked(self) -> None:
        """Unlocking every other achievement triggers true_hacker."""
        from wet_run.achievements import (
            ACH_TRUE_HACKER,
            ALL_ACHIEVEMENTS,
            check_true_hacker,
        )

        s = AchievementState()
        # Initially not unlocked.
        assert check_true_hacker(s) is None
        # Unlock every other achievement.
        for ach in ALL_ACHIEVEMENTS:
            if ach.id == ACH_TRUE_HACKER.id:
                continue  # skip self
            s.unlock(ach.id)
        # Now true_hacker should unlock.
        ach = check_true_hacker(s)
        assert ach is not None
        assert ach.id == ACH_TRUE_HACKER.id

    def test_true_hacker_not_triggered_via_event_when_not_all_unlocked(
        self,
    ) -> None:
        """Event-style call must NOT unlock true_hacker prematurely."""
        from wet_run.achievements import (
            ACH_MATRIX_MASTER,
            ACH_TRUE_HACKER,
            ALL_ACHIEVEMENTS,
            check_mastery_event,
        )

        s = AchievementState()
        # Unlock fewer than ALL_ACHIEVEMENTS - 1 (skip both
        # true_hacker and matrix_master so the combined check still
        # has matrix_master to potentially fire).
        for ach in ALL_ACHIEVEMENTS[:20]:
            if ach.id in (ACH_TRUE_HACKER.id, ACH_MATRIX_MASTER.id):
                continue
            s.unlock(ach.id)
        # Fire the event — should unlock matrix_master (value 70 ≥ 60)
        # but NOT true_hacker (insufficient unlocks).
        unlocked = check_mastery_event(s, "ppl_zdr_combined", value=70)
        unlocked_ids = {a.id for a in unlocked}
        assert "matrix_master" in unlocked_ids
        assert "true_hacker" not in unlocked_ids
        assert not s.is_unlocked(ACH_TRUE_HACKER.id)

    def test_zdr_cleared_tracks_max(self) -> None:
        """Repeated zdr_cleared events keep the highest value."""
        from wet_run.achievements import check_mastery_event

        s = AchievementState()
        check_mastery_event(s, "zdr_cleared", value=10)
        check_mastery_event(s, "zdr_cleared", value=25)
        check_mastery_event(s, "zdr_cleared", value=15)  # should not decrease
        assert s.get_progress("max_zdr_cleared") == 25

    def test_combined_event_unlocks_true_hacker(self) -> None:
        """When all others unlocked, ppl_zdr_combined event triggers true_hacker."""
        from wet_run.achievements import (
            ACH_MATRIX_MASTER,
            ACH_TRUE_HACKER,
            ALL_ACHIEVEMENTS,
            check_mastery_event,
        )

        s = AchievementState()
        for ach in ALL_ACHIEVEMENTS:
            if ach.id in (ACH_TRUE_HACKER.id, ACH_MATRIX_MASTER.id):
                continue  # skip self + already-eligible
            s.unlock(ach.id)
        # Fire the event — it should unlock matrix_master AND true_hacker.
        unlocked = check_mastery_event(s, "ppl_zdr_combined", value=70)
        unlocked_ids = {a.id for a in unlocked}
        assert "matrix_master" in unlocked_ids
        assert "true_hacker" in unlocked_ids


# ----------------------------------------------------------------------------
# Display helpers
# ----------------------------------------------------------------------------


class TestDisplayHelpers:
    def test_render_unlocked(self) -> None:
        text = render_achievement(ACH_FIRST_BLOOD, unlocked=True)
        assert "✅" in text
        assert "첫 피" in text
        assert "BRONZE" in text

    def test_render_locked(self) -> None:
        text = render_achievement(ACH_FIRST_BLOOD, unlocked=False)
        assert "🔒" in text
        assert "첫 피" in text

    def test_render_shows_credits(self) -> None:
        text = render_achievement(ACH_CENTURION, unlocked=False)
        assert "1500 크레딧" in text

    def test_get_achievements_summary(self) -> None:
        s = AchievementState()
        s.unlock("first_blood")
        s.unlock("case_journey")
        summary = get_achievements_summary(s)
        assert summary["total_unlocked"] == 2
        assert summary["total_available"] == 28
        assert summary["credits_earned"] == 150  # 50 + 100
        assert "by_category" in summary


# ----------------------------------------------------------------------------
# Specific achievement data validation
# ----------------------------------------------------------------------------


class TestSpecificAchievements:
    def test_first_blood_bronze(self) -> None:
        assert ACH_FIRST_BLOOD.tier == AchievementTier.BRONZE
        assert ACH_FIRST_BLOOD.reward_credits == 50
        assert ACH_FIRST_BLOOD.category == AchievementCategory.COMBAT

    def test_platinum_achievements_have_high_rewards(self) -> None:
        platinum_achs = [a for a in ALL_ACHIEVEMENTS if a.tier == AchievementTier.PLATINUM]
        for ach in platinum_achs:
            assert ach.reward_credits >= 2000

    def test_combat_achievements_are_combat_category(self) -> None:
        for ach_id in (
            "first_blood",
            "sharpshooter",
            "combo_master",
            "undefeated",
            "boss_slayer",
            "goliath_slayer",
            "centurion",
        ):
            ach = get_achievement(ach_id)
            assert ach is not None
            assert ach.category == AchievementCategory.COMBAT

    def test_story_achievements_have_story_category(self) -> None:
        for ach_id in ("case_journey", "sil_awakening", "kas_rise", "five_tales", "the_truth"):
            ach = get_achievement(ach_id)
            assert ach is not None
            assert ach.category == AchievementCategory.STORY


# ----------------------------------------------------------------------------
# Integration smoke
# ----------------------------------------------------------------------------


class TestIntegration:
    def test_full_combat_session(self) -> None:
        """Simulate a full combat session: 1 kill, 10 crits, 6 combo."""
        s = AchievementState()
        check_combat_event(s, "ice_killed", value=1)
        check_combat_event(s, "crit_hit", value=10)
        check_combat_event(s, "max_combo", value=6)
        check_combat_event(s, "won_fight", value=1)
        assert s.get_total_unlocked() >= 3
        assert s.total_credits_earned > 0

    def test_korean_names_present(self) -> None:
        """All achievements should have Korean names."""
        for ach in ALL_ACHIEVEMENTS:
            # Check that name_ko contains at least one Korean character
            assert any("\uac00" <= c <= "\ud7a3" for c in ach.name_ko), (
                f"{ach.id} missing Korean name"
            )

    def test_completion_pct_progression(self) -> None:
        s1 = AchievementState()
        s2 = AchievementState()
        s2.unlock("first_blood")
        assert s2.get_completion_pct() > s1.get_completion_pct()
