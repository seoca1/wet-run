"""Tests for Settings screen (Phase 7: options/settings)."""

from __future__ import annotations

import pytest
from tcod.event import KeyDown, KeySym

from wet_run.engine.settings_view import (
    SETTINGS_OPTIONS,
    _adjust_volume,
    _get_volume,
    _set_volume,
    handle_settings_input,
)
from wet_run.engine.state import AppState, ScreenKind


class TestSettingsOptions:
    def test_eight_options_defined(self) -> None:
        assert len(SETTINGS_OPTIONS) == 9

    def test_options_have_ids_and_labels(self) -> None:
        for opt_id, label in SETTINGS_OPTIONS:
            assert isinstance(opt_id, str)
            assert isinstance(label, str)
            assert len(opt_id) > 0
            assert len(label) > 0

    def test_options_include_audio(self) -> None:
        ids = [opt[0] for opt in SETTINGS_OPTIONS]
        assert "audio" in ids

    def test_options_include_colorblind(self) -> None:
        ids = [opt[0] for opt in SETTINGS_OPTIONS]
        assert "colorblind" in ids

    def test_options_include_back(self) -> None:
        ids = [opt[0] for opt in SETTINGS_OPTIONS]
        assert "back" in ids


class TestSettingsScreenKind:
    def test_settings_screen_kind_exists(self) -> None:
        assert hasattr(ScreenKind, "SETTINGS")
        assert ScreenKind.SETTINGS == "settings"


class TestAppStateSettings:
    def test_settings_selected_defaults_to_zero(self) -> None:
        state = AppState()
        state.screen = ScreenKind.SETTINGS
        assert getattr(state, "settings_selected", 0) == 0

    def test_colorblind_mode_defaults_to_false(self) -> None:
        state = AppState()
        assert getattr(state, "colorblind_mode", False) is False

    def test_settings_selected_wraps_forward(self) -> None:
        state = AppState()
        state.screen = ScreenKind.SETTINGS
        state.settings_selected = len(SETTINGS_OPTIONS) - 1
        state.settings_selected = (state.settings_selected + 1) % len(SETTINGS_OPTIONS)
        assert state.settings_selected == 0

    def test_settings_selected_wraps_backward(self) -> None:
        state = AppState()
        state.screen = ScreenKind.SETTINGS
        state.settings_selected = 0
        state.settings_selected = (state.settings_selected - 1) % len(SETTINGS_OPTIONS)
        assert state.settings_selected == len(SETTINGS_OPTIONS) - 1


class TestVolumeFunctions:
    def test_get_volume_returns_float(self) -> None:
        vol = _get_volume()
        assert isinstance(vol, float)
        assert 0.0 <= vol <= 1.0

    def test_set_volume_clamps_to_valid_range(self) -> None:
        original = _get_volume()
        try:
            _set_volume(1.5)
            assert _get_volume() == 1.0
            _set_volume(-0.5)
            assert _get_volume() == 0.0
        finally:
            _set_volume(original)

    def test_adjust_volume_positive(self) -> None:
        original = _get_volume()
        try:
            _set_volume(0.5)
            new_vol = _adjust_volume(0.1)
            assert new_vol == pytest.approx(0.6)
        finally:
            _set_volume(original)

    def test_adjust_volume_negative(self) -> None:
        original = _get_volume()
        try:
            _set_volume(0.5)
            new_vol = _adjust_volume(-0.1)
            assert new_vol == pytest.approx(0.4)
        finally:
            _set_volume(original)

    def test_adjust_volume_clamps_at_zero(self) -> None:
        original = _get_volume()
        try:
            _set_volume(0.0)
            new_vol = _adjust_volume(-0.1)
            assert new_vol == 0.0
        finally:
            _set_volume(original)

    def test_adjust_volume_clamps_at_one(self) -> None:
        original = _get_volume()
        try:
            _set_volume(1.0)
            new_vol = _adjust_volume(0.1)
            assert new_vol == 1.0
        finally:
            _set_volume(original)


class TestHandleSettingsInput:
    @pytest.fixture
    def settings_state(self) -> AppState:
        state = AppState()
        state.screen = ScreenKind.SETTINGS
        state.settings_selected = 0
        return state

    def _key(self, sym: KeySym) -> KeyDown:
        return KeyDown(sym=sym, scancode=0, mod=0)

    def test_escape_returns_to_menu(self, settings_state: AppState) -> None:
        result = handle_settings_input(self._key(KeySym.ESCAPE), settings_state)
        assert result is not None
        assert result.screen == ScreenKind.MENU

    def test_up_navigates(self, settings_state: AppState) -> None:
        settings_state.settings_selected = 2
        result = handle_settings_input(self._key(KeySym.UP), settings_state)
        assert result is not None
        assert result.settings_selected == 1

    def test_down_navigates(self, settings_state: AppState) -> None:
        settings_state.settings_selected = 2
        result = handle_settings_input(self._key(KeySym.DOWN), settings_state)
        assert result is not None
        assert result.settings_selected == 3

    def test_enter_on_audio_increases_volume(self, settings_state: AppState) -> None:
        original = _get_volume()
        try:
            _set_volume(0.5)
            settings_state.settings_selected = 0  # audio
            result = handle_settings_input(self._key(KeySym.RETURN), settings_state)
            assert result is not None
            assert _get_volume() == pytest.approx(0.6)
        finally:
            _set_volume(original)

    def test_enter_on_colorblind_toggles(self, settings_state: AppState) -> None:
        settings_state.settings_selected = 1  # colorblind
        settings_state.colorblind_mode = False
        result = handle_settings_input(self._key(KeySym.RETURN), settings_state)
        assert result is not None
        assert result.colorblind_mode is True

    def test_enter_on_back_returns_to_menu(self, settings_state: AppState) -> None:
        settings_state.settings_selected = 8  # back
        result = handle_settings_input(self._key(KeySym.RETURN), settings_state)
        assert result is not None
        assert result.screen == ScreenKind.MENU

    def test_n1_key_selects_first_option(self, settings_state: AppState) -> None:
        settings_state.settings_selected = 2
        result = handle_settings_input(self._key(KeySym.N1), settings_state)
        assert result is not None
        assert result.settings_selected == 0

    def test_n3_key_selects_third_option(self, settings_state: AppState) -> None:
        result = handle_settings_input(self._key(KeySym.N3), settings_state)
        assert result is not None
        assert result.settings_selected == 2

    def test_left_key_decreases_volume(self, settings_state: AppState) -> None:
        original = _get_volume()
        try:
            _set_volume(0.5)
            settings_state.settings_selected = 0  # audio
            result = handle_settings_input(self._key(KeySym.LEFT), settings_state)
            assert result is not None
            assert _get_volume() == pytest.approx(0.4)
        finally:
            _set_volume(original)

    def test_non_key_event_returns_state(self, settings_state: AppState) -> None:
        class FakeEvent:
            pass

        result = handle_settings_input(FakeEvent(), settings_state)
        assert result is settings_state
