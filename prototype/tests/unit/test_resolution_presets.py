"""Tests for ADR-0198 ResolutionPreset + adaptive layout (Commit 7)."""

from __future__ import annotations

import pytest

from wet_run.engine.config import (
    DEFAULT_RESOLUTION,
    RESOLUTION_PRESETS,
    ResolutionPreset,
)
from wet_run.engine.layout import RegionId, compute_status_panel_width, make_shell
from wet_run.engine.state import AppState


class TestResolutionPreset:
    """ResolutionPreset dataclass + 8 named presets."""

    def test_default_resolution_is_classic(self) -> None:
        assert DEFAULT_RESOLUTION == "classic"

    def test_all_8_presets_defined(self) -> None:
        assert len(RESOLUTION_PRESETS) == 8

    def test_required_preset_names_present(self) -> None:
        for name in (
            "classic",
            "compact",
            "wide",
            "ultrawide",
            "tablet_portrait",
            "tablet_landscape",
            "phone_landscape",
            "auto",
        ):
            assert name in RESOLUTION_PRESETS, f"missing preset: {name}"

    def test_classic_preset_dimensions(self) -> None:
        p = RESOLUTION_PRESETS["classic"]
        assert p.cols == 80
        assert p.rows == 50
        assert p.tier == 1

    def test_auto_preset_zero_dimensions(self) -> None:
        """Auto preset defers to device detection (Tier 2)."""
        p = RESOLUTION_PRESETS["auto"]
        assert p.cols == 0
        assert p.rows == 0
        assert p.tier == 2

    def test_all_tier1_presets_have_positive_dims(self) -> None:
        for name, p in RESOLUTION_PRESETS.items():
            if p.tier == 1:
                assert p.cols > 0, f"{name} tier 1 has 0 cols"
                assert p.rows > 0, f"{name} tier 1 has 0 rows"
                assert p.rows >= 20, f"{name} rows too small for chrome"

    def test_preset_immutable(self) -> None:
        """ResolutionPreset is frozen — should not allow mutation."""
        from dataclasses import FrozenInstanceError

        p = RESOLUTION_PRESETS["classic"]
        with pytest.raises(FrozenInstanceError):
            p.cols = 100  # type: ignore[misc]

    def test_preset_has_required_fields(self) -> None:
        p = ResolutionPreset(
            name="test",
            cols=80,
            rows=50,
            ratio="8:5",
            target_device="test",
            tier=1,
        )
        assert p.name == "test"
        assert p.cols == 80
        assert p.rows == 50
        assert p.ratio == "8:5"
        assert p.target_device == "test"
        assert p.tier == 1


class TestComputeStatusPanelWidth:
    """Adaptive status_panel_w tiers (ADR-0198 §Adaptive status_panel_w)."""

    def test_wide_tier_returns_32(self) -> None:
        assert compute_status_panel_width(100) == 32
        assert compute_status_panel_width(120) == 32
        assert compute_status_panel_width(200) == 32

    def test_classic_tier_returns_28(self) -> None:
        assert compute_status_panel_width(80) == 28
        assert compute_status_panel_width(90) == 28
        assert compute_status_panel_width(99) == 28

    def test_compact_tier_returns_22(self) -> None:
        assert compute_status_panel_width(60) == 22
        assert compute_status_panel_width(70) == 22
        assert compute_status_panel_width(79) == 22

    def test_phone_tier_returns_18(self) -> None:
        assert compute_status_panel_width(40) == 18
        assert compute_status_panel_width(50) == 18
        assert compute_status_panel_width(59) == 18

    def test_status_panel_always_smaller_than_width(self) -> None:
        """Status panel must always leave room for MAIN area."""
        for w in (40, 50, 60, 70, 80, 90, 100, 120):
            sp = compute_status_panel_width(w)
            assert sp < w // 2, f"status panel {sp} too wide for total {w}"


class TestMakeShellAdaptive:
    """make_shell() adapts region sizes to width/height (ADR-0198)."""

    def test_classic_default_80x50(self) -> None:
        shell = make_shell(80, 50)
        assert shell[RegionId.MAIN].w == 80 - 28  # 52
        assert shell[RegionId.STATUS_PANEL].w == 28
        assert shell[RegionId.STATUS_PANEL].h == 35
        assert shell[RegionId.SIDE].y == 39
        assert shell[RegionId.CONTROLS].y == 45
        assert shell[RegionId.FOOTER].y == 49

    def test_wide_preset_shell_100x55(self) -> None:
        shell = make_shell(100, 55)
        assert shell[RegionId.MAIN].w == 100 - 32  # 68 (wider status panel)
        assert shell[RegionId.STATUS_PANEL].w == 32

    def test_compact_preset_shell_60x35(self) -> None:
        shell = make_shell(60, 35)
        assert shell[RegionId.MAIN].w == 60 - 22  # 38
        assert shell[RegionId.STATUS_PANEL].w == 22

    def test_phone_preset_shell_50x40(self) -> None:
        shell = make_shell(50, 40)
        assert shell[RegionId.STATUS_PANEL].w == 18

    def test_shell_regions_within_console_bounds(self) -> None:
        """All regions must fit within the console dimensions."""
        for cols, rows in ((80, 50), (100, 55), (60, 35), (120, 50)):
            shell = make_shell(cols, rows)
            for region in shell.values():
                assert region.x2 < cols, f"{region.id}: x2 {region.x2} >= cols {cols}"
                assert region.y2 < rows, f"{region.id}: y2 {region.y2} >= rows {rows}"

    def test_shell_regions_no_overlap_main_status(self) -> None:
        """MAIN and STATUS_PANEL must not overlap horizontally."""
        for cols in (80, 100, 120):
            shell = make_shell(cols, 50)
            main = shell[RegionId.MAIN]
            panel = shell[RegionId.STATUS_PANEL]
            assert main.x2 < panel.x or panel.x2 < main.x


class TestAppStateResolution:
    """AppState.resolution field (Commit 3)."""

    def test_default_resolution_field(self) -> None:
        s = AppState()
        assert s.resolution == "classic"

    def test_resolution_field_can_be_set(self) -> None:
        s = AppState()
        s.resolution = "wide"
        assert s.resolution == "wide"

    def test_resolution_round_trip_via_save_manager(self) -> None:
        """Save manager preserves resolution field (GA-004 + ADR-0198)."""
        from wet_run.engine.save_manager import SaveManager

        state = AppState()
        state.resolution = "tablet_landscape"
        # Use default factory methods that don't depend on disk.
        sm = SaveManager.__new__(SaveManager)
        # Round-trip via the methods added in Commit 3.
        data = sm._serialize_app_state(state)
        assert data["resolution"] == "tablet_landscape"

        # Restore test
        state2 = AppState()
        sm._restore_app_state_fields(state2, data)
        assert state2.resolution == "tablet_landscape"

    def test_resolution_legacy_save_default_to_classic(self) -> None:
        """Saves without 'resolution' key (legacy) load as 'classic'."""
        from wet_run.engine.save_manager import SaveManager

        sm = SaveManager.__new__(SaveManager)
        state = AppState()
        sm._restore_app_state_fields(state, {})
        assert state.resolution == "classic"
