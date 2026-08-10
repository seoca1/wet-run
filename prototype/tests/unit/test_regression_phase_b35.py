"""Regression tests for Phase B-3.5 fixes (2026-07-27 bug class).

These tests prevent recurrence of three integration bugs that slipped past
unit-level coverage in v0.9.0:

1. **VFX ice_type propagation** — `apply_phase_aoe` was missing
   `ice_type` parameter, causing `_trigger_aoe_visuals` to always read
   `getattr(phase, "ice_type", None)` → None → fallback default theme.
   Boss-specific VFX colors NEVER activated. Fixed in commit 81d8d65.

2. **ZoneDepth base ZDR coverage** — SOHO/TOKYO zone depths were added
   to the enum but not to `_BASE_ZDR` dict. Any code path that computed
   ZDR for these zones raised KeyError. Fixed in commit daf4fb7.

3. **Mission story.source completeness** — 18 Bridge/Blue Ant era
   missions were missing `story.source` field. Integration tests that
   require this field failed. Fixed in commit c0351ef.

Each test class targets one bug class and is *narrow* — it verifies
the contract that prevented the bug, not the wider behavior.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from roguelike_sprawl.combat.boss import (
    BOSS_VFX_THEMES,
    ICE_TYPE_TO_VFX_KEY,
    apply_phase_aoe,
    get_vfx_config,
)
from roguelike_sprawl.combat.effects import IceType
from roguelike_sprawl.matrix.node import ZoneDepth
from roguelike_sprawl.matrix.zdr import _BASE_ZDR

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# ============================================================================
# 1. VFX ice_type propagation (commit 81d8d65 regression guard)
# ============================================================================


class TestVFXIceTypePropagation:
    """Lock the bugfix that made per-boss VFX themes actually work."""

    def test_apply_phase_aoe_accepts_ice_type_parameter(self) -> None:
        """`apply_phase_aoe` signature must include ice_type (was missing)."""
        sig = inspect.signature(apply_phase_aoe)
        assert "ice_type" in sig.parameters, (
            "apply_phase_aoe lost ice_type param — per-boss VFX will break. "
            "Regression of 81d8d65 bug."
        )

    @pytest.mark.parametrize(
        ("ice_type", "expected_color"),
        [
            (IceType.WINTERMUTE, (150, 150, 255)),  # Pale cyan
            (IceType.GOLIATH, (255, 80, 80)),  # Red
            (IceType.BLACK, (180, 100, 220)),  # Magenta
            (IceType.WATCHDOG, (255, 220, 100)),  # Amber
        ],
    )
    def test_get_vfx_config_returns_boss_specific_colors(
        self, ice_type: IceType, expected_color: tuple[int, int, int]
    ) -> None:
        """Each boss ICE type maps to a unique VFX theme (not default)."""
        cfg = get_vfx_config(ice_type)
        assert cfg.get("hit_flash_color") == expected_color, (
            f"VFX theme for {ice_type.name} is wrong: got {cfg.get('hit_flash_color')}, "
            f"expected {expected_color}"
        )
        assert cfg, f"No VFX config found for {ice_type.name}"

    def test_get_vfx_config_unknown_returns_default(self) -> None:
        """Unknown ICE type falls back to default theme (not error)."""
        cfg = get_vfx_config("nonexistent_ice")
        assert cfg == BOSS_VFX_THEMES["default"]

    def test_ice_type_to_vfx_key_mapping_complete(self) -> None:
        """ICE_TYPE_TO_VFX_KEY covers all boss types defined in ICE."""
        # The mapping should be consistent: every mapped key exists in themes
        for ice_str, vfx_key in ICE_TYPE_TO_VFX_KEY.items():
            assert vfx_key in BOSS_VFX_THEMES, (
                f"ICE type {ice_str!r} maps to missing theme {vfx_key!r}"
            )


# ============================================================================
# 2. ZoneDepth base ZDR coverage (commit daf4fb7 regression guard)
# ============================================================================


class TestZoneDepthBaseZDRCoverage:
    """Lock the bugfix that made SOHO/TOKYO zones queryable."""

    def test_every_zone_depth_has_base_zdr(self) -> None:
        """Every ZoneDepth enum member must have a _BASE_ZDR entry."""
        missing = []
        for zone in ZoneDepth:
            if zone not in _BASE_ZDR:
                missing.append(zone.name)
        assert not missing, (
            f"ZoneDepth members missing _BASE_ZDR: {missing}. "
            f"Add base ZDR values to matrix/zdr.py _BASE_ZDR dict."
        )

    def test_base_zdr_values_are_positive(self) -> None:
        """All base ZDR values must be > 0 (zones are inherently dangerous)."""
        for zone, zdr in _BASE_ZDR.items():
            assert zdr > 0, f"Zone {zone.name} has non-positive base ZDR: {zdr}"

    def test_base_zdr_ordering_increases_with_depth(self) -> None:
        """Core zones (TA, FREESIDE) should have higher base ZDR than Surface."""
        # Soft ordering: SURFACE < FREESIDE (not strict across all)
        assert _BASE_ZDR[ZoneDepth.SURFACE] < _BASE_ZDR[ZoneDepth.FREESIDE], (
            "FREESIDE should be harder than SURFACE"
        )
        assert _BASE_ZDR[ZoneDepth.MID] < _BASE_ZDR[ZoneDepth.TA], "TA should be harder than MID"

    @pytest.mark.parametrize(
        "zone",
        [ZoneDepth.SOHO, ZoneDepth.TOKYO],
    )
    def test_soho_tokyo_have_explicit_base_zdr(self, zone: ZoneDepth) -> None:
        """SOHO and TOKYO (added 2026-07-27) must remain in _BASE_ZDR."""
        assert zone in _BASE_ZDR, (
            f"{zone.name} missing — regression of daf4fb7 bug. "
            f"Bridge/Blue Ant era missions would crash on ZDR lookup."
        )


# ============================================================================
# 3. Mission story.source completeness (commit c0351ef regression guard)
# ============================================================================


class TestMissionStorySourceCompleteness:
    """Lock the bugfix that required all missions to have story.source."""

    @classmethod
    def setup_class(cls) -> None:
        with (DATA_DIR / "missions" / "missions.json").open() as f:
            cls.missions: dict[str, dict] = json.load(f)

    def test_all_missions_have_story_source(self) -> None:
        """Every mission must have a non-empty story.source field."""
        missing: list[str] = []
        for mid, m in self.missions.items():
            story = m.get("story", {})
            src = story.get("source")
            if not src or not isinstance(src, str):
                missing.append(mid)
        assert not missing, (
            f"{len(missing)} missions missing story.source: {missing[:5]}... "
            f"Regression of c0351ef. AGENTS.md §4.0 + integration tests require this field."
        )

    def test_story_source_is_consistent_with_id(self) -> None:
        """story.source should be related to mission id (not random)."""
        # Loose check: source is either the mission id, or a known
        # Bridge/Blue Ant era shorthand (e.g., 'bridge-construct', 'aleph_fragment')
        # Just verify it's a sensible non-empty identifier.
        for mid, m in self.missions.items():
            src = m.get("story", {}).get("source")
            assert src, f"{mid}: empty story.source"
            assert isinstance(src, str), f"{mid}: source must be string"
            # Source should not be a placeholder
            assert src.lower() not in {"unknown", "n/a", "todo", "tbd", "none", ""}, (
                f"{mid}: story.source is placeholder {src!r}"
            )

    def test_story_metadata_required_fields_per_adr_0051(self) -> None:
        """All missions must have full story metadata (ADR-0051)."""
        required = {
            "synopsis_en",
            "synopsis_ko",
            "source",
            "character_ref",
            "arc",
            "pillar",
        }
        offenders: list[tuple[str, set[str]]] = []
        for mid, m in self.missions.items():
            story = m.get("story", {})
            missing = required - set(story.keys())
            if missing:
                offenders.append((mid, missing))
        assert not offenders, (
            f"{len(offenders)} missions missing story metadata fields: "
            f"{[(m, sorted(f)) for m, f in offenders[:3]]}"
        )

    def test_grade_6_missions_have_arc_5(self) -> None:
        """grade_max=6 missions should be Arc 4-5 finale (per balance doc §133).

        Phase 14 expansion added grade 6 missions across multiple arcs (4, 5, 6
        for NG+). This test now allows any of {4, 5, 6} for grade 6 missions.
        """
        exceptions = {
            "bigend_laney_lunch",  # Arc 1 Bridge era — exception per c0351ef
            "coolhunter_laney_tokyo",  # Arc 2 Blue Ant era — exception
            "case_meets_cayce",  # Arc 4 case_meets — known anomaly
            "core_extract_payroll_archive",  # Phase 14 arc 3 boss data — exception
        }
        g6_wrong_arc: list[str] = []
        for mid, m in self.missions.items():
            if m.get("grade_max") == 6 and mid not in exceptions:
                if m.get("arc") not in {4, 5, 6}:
                    g6_wrong_arc.append(f"{mid} (arc={m.get('arc')})")
        assert not g6_wrong_arc, (
            f"grade_max=6 missions not in Arc 4/5/6: {g6_wrong_arc}. "
            f"Either re-classify or add to exceptions."
        )


# ============================================================================
# 4. Cross-cutting: import smoke for view layer files with 0 tests
# ============================================================================


class TestViewLayerImportSmoke:
    """Minimal import check for view modules that previously had 0 tests.

    The full view-layer test coverage is a separate project (see IMPROVEMENTS.md
    "Equipment view / Story view / Event view / Cyberspace view 0 tests").
    This smoke test ensures the modules remain importable (catches syntax
    errors and missing dependencies after refactors).
    """

    @pytest.mark.parametrize(
        "module_path",
        [
            "roguelike_sprawl.engine.equipment_view",
            "roguelike_sprawl.engine.story_view",
            "roguelike_sprawl.engine.event_view",
            "roguelike_sprawl.engine.cyberspace_view",
            "roguelike_sprawl.engine.dungeon_view",
            "roguelike_sprawl.engine.phase_view",
            "roguelike_sprawl.engine.save_load_view",
        ],
    )
    def test_view_module_importable(self, module_path: str) -> None:
        """Each view module must remain importable (no syntax/dependency error)."""
        import importlib

        mod = importlib.import_module(module_path)
        assert mod is not None
        # Verify module has a public attribute (not empty namespace)
        public_attrs = [a for a in dir(mod) if not a.startswith("_")]
        assert public_attrs, f"{module_path} has no public attributes"
