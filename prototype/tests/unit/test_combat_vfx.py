"""Tests for matrix / dungeon VFX (ADR-0060 Phase 1.5).

Covers the four spawn helpers added to combat/effects.py:
    - spawn_jackin_glitch: matrix entry glitch
    - spawn_room_flash: short flash on room transition
    - spawn_data_acquired: gold burst on data pickup
    - spawn_jackout_whiteout: whiteout on extraction gate

Each helper must populate CombatEffects fields correctly (particles,
cinematic, shake, hit_flash).  Layer 1 of the 5-Layer VFX system is
reused; new symbols/text reflect cyberspace atmosphere.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


from wet_run.combat.effects import (  # noqa: E402
    CombatEffects,
    spawn_data_acquired,
    spawn_jackin_glitch,
    spawn_jackout_whiteout,
    spawn_room_flash,
)

# ============================================================================
# spawn_jackin_glitch
# ============================================================================


class TestJackInGlitch:
    def test_populates_particles(self) -> None:
        e = CombatEffects()
        assert e.particles.particles == []
        spawn_jackin_glitch(e)
        assert len(e.particles.particles) > 0

    def test_sets_cinematic(self) -> None:
        e = CombatEffects()
        spawn_jackin_glitch(e)
        assert e.cinematic is not None
        assert e.cinematic.name == "jackin"
        # 3 phases: JACKING IN, SCANNING HOST, CYBERSPACE LOADED
        assert len(e.cinematic.phases) == 3

    def test_triggers_shake_and_flash(self) -> None:
        e = CombatEffects()
        spawn_jackin_glitch(e)
        assert e.shake.intensity == 80
        assert e.shake.duration_ms == 180
        assert e.hit_flash.duration_ms == 120
        assert e.hit_flash.color == (120, 220, 220)


# ============================================================================
# spawn_room_flash
# ============================================================================


class TestRoomFlash:
    def test_default_color_gold(self) -> None:
        e = CombatEffects()
        spawn_room_flash(e)
        assert e.hit_flash.color == (180, 180, 100)
        assert e.hit_flash.duration_ms == 80

    def test_custom_color(self) -> None:
        e = CombatEffects()
        spawn_room_flash(e, color=(255, 0, 0))
        assert e.hit_flash.color == (255, 0, 0)

    def test_spawns_particles(self) -> None:
        e = CombatEffects()
        spawn_room_flash(e)
        assert len(e.particles.particles) >= 4


# ============================================================================
# spawn_data_acquired
# ============================================================================


class TestDataAcquired:
    def test_sets_gold_particles(self) -> None:
        e = CombatEffects()
        spawn_data_acquired(e)
        # All particles use gold color
        for p in e.particles.particles:
            assert p.color == (255, 215, 0)

    def test_cinematic_data_acquired(self) -> None:
        e = CombatEffects()
        spawn_data_acquired(e)
        assert e.cinematic is not None
        assert e.cinematic.name == "data_acquired"
        assert any("DATA FRAGMENT" in text for text, _, _ in e.cinematic.phases)

    def test_triggers_gold_flash(self) -> None:
        e = CombatEffects()
        spawn_data_acquired(e)
        assert e.hit_flash.color == (255, 215, 0)


# ============================================================================
# spawn_jackout_whiteout
# ============================================================================


class TestJackOutWhiteout:
    def test_white_flash(self) -> None:
        e = CombatEffects()
        spawn_jackout_whiteout(e)
        assert e.hit_flash.color == (255, 255, 255)
        assert e.hit_flash.duration_ms == 260

    def test_three_phase_cinematic(self) -> None:
        e = CombatEffects()
        spawn_jackout_whiteout(e)
        assert e.cinematic is not None
        assert e.cinematic.name == "jackout"
        assert len(e.cinematic.phases) == 3
        phase_texts = [text for text, _, _ in e.cinematic.phases]
        assert any("JACKING OUT" in t for t in phase_texts)
        assert any("CONNECTION SEVERED" in t for t in phase_texts)
        assert any("MATRIX CLOSED" in t for t in phase_texts)


# ============================================================================
# Integration: chain VFX triggers
# ============================================================================


class TestVFXChain:
    def test_full_jackin_to_jackout_cycle(self) -> None:
        """A single CombatEffects instance should survive the full cycle."""
        e = CombatEffects()
        spawn_jackin_glitch(e)
        assert e.cinematic is not None
        spawn_room_flash(e)
        spawn_data_acquired(e)
        assert e.cinematic is not None  # newest cinematic replaces
        spawn_jackout_whiteout(e)
        assert e.cinematic.name == "jackout"

        # Step once to advance animations
        e.step(50)
        # hit_flash + shake decay but don't necessarily expire after 50ms
        assert e.hit_flash.elapsed_ms >= 50
