"""Unit tests for Auto-Play Tempo Layering (ADR-0140 P2.8).

Covers:
- TempoMode enum values
- get_tempo_multiplier for each mode
- String-mode acceptance
- cycle_tempo_mode SLOW → NORMAL → FAST → SLOW
- DEFAULT_TEMPO_MODE = NORMAL
- main_loop integration: tempo multiplier applied to elapsed_ms
"""

from __future__ import annotations

from wet_run.engine.auto_play_tempo import (
    DEFAULT_TEMPO_MODE,
    TEMPO_MULTIPLIERS,
    TempoMode,
    cycle_tempo_mode,
    get_tempo_multiplier,
)
from wet_run.engine.graphic_novel_data import DialogueLine, SceneData
from wet_run.engine.main_loop import _advance_graphic_novel
from wet_run.engine.state import ScreenKind


class TestTempoMode:
    """TempoMode enum values and default."""

    def test_modes_exist(self) -> None:
        assert TempoMode.SLOW == "slow"
        assert TempoMode.NORMAL == "normal"
        assert TempoMode.FAST == "fast"

    def test_default_is_normal(self) -> None:
        assert DEFAULT_TEMPO_MODE is TempoMode.NORMAL


class TestTempoMultipliers:
    """Multiplier lookup for each mode."""

    def test_slow_multiplier(self) -> None:
        assert get_tempo_multiplier(TempoMode.SLOW) == 0.7

    def test_normal_multiplier(self) -> None:
        assert get_tempo_multiplier(TempoMode.NORMAL) == 1.0

    def test_fast_multiplier(self) -> None:
        assert get_tempo_multiplier(TempoMode.FAST) == 1.5

    def test_string_input_slow(self) -> None:
        assert get_tempo_multiplier("slow") == 0.7

    def test_string_input_normal(self) -> None:
        assert get_tempo_multiplier("normal") == 1.0

    def test_string_input_fast(self) -> None:
        assert get_tempo_multiplier("fast") == 1.5

    def test_unknown_string_defaults_to_normal(self) -> None:
        assert get_tempo_multiplier("unknown_mode") == 1.0

    def test_multiplier_table_complete(self) -> None:
        for mode in TempoMode:
            assert mode in TEMPO_MULTIPLIERS


class TestCycleTempoMode:
    """Cycle through SLOW → NORMAL → FAST → SLOW."""

    def test_slow_to_normal(self) -> None:
        assert cycle_tempo_mode(TempoMode.SLOW) is TempoMode.NORMAL

    def test_normal_to_fast(self) -> None:
        assert cycle_tempo_mode(TempoMode.NORMAL) is TempoMode.FAST

    def test_fast_to_slow(self) -> None:
        assert cycle_tempo_mode(TempoMode.FAST) is TempoMode.SLOW

    def test_full_cycle(self) -> None:
        current = TempoMode.SLOW
        for _ in range(6):
            current = cycle_tempo_mode(current)
        assert current is TempoMode.SLOW


class TestMainLoopIntegration:
    """Verify _advance_graphic_novel applies tempo multiplier to elapsed_ms."""

    @staticmethod
    def _make_state_with_scene(duration_ms: int = 5000) -> object:
        state = type(
            "S",
            (),
            {
                "gn_scenes": [
                    SceneData(
                        id="test_scene",
                        character="novice",
                        order=0,
                        title_en="Test",
                        title_ko="",
                        background_id="test_bg",
                        portrait_left=None,
                        portrait_right=None,
                        dialogue=(
                            DialogueLine(
                                speaker="narrator",
                                speaker_ko="narrator",
                                portrait=None,
                                text_en="Hello world",
                                text_ko="",
                                duration_ms=duration_ms,
                            ),
                        ),
                        next_scene=None,
                    )
                ],
                "gn_scene_index": 0,
                "gn_dialogue_index": 0,
                "gn_elapsed_ms": 0.0,
                "gn_paused": False,
                "screen": ScreenKind.GRAPHIC_NOVEL,
                "tempo_mode": "normal",
            },
        )()
        return state

    def test_normal_mode_full_delta(self) -> None:
        """1.0x multiplier — full delta_s * 1000 advance."""
        state = self._make_state_with_scene(duration_ms=5000)
        _advance_graphic_novel(state, delta_s=1.0)
        assert state.gn_elapsed_ms == 1000.0

    def test_slow_mode_reduced_delta(self) -> None:
        """0.7x multiplier — reduced advance rate."""
        state = self._make_state_with_scene(duration_ms=5000)
        state.tempo_mode = "slow"
        _advance_graphic_novel(state, delta_s=1.0)
        assert state.gn_elapsed_ms == 700.0

    def test_fast_mode_increased_delta(self) -> None:
        """1.5x multiplier — increased advance rate."""
        state = self._make_state_with_scene(duration_ms=5000)
        state.tempo_mode = "fast"
        _advance_graphic_novel(state, delta_s=1.0)
        assert state.gn_elapsed_ms == 1500.0

    def test_fast_mode_triggers_advance_sooner(self) -> None:
        """FAST mode should advance to next dialogue sooner than NORMAL."""
        duration = 1000
        delta = 0.5  # 500ms real time

        state_normal = self._make_state_with_scene(duration_ms=duration)
        state_normal.tempo_mode = "normal"
        _advance_graphic_novel(state_normal, delta_s=delta)
        assert state_normal.gn_elapsed_ms < duration
        assert state_normal.gn_dialogue_index == 0

        state_fast = self._make_state_with_scene(duration_ms=duration)
        state_fast.tempo_mode = "fast"
        _advance_graphic_novel(state_fast, delta_s=delta)
        # FAST multiplier (1.5x) → 750ms effective → still not 1000ms
        assert state_fast.gn_elapsed_ms > state_normal.gn_elapsed_ms
        assert state_fast.gn_dialogue_index == 0

    def test_unknown_tempo_mode_falls_back_to_normal(self) -> None:
        """Unknown tempo_mode string falls back to 1.0x (NORMAL)."""
        state = self._make_state_with_scene(duration_ms=5000)
        state.tempo_mode = "unknown"
        _advance_graphic_novel(state, delta_s=1.0)
        assert state.gn_elapsed_ms == 1000.0


__all__ = [
    "TestTempoMode",
    "TestTempoMultipliers",
    "TestCycleTempoMode",
    "TestMainLoopIntegration",
]
