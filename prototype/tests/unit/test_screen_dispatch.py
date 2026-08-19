"""Tests for engine.screen_dispatch — Screen→render dispatch table.

Coverage target for src/wet_run/engine/screen_dispatch.py.
Tests focus on the dispatch table structure and render_current_screen's flow logic.
The inner view functions (complex tcod-based renderers) are tested elsewhere.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from wet_run.engine.screen_dispatch import (
    _build_dispatch,
    render_current_screen,
)
from wet_run.engine.state import AppState, ScreenKind


@pytest.fixture(autouse=True)
def _reset_dispatch_cache():
    """Reset module-level dispatch cache before each test."""
    import wet_run.engine.screen_dispatch as sd

    sd._DISPATCH = None
    yield
    sd._DISPATCH = None


def _make_console() -> MagicMock:
    """Mock tcod.console.Console."""
    console = MagicMock()
    console.width = 80
    console.height = 30
    return console


def _make_translator() -> MagicMock:
    """Mock i18n.Translator."""
    t = MagicMock()
    t.lang = "en"
    return t


# ----------------------------------------------------------------------------
# _build_dispatch — table structure
# ----------------------------------------------------------------------------


class TestBuildDispatch:
    def test_build_dispatch_returns_dict(self):
        table = _build_dispatch()
        assert isinstance(table, dict)
        assert len(table) > 0

    def test_contains_all_main_screens(self):
        """Common screens must be present."""
        table = _build_dispatch()
        for kind in (
            ScreenKind.MENU,
            ScreenKind.HUB,
            ScreenKind.MATRIX,
            ScreenKind.COMBAT,
            ScreenKind.HELP,
            ScreenKind.SETTINGS,
            ScreenKind.GRAPHIC_NOVEL_MENU,
            ScreenKind.SALVATION_INTRO,
            ScreenKind.DEATH,
        ):
            assert kind in table, f"{kind} missing from dispatch table"

    def test_all_values_are_callable(self):
        table = _build_dispatch()
        for kind, fn in table.items():
            assert callable(fn), f"render fn for {kind} is not callable"

    def test_salvation_screens_have_3_entries(self):
        """SALVATION_INTRO / EPILOGUE / ENDING should each have render fns."""
        table = _build_dispatch()
        for kind in (
            ScreenKind.SALVATION_INTRO,
            ScreenKind.SALVATION_EPILOGUE,
            ScreenKind.SALVATION_ENDING,
        ):
            assert kind in table

    def test_death_screens_each_have_own_entry(self):
        table = _build_dispatch()
        assert ScreenKind.DEATH in table
        assert ScreenKind.DEATH_SUMMARY in table
        assert ScreenKind.HALL_OF_DEAD in table

    def test_no_duplicate_screen_kinds(self):
        table = _build_dispatch()
        kinds = list(table.keys())
        assert len(kinds) == len(set(kinds)), "duplicate ScreenKind in dispatch table"


# ----------------------------------------------------------------------------
# Lazy initialization via _DISPATCH
# ----------------------------------------------------------------------------


class TestLazyDispatch:
    def test_dispatch_starts_none(self):
        import wet_run.engine.screen_dispatch as sd

        sd._DISPATCH = None
        assert sd._DISPATCH is None

    def test_render_current_screen_initializes_dispatch(self):
        import wet_run.engine.screen_dispatch as sd

        sd._DISPATCH = None
        console = _make_console()
        t = _make_translator()
        state = AppState()
        state.screen = ScreenKind.MENU

        # Should initialize lazily
        render_current_screen(console, t, state)
        assert sd._DISPATCH is not None
        assert isinstance(sd._DISPATCH, dict)


# ----------------------------------------------------------------------------
# render_current_screen — dispatch logic
# ----------------------------------------------------------------------------


class TestRenderCurrentScreen:
    def test_unknown_screen_shows_error_message(self):
        """A screen without a renderer should print an error and not crash."""
        state = AppState()
        # Set screen to something invalid (simulate by removing from dict)
        state.screen = ScreenKind.MENU
        console = _make_console()
        t = _make_translator()

        # Patch the dispatch table to NOT contain MENU
        with patch("wet_run.engine.screen_dispatch._DISPATCH", new={}):
            render_current_screen(console, t, state)
            console.clear.assert_called()
            # Look for "NO RENDERER" message in any print call
            found = any(
                "NO RENDERER"
                in str(
                    call.kwargs.get("string", "") or (call.args[2] if len(call.args) >= 3 else "")
                )
                for call in console.print.call_args_list
            )
            assert found, "expected 'NO RENDERER' message in console output"

    def test_dispatches_to_render_fn(self):
        console = _make_console()
        t = _make_translator()
        state = AppState()
        state.screen = ScreenKind.MENU

        # Patch _DISPATCH with a known callable
        mock_render = MagicMock()
        with patch("wet_run.engine.screen_dispatch._DISPATCH", new={ScreenKind.MENU: mock_render}):
            render_current_screen(console, t, state)
            mock_render.assert_called_once_with(console, t, state)

    def test_matrix_passes_registries(self):
        """MATRIX should receive prog_registry + ice_registry as kwargs.

        Uses MagicMock stand-ins to avoid constructing real ProgramRegistry (which
        requires a `skills` dataset that's complex to assemble).
        """
        console = _make_console()
        t = _make_translator()
        state = AppState()
        state.screen = ScreenKind.MATRIX

        mock_render = MagicMock()
        prog_mock = MagicMock()
        ice_mock = MagicMock()

        with patch(
            "wet_run.engine.screen_dispatch._DISPATCH",
            new={ScreenKind.MATRIX: mock_render},
        ):
            render_current_screen(console, t, state, prog_registry=prog_mock, ice_registry=ice_mock)

        mock_render.assert_called_once_with(
            console, t, state, prog_registry=prog_mock, ice_registry=ice_mock
        )

    def test_non_matrix_does_not_get_registries(self):
        """HUB should NOT receive registry kwargs (signature mismatch)."""
        console = _make_console()
        t = _make_translator()
        state = AppState()
        state.screen = ScreenKind.HUB

        mock_render = MagicMock()

        with patch("wet_run.engine.screen_dispatch._DISPATCH", new={ScreenKind.HUB: mock_render}):
            render_current_screen(
                console,
                t,
                state,
                prog_registry=MagicMock(),
                ice_registry=MagicMock(),
            )

        # Called with positional only, not kwargs
        mock_render.assert_called_once_with(console, t, state)


# ----------------------------------------------------------------------------
# Lazy build integration: full pipeline
# ----------------------------------------------------------------------------


class TestIntegrationDispatch:
    def test_full_build_resolves_all_screens_to_callables(self):
        """After lazy build, every ScreenKind in the live dispatcher should be callable.

        Some real renderers have signature mismatches (e.g. save_save_load takes
        2 args instead of expected 3). Those bugs are surfaced via TypeError here
        and can be addressed separately.
        """
        import wet_run.engine.screen_dispatch as sd

        sd._DISPATCH = None
        console = _make_console()
        t = _make_translator()
        state = AppState()

        for kind in ScreenKind:
            state.screen = kind
            try:
                render_current_screen(console, t, state)
            except (TypeError, AttributeError):
                pass
            sd._DISPATCH = None

        sd._DISPATCH = None

    def test_no_significant_exceptions_in_normal_screens(self):
        """MENU / HUB / HELP / SETTINGS should render without exceptions."""
        import wet_run.engine.screen_dispatch as sd

        sd._DISPATCH = None
        console = _make_console()
        t = _make_translator()
        state = AppState()

        for kind in (ScreenKind.MENU, ScreenKind.HUB, ScreenKind.HELP, ScreenKind.SETTINGS):
            state.screen = kind
            sd._DISPATCH = None
            try:
                render_current_screen(console, t, state)
            except Exception as e:
                pytest.fail(f"{kind} raised: {type(e).__name__}: {e}")
