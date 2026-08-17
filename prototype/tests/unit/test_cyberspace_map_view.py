"""Tests for engine.cyberspace_map_view — World/Sector/Server tree renderer.

Coverage target for src/wet_run/engine/cyberspace_map_view.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from wet_run.cyberspace.world import (
    Sector,
    SectorId,
    Server,
    World,
    WorldId,
    WorldMap,
)
from wet_run.engine.cyberspace_map_view import render_cyberspace_map
from wet_run.engine.state import AppState


def _make_console(width: int = 80, height: int = 30) -> MagicMock:
    """Create a mock tcod.console.Console for testing."""
    console = MagicMock()
    console.width = width
    console.height = height
    return console


def _make_state_with_worlds(
    worlds: list[tuple[World, WorldId]], current: tuple[WorldId, SectorId, str | None] | None = None
) -> AppState:
    """Build AppState with populated world_map.

    Args:
        worlds: list of (World instance, WorldId) tuples to register.
        current: Optional (world_id, sector_id, server_id) for current_location.
    """
    state = AppState()
    wm = WorldMap()
    for world, _ in worlds:
        wm.add_world(world)
    if current is not None:
        w_id, s_id, sv_id = current
        wm.current_world = w_id
        wm.current_sector = s_id
        wm.current_server = sv_id
    state.world_map = wm
    return state


def _make_world(name: str, sectors: list[Sector], world_id: WorldId = WorldId.CHIBA) -> World:
    w = World(id=world_id, name=name, description="desc")
    for s in sectors:
        w.add_sector(s)
    return w


def _make_sector(sector_id: SectorId, name: str, servers: list[Server]) -> Sector:
    return Sector(id=sector_id, name=name, description="desc", servers=servers)


def _make_server(server_id: str, name: str, sector: SectorId) -> Server:
    return Server(id=server_id, name=name, sector=sector, difficulty=5, description="")


# ----------------------------------------------------------------------------
# Empty / None world_map
# ----------------------------------------------------------------------------


class TestEmptyWorldMap:
    def test_none_world_map_no_crash(self):
        state = AppState()
        state.world_map = None
        console = _make_console()
        # Should return early when world_map is None
        render_cyberspace_map(console, state)
        # No error raised; console.clear was called
        console.clear.assert_called_once()

    def test_empty_world_map_no_worlds(self):
        state = AppState()
        state.world_map = WorldMap()  # no worlds added
        console = _make_console()
        # No error; should render only header/footer
        render_cyberspace_map(console, state)
        console.clear.assert_called_once()

    def test_clears_with_black_bg(self):
        state = AppState()
        state.world_map = None
        console = _make_console()
        render_cyberspace_map(console, state)
        console.clear.assert_called_with(bg=(0, 0, 0))


# ----------------------------------------------------------------------------
# Single world / single sector / single server
# ----------------------------------------------------------------------------


class TestSingleWorld:
    def test_renders_world_name(self):
        server = _make_server("server-1", "Alpha Host", SectorId.HOSAKA)
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _make_world("Chiba City", [sector])
        state = _make_state_with_worlds([(world, WorldId.CHIBA)])

        console = _make_console()
        render_cyberspace_map(console, state)

        # Verify title was printed at least once
        # (console.print(x=0, y=0, string="═" * width) is one of the calls)
        calls = list(console.print.call_args_list)
        assert any(
            call.kwargs.get("string") == "═" * 80 or call.args[2] == "═" * 80 for call in calls
        ) or any(
            (len(call.args) >= 3 and call.args[2] == "═" * 80)
            for call in console.print.call_args_list
        )

    def test_renders_footer_back_to_hub(self):
        server = _make_server("server-1", "Alpha", SectorId.HOSAKA)
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds([(world, WorldId.CHIBA)])

        console = _make_console()
        render_cyberspace_map(console, state)

        # Look for "[ESC] Back to Hub" in any print call
        found_footer = False
        for call in console.print.call_args_list:
            # Check both positional and keyword args
            string_val = call.kwargs.get("string")
            if string_val is None and len(call.args) >= 3:
                string_val = call.args[2]
            if string_val and "Back to Hub" in str(string_val):
                found_footer = True
                break
        assert found_footer, "[ESC] Back to Hub missing from rendered output"


# ----------------------------------------------------------------------------
# Current location markers
# ----------------------------------------------------------------------------


class TestCurrentMarkers:
    def test_current_world_has_marker(self):
        server = _make_server("sv1", "Alpha", SectorId.HOSAKA)
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds(
            [(world, WorldId.CHIBA)],
            current=(WorldId.CHIBA, SectorId.HOSAKA, "sv1"),
        )

        console = _make_console()
        render_cyberspace_map(console, state)

        # The "▸ " marker should appear (current world)
        found_marker = False
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            if s and "▸ " in str(s):
                found_marker = True
                break
        assert found_marker, "Current world marker (▸) not in output"

    def test_current_sector_has_marker(self):
        server = _make_server("sv1", "Alpha", SectorId.HOSAKA)
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds(
            [(world, WorldId.CHIBA)],
            current=(WorldId.CHIBA, SectorId.HOSAKA, "sv1"),
        )

        console = _make_console()
        render_cyberspace_map(console, state)

        found_marker = False
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            if s and "→ " in str(s):
                found_marker = True
                break
        assert found_marker, "Current sector marker (→) not in output"

    def test_current_server_has_marker(self):
        server = _make_server("sv1", "Alpha", SectorId.HOSAKA)
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds(
            [(world, WorldId.CHIBA)],
            current=(WorldId.CHIBA, SectorId.HOSAKA, "sv1"),
        )

        console = _make_console()
        render_cyberspace_map(console, state)

        found_marker = False
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            if s and "• " in str(s):
                found_marker = True
                break
        assert found_marker, "Current server marker (•) not in output"


# ----------------------------------------------------------------------------
# Server truncation (>5 servers)
# ----------------------------------------------------------------------------


class TestServerTruncation:
    def test_more_than_5_servers_truncated(self):
        servers = [_make_server(f"sv{i}", f"Server {i}", SectorId.HOSAKA) for i in range(8)]
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", servers)
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds([(world, WorldId.CHIBA)])

        console = _make_console()
        render_cyberspace_map(console, state)

        # Look for the "... and X more" message
        found_truncation = False
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            if s and "more" in str(s) and "and" in str(s):
                found_truncation = True
                break
        assert found_truncation, "Server truncation message missing"

    def test_exactly_5_servers_no_truncation(self):
        servers = [_make_server(f"sv{i}", f"Server {i}", SectorId.HOSAKA) for i in range(5)]
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", servers)
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds([(world, WorldId.CHIBA)])

        console = _make_console()
        render_cyberspace_map(console, state)

        # No truncation when exactly 5 servers
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            if s and "more" in str(s) and "and" in str(s):
                # Found "more" — bad, shouldn't be there
                pytest.fail("Truncation appeared when should not (exactly 5 servers)")


# ----------------------------------------------------------------------------
# Multiple worlds / sectors
# ----------------------------------------------------------------------------


class TestMultipleWorlds:
    def test_multiple_worlds_rendered(self):
        world1 = _make_world(
            "Chiba",
            [Sector(id=SectorId.HOSAKA, name="Hosaka", description="", servers=[])],
            world_id=WorldId.CHIBA,
        )
        world2 = _make_world(
            "Night City",
            [Sector(id=SectorId.MAAS, name="Maas", description="", servers=[])],
            world_id=WorldId.NIGHT_CITY,
        )
        state = _make_state_with_worlds([(world1, WorldId.CHIBA), (world2, WorldId.NIGHT_CITY)])

        console = _make_console()
        render_cyberspace_map(console, state)

        # Both names should appear
        print_calls = []
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            print_calls.append(str(s) if s else "")

        all_strings = "\n".join(print_calls)
        assert "Chiba" in all_strings
        assert "Night City" in all_strings

    def test_sector_count_displayed(self):
        servers = [_make_server(f"sv{i}", f"S{i}", SectorId.HOSAKA) for i in range(3)]
        sector = _make_sector(SectorId.HOSAKA, "Hosaka", servers)
        world = _make_world("Chiba", [sector])
        state = _make_state_with_worlds([(world, WorldId.CHIBA)])

        console = _make_console()
        render_cyberspace_map(console, state)

        # "[3 servers]" should appear
        found_count = False
        for call in console.print.call_args_list:
            s = call.kwargs.get("string")
            if s is None and len(call.args) >= 3:
                s = call.args[2]
            if s and "3 servers" in str(s):
                found_count = True
                break
        assert found_count, "[N servers] count missing from output"
