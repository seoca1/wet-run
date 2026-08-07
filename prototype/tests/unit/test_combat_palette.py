"""Tests for combat palette + bundle refactor (combat/palette.py, bundle.py).

Validates:
- Palette color constants are well-defined RGB tuples
- Helper functions return correct colors for given inputs
- Palette is used consistently across combat modules
- CombatEffectsBundle combines all subsystems
- Bundle step/clear/has_active_effects work correctly
- Bundle setup_combat initializes HUD values
"""

from __future__ import annotations

import pytest

from roguelike_sprawl.combat.bundle import CombatEffectsBundle, create_bundle
from roguelike_sprawl.combat.combo import (
    ALL_STAGES,
    CHAIN,
    FLURRY,
    RAMPAGE,
    WARMUP,
)
from roguelike_sprawl.combat.palette import (
    BUFF_COLOR,
    CRIT_COLOR,
    DAMAGE_COLOR,
    DEBUFF_COLOR,
    DEFAULT_COLOR,
    GLITCH_COLOR,
    HEAL_COLOR,
    HP_CRIT_COLOR,
    HP_HIGH_COLOR,
    HP_LOW_COLOR,
    HP_MID_COLOR,
    ICE_BLACK_PALETTE,
    ICE_BREAK_COLOR,
    ICE_CONSTRUCT_PALETTE,
    ICE_GOLIATH_PALETTE,
    ICE_PALETTES,
    ICE_STANDARD_PALETTE,
    ICE_WATCHDOG_PALETTE,
    PHASE_COLORS,
    SHIELD_COLOR,
    STUN_COLOR,
    TIER_BRONZE,
    TIER_GOLD,
    TIER_PLATINUM,
    TIER_SILVER,
    VIGNETTE_COLOR,
    fade_color,
    get_color_for_combo_stage,
    get_color_for_hp_pct,
    get_color_for_phase,
    get_color_for_tier,
    get_palette_for_ice,
)

# ----------------------------------------------------------------------------
# Color constants
# ----------------------------------------------------------------------------


def _is_valid_rgb(c: tuple[int, int, int]) -> bool:
    return len(c) == 3 and all(isinstance(x, int) for x in c) and all(0 <= x <= 255 for x in c)


class TestColorConstants:
    @pytest.mark.parametrize(
        "color",
        [
            DAMAGE_COLOR,
            CRIT_COLOR,
            HEAL_COLOR,
            SHIELD_COLOR,
            BUFF_COLOR,
            DEBUFF_COLOR,
            STUN_COLOR,
            GLITCH_COLOR,
            DEFAULT_COLOR,
            ICE_BREAK_COLOR,
            VIGNETTE_COLOR,
            HP_HIGH_COLOR,
            HP_MID_COLOR,
            HP_LOW_COLOR,
            HP_CRIT_COLOR,
        ],
    )
    def test_color_valid_rgb(self, color: tuple[int, int, int]) -> None:
        assert _is_valid_rgb(color)

    def test_hp_progression_green_drops(self) -> None:
        # As HP decreases, green component drops (high → yellow → orange → red)
        assert HP_HIGH_COLOR[1] > HP_MID_COLOR[1]
        assert HP_MID_COLOR[1] > HP_LOW_COLOR[1]
        assert HP_LOW_COLOR[1] > HP_CRIT_COLOR[1]

    def test_damage_is_red(self) -> None:
        assert DAMAGE_COLOR[0] > DAMAGE_COLOR[1]
        assert DAMAGE_COLOR[0] > DAMAGE_COLOR[2]

    def test_heal_is_green(self) -> None:
        assert HEAL_COLOR[1] > HEAL_COLOR[0]

    def test_shield_is_cyan(self) -> None:
        assert SHIELD_COLOR[2] > SHIELD_COLOR[0]
        assert SHIELD_COLOR[1] > SHIELD_COLOR[0]

    def test_glitch_is_magenta(self) -> None:
        assert GLITCH_COLOR[0] == 255
        assert GLITCH_COLOR[1] == 0
        assert GLITCH_COLOR[2] == 255


# ----------------------------------------------------------------------------
# Phase colors
# ----------------------------------------------------------------------------


class TestPhaseColors:
    def test_four_phases(self) -> None:
        assert len(PHASE_COLORS) == 4

    def test_phase_color_valid(self) -> None:
        for color in PHASE_COLORS:
            assert _is_valid_rgb(color)

    def test_phase_color_escalation(self) -> None:
        # Each phase should be redder than the previous
        for i in range(len(PHASE_COLORS) - 1):
            current = PHASE_COLORS[i]
            next_phase = PHASE_COLORS[i + 1]
            # Red should be increasing (warning -> danger -> critical)
            assert next_phase[0] >= current[0]


# ----------------------------------------------------------------------------
# ICE palettes
# ----------------------------------------------------------------------------


class TestICEPalettes:
    def test_five_ice_types(self) -> None:
        assert len(ICE_PALETTES) == 5

    def test_standard_palette(self) -> None:
        assert "standard" in ICE_PALETTES
        assert len(ICE_STANDARD_PALETTE) >= 3

    def test_watchdog_palette(self) -> None:
        assert "watchdog" in ICE_PALETTES
        assert len(ICE_WATCHDOG_PALETTE) >= 3

    def test_goliath_palette(self) -> None:
        assert "goliath" in ICE_PALETTES
        assert len(ICE_GOLIATH_PALETTE) >= 3

    def test_black_palette(self) -> None:
        assert "black" in ICE_PALETTES
        assert len(ICE_BLACK_PALETTE) >= 3

    def test_construct_palette(self) -> None:
        assert "construct" in ICE_PALETTES
        assert len(ICE_CONSTRUCT_PALETTE) >= 3

    def test_goliath_has_red(self) -> None:
        # GOLIATH should have red colors
        for color in ICE_GOLIATH_PALETTE:
            if color[0] > 200 and color[1] < 100:
                return
        # If no red found, fail
        assert any(c[0] > 200 and c[1] < 100 for c in ICE_GOLIATH_PALETTE)

    def test_black_has_magenta(self) -> None:
        # BLACK palette should have GLITCH_COLOR or similar magenta
        has_magenta = False
        for color in ICE_BLACK_PALETTE:
            if color[0] == 255 and color[2] == 255 and color[1] == 0:
                has_magenta = True
                break
        assert has_magenta


# ----------------------------------------------------------------------------
# Tier colors
# ----------------------------------------------------------------------------


class TestTierColors:
    def test_tier_colors_valid(self) -> None:
        for c in (TIER_BRONZE, TIER_SILVER, TIER_GOLD, TIER_PLATINUM):
            assert _is_valid_rgb(c)

    def test_bronze_is_orange(self) -> None:
        # Bronze is warm: high R, mid G, low B
        assert TIER_BRONZE[0] > TIER_BRONZE[2]

    def test_gold_is_yellow(self) -> None:
        # Gold is yellow: high R, high G, low B
        assert TIER_GOLD[0] > 200
        assert TIER_GOLD[1] > 200
        assert TIER_GOLD[2] < 100


# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


HP_TIER_CASES: list[tuple[float, tuple[int, int, int]]] = [
    (1.0, HP_HIGH_COLOR),
    (0.6, HP_HIGH_COLOR),
    (0.5, HP_MID_COLOR),
    (0.4, HP_MID_COLOR),
    (0.3, HP_LOW_COLOR),
    (0.2, HP_LOW_COLOR),
    (0.1, HP_CRIT_COLOR),
    (0.0, HP_CRIT_COLOR),
]


class TestGetColorForHpPct:
    @pytest.mark.parametrize("case_idx", list(range(len(HP_TIER_CASES))))
    def test_tiers(self, case_idx: int) -> None:
        hp_pct, expected = HP_TIER_CASES[case_idx]
        assert get_color_for_hp_pct(hp_pct) == expected

    def test_boundary_50pct(self) -> None:
        # > 50% is high
        assert get_color_for_hp_pct(0.51) == HP_HIGH_COLOR
        # = 50% is mid
        assert get_color_for_hp_pct(0.5) == HP_MID_COLOR


class TestGetColorForPhase:
    def test_valid_indices(self) -> None:
        for i in range(4):
            assert get_color_for_phase(i) == PHASE_COLORS[i]

    def test_out_of_range(self) -> None:
        # Should clamp to default (silver)
        assert get_color_for_phase(99) == PHASE_COLORS[0]
        assert get_color_for_phase(-1) == PHASE_COLORS[0]


class TestGetColorForComboStage:
    def test_valid_indices(self) -> None:
        from roguelike_sprawl.combat.palette import COMBO_STAGE_COLORS

        for i in range(5):
            assert get_color_for_combo_stage(i) == COMBO_STAGE_COLORS[i]

    def test_out_of_range(self) -> None:
        assert get_color_for_combo_stage(99) == (200, 200, 200)


class TestGetPaletteForIce:
    def test_known_types(self) -> None:
        assert get_palette_for_ice("standard") == ICE_STANDARD_PALETTE
        assert get_palette_for_ice("watchdog") == ICE_WATCHDOG_PALETTE
        assert get_palette_for_ice("goliath") == ICE_GOLIATH_PALETTE
        assert get_palette_for_ice("black") == ICE_BLACK_PALETTE
        assert get_palette_for_ice("construct") == ICE_CONSTRUCT_PALETTE

    def test_unknown_falls_back_to_standard(self) -> None:
        assert get_palette_for_ice("xyz_unknown") == ICE_STANDARD_PALETTE


class TestGetColorForTier:
    def test_known_tiers(self) -> None:
        assert get_color_for_tier("bronze") == TIER_BRONZE
        assert get_color_for_tier("silver") == TIER_SILVER
        assert get_color_for_tier("gold") == TIER_GOLD
        assert get_color_for_tier("platinum") == TIER_PLATINUM

    def test_unknown_falls_back(self) -> None:
        assert get_color_for_tier("xyz") == TIER_BRONZE


class TestFadeColor:
    def test_full_alpha(self) -> None:
        assert fade_color((200, 100, 50), 1.0) == (200, 100, 50)

    def test_half_alpha(self) -> None:
        assert fade_color((200, 100, 50), 0.5) == (100, 50, 25)

    def test_zero_alpha(self) -> None:
        assert fade_color((200, 100, 50), 0.0) == (0, 0, 0)


# ----------------------------------------------------------------------------
# Combo stage colors match palette
# ----------------------------------------------------------------------------


class TestComboStageColorsConsistent:
    def test_warmup_color(self) -> None:
        assert WARMUP.color == (200, 200, 200)

    def test_chain_color(self) -> None:
        assert CHAIN.color == (100, 230, 130)

    def test_flurry_color(self) -> None:
        assert FLURRY.color == (255, 200, 80)

    def test_rampage_color(self) -> None:
        assert RAMPAGE.color == (255, 100, 80)


# ----------------------------------------------------------------------------
# CombatEffectsBundle
# ----------------------------------------------------------------------------


class TestCombatEffectsBundle:
    def test_create_bundle(self) -> None:
        bundle = create_bundle()
        assert bundle is not None
        assert bundle.effects is not None
        assert bundle.hud is not None
        assert bundle.combo is not None
        assert bundle.combo_visual is not None

    def test_default_construction(self) -> None:
        bundle = CombatEffectsBundle()
        assert bundle.combo.count == 0
        assert bundle.combo.current_stage.name == "WARMUP"

    def test_step(self) -> None:
        bundle = create_bundle()
        bundle.combo.register_hit(current_ms=0)
        bundle.combo.register_hit(current_ms=500)
        bundle.combo.register_hit(current_ms=1000)  # stage up to CHAIN
        bundle.combo_visual.counter_pulse_ms = 200
        bundle.step(50)
        # All systems stepped
        assert bundle.combo.elapsed_ms == 50

    def test_clear(self) -> None:
        bundle = create_bundle()
        bundle.combo.register_hit(current_ms=0)
        bundle.combo.register_hit(current_ms=500)
        bundle.combo_visual.counter_pulse_ms = 200
        bundle.clear()
        assert bundle.combo.count == 0
        assert bundle.combo.current_stage.name == "WARMUP"
        assert bundle.combo_visual.counter_pulse_ms == 0

    def test_has_active_effects_empty(self) -> None:
        bundle = create_bundle()
        # Default state should be quiet
        # (vignette might have small flash_intensity but should be ~0)
        # Actually, vignette.flash_intensity defaults to 0
        # So has_active_effects should be False
        # (Note: HUD vignette.intensity is 0 by default)
        # But let me check after clear()
        bundle.clear()
        assert not bundle.has_active_effects()

    def test_has_active_with_combo_end(self) -> None:
        bundle = create_bundle()
        bundle.combo.register_hit(current_ms=0)
        bundle.combo.register_hit(current_ms=500)
        # Manually set end cinematic
        bundle.combo_visual.end_ms = 1000
        bundle.combo_visual.end_text = "[ 콤보 종료 ]"
        assert bundle.has_active_effects()

    def test_setup_combat(self) -> None:
        bundle = create_bundle()
        bundle.setup_combat(
            player_max_hp=100,
            player_max_shield=50,
            enemy_max_hp=80,
            enemy_max_shield=0,
            window_ms=3000,
        )
        assert bundle.hud.player_health.max_hp == 100
        assert bundle.hud.player_health.max_shield == 50
        assert bundle.hud.enemy_health.max_hp == 80
        assert bundle.combo.window_ms == 3000
        assert bundle.combo.count == 0

    def test_bundle_preserves_combo_max(self) -> None:
        bundle = create_bundle()
        for i in range(7):
            bundle.combo.register_hit(current_ms=i * 500)
        bundle.clear()
        # max_combo_reached persists
        assert bundle.combo.max_combo_reached == 7


# ----------------------------------------------------------------------------
# Integration with other modules
# ----------------------------------------------------------------------------


class TestPaletteIntegration:
    def test_combo_module_uses_palette(self) -> None:
        """All ComboStage colors should match palette values."""
        from roguelike_sprawl.combat.palette import COMBO_STAGE_COLORS

        for stage in ALL_STAGES:
            assert stage.color == COMBO_STAGE_COLORS[stage.index]

    def test_hud_module_uses_palette(self) -> None:
        """HUD module should import from palette (no local redefinition)."""
        # Check that the module file imports from palette
        from roguelike_sprawl.combat import hud

        source = open(hud.__file__).read()
        assert "from .palette import" in source

    def test_effects_module_uses_palette(self) -> None:
        """Effects module should import from palette (no local redefinition)."""
        from roguelike_sprawl.combat import effects

        source = open(effects.__file__).read()
        assert "from .palette import" in source

    def test_bosses_module_uses_palette(self) -> None:
        """Bosses module should reference palette palettes."""
        from roguelike_sprawl.combat import bosses, bosses_cinematic

        source = bosses.__file__
        assert source is not None
        with open(source) as f:
            bosses_src = f.read()
        with open(bosses_cinematic.__file__) as f:
            cinematic_src = f.read()
        combined = bosses_src + cinematic_src
        assert "ICE_GOLIATH_PALETTE" in combined or "ICE_BLACK_PALETTE" in combined
