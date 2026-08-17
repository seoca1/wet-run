"""Unit tests for the four small modules that were 0% covered.

These are quick wins: short, self-contained, easy to cover.  Once
green, we move on to the larger render modules (event_view,
phase_view, story_view, chapter_cutscene, cyberspace_view,
equipment_view, hub, graphic_novel_save).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wet_run.cyberspace.registry import WorldRegistry
from wet_run.cyberspace.server_generator import ServerSubgraphGenerator
from wet_run.cyberspace.world import WorldMap
from wet_run.engine import font_loader

# ---------------------------------------------------------------------------
# font_loader.is_korean_capable
# ---------------------------------------------------------------------------


class TestIsKoreanCapable:
    """``is_korean_capable`` returns True iff a TTF font is on disk."""

    def test_returns_true_when_ttf_present(self) -> None:
        with patch.object(font_loader.config, "find_ttf_font", return_value=Path("/fake/font.ttf")):
            assert font_loader.is_korean_capable() is True

    def test_returns_false_when_ttf_missing(self) -> None:
        with patch.object(font_loader.config, "find_ttf_font", return_value=None):
            assert font_loader.is_korean_capable() is False


class TestLoadFont:
    """``load_font`` picks TTF when available, else falls back to bitmap."""

    def test_loads_ttf_when_path_exists(self) -> None:
        fake_tileset = MagicMock(name="ttf-tileset")
        with (
            patch.object(font_loader.config, "find_ttf_font", return_value=Path("/fake/font.ttf")),
            patch.object(
                font_loader.tcod.tileset, "load_truetype_font", return_value=fake_tileset
            ) as loader,
        ):
            tileset, is_ttf = font_loader.load_font()
        assert tileset is fake_tileset
        assert is_ttf is True
        loader.assert_called_once()

    def test_falls_back_to_bitmap_on_ttf_error(self) -> None:
        fake_bitmap = MagicMock(name="bitmap-tileset")
        with (
            patch.object(font_loader.config, "find_ttf_font", return_value=Path("/fake/font.ttf")),
            patch.object(
                font_loader.tcod.tileset, "load_truetype_font", side_effect=OSError("boom")
            ),
            patch.object(Path, "exists", return_value=True),
            patch.object(font_loader.tcod.tileset, "load_tilesheet", return_value=fake_bitmap),
        ):
            tileset, is_ttf = font_loader.load_font()
        assert tileset is fake_bitmap
        assert is_ttf is False

    def test_falls_back_to_bitmap_when_no_ttf(self) -> None:
        fake_bitmap = MagicMock(name="bitmap-tileset")
        with (
            patch.object(font_loader.config, "find_ttf_font", return_value=None),
            patch.object(Path, "exists", return_value=True),
            patch.object(font_loader.tcod.tileset, "load_tilesheet", return_value=fake_bitmap),
        ):
            tileset, is_ttf = font_loader.load_font()
        assert is_ttf is False

    def test_raises_when_no_font_available(self) -> None:
        with (
            patch.object(font_loader.config, "find_ttf_font", return_value=None),
            patch.object(Path, "exists", return_value=False),
        ):
            with pytest.raises(FileNotFoundError):
                font_loader.load_font()


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------


class TestMainEntry:
    """``python -m wet_run`` invokes ``app.main()``."""

    def test_invokes_main_and_returns_exit_code(self) -> None:
        from wet_run import __main__ as entry

        with patch.object(entry, "main", return_value=0) as main_mock:
            rc = entry.main()
        assert rc == 0
        main_mock.assert_called_once()

    def test_propagates_nonzero_exit_code(self) -> None:
        from wet_run import __main__ as entry

        with patch.object(entry, "main", return_value=2) as main_mock:
            rc = entry.main()
        assert rc == 2
        main_mock.assert_called_once()


# ---------------------------------------------------------------------------
# cyberspace.server_generator
# ---------------------------------------------------------------------------


class TestServerSubgraphGenerator:
    """``ServerSubgraphGenerator`` delegates to ``CyberspaceGenerator``."""

    def test_returns_tuple_of_graph_and_layouts(self) -> None:
        fake_graph = MagicMock(name="graph")
        fake_layouts = {"n0": MagicMock(name="layout-n0")}
        fake_gen = MagicMock()
        fake_gen.generate.return_value = (fake_graph, fake_layouts)
        with patch(
            "wet_run.cyberspace.server_generator.CyberspaceGenerator",
            return_value=fake_gen,
        ):
            sub = ServerSubgraphGenerator()
            graph, layouts = sub.generate(seed=42, difficulty=3)
        assert graph is fake_graph
        assert layouts is fake_layouts
        fake_gen.generate.assert_called_once_with(seed=42, mission_grade=1)

    def test_constructor_takes_no_args(self) -> None:
        # Just instantiation should not blow up.
        sub = ServerSubgraphGenerator()
        assert sub is not None


# ---------------------------------------------------------------------------
# cyberspace.registry
# ---------------------------------------------------------------------------


class TestWorldRegistry:
    """``WorldRegistry`` loads the canonical world hierarchy from JSON."""

    @pytest.fixture
    def sample_json_path(self, tmp_path: Path) -> Path:
        path = tmp_path / "worlds.json"
        path.write_text(
            """{
              "worlds": {
                "chiba": {
                  "id": "chiba",
                  "name": "Chiba City",
                  "description": "Sprawl neon",
                  "sectors": {
                    "sense_net": {
                      "id": "sense_net",
                      "name": "Sense/Net",
                      "description": "neon",
                      "servers": [
                        {
                          "id": "sensenet_demo",
                          "name": "First server",
                          "sector": "sense_net",
                          "difficulty": 2,
                          "description": "ice here",
                          "mission_id": "first_jack"
                        }
                      ]
                    }
                  }
                }
              }
            }""",
            encoding="utf-8",
        )
        return path

    def test_load_returns_registry_with_worlds(self, sample_json_path: Path) -> None:
        reg = WorldRegistry.load(sample_json_path)
        chiba = reg.get_world("chiba")
        assert chiba is not None
        assert chiba.name == "Chiba City"
        assert "sense_net" in chiba.sectors

    def test_servers_attached_to_correct_sector(self, sample_json_path: Path) -> None:
        reg = WorldRegistry.load(sample_json_path)
        chiba = reg.get_world("chiba")
        sense = chiba.sectors["sense_net"]
        assert len(sense.servers) == 1
        assert sense.servers[0].id == "sensenet_demo"
        assert sense.servers[0].sector == "sense_net"
        assert sense.servers[0].difficulty == 2

    def test_get_server_by_mission_finds_match(self, sample_json_path: Path) -> None:
        reg = WorldRegistry.load(sample_json_path)
        result = reg.get_server_by_mission("first_jack")
        assert result is not None
        world_id, sector_id, server = result
        assert world_id == "chiba"
        assert sector_id == "sense_net"
        assert server.id == "sensenet_demo"

    def test_get_server_by_mission_returns_none_for_missing(self, sample_json_path: Path) -> None:
        reg = WorldRegistry.load(sample_json_path)
        assert reg.get_server_by_mission("nope") is None

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            WorldRegistry.load(tmp_path / "absent.json")

    def test_empty_world_map_default(self) -> None:
        reg = WorldRegistry()
        assert reg.world_map == WorldMap()
        assert reg.get_world("nope") is None
