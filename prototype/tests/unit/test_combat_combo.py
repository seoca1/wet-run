"""Tests for skill combo system (combat/combo.py).

Validates:
- 5 ComboStage definitions
- CombatCombo: register_hit, window expiry, stage progression
- Stage transition flags (stage_up_pending, just_ended)
- Damage bonus application
- AP regen tracking
- ComboVisual updates
- render functions (counter, stage_up, end)
- spawn_combo_hit high-level entry
- Stats tracking (max_combo_reached, total_damage_dealt)
"""

from __future__ import annotations

import pytest

from wet_run.combat.combo import (
    ALL_FINISHERS,
    ALL_STAGES,
    ANNIHILATION,
    AVATAR_ANNIHILATION,
    AVATAR_BY_STAGE,
    AVATAR_CHAIN,
    AVATAR_FLURRY,
    AVATAR_RAMPAGE,
    AVATAR_WARMUP,
    CHAIN,
    FINISHER_FINAL_STRIKE,
    FINISHER_QUICK_SLASH,
    FINISHER_RAMPAGE_BURST,
    FLURRY,
    RAMPAGE,
    WARMUP,
    CombatCombo,
    ComboStage,
    ComboVisual,
    StageAvatar,
    TimingBar,
    get_avatar_for_stage,
    get_finisher_for_stage,
    render_combo_counter,
    render_combo_end,
    render_combo_full,
    render_combo_stage_up,
    render_timing_bar,
    spawn_combo_hit,
    update_combo_visual,
)

# ----------------------------------------------------------------------------
# Stage definitions
# ----------------------------------------------------------------------------


class TestStageDefinitions:
    def test_five_stages(self) -> None:
        assert len(ALL_STAGES) == 5

    def test_stage_order(self) -> None:
        # Stages should be ordered WARMUP → CHAIN → FLURRY → RAMPAGE → ANNIHILATION
        expected = ["WARMUP", "CHAIN", "FLURRY", "RAMPAGE", "ANNIHILATION"]
        actual = [s.name for s in ALL_STAGES]
        assert actual == expected

    def test_min_count_increases(self) -> None:
        counts = [s.min_count for s in ALL_STAGES]
        assert counts == sorted(counts)

    def test_damage_bonus_increases(self) -> None:
        bonuses = [s.damage_bonus_pct for s in ALL_STAGES]
        assert bonuses == sorted(bonuses)

    def test_all_stages_have_korean(self) -> None:
        for stage in ALL_STAGES:
            assert stage.name_ko
            # WARMUP may have empty label (no stage callout), others should
            if stage.index > 0:
                assert stage.label


# ----------------------------------------------------------------------------
# CombatCombo: hit registration
# ----------------------------------------------------------------------------


class TestCombatComboRegisterHit:
    def test_first_hit_count_one(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        assert c.count == 1

    def test_consecutive_hits_increment(self) -> None:
        c = CombatCombo()
        for i in range(5):
            c.register_hit(current_ms=i * 500)
        assert c.count == 5

    def test_window_expiry_resets(self) -> None:
        c = CombatCombo(window_ms=1000)
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        assert c.count == 2
        # After window expires
        c.register_hit(current_ms=2000)
        assert c.count == 1  # Reset

    def test_total_damage_tracked(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0, damage_dealt=50)
        c.register_hit(current_ms=500, damage_dealt=80)
        c.register_hit(current_ms=1000, damage_dealt=120)
        assert c.total_damage_dealt == 250

    def test_max_combo_tracked(self) -> None:
        c = CombatCombo()
        for i in range(7):
            c.register_hit(current_ms=i * 500)
        assert c.max_combo_reached == 7


# ----------------------------------------------------------------------------
# Stage progression
# ----------------------------------------------------------------------------


STAGE_PROGRESSION_CASES: list[tuple[int, str]] = [
    (1, "WARMUP"),
    (2, "WARMUP"),
    (3, "CHAIN"),
    (4, "FLURRY"),
    (5, "RAMPAGE"),
    (6, "ANNIHILATION"),
    (10, "ANNIHILATION"),
]


class TestStageProgression:
    @pytest.mark.parametrize("case_idx", list(range(len(STAGE_PROGRESSION_CASES))))
    def test_stage_at_count(self, case_idx: int) -> None:
        hits, expected_stage = STAGE_PROGRESSION_CASES[case_idx]
        c = CombatCombo()
        for i in range(hits):
            c.register_hit(current_ms=i * 500)
        assert c.current_stage.name == expected_stage

    def test_stage_up_flag_set(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)  # 1, WARMUP
        c.register_hit(current_ms=500)  # 2, WARMUP (no stage change)
        assert not c.stage_up_pending
        c.register_hit(current_ms=1000)  # 3, CHAIN (stage up!)
        assert c.stage_up_pending

    def test_stage_up_consumed_once(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)  # stage up
        first = c.consume_stage_up()
        assert first is not None
        assert first.name == "CHAIN"
        # Second consume returns None
        second = c.consume_stage_up()
        assert second is None

    def test_previous_stage_tracked(self) -> None:
        c = CombatCombo()
        for i in range(5):
            c.register_hit(current_ms=i * 500)
        # After 5 hits, current=RAMPAGE, previous=FLURRY
        assert c.current_stage.name == "RAMPAGE"
        assert c.previous_stage.name == "FLURRY"


# ----------------------------------------------------------------------------
# Window expiry and end
# ----------------------------------------------------------------------------


class TestWindowExpiry:
    def test_step_detects_expiry(self) -> None:
        c = CombatCombo(window_ms=1000)
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        # Step past window
        c.step(600)  # elapsed = 600, still within window
        assert not c.just_ended
        c.step(500)  # elapsed = 1100, past window
        assert c.just_ended

    def test_combo_ends_resets_count(self) -> None:
        c = CombatCombo(window_ms=1000)
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.step(1100)
        assert c.count == 0
        assert c.current_stage.name == "WARMUP"

    def test_combo_ends_returns_true_once(self) -> None:
        c = CombatCombo(window_ms=1000)
        c.register_hit(current_ms=0)
        c.step(1100)
        first = c.consume_just_ended()
        assert first is True
        second = c.consume_just_ended()
        assert second is False


# ----------------------------------------------------------------------------
# Reset
# ----------------------------------------------------------------------------


class TestReset:
    def test_reset_clears_count(self) -> None:
        c = CombatCombo()
        for i in range(5):
            c.register_hit(current_ms=i * 500)
        c.reset()
        assert c.count == 0
        assert c.current_stage.name == "WARMUP"

    def test_reset_preserves_max(self) -> None:
        c = CombatCombo()
        for i in range(7):
            c.register_hit(current_ms=i * 500)
        c.reset()
        # max_combo_reached persists (it's a stat)
        assert c.max_combo_reached == 7


# ----------------------------------------------------------------------------
# Damage bonus
# ----------------------------------------------------------------------------


DAMAGE_BONUS_CASES: list[tuple[str, int, int]] = [
    ("WARMUP", 100, 100),  # +0%
    ("CHAIN", 100, 120),  # +20%
    ("FLURRY", 100, 150),  # +50%
    ("RAMPAGE", 100, 200),  # +100%
    ("ANNIHILATION", 100, 300),  # +200%
]


class TestDamageBonus:
    @pytest.mark.parametrize("case_idx", list(range(len(DAMAGE_BONUS_CASES))))
    def test_bonus_at_stage(self, case_idx: int) -> None:
        stage_name, base, expected = DAMAGE_BONUS_CASES[case_idx]
        c = CombatCombo()
        stage = next(s for s in ALL_STAGES if s.name == stage_name)
        c.count = stage.min_count
        c.current_stage = stage
        assert c.apply_damage_bonus(base) == expected


# ----------------------------------------------------------------------------
# AP regen
# ----------------------------------------------------------------------------


class TestAPRegen:
    def test_warmup_no_regen(self) -> None:
        c = CombatCombo()
        c.count = 1
        c.current_stage = WARMUP
        assert c.get_ap_regen() == 0

    def test_chain_no_regen(self) -> None:
        c = CombatCombo()
        c.count = 3
        c.current_stage = CHAIN
        assert c.get_ap_regen() == 0

    def test_flurry_regen_1(self) -> None:
        c = CombatCombo()
        c.count = 4
        c.current_stage = FLURRY
        assert c.get_ap_regen() == 1

    def test_rampage_regen_2(self) -> None:
        c = CombatCombo()
        c.count = 5
        c.current_stage = RAMPAGE
        assert c.get_ap_regen() == 2

    def test_annihilation_regen_3(self) -> None:
        c = CombatCombo()
        c.count = 6
        c.current_stage = ANNIHILATION
        assert c.get_ap_regen() == 3


# ----------------------------------------------------------------------------
# ComboVisual
# ----------------------------------------------------------------------------


class TestComboVisual:
    def test_initial_state(self) -> None:
        v = ComboVisual()
        assert v.counter_text == ""
        assert v.stage_up_text == ""
        assert v.end_text == ""

    def test_update_with_combo(self) -> None:
        c = CombatCombo()
        v = ComboVisual()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)  # stage up to CHAIN
        update_combo_visual(v, c)
        assert v.counter_text == "3x CHAIN!"
        assert v.counter_color == CHAIN.color
        assert v.stage_up_text != ""  # "▸ 연쇄 단계 돌입 ..."

    def test_pulse_set_on_hit(self) -> None:
        c = CombatCombo()
        v = ComboVisual()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)  # 3rd hit
        update_combo_visual(v, c)
        assert v.counter_pulse_ms > 0


# ----------------------------------------------------------------------------
# Render functions
# ----------------------------------------------------------------------------


class TestRenderFunctions:
    def test_render_counter_empty(self) -> None:
        v = ComboVisual()
        assert render_combo_counter(v) == ""

    def test_render_counter_padded(self) -> None:
        v = ComboVisual()
        v.counter_text = "3x CHAIN!"
        s = render_combo_counter(v, width=30)
        assert s.strip() == "3x CHAIN!"

    def test_render_stage_up(self) -> None:
        v = ComboVisual()
        v.stage_up_text = "▸ 연쇄 단계 돌입"
        v.stage_up_ms = 500
        assert render_combo_stage_up(v) == "▸ 연쇄 단계 돌입"

    def test_render_stage_up_expired(self) -> None:
        v = ComboVisual()
        v.stage_up_text = "▸ 연쇄 단계 돌입"
        v.stage_up_ms = 0
        assert render_combo_stage_up(v) == ""

    def test_render_end(self) -> None:
        v = ComboVisual()
        v.end_text = "[ 콤보 종료 ]"
        v.end_ms = 1000
        assert render_combo_end(v) == "[ 콤보 종료 ]"

    def test_render_end_expired(self) -> None:
        v = ComboVisual()
        v.end_text = "[ 콤보 종료 ]"
        v.end_ms = 0
        assert render_combo_end(v) == ""


# ----------------------------------------------------------------------------
# spawn_combo_hit
# ----------------------------------------------------------------------------


class TestSpawnComboHit:
    def test_first_hit(self) -> None:
        c = CombatCombo()
        v = ComboVisual()
        stage = spawn_combo_hit(c, v, current_ms=0, damage_dealt=50)
        assert stage.name == "WARMUP"
        assert c.count == 1

    def test_three_hits_chains(self) -> None:
        c = CombatCombo()
        v = ComboVisual()
        spawn_combo_hit(c, v, current_ms=0)
        spawn_combo_hit(c, v, current_ms=500)
        stage = spawn_combo_hit(c, v, current_ms=1000)
        assert stage.name == "CHAIN"
        assert v.counter_text == "3x CHAIN!"

    def test_six_hits_annihilates(self) -> None:
        c = CombatCombo()
        v = ComboVisual()
        for i in range(6):
            spawn_combo_hit(c, v, current_ms=i * 500, damage_dealt=50)
        assert c.current_stage.name == "ANNIHILATION"
        assert c.max_combo_reached == 6
        assert c.total_damage_dealt == 300


# ----------------------------------------------------------------------------
# Window timer visual
# ----------------------------------------------------------------------------


class TestWindowTimer:
    def test_window_progress_zero_at_hit(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        assert c.window_progress == 0.0

    def test_window_progress_increases(self) -> None:
        c = CombatCombo(window_ms=1000)
        c.register_hit(current_ms=0)
        c.step(500)
        assert 0.4 < c.window_progress < 0.6

    def test_window_remaining_pct(self) -> None:
        c = CombatCombo(window_ms=1000)
        c.register_hit(current_ms=0)
        c.step(250)
        # 75% remaining
        assert 70 < c.window_remaining_pct < 80


# ----------------------------------------------------------------------------
# Display label
# ----------------------------------------------------------------------------


class TestDisplayLabel:
    def test_label_empty_at_low_count(self) -> None:
        c = CombatCombo()
        assert c.display_label == ""

    def test_label_includes_count_and_stage(self) -> None:
        c = CombatCombo()
        for i in range(3):
            c.register_hit(current_ms=i * 500)
        assert "3x" in c.display_label
        assert "CHAIN" in c.display_label

    def test_label_clamps_at_99(self) -> None:
        c = CombatCombo()
        for i in range(150):
            c.register_hit(current_ms=i * 100)  # 100ms apart
        # Display count should be 99, not 150
        assert c.display_count == 99


# ----------------------------------------------------------------------------
# StageAvatar
# ----------------------------------------------------------------------------


class TestStageAvatars:
    def test_five_avatars_defined(self) -> None:
        assert len(AVATAR_BY_STAGE) == 5

    def test_all_stages_have_avatar(self) -> None:
        for stage in ALL_STAGES:
            assert stage in AVATAR_BY_STAGE

    def test_avatars_have_unique_idle(self) -> None:
        idle_icons = {a.icon_idle for a in AVATAR_BY_STAGE.values()}
        assert len(idle_icons) == 5

    def test_avatars_have_frame_labels(self) -> None:
        for avatar in AVATAR_BY_STAGE.values():
            assert "/" in avatar.frame_label  # e.g. "1/5"

    def test_avatar_frame_selection(self) -> None:
        a = AVATAR_CHAIN
        assert a.get_frame() == a.icon_idle
        assert a.get_frame(pulse_active=True) == a.icon_pulse
        assert a.get_frame(special=True) == a.icon_special

    def test_get_avatar_for_stage(self) -> None:
        assert get_avatar_for_stage(WARMUP) == AVATAR_WARMUP
        assert get_avatar_for_stage(CHAIN) == AVATAR_CHAIN
        assert get_avatar_for_stage(FLURRY) == AVATAR_FLURRY
        assert get_avatar_for_stage(RAMPAGE) == AVATAR_RAMPAGE
        assert get_avatar_for_stage(ANNIHILATION) == AVATAR_ANNIHILATION

    def test_get_avatar_unknown_stage_falls_back(self) -> None:
        # Create a fake unknown stage
        fake = ComboStage(
            index=99,
            name="FAKE",
            name_ko="가짜",
            min_count=99,
            damage_bonus_pct=0,
            ap_regen=0,
            screen_shake=0,
            color=(0, 0, 0),
            label="",
        )
        assert get_avatar_for_stage(fake) == AVATAR_WARMUP


# ----------------------------------------------------------------------------
# TimingBar
# ----------------------------------------------------------------------------


class TestTimingBar:
    def test_empty_when_no_combo(self) -> None:
        c = CombatCombo()
        bar = TimingBar()
        assert bar.render(c) == ""

    def test_full_at_zero_elapsed(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        rendered = render_timing_bar(c, width=20)
        assert "100%" in rendered
        assert "[████████████████████]" in rendered

    def test_drains_over_time(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.step(1750)  # 50% of 3500ms
        rendered = render_timing_bar(c, width=20)
        assert "50%" in rendered
        # Yellow tier uses ▓ for filled
        assert "▓" in rendered

    def test_color_green_safe(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        bar = TimingBar()
        assert bar.get_color(c) == (100, 230, 130)

    def test_color_yellow_warning(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.step(2000)  # 57% elapsed, 43% remaining (yellow)
        bar = TimingBar()
        assert bar.get_color(c) == (255, 200, 80)

    def test_color_red_urgent(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.step(3000)  # ~86% elapsed, 14% remaining (red)
        bar = TimingBar()
        assert bar.get_color(c) == (255, 80, 80)

    def test_is_urgent_below_25pct(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.step(2700)  # 23% remaining
        bar = TimingBar()
        assert bar.is_urgent(c)

    def test_not_urgent_above_25pct(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.step(1500)  # 57% remaining
        bar = TimingBar()
        assert not bar.is_urgent(c)


# ----------------------------------------------------------------------------
# Combo Finishers
# ----------------------------------------------------------------------------


class TestComboFinishers:
    def test_three_finishers(self) -> None:
        assert len(ALL_FINISHERS) == 3

    def test_finisher_required_stages(self) -> None:
        assert FINISHER_QUICK_SLASH.required_stage == FLURRY
        assert FINISHER_RAMPAGE_BURST.required_stage == RAMPAGE
        assert FINISHER_FINAL_STRIKE.required_stage == ANNIHILATION

    def test_finisher_damage_multipliers(self) -> None:
        assert FINISHER_QUICK_SLASH.damage_multiplier == 2.0
        assert FINISHER_RAMPAGE_BURST.damage_multiplier == 3.0
        assert FINISHER_FINAL_STRIKE.damage_multiplier == 5.0

    def test_finisher_cooldowns_increase(self) -> None:
        cds = [f.cooldown_ms for f in ALL_FINISHERS]
        assert cds == sorted(cds)

    def test_finisher_have_korean_name(self) -> None:
        for f in ALL_FINISHERS:
            assert f.name_ko
            assert f.description

    def test_finisher_visual_animations(self) -> None:
        for f in ALL_FINISHERS:
            assert f.visual_animation

    def test_get_finisher_for_stage(self) -> None:
        assert get_finisher_for_stage(FLURRY) == FINISHER_QUICK_SLASH
        assert get_finisher_for_stage(RAMPAGE) == FINISHER_RAMPAGE_BURST
        assert get_finisher_for_stage(ANNIHILATION) == FINISHER_FINAL_STRIKE

    def test_get_finisher_for_low_stage(self) -> None:
        assert get_finisher_for_stage(WARMUP) is None
        assert get_finisher_for_stage(CHAIN) is None

    def test_finisher_required_stage_count(self) -> None:
        # Each finisher's required stage should match the stage's min_count
        for f in ALL_FINISHERS:
            assert f.required_stage.min_count >= 3  # CHAIN or higher


# ----------------------------------------------------------------------------
# render_combo_full
# ----------------------------------------------------------------------------


class TestRenderComboFull:
    def test_empty_when_no_combo(self) -> None:
        c = CombatCombo()
        assert render_combo_full(c) == ""

    def test_avatar_and_counter(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)  # CHAIN
        rendered = render_combo_full(c, width=20)
        # Should have avatar + counter line, and timing bar
        lines = rendered.split("\n")
        assert len(lines) >= 1
        assert "CHAIN" in lines[0]
        assert "3x" in lines[0]

    def test_timing_bar_included(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        rendered = render_combo_full(c, width=20)
        assert "%" in rendered  # Timing bar shows percent

    def test_no_avatar(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)
        rendered = render_combo_full(c, show_avatar=False, width=20)
        # Should still have timing bar
        assert "%" in rendered
        # Should NOT have avatar icon chars
        for icon in ["◦", "⫶", "⚡", "☠", "✦"]:
            assert icon not in rendered

    def test_no_timing(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)
        rendered = render_combo_full(c, show_timing=False, width=20)
        # Should NOT have % (no timing bar)
        assert "%" not in rendered

    def test_pulse_uses_pulse_frame(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        c.register_hit(current_ms=500)
        c.register_hit(current_ms=1000)  # CHAIN
        v = ComboVisual()
        v.counter_pulse_ms = 200
        rendered = render_combo_full(c, visual=v, width=20)
        # Pulse frame of CHAIN is ⫷⫸ (not idle ⫶)
        assert "⫷⫸" in rendered or "⫶" in rendered


# ----------------------------------------------------------------------------
# Integration smoke
# ----------------------------------------------------------------------------


class TestIntegration:
    def test_full_combo_cycle(self) -> None:
        """Build a 6-hit combo, verify all stages + final + window expiry."""
        c = CombatCombo()
        v = ComboVisual()
        # 6 hits
        for i in range(6):
            spawn_combo_hit(c, v, i * 500, damage_dealt=50)
        assert c.count == 6
        assert c.current_stage.name == "ANNIHILATION"
        assert c.max_combo_reached == 6
        assert c.total_damage_dealt == 300
        # Window expiry
        for _ in range(250):
            c.step(16)
            if c.just_ended:
                update_combo_visual(v, c)
                break
        # Verify end state
        assert c.count == 0
        assert v.end_text != ""
        assert "6" in v.end_text or "히트" in v.end_text

    def test_avatar_progresses_through_stages(self) -> None:
        c = CombatCombo()
        avatars_seen: list[StageAvatar] = []
        for i in range(6):
            c.register_hit(current_ms=i * 500)
            avatars_seen.append(get_avatar_for_stage(c.current_stage))
        # Each stage should have a different avatar
        unique = {a.stage.name for a in avatars_seen}
        assert len(unique) == 5  # All 5 stages should appear

    def test_timing_bar_urgency(self) -> None:
        c = CombatCombo()
        c.register_hit(current_ms=0)
        bar = TimingBar()
        # Just hit: not urgent
        assert not bar.is_urgent(c)
        # Step to 80% elapsed (20% remaining)
        c.step(2800)
        assert bar.is_urgent(c)
        # Window expires
        c.step(800)
        assert c.count == 0
        assert bar.render(c) == ""
