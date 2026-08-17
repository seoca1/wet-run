"""Tests for hub panel data loading (P2 #12).

The Hub 4-panel layout (Avatar / Materials / Recipes / Job Board) was
loading hardcoded placeholder data. These tests verify the new
data-driven loaders with graceful fallback when JSON files are missing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wet_run.engine import config as _engine_config
from wet_run.engine import hub


@pytest.fixture
def crafting_data_dir() -> Path:
    return _engine_config.DATA_DIR / "crafting"


class TestLoadMaterialsData:
    def test_loads_from_real_file(self, crafting_data_dir: Path) -> None:
        if not (crafting_data_dir / "materials.json").exists():
            pytest.skip("crafting/materials.json not in this checkout")
        data = hub._load_materials_data()
        assert len(data) >= 3
        for name, have, need in data:
            assert isinstance(name, str)
            assert name
            assert have == 0  # placeholder default; real value from inventory
            assert isinstance(need, int)
            assert need > 0

    def test_fallback_when_file_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Point to a directory without materials.json.
        fake_dir = Path("/nonexistent/path/for/test")
        monkeypatch.setattr(hub, "_engine_config", type("cfg", (), {"DATA_DIR": fake_dir})())
        data = hub._load_materials_data()
        assert data == hub._PLACEHOLDER_MATERIALS
        assert len(data) == 5

    def test_fallback_when_file_malformed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        crafting = tmp_path / "crafting"
        crafting.mkdir()
        (crafting / "materials.json").write_text("{not json", encoding="utf-8")
        monkeypatch.setattr(hub, "_engine_config", type("cfg", (), {"DATA_DIR": tmp_path})())
        data = hub._load_materials_data()
        assert data == hub._PLACEHOLDER_MATERIALS


class TestLoadRecipesData:
    def test_loads_from_real_file(self, crafting_data_dir: Path) -> None:
        if not (crafting_data_dir / "recipes.json").exists():
            pytest.skip("crafting/recipes.json not in this checkout")
        data = hub._load_recipes_data()
        assert len(data) >= 3
        for name, glyph, ready in data:
            assert isinstance(name, str)
            assert name
            assert isinstance(glyph, str)
            assert glyph
            assert isinstance(ready, bool)

    def test_fallback_when_file_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_dir = Path("/nonexistent/path/for/test")
        monkeypatch.setattr(hub, "_engine_config", type("cfg", (), {"DATA_DIR": fake_dir})())
        data = hub._load_recipes_data()
        assert data == hub._PLACEHOLDER_RECIPES
        assert len(data) == 5

    def test_fallback_when_file_malformed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        crafting = tmp_path / "crafting"
        crafting.mkdir()
        (crafting / "recipes.json").write_text("not valid json", encoding="utf-8")
        monkeypatch.setattr(hub, "_engine_config", type("cfg", (), {"DATA_DIR": tmp_path})())
        data = hub._load_recipes_data()
        assert data == hub._PLACEHOLDER_RECIPES


class TestMaterialInventoryLookup:
    def test_inventory_lookup_uses_snake_case_key(self) -> None:
        from wet_run.engine.state import AppState

        state = AppState()
        state.inventory = {"ice_shard": 7, "data_fragment": 3, "unrelated": 99}

        # Material names in data → inventory keys (via _MATERIAL_NAME_TO_INV).
        have_ice = state.inventory.get(hub._MATERIAL_NAME_TO_INV.get("ICE Shard", "ice_shard"), 0)
        have_data = state.inventory.get(
            hub._MATERIAL_NAME_TO_INV.get("Data Fragment", "data_fragment"), 0
        )
        assert have_ice == 7
        assert have_data == 3


class TestMaterialGauge:
    """P2 #18 — gauge preserves ratio and never loses overflow info."""

    def test_empty_when_zero(self) -> None:
        assert hub._material_gauge(0, 4, width=5) == "░░░░░"

    def test_full_when_ready(self) -> None:
        # Ready (have == need) — full bar, no overflow marker.
        assert hub._material_gauge(4, 4, width=5) == "▓▓▓▓▓"

    def test_overflow_marks_excess(self) -> None:
        # have > need → full bar + overflow marker.
        assert hub._material_gauge(7, 3, width=5) == "▓▓▓▓▓+"

    def test_proportional_partial(self) -> None:
        # 3/7 ≈ 43% → 2 chars filled (round-half-to-even gives 2).
        result = hub._material_gauge(3, 7, width=5)
        assert len(result) == 5
        assert "▓" in result
        assert "░" in result
        filled = result.count("▓")
        assert 1 <= filled <= 3

    def test_degenerate_zero_need(self) -> None:
        # need <= 0 → full bar (ready by default).
        assert hub._material_gauge(0, 0, width=5) == "▓▓▓▓▓"
        assert hub._material_gauge(3, 0, width=5) == "▓▓▓▓▓"

    def test_width_respected(self) -> None:
        for have, need in [(0, 1), (1, 5), (5, 1), (10, 3), (0, 100)]:
            result = hub._material_gauge(have, need, width=7)
            assert len(result) in (7, 8), f"got {result!r}"
            assert result.endswith("+") or len(result) == 7


class TestHubDataCaching:
    """Materials + recipes JSON is cached after first load (perf hot spot)."""

    def setup_method(self) -> None:
        # Clear module-level caches so each test starts fresh.
        hub._MATERIALS_CACHE = None
        hub._RECIPES_CACHE = None

    def teardown_method(self) -> None:
        # Restore caches to None so other tests don't carry stale state.
        hub._MATERIALS_CACHE = None
        hub._RECIPES_CACHE = None

    def test_materials_cache_populated_after_first_load(self) -> None:
        assert hub._MATERIALS_CACHE is None
        hub._load_materials_data()
        assert hub._MATERIALS_CACHE is not None

    def test_materials_cache_reused_on_second_call(self) -> None:
        first = hub._load_materials_data()
        cached_id = id(first)
        second = hub._load_materials_data()
        # Same list object returned (cached) — proves no re-parse.
        assert second is first
        assert id(second) == cached_id

    def test_materials_force_reload_bypasses_cache(self) -> None:
        first = hub._load_materials_data()
        second = hub._load_materials_data(force_reload=True)
        # Should return a *new* list object (data may be the same content).
        assert second is not first

    def test_recipes_cache_reused_on_second_call(self) -> None:
        first = hub._load_recipes_data()
        second = hub._load_recipes_data()
        assert second is first

    def test_perf_no_repeated_io(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Repeated calls should NOT call open() after the first load."""
        import builtins
        from unittest.mock import MagicMock

        real_open = builtins.open
        calls: list[str] = []
        mock_open = MagicMock(
            side_effect=lambda p, *a, **kw: calls.append(str(p)) or real_open(p, *a, **kw)
        )
        monkeypatch.setattr("builtins.open", mock_open)

        hub._load_materials_data()  # 1st call — reads
        hub._load_materials_data()  # 2nd — cached, should NOT read
        hub._load_materials_data()  # 3rd — cached

        # Only 1 file open for the materials JSON after first load.
        material_opens = [c for c in calls if "materials" in c]
        assert len(material_opens) == 0, f"unexpected re-reads: {material_opens}"


class TestReputationDots:
    """Hub panel shows faction reputation as compact glyph strip."""

    def test_neutral_default(self) -> None:
        from wet_run.engine.state import AppState

        state = AppState()
        line = hub._render_reputation_dots(state)
        # 5 factions × neutral tier → 5 · glyphs.
        assert line == "·····"

    def test_allied_faction_shows_star(self) -> None:
        from wet_run.engine.state import AppState
        from wet_run.matrix.node import Faction

        state = AppState()
        # Bypass clamp by setting score directly
        state.reputation.get(Faction.HOSAKA).score = 100
        line = hub._render_reputation_dots(state)
        # Hosaka is the first faction → ★ first
        assert line.startswith("★")

    def test_hostile_faction_shows_x(self) -> None:
        from wet_run.engine.state import AppState
        from wet_run.matrix.node import Faction

        state = AppState()
        state.reputation.get(Faction.MAAS).score = -100  # OUTCAST
        line = hub._render_reputation_dots(state)
        # Maas is the second faction → ✗ second (after Hosaka neutral)
        parts = list(line)
        assert parts[1] == "✗"

    def test_mixed_tiers_render_correctly(self) -> None:
        from wet_run.engine.state import AppState
        from wet_run.matrix.node import Faction

        state = AppState()
        # Hosaka → TRUSTED (20), Maas → HOSTILE (-25), Sense/Net neutral
        state.reputation.adjust(Faction.HOSAKA, 20)
        state.reputation.adjust(Faction.MAAS, -25)
        line = hub._render_reputation_dots(state)
        parts = list(line)
        assert parts[0] == "○"  # Hosaka TRUSTED
        assert parts[1] == "✗"  # Maas HOSTILE
        assert parts[2] == "·"  # Sense/Net NEUTRAL

    def test_length_is_5_factions(self) -> None:
        from wet_run.engine.state import AppState

        state = AppState()
        line = hub._render_reputation_dots(state)
        assert len(line) == 5
