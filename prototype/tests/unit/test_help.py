"""Tests for Help screen (Phase 7: tutorial/onboarding)."""

from __future__ import annotations

from wet_run.engine.help_view import HELP_PAGES
from wet_run.engine.state import AppState, ScreenKind


class TestHelpPages:
    def test_six_pages_defined(self) -> None:
        # 6 pages as of ADR-0197 (added GAMEPAD / CONTROLLER).
        assert len(HELP_PAGES) == 6

    def test_all_pages_have_title(self) -> None:
        for page in HELP_PAGES:
            assert "title" in page
            assert "lines" in page
            assert len(page["lines"]) > 0

    def test_page_titles_are_uppercase(self) -> None:
        for page in HELP_PAGES:
            assert page["title"].isupper() or " " in page["title"]


class TestHelpScreenKind:
    def test_help_screen_kind_exists(self) -> None:
        assert hasattr(ScreenKind, "HELP")
        assert ScreenKind.HELP == "help"


class TestAppStateHelpPage:
    def test_help_page_defaults_to_zero(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HELP
        assert getattr(state, "help_page", 0) == 0

    def test_help_page_wraps_forward(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HELP
        state.help_page = 5  # Last page (0-indexed)
        state.help_page = (state.help_page + 1) % len(HELP_PAGES)
        assert state.help_page == 0

    def test_help_page_wraps_backward(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HELP
        state.help_page = 0
        state.help_page = (state.help_page - 1) % len(HELP_PAGES)
        assert state.help_page == 5


class TestHelpMenuIntegration:
    def test_menu_option_7_is_help(self) -> None:
        from wet_run.engine.menu import MENU_OPTION_COUNT, OPTION_HELP

        assert OPTION_HELP == 7
        assert MENU_OPTION_COUNT == 9
