"""Tests for combat HUD (combat/hud.py).

Validates:
- HealthState: HP/shield drain animation
- AlertLevel transitions at HP thresholds
- LowHpState: pulse, vignette, desaturation
- PhaseColorState: boss phase color transitions
- BarFlash: damage/heal flash timing
- CameraVignette: render, flash
- render_health_bar / render_health_bar_rich: output format
- render_vignette: edge darkening pattern
- CombatHUD: take_damage, heal, set_boss_phase, step
"""

from __future__ import annotations

import pytest

from wet_run.combat.hud import (
    PHASE_COLORS,
    AlertLevel,
    BarFlash,
    CameraVignette,
    CombatHUD,
    HealthState,
    LowHpState,
    PhaseColorState,
    is_pulsing,
    render_health_bar,
    render_health_bar_rich,
    render_vignette,
    update_low_hp_state,
)

# ----------------------------------------------------------------------------
# HealthState
# ----------------------------------------------------------------------------


class TestHealthState:
    def test_initial(self) -> None:
        h = HealthState(current_hp=100, max_hp=100)
        assert h.current_hp == 100
        assert h.max_hp == 100
        assert h.current_shield == 0
        assert h.max_shield == 0

    def test_with_shield(self) -> None:
        h = HealthState(
            current_hp=100,
            max_hp=100,
            current_shield=50,
            max_shield=50,
        )
        assert h.current_shield == 50
        assert h.max_shield == 50


# ----------------------------------------------------------------------------
# AlertLevel
# ----------------------------------------------------------------------------


ALERT_CASES: list[tuple[int, AlertLevel]] = [
    (100, AlertLevel.HEALTHY),
    (50, AlertLevel.HEALTHY),
    (31, AlertLevel.HEALTHY),
    (30, AlertLevel.LOW),
    (20, AlertLevel.LOW),
    (11, AlertLevel.LOW),
    (10, AlertLevel.CRITICAL),
    (5, AlertLevel.CRITICAL),
    (0, AlertLevel.CRITICAL),
]


class TestAlertLevelTransitions:
    @pytest.mark.parametrize("case_idx", list(range(len(ALERT_CASES))))
    def test_thresholds(self, case_idx: int) -> None:
        hp_pct, expected = ALERT_CASES[case_idx]
        state = LowHpState()
        result = update_low_hp_state(state, hp_pct, 16)
        assert result == expected


# ----------------------------------------------------------------------------
# LowHpState
# ----------------------------------------------------------------------------


class TestLowHpState:
    def test_initial_healthy(self) -> None:
        s = LowHpState()
        assert s.alert_level == AlertLevel.HEALTHY
        assert s.vignette_intensity == 0.0

    def test_low_intensifies_vignette(self) -> None:
        s = LowHpState()
        for _ in range(50):
            update_low_hp_state(s, 20, 50)
        assert s.alert_level == AlertLevel.LOW
        assert s.vignette_intensity > 0.0
        # Should be approaching target 0.3
        assert 0.25 < s.vignette_intensity < 0.35

    def test_critical_intensifies_more(self) -> None:
        s = LowHpState()
        for _ in range(100):
            update_low_hp_state(s, 5, 50)
        assert s.alert_level == AlertLevel.CRITICAL
        assert s.vignette_intensity > 0.5
        # Should be approaching target 0.7
        assert 0.6 < s.vignette_intensity < 0.8

    def test_critical_desaturates(self) -> None:
        s = LowHpState()
        for _ in range(200):
            update_low_hp_state(s, 5, 50)
        assert s.desaturation > 0.3

    def test_pulse_cycles(self) -> None:
        s = LowHpState()
        update_low_hp_state(s, 5, 16)  # critical
        assert s.pulse_elapsed_ms > 0
        # After full period
        update_low_hp_state(s, 5, s.pulse_period_ms)
        assert s.pulse_elapsed_ms == 0  # cycled

    def test_is_pulsing_first_half(self) -> None:
        s = LowHpState()
        s.pulse_elapsed_ms = 100  # < pulse_period_ms // 2 = 300
        assert is_pulsing(s)

    def test_is_pulsing_second_half(self) -> None:
        s = LowHpState()
        s.pulse_elapsed_ms = 400  # > 300
        assert not is_pulsing(s)


# ----------------------------------------------------------------------------
# PhaseColorState
# ----------------------------------------------------------------------------


class TestPhaseColorState:
    def test_default(self) -> None:
        p = PhaseColorState()
        assert p.phase_index == 0
        assert p.custom_color is None
        assert p.transition_ms == 0

    def test_set_phase(self) -> None:
        p = PhaseColorState()
        p.set_phase(2, color=(255, 0, 0))
        assert p.phase_index == 2
        assert p.custom_color == (255, 0, 0)
        assert p.transition_ms == 400

    def test_step_completes_transition(self) -> None:
        p = PhaseColorState()
        p.set_phase(1)
        p.step(200)
        assert 0.0 < p.transition_progress < 1.0
        p.step(300)
        assert p.transition_ms == 0
        assert p.transition_progress == 1.0


# ----------------------------------------------------------------------------
# BarFlash
# ----------------------------------------------------------------------------


class TestBarFlash:
    def test_default_inactive(self) -> None:
        f = BarFlash()
        assert not f.is_active
        assert f.alpha == 0.0

    def test_trigger_activates(self) -> None:
        f = BarFlash()
        f.trigger(color=(255, 0, 0), duration_ms=200)
        assert f.is_active
        assert f.color == (255, 0, 0)

    def test_alpha_decays(self) -> None:
        f = BarFlash()
        f.trigger(color=(255, 0, 0), duration_ms=200)
        f.step(100)
        assert 0.0 < f.alpha < 1.0
        f.step(200)
        assert not f.is_active


# ----------------------------------------------------------------------------
# CameraVignette
# ----------------------------------------------------------------------------


class TestCameraVignette:
    def test_default_zero(self) -> None:
        v = CameraVignette()
        assert v.total_intensity == 0.0

    def test_flash_overrides(self) -> None:
        v = CameraVignette(intensity=0.3)
        v.flash(intensity=0.5, duration_ms=200)
        assert v.total_intensity == pytest.approx(0.8)

    def test_flash_fades(self) -> None:
        v = CameraVignette()
        v.flash(intensity=1.0, duration_ms=100)
        assert v.total_intensity == 1.0
        v.step(100)
        assert v.flash_intensity == 0.0

    def test_render_returns_string(self) -> None:
        v = CameraVignette(intensity=0.8)
        s = render_vignette(v, 30, 8)
        assert isinstance(s, str)
        assert len(s.split("\n")) == 8

    def test_render_zero_returns_empty(self) -> None:
        v = CameraVignette()
        s = render_vignette(v, 30, 8)
        assert s == ""

    def test_vignette_darker_at_edges(self) -> None:
        v = CameraVignette(intensity=1.0)
        s = render_vignette(v, 30, 8)
        lines = s.split("\n")
        # Center should be emptier than edges
        center_line = lines[len(lines) // 2]
        center_chars = sum(1 for c in center_line if c != " ")
        edge_chars = sum(1 for c in lines[0] if c != " ")
        assert edge_chars > center_chars


# ----------------------------------------------------------------------------
# render_health_bar
# ----------------------------------------------------------------------------


class TestRenderHealthBar:
    def test_full_hp(self) -> None:
        h = HealthState(current_hp=100, max_hp=100, displayed_hp=100.0)
        bar = render_health_bar(h, width=20)
        assert "[████████████████████]" in bar
        assert "100/100 HP" in bar

    def test_empty_hp(self) -> None:
        h = HealthState(current_hp=0, max_hp=100, displayed_hp=0.0)
        bar = render_health_bar(h, width=20)
        assert "[░░░░░░░░░░░░░░░░░░░░]" in bar
        assert "0/100 HP" in bar

    def test_half_hp(self) -> None:
        h = HealthState(current_hp=50, max_hp=100, displayed_hp=50.0)
        bar = render_health_bar(h, width=20)
        assert "[██████████░░░░░░░░░░]" in bar

    def test_shield_bar(self) -> None:
        h = HealthState(
            current_hp=100,
            max_hp=100,
            current_shield=25,
            max_shield=50,
            displayed_hp=100.0,
            displayed_shield=25.0,
        )
        bar = render_health_bar(h, width=20)
        assert "[▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░]" in bar
        assert "SH" in bar

    def test_no_shield_no_sh_text(self) -> None:
        h = HealthState(current_hp=100, max_hp=100, displayed_hp=100.0)
        bar = render_health_bar(h, width=20)
        assert "SH" not in bar

    def test_rich_returns_color(self) -> None:
        h = HealthState(current_hp=100, max_hp=100, displayed_hp=100.0)
        text, color = render_health_bar_rich(h, width=20)
        assert isinstance(text, str)
        assert len(color) == 3
        # Full HP should be green
        assert color == (100, 230, 130)

    def test_low_hp_red(self) -> None:
        h = HealthState(current_hp=5, max_hp=100, displayed_hp=5.0)
        text, color = render_health_bar_rich(h, width=20)
        # Critical should be red
        assert color == (255, 30, 30)

    def test_phase_color_overrides(self) -> None:
        h = HealthState(current_hp=50, max_hp=100, displayed_hp=50.0)
        phase = PhaseColorState(custom_color=(255, 255, 0))
        text, color = render_health_bar_rich(h, phase_color=phase, width=20)
        assert color == (255, 255, 0)

    def test_phase_transition_white(self) -> None:
        h = HealthState(current_hp=50, max_hp=100, displayed_hp=50.0)
        phase = PhaseColorState(custom_color=(255, 255, 0), transition_ms=400, elapsed_ms=0)
        text, color = render_health_bar_rich(h, phase_color=phase, width=20)
        # During transition, color flashes white
        assert color == (255, 255, 255)


# ----------------------------------------------------------------------------
# CombatHUD
# ----------------------------------------------------------------------------


class TestCombatHUD:
    def test_default_construction(self) -> None:
        hud = CombatHUD()
        assert hud.player_health.current_hp == 100
        assert hud.enemy_health.current_hp == 100

    def test_take_damage_player(self) -> None:
        hud = CombatHUD()
        hud.take_damage("player", 30)
        assert hud.player_health.current_hp == 70
        assert hud.player_health.drain_ms > 0
        assert hud.player_damage_flash.is_active

    def test_take_damage_enemy(self) -> None:
        hud = CombatHUD()
        hud.take_damage("enemy", 50)
        assert hud.enemy_health.current_hp == 50
        assert hud.enemy_damage_flash.is_active

    def test_take_damage_clamps_to_zero(self) -> None:
        hud = CombatHUD()
        hud.take_damage("player", 9999)
        assert hud.player_health.current_hp == 0

    def test_heal_player(self) -> None:
        hud = CombatHUD()
        hud.take_damage("player", 50)  # 100 -> 50
        hud.heal("player", 30)
        assert hud.player_health.current_hp == 80
        assert hud.player_heal_flash.is_active

    def test_heal_clamps_to_max(self) -> None:
        hud = CombatHUD()
        hud.heal("player", 9999)
        assert hud.player_health.current_hp == 100

    def test_set_boss_phase(self) -> None:
        hud = CombatHUD()
        hud.set_boss_phase("enemy", 2, color=(255, 50, 50))
        assert hud.enemy_phase.phase_index == 2
        assert hud.enemy_phase.custom_color == (255, 50, 50)
        assert hud.vignette.flash_intensity > 0

    def test_step_drain_animation(self) -> None:
        hud = CombatHUD()
        hud.take_damage("player", 30)  # 100 -> 70
        # displayed_hp starts at 100, should drain to 70
        for _ in range(20):
            hud.step(50)
        assert hud.player_health.displayed_hp == pytest.approx(70.0, abs=1.0)

    def test_step_updates_low_hp(self) -> None:
        hud = CombatHUD()
        hud.player_health.current_hp = 25
        for _ in range(50):
            hud.step(50)
        assert hud.player_low_hp.alert_level == AlertLevel.LOW

    def test_step_vignette_increases(self) -> None:
        hud = CombatHUD()
        hud.player_health.current_hp = 5
        for _ in range(100):
            hud.step(50)
        assert hud.vignette.intensity > 0.5


# ----------------------------------------------------------------------------
# Color palette
# ----------------------------------------------------------------------------


class TestColorPalette:
    def test_hp_high_is_green(self) -> None:
        from wet_run.combat.hud import HP_HIGH_COLOR

        assert HP_HIGH_COLOR[1] > HP_HIGH_COLOR[0]

    def test_hp_crit_is_red(self) -> None:
        from wet_run.combat.hud import HP_CRIT_COLOR

        assert HP_CRIT_COLOR[0] > HP_CRIT_COLOR[1]

    def test_phase_colors_progression(self) -> None:
        # PHASE_COLORS should escalate intensity
        # (silver → warning → danger → critical)
        assert len(PHASE_COLORS) >= 3
        # Each color should be unique
        unique = set(PHASE_COLORS)
        assert len(unique) == len(PHASE_COLORS)
