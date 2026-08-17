"""Unit tests for cinematic input handling (semi-auto mode)."""

from __future__ import annotations

from tcod.event import KeyDown, KeySym, Modifier, Scancode

from wet_run.engine.state import AppState
from wet_run.engine.story_cinematic import (
    PROLOGUE_SCENE,
    CinematicState,
    StoryLine,
    StoryScene,
    TextSpeed,
    handle_cinematic_input,
    step_cinematic,
)


def _make_event(sym: KeySym) -> KeyDown:
    return KeyDown(sym=sym, scancode=Scancode.UP, mod=Modifier.NONE)


def _make_test_scene() -> StoryScene:
    """Build a 3-line test scene with predictable timing."""
    return StoryScene(
        id="test_scene",
        title_en="Test",
        title_ko="테스트",
        lines=(
            StoryLine(
                text_en="First line.",
                text_ko="첫 줄.",
                speed=TextSpeed.FAST,
                pause_ms=100,
            ),
            StoryLine(
                text_en="Second line here.",
                text_ko="둘째 줄.",
                speed=TextSpeed.FAST,
                pause_ms=100,
            ),
            StoryLine(
                text_en="Third.",
                text_ko="셋째.",
                speed=TextSpeed.FAST,
                pause_ms=100,
            ),
        ),
    )


class TestSemiAutoTyping:
    """step_cinematic auto-progresses typing (no input needed)."""

    def test_typing_progresses_with_time(self) -> None:
        """Without input, typing advances based on elapsed time."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)

        # Run for enough elapsed_ms to type "First line." (11 chars at 60/s = 183ms)
        step_cinematic(state, elapsed_ms=300)

        # First line should be complete
        assert state.current_char_index >= len(scene.lines[0].text_en)

    def test_typing_continues_across_frames(self) -> None:
        """Multiple small steps also complete the line."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)

        step_cinematic(state, elapsed_ms=50)
        assert state.current_char_index < len(scene.lines[0].text_en)

        step_cinematic(state, elapsed_ms=200)
        assert state.current_char_index >= len(scene.lines[0].text_en)


class TestSemiAutoAdvance:
    """Auto-advance after pause_ms between lines."""

    def test_pauses_then_advances(self) -> None:
        """After pause_ms, scene auto-advances to next line."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)

        # Type the first line
        step_cinematic(state, elapsed_ms=200)
        assert state.current_line_index == 0
        # Wait the pause_ms
        step_cinematic(state, elapsed_ms=200 + 150)
        assert state.current_line_index == 1


class TestInputSkipTyping:
    """ENTER/SPACE during typing instantly completes the line."""

    def test_enter_completeline_during_typing(self) -> None:
        """ENTER while typing completes the current line."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        # Start typing
        step_cinematic(state, elapsed_ms=20)
        partial = state.current_char_index
        assert partial < len(scene.lines[0].text_en)

        # ENTER should complete the line
        ev = _make_event(KeySym.RETURN)
        handle_cinematic_input(ev, app_state, state)

        # The current line is now complete
        assert state.current_char_index == len(scene.lines[0].text_en)
        # Did not advance yet (semi-auto: ENTER completes, second ENTER advances)
        assert state.current_line_index == 0

    def test_two_enters_advance(self) -> None:
        """Two ENTERs: first completes typing, second advances."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        # Start typing
        step_cinematic(state, elapsed_ms=20)
        # First ENTER: complete line
        handle_cinematic_input(_make_event(KeySym.RETURN), app_state, state)
        assert state.current_line_index == 0
        # Second ENTER: advance
        handle_cinematic_input(_make_event(KeySym.RETURN), app_state, state)
        assert state.current_line_index == 1

    def test_space_works_like_enter(self) -> None:
        """SPACE has the same effect as ENTER."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        step_cinematic(state, elapsed_ms=20)
        handle_cinematic_input(_make_event(KeySym.SPACE), app_state, state)
        assert state.current_char_index == len(scene.lines[0].text_en)


class TestInputSkipPause:
    """ENTER/SPACE during pause skips the auto-pause and advances."""

    def test_enter_during_pause_advances(self) -> None:
        """ENTER between lines skips the pause and goes to next line."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        # Type the first line completely (advance to typing-complete state)
        step_cinematic(state, elapsed_ms=200)
        # Complete the line via ENTER
        handle_cinematic_input(_make_event(KeySym.RETURN), app_state, state)
        # Now we're in "typing complete" state — another ENTER should advance
        handle_cinematic_input(_make_event(KeySym.RETURN), app_state, state)
        assert state.current_line_index == 1


class TestInputSkipScene:
    """ESC skips the entire scene."""

    def test_escape_finishes_scene(self) -> None:
        """ESC marks the scene as finished immediately."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        step_cinematic(state, elapsed_ms=20)
        ev = _make_event(KeySym.ESCAPE)
        result = handle_cinematic_input(ev, app_state, state)

        assert result is True
        assert state.finished is True
        assert state.current_line_index == len(scene.lines)


class TestInputQuit:
    """Q quits the game."""

    def test_q_returns_false(self) -> None:
        """Q returns False (signal to quit the main loop)."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        ev = _make_event(KeySym.Q)
        result = handle_cinematic_input(ev, app_state, state)

        assert result is False


class TestSceneCompletion:
    """End of scene behavior."""

    def test_enter_on_last_line_finishes(self) -> None:
        """ENTER on the last line marks the scene as finished."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        # Jump to the last line
        state.current_line_index = 2
        # Complete the last line's typing
        step_cinematic(state, elapsed_ms=200)
        # ENTER advances (which finishes the scene since it's the last)
        handle_cinematic_input(_make_event(KeySym.RETURN), app_state, state)

        assert state.finished is True

    def test_completed_scene_ignores_enter(self) -> None:
        """ENTER on a completed scene does not crash."""
        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        state.finished = True
        app_state = AppState()

        ev = _make_event(KeySym.RETURN)
        result = handle_cinematic_input(ev, app_state, state)

        # Just doesn't crash; no state change
        assert result is True


class TestRealSceneFlow:
    """End-to-end flow with the real PROLOGUE_SCENE."""

    def test_can_progress_through_prologue(self) -> None:
        """A player can advance through the prologue with ENTER."""
        state = CinematicState(scene=PROLOGUE_SCENE, show_korean=False)
        app_state = AppState()

        # Simulate typing the first line
        step_cinematic(state, elapsed_ms=200)
        # Complete + advance
        for _ in range(2):
            handle_cinematic_input(_make_event(KeySym.RETURN), app_state, state)
        # Should have advanced
        assert state.current_line_index >= 1

    def test_can_escape_prologue(self) -> None:
        """A player can escape the prologue with ESC."""
        state = CinematicState(scene=PROLOGUE_SCENE, show_korean=False)
        app_state = AppState()

        handle_cinematic_input(_make_event(KeySym.ESCAPE), app_state, state)

        assert state.finished is True
        assert state.current_line_index == len(PROLOGUE_SCENE.lines)


class TestNonKeyIgnored:
    """Non-key events are ignored."""

    def test_non_key_event_returns_true(self) -> None:
        """Mouse events etc. don't affect cinematic state."""

        class MouseEvent:
            pass

        scene = _make_test_scene()
        state = CinematicState(scene=scene)
        app_state = AppState()

        result = handle_cinematic_input(MouseEvent(), app_state, state)

        assert result is True
        assert state.current_line_index == 0
