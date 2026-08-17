"""Tests for combat visual effects (combat/effects.py).

Validates:
- Animation primitive: step, current_frame, is_finished, progress
- Particle system: spawn, step, life/alpha, gravity
- ScreenShake: trigger, decay, offset
- FloatingNumber: rise, fade, is_alive
- HitFlash: trigger, decay, alpha
- CinematicSequence: phases, progression, is_finished
- ComboCounter: window, reset, label
- CombatEffects: container, step, clear, has_active_effects
- 15 skill effect animations: all defined, all complete in reasonable time
- 5 ICE types: intro and death sequences
- High-level spawners: spawn_hit_effects, spawn_ice_intro, spawn_ice_death,
  spawn_critical
"""

from __future__ import annotations

import pytest

from wet_run.combat.effects import (
    DAMAGE_COLOR,
    HEAL_COLOR,
    Animation,
    AnimationFrame,
    CinematicSequence,
    CombatEffects,
    ComboCounter,
    FloatingNumber,
    HitFlash,
    IceType,
    Particle,
    ParticleSystem,
    ScreenShake,
    StatusIcon,
    get_animation_for_effect,
    ice_death_sequence,
    ice_intro_sequence,
    spawn_critical,
    spawn_hit_effects,
    spawn_ice_death,
    spawn_ice_intro,
)

ALL_EFFECTS = [
    "attack",
    "heavy_attack",
    "pierce",
    "multi_hit",
    "dot",
    "shield",
    "heal",
    "regen",
    "buff",
    "debuff",
    "stun",
    "counter",
    "lifesteal",
    "detect",
    "poison",
]


# ----------------------------------------------------------------------------
# Animation
# ----------------------------------------------------------------------------


class TestAnimation:
    def test_initial_state(self) -> None:
        a = Animation(frames=(AnimationFrame("x", (0, 0, 0), 100),))
        assert not a.is_finished
        assert a.current_frame is not None
        assert a.current_frame.text == "x"
        assert a.progress() == 0.0

    def test_step_advances(self) -> None:
        a = Animation(
            frames=(
                AnimationFrame("a", (0, 0, 0), 100),
                AnimationFrame("b", (0, 0, 0), 100),
            )
        )
        a.step(50)
        assert a.current_frame.text == "a"
        a.step(60)
        assert a.current_frame.text == "b"
        a.step(200)
        assert a.is_finished
        assert a.current_frame is None

    def test_progress(self) -> None:
        a = Animation(
            frames=(
                AnimationFrame("a", (0, 0, 0), 100),
                AnimationFrame("b", (0, 0, 0), 100),
            )
        )
        a.step(100)
        assert 0.4 < a.progress() < 0.6  # ~50% through

    def test_total_duration(self) -> None:
        a = Animation(
            frames=(
                AnimationFrame("a", (0, 0, 0), 80),
                AnimationFrame("b", (0, 0, 0), 100),
                AnimationFrame("c", (0, 0, 0), 120),
            )
        )
        assert a.total_duration_ms == 300

    def test_empty_frames(self) -> None:
        a = Animation(frames=())
        assert a.is_finished
        assert a.total_duration_ms == 0


# ----------------------------------------------------------------------------
# Particle
# ----------------------------------------------------------------------------


class TestParticle:
    def test_initial_state(self) -> None:
        p = Particle(x=0, y=0, vx=10, vy=0, char="*", color=(255, 0, 0))
        assert p.is_alive
        assert 0.0 < p.alpha <= 1.0

    def test_step_moves(self) -> None:
        p = Particle(x=0, y=0, vx=10, vy=0, char="*", color=(0, 0, 0), max_life_ms=200)
        p.step(100)
        assert p.x > 0  # moved right
        p.step(200)
        assert not p.is_alive  # expired

    def test_alpha_decreases(self) -> None:
        p = Particle(x=0, y=0, vx=0, vy=0, char="*", color=(0, 0, 0), max_life_ms=100)
        a0 = p.alpha
        p.step(50)
        a1 = p.alpha
        assert a1 < a0

    def test_gravity(self) -> None:
        p = Particle(x=0, y=0, vx=0, vy=0, char="*", color=(0, 0, 0), gravity=100.0)
        p.step(100)  # 0.1s
        assert p.vy > 0  # gravity pulled down


class TestParticleSystem:
    def test_spawn_burst(self) -> None:
        ps = ParticleSystem()
        ps.spawn_burst(0, 0, count=5, speed=20.0)
        assert len(ps.particles) == 5

    def test_spawn_upward(self) -> None:
        ps = ParticleSystem()
        ps.spawn_upward(0, 0, count=4)
        assert len(ps.particles) == 4
        for p in ps.particles:
            assert p.vy < 0  # upward

    def test_step_removes_dead(self) -> None:
        ps = ParticleSystem()
        ps.spawn_burst(0, 0, count=3, life_ms=100, speed=10.0)
        assert len(ps.particles) == 3
        ps.step(150)  # all should die
        assert len(ps.particles) == 0

    def test_clear(self) -> None:
        ps = ParticleSystem()
        ps.spawn_burst(0, 0, count=5)
        ps.clear()
        assert len(ps.particles) == 0


# ----------------------------------------------------------------------------
# ScreenShake
# ----------------------------------------------------------------------------


class TestScreenShake:
    def test_no_shake_default(self) -> None:
        s = ScreenShake()
        assert s.offset() == (0, 0)

    def test_trigger_creates_offset(self) -> None:
        s = ScreenShake()
        s.trigger(intensity=3.0, duration_ms=200)
        dx, dy = s.offset()
        assert -3 <= dx <= 3
        assert -3 <= dy <= 3

    def test_shake_decays_to_zero(self) -> None:
        s = ScreenShake()
        s.trigger(intensity=2.0, duration_ms=100)
        s.step(150)  # past duration
        assert s.offset() == (0, 0)

    def test_step_advances_time(self) -> None:
        s = ScreenShake()
        s.trigger(intensity=2.0, duration_ms=200)
        s.step(50)
        s.step(50)
        s.step(150)
        assert s.intensity == 0.0  # finished

    def test_strong_takes_precedence(self) -> None:
        s = ScreenShake()
        s.trigger(intensity=1.0, duration_ms=100)
        s.trigger(intensity=5.0, duration_ms=500)
        assert s.intensity == 5.0
        assert s.duration_ms == 500


# ----------------------------------------------------------------------------
# FloatingNumber
# ----------------------------------------------------------------------------


class TestFloatingNumber:
    def test_initial_state(self) -> None:
        n = FloatingNumber(x=0, y=0, value=50, color=DAMAGE_COLOR)
        assert n.is_alive
        assert "50" in n.text
        assert not n.is_crit

    def test_crit_text(self) -> None:
        n = FloatingNumber(x=0, y=0, value=99, color=DAMAGE_COLOR, is_crit=True)
        assert n.text == "!99!"
        assert n.is_crit

    def test_rises(self) -> None:
        n = FloatingNumber(x=0, y=10.0, value=10, color=DAMAGE_COLOR)
        n.step(100)
        assert n.y < 10.0  # rose

    def test_fades_and_dies(self) -> None:
        n = FloatingNumber(x=0, y=0, value=10, color=DAMAGE_COLOR, max_life_ms=100)
        n.step(50)
        assert 0.0 < n.alpha < 1.0
        n.step(100)
        assert not n.is_alive


# ----------------------------------------------------------------------------
# HitFlash
# ----------------------------------------------------------------------------


class TestHitFlash:
    def test_default_inactive(self) -> None:
        f = HitFlash()
        assert not f.is_active
        assert f.alpha == 0.0

    def test_trigger_activates(self) -> None:
        f = HitFlash()
        f.trigger(color=(255, 0, 0), duration_ms=100)
        assert f.is_active
        assert f.color == (255, 0, 0)

    def test_decays(self) -> None:
        f = HitFlash()
        f.trigger(duration_ms=100)
        f.step(50)
        assert 0.0 < f.alpha < 1.0
        f.step(100)
        assert not f.is_active


# ----------------------------------------------------------------------------
# CinematicSequence
# ----------------------------------------------------------------------------


class TestCinematicSequence:
    def test_phases_progress(self) -> None:
        c = CinematicSequence(
            name="test",
            phases=(
                ("a", (0, 0, 0), 100),
                ("b", (0, 0, 0), 100),
                ("c", (0, 0, 0), 100),
            ),
        )
        assert c.current_phase is not None
        assert c.current_phase[0] == "a"
        c.step(50)
        assert c.current_phase[0] == "a"  # still in first phase
        c.step(60)  # cumulative 110 → in second phase
        assert c.current_phase[0] == "b"
        c.step(50)  # cumulative 160 → still in second
        c.step(50)  # cumulative 210 → in third
        assert c.current_phase[0] == "c"
        c.step(200)  # past end
        assert c.is_finished
        assert c.current_phase is None


# ----------------------------------------------------------------------------
# ComboCounter
# ----------------------------------------------------------------------------


class TestComboCounter:
    def test_first_hit_is_one(self) -> None:
        c = ComboCounter()
        assert c.register_hit(1000) == 1

    def test_consecutive_increments(self) -> None:
        c = ComboCounter()
        c.register_hit(1000)
        c.register_hit(1500)  # within window
        c.register_hit(2000)
        assert c.count == 3

    def test_window_expires(self) -> None:
        c = ComboCounter()
        c.register_hit(1000)
        c.register_hit(5000)  # past window
        assert c.count == 1

    def test_label_appears_at_2(self) -> None:
        c = ComboCounter()
        c.register_hit(0)
        assert c.label == ""
        c.register_hit(100)
        assert "2x HIT" in c.label

    def test_rampage_label(self) -> None:
        c = ComboCounter()
        for i in range(5):
            c.register_hit(i * 100)
        assert "RAMPAGE" in c.label

    def test_reset(self) -> None:
        c = ComboCounter()
        for i in range(3):
            c.register_hit(i * 100)
        c.reset()
        assert c.count == 0


# ----------------------------------------------------------------------------
# CombatEffects container
# ----------------------------------------------------------------------------


class TestCombatEffects:
    def test_empty_state(self) -> None:
        e = CombatEffects()
        assert not e.has_active_effects()

    def test_clear(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 0, 0, 10)
        e.clear()
        assert not e.has_active_effects()
        assert e.combo.count == 0
        assert e.cinematic is None

    def test_step_advances_all(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 0, 0, 10, effect_type="attack")
        e.step(100)
        e.step(5000)
        assert not e.has_active_effects()

    def test_slow_motion(self) -> None:
        e = CombatEffects()
        e.slow_motion_ms = 1000
        e.step(100)  # first 100ms is slow
        assert e.slow_motion_ms < 1000  # decremented

    def test_has_active_with_cinematic(self) -> None:
        e = CombatEffects()
        e.cinematic = CinematicSequence(name="t", phases=(("a", (0, 0, 0), 100),))
        assert e.has_active_effects()


# ----------------------------------------------------------------------------
# 15 SkillEffect animations
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("effect_name", ALL_EFFECTS)
class TestSkillEffectAnimations:
    def test_animation_factory_returns_animation(self, effect_name: str) -> None:
        anim = get_animation_for_effect(effect_name)
        assert isinstance(anim, Animation)

    def test_animation_has_frames(self, effect_name: str) -> None:
        anim = get_animation_for_effect(effect_name)
        assert len(anim.frames) >= 1

    def test_animation_completes_in_reasonable_time(self, effect_name: str) -> None:
        anim = get_animation_for_effect(effect_name)
        # Animations should complete in 0.1s to 2.5s
        assert 100 <= anim.total_duration_ms <= 2500

    def test_animation_has_colored_frames(self, effect_name: str) -> None:
        anim = get_animation_for_effect(effect_name)
        for frame in anim.frames:
            assert len(frame.color) == 3
            for c in frame.color:
                assert 0 <= c <= 255


# ----------------------------------------------------------------------------
# 5 ICE types
# ----------------------------------------------------------------------------


ALL_ICE_TYPES = [
    IceType.STANDARD,
    IceType.WATCHDOG,
    IceType.GOLIATH,
    IceType.BLACK,
    IceType.CONSTRUCT,
]


@pytest.mark.parametrize("ice_type", ALL_ICE_TYPES)
class TestIceSequences:
    def test_intro_has_phases(self, ice_type: IceType) -> None:
        seq = ice_intro_sequence(ice_type, "TEST-ICE")
        assert len(seq.phases) >= 3

    def test_intro_completes_in_reasonable_time(self, ice_type: IceType) -> None:
        seq = ice_intro_sequence(ice_type, "TEST-ICE")
        assert 500 <= seq.total_duration_ms <= 3000

    def test_death_has_phases(self, ice_type: IceType) -> None:
        seq = ice_death_sequence(ice_type)
        assert len(seq.phases) >= 3

    def test_death_completes_quickly(self, ice_type: IceType) -> None:
        seq = ice_death_sequence(ice_type)
        assert 300 <= seq.total_duration_ms <= 1500


# ----------------------------------------------------------------------------
# High-level spawners
# ----------------------------------------------------------------------------


class TestSpawnHitEffects:
    def test_basic_attack_spawns_all_layers(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 5.0, 5.0, 30, effect_type="attack")
        assert len(e.animations) == 1
        assert len(e.particles.particles) >= 5
        assert len(e.floating_numbers) == 1
        assert e.hit_flash.is_active
        assert e.shake.intensity > 0

    def test_crit_spawns_more(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 5.0, 5.0, 99, effect_type="attack", is_crit=True)
        crit_particles = e.particles.particles
        assert len(crit_particles) >= 8  # crit has 10
        assert e.floating_numbers[0].is_crit

    def test_heal_uses_heal_particles(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 0, 0, 20, effect_type="heal")
        # Heal spawns upward particles (vy < 0)
        for p in e.particles.particles:
            assert p.vy < 0

    def test_dot_uses_purple_particles(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 0, 0, 10, effect_type="dot")
        for p in e.particles.particles:
            # Purple-ish
            assert p.color[2] > p.color[0]  # more blue than red

    def test_heavy_attack_more_shake(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 0, 0, 50, effect_type="heavy_attack")
        assert e.shake.intensity >= 2.0

    def test_unknown_effect_falls_back_to_attack(self) -> None:
        e = CombatEffects()
        spawn_hit_effects(e, 0, 0, 10, effect_type="unknown_xyz")
        # Should still spawn something (attack fallback)
        assert len(e.animations) == 1


class TestSpawnIceCinematic:
    def test_ice_intro_sets_cinematic(self) -> None:
        e = CombatEffects()
        spawn_ice_intro(e, IceType.GOLIATH, "GOLIATH-V")
        assert e.cinematic is not None
        assert e.slow_motion_ms > 0

    def test_ice_death_sets_cinematic(self) -> None:
        e = CombatEffects()
        spawn_ice_death(e, IceType.STANDARD)
        assert e.cinematic is not None
        assert e.shake.intensity > 0


class TestSpawnCritical:
    def test_critical_has_all_layers(self) -> None:
        e = CombatEffects()
        spawn_critical(e, 0, 0, 99)
        assert len(e.animations) >= 1
        assert len(e.particles.particles) >= 8
        assert e.floating_numbers[0].is_crit
        assert e.shake.intensity >= 3.0
        assert e.slow_motion_ms > 0
        assert e.hit_flash.is_active


# ----------------------------------------------------------------------------
# StatusIcon enum
# ----------------------------------------------------------------------------


class TestStatusIcon:
    def test_all_icons_distinct(self) -> None:
        icons = [s.value for s in StatusIcon]
        assert len(icons) == len(set(icons))

    def test_known_icons(self) -> None:
        assert StatusIcon.POISON.value == "P"
        assert StatusIcon.STUN.value == "S"
        assert StatusIcon.SHIELD.value == "❖"
        assert StatusIcon.BUFF.value == "↑"


# ----------------------------------------------------------------------------
# ICE type distinctness
# ----------------------------------------------------------------------------


class TestIceTypeDistinctness:
    def test_each_ice_has_unique_intro(self) -> None:
        # Compare by phase text content, not object identity
        signatures = []
        for it in IceType:
            seq = ice_intro_sequence(it, "X")
            sig = "|".join(p[0] for p in seq.phases)
            signatures.append(sig)
        assert len(set(signatures)) == len(IceType), f"Some ICE types share intros: {signatures}"

    def test_each_ice_has_unique_death(self) -> None:
        signatures = []
        for it in IceType:
            seq = ice_death_sequence(it)
            sig = "|".join(p[0] for p in seq.phases)
            signatures.append(sig)
        assert len(set(signatures)) == len(IceType), f"Some ICE types share deaths: {signatures}"

    def test_black_ice_has_glitch(self) -> None:
        # BLACK ICE intro should have magenta glitch color
        seq = ice_intro_sequence(IceType.BLACK, "BLACK")
        has_magenta = any(phase[1] == (255, 0, 255) for phase in seq.phases)
        assert has_magenta

    def test_goliath_intro_is_dramatic(self) -> None:
        # GOLIATH intro should have intense red
        seq = ice_intro_sequence(IceType.GOLIATH, "GOLIATH")
        has_red = any(phase[1][0] > 200 and phase[1][1] < 100 for phase in seq.phases)
        assert has_red


# ----------------------------------------------------------------------------
# Colors palette
# ----------------------------------------------------------------------------


class TestColorPalette:
    def test_damage_is_red(self) -> None:
        assert DAMAGE_COLOR[0] > DAMAGE_COLOR[1]  # red > green
        assert DAMAGE_COLOR[0] > DAMAGE_COLOR[2]  # red > blue

    def test_heal_is_green(self) -> None:
        assert HEAL_COLOR[1] > HEAL_COLOR[0]
        assert HEAL_COLOR[1] > HEAL_COLOR[2]


# ----------------------------------------------------------------------------
# Performance smoke
# ----------------------------------------------------------------------------


class TestPerformance:
    def test_many_effects_settle_quickly(self) -> None:
        e = CombatEffects()
        for _ in range(10):
            spawn_hit_effects(e, 0, 0, 10)
        for _ in range(200):
            e.step(50)
            if not e.has_active_effects():
                break
        assert not e.has_active_effects()

    def test_combo_with_animations(self) -> None:
        e = CombatEffects()
        for i in range(5):
            spawn_hit_effects(e, 0, 0, 10, is_crit=True)
            e.combo.register_hit(i * 100)
        assert e.combo.count == 5
        assert "RAMPAGE" in e.combo.label


class TestScreenFlash:
    """Tests for full-screen flash effect (ADR-0125 follow-up: AoE visual effect)."""

    def test_initial_state_inactive(self) -> None:
        from wet_run.combat.effects import ScreenFlash

        sf = ScreenFlash()
        assert sf.is_active is False
        assert sf.alpha == 0.0

    def test_trigger_activates_flash(self) -> None:
        from wet_run.combat.effects import ScreenFlash

        sf = ScreenFlash()
        sf.trigger(color=(255, 80, 80), duration_ms=200)
        assert sf.is_active is True
        assert sf.alpha == 1.0
        assert sf.color == (255, 80, 80)

    def test_attack_phase_holds_full_alpha(self) -> None:
        from wet_run.combat.effects import ScreenFlash

        sf = ScreenFlash(duration_ms=200)
        sf.elapsed_ms = 20  # 10% progress, within attack phase
        assert sf.alpha == 1.0

    def test_fade_phase_eases_out(self) -> None:
        from wet_run.combat.effects import ScreenFlash

        sf = ScreenFlash(duration_ms=100)
        sf.elapsed_ms = 80  # 80% progress, deep in fade
        # Expected fade = (0.80 - 0.15) / 0.85 ≈ 0.765
        # alpha = 1 - 0.765² ≈ 0.415
        assert 0.4 < sf.alpha < 0.5

    def test_expires_after_duration(self) -> None:
        from wet_run.combat.effects import ScreenFlash

        sf = ScreenFlash(duration_ms=100)
        sf.step(100)
        assert sf.is_active is False
        assert sf.alpha == 0.0

    def test_spawn_aoe_screen_flash_triggers_both(self) -> None:
        from wet_run.combat.effects import (
            CombatEffects,
            spawn_aoe_screen_flash,
        )

        effects = CombatEffects()
        spawn_aoe_screen_flash(effects, color=(255, 100, 100))
        assert effects.screen_flash.is_active is True
        assert effects.screen_flash.color == (255, 100, 100)
        assert effects.shake.intensity > 0
