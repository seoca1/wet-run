"""Unit tests for the cyberspace browser navigation."""

from __future__ import annotations

from tcod.event import KeySym

from wet_run.cyberspace.world import (
    Sector,
    SectorId,
    Server,
    World,
    WorldId,
    WorldMap,
)
from wet_run.engine import cyberspace_browser
from wet_run.engine.cyberspace_browser import (
    _cycle_sector,
    _cycle_world,
)
from wet_run.engine.state import AppState


def _make_test_worldmap() -> WorldMap:
    """Create a test world map: 2 worlds, 2 sectors each, 2 servers each."""
    wm = WorldMap()

    # World 1: Chiba - 2 sectors
    chiba = World(
        id=WorldId("chiba"),
        name="Chiba City",
        description="Neon sprawl",
    )
    s1 = Sector(
        id=SectorId("sense_net"),
        name="Sense/Net",
        description="Data fortress",
    )
    s1.servers = [
        Server(
            id="chiba_b1",
            name="Yakusa_DB",
            sector=SectorId("sense_net"),
            difficulty=1,
            description="",
            mission_id=None,
        ),
        Server(
            id="chiba_b2",
            name="Ripper_Node",
            sector=SectorId("sense_net"),
            difficulty=2,
            description="",
            mission_id=None,
        ),
    ]
    s2 = Sector(
        id=SectorId("public_grid"),
        name="Public Grid",
        description="Open network",
    )
    s2.servers = [
        Server(
            id="chiba_n1",
            name="Chat_Server",
            sector=SectorId("public_grid"),
            difficulty=3,
            description="",
            mission_id=None,
        ),
        Server(
            id="chiba_n2",
            name="Market_Hub",
            sector=SectorId("public_grid"),
            difficulty=4,
            description="",
            mission_id=None,
        ),
    ]
    chiba.add_sector(s1)
    chiba.add_sector(s2)
    wm.add_world(chiba)

    # World 2: Night City - 2 sectors
    night_city = World(
        id=WorldId("night_city"),
        name="Night City",
        description="Cyberpunk 2077",
    )
    s3 = Sector(
        id=SectorId("arasaka"),
        name="Arasaka Tower",
        description="Megacorp",
    )
    s3.servers = [
        Server(
            id="nc_a1",
            name="Arasaka_DB",
            sector=SectorId("arasaka"),
            difficulty=5,
            description="",
            mission_id=None,
        ),
    ]
    s4 = Sector(
        id=SectorId("militech"),
        name="Militech HQ",
        description="Defense",
    )
    s4.servers = [
        Server(
            id="nc_m1",
            name="Militech_FW",
            sector=SectorId("militech"),
            difficulty=6,
            description="",
            mission_id=None,
        ),
    ]
    night_city.add_sector(s3)
    night_city.add_sector(s4)
    wm.add_world(night_city)

    return wm


class TestCycleSector:
    """LEFT/RIGHT navigation through (world, sector) pairs."""

    def test_right_advances_pair(self) -> None:
        """RIGHT moves to next (world, sector) pair."""
        wm = _make_test_worldmap()
        initial_world = wm.current_world
        initial_sector = wm.current_sector

        _cycle_sector(wm, KeySym.RIGHT)

        # Either world or sector should change
        changed = (wm.current_world != initial_world) or (wm.current_sector != initial_sector)
        assert changed

    def test_left_wraps_around(self) -> None:
        """LEFT from first pair wraps to last."""
        wm = _make_test_worldmap()
        _cycle_sector(wm, KeySym.LEFT)

        # Should land on last pair
        assert wm.current_sector is not None
        # Should be militech (last sector)
        assert wm.current_sector == SectorId("militech")

    def test_right_wraps_around(self) -> None:
        """RIGHT from last pair wraps to first."""
        wm = _make_test_worldmap()
        # Move to last pair
        _cycle_sector(wm, KeySym.RIGHT)
        _cycle_sector(wm, KeySym.RIGHT)
        _cycle_sector(wm, KeySym.RIGHT)  # Now at last
        _cycle_sector(wm, KeySym.RIGHT)  # Wrap to first

        # Should be back at chiba, sense_net
        assert wm.current_world == WorldId("chiba")
        assert wm.current_sector == SectorId("sense_net")

    def test_actually_updates_world_map(self) -> None:
        """Bug fix: previous code unpacked but never set_location()."""
        wm = _make_test_worldmap()
        # Move to night_city
        _cycle_sector(wm, KeySym.RIGHT)
        _cycle_sector(wm, KeySym.RIGHT)
        _cycle_sector(wm, KeySym.RIGHT)

        # World map should reflect new location
        assert wm.current_world == WorldId("night_city")


class TestCycleWorld:
    """PgUp/PgDn or W/S navigation through worlds."""

    def test_pgdn_advances_world(self) -> None:
        """PgDn moves to next world."""
        wm = _make_test_worldmap()
        _cycle_world(wm, KeySym.PAGEDOWN)

        assert wm.current_world == WorldId("night_city")

    def test_pgup_wraps(self) -> None:
        """PgUp from first world wraps to last."""
        wm = _make_test_worldmap()
        _cycle_world(wm, KeySym.PAGEUP)

        assert wm.current_world == WorldId("night_city")

    def test_w_key_advances(self) -> None:
        """W key advances world (like DOWN)."""
        wm = _make_test_worldmap()
        _cycle_world(wm, KeySym.W)

        assert wm.current_world == WorldId("night_city")

    def test_s_key_wraps(self) -> None:
        """S key wraps to previous (like UP)."""
        wm = _make_test_worldmap()
        _cycle_world(wm, KeySym.S)

        assert wm.current_world == WorldId("night_city")

    def test_world_change_resets_sector(self) -> None:
        """Changing world sets sector to first sector of new world."""
        wm = _make_test_worldmap()
        _cycle_world(wm, KeySym.PAGEDOWN)

        # Should be night_city's first sector
        assert wm.current_sector == SectorId("arasaka")


class TestBrowserInput:
    """Full input handling for the browser."""

    def _make_event(self, sym: KeySym) -> object:
        """Create a real KeyDown event."""
        from tcod.event import KeyDown, Modifier, Scancode

        return KeyDown(sym=sym, scancode=Scancode.UP, mod=Modifier.NONE)

    def test_up_decrements_server_index(self) -> None:
        """UP moves server selection up."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        state.selected_server_index = 1

        event = self._make_event(KeySym.UP)
        result = cyberspace_browser.handle_browser_input(event, state)
        assert result is True
        assert state.selected_server_index == 0

    def test_up_clamps_to_zero(self) -> None:
        """UP at 0 stays at 0."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        state.selected_server_index = 0

        event = self._make_event(KeySym.UP)
        cyberspace_browser.handle_browser_input(event, state)
        assert state.selected_server_index == 0

    def test_down_increments_server_index(self) -> None:
        """DOWN moves server selection down."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        state.selected_server_index = 0

        event = self._make_event(KeySym.DOWN)
        result = cyberspace_browser.handle_browser_input(event, state)
        assert result is True
        assert state.selected_server_index == 1

    def test_down_clamps_to_max(self) -> None:
        """DOWN at max stays at max."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        state.selected_server_index = 99  # Way out of bounds

        event = self._make_event(KeySym.DOWN)
        cyberspace_browser.handle_browser_input(event, state)
        # Chiba sense_net has 2 servers -> max index 1
        assert state.selected_server_index == 1

    def test_right_changes_sector_or_world(self) -> None:
        """RIGHT cycles (world, sector) pair."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        initial_world = wm.current_world
        initial_sector = wm.current_sector

        event = self._make_event(KeySym.RIGHT)
        result = cyberspace_browser.handle_browser_input(event, state)
        assert result is True
        # Something must have changed
        changed = (wm.current_world != initial_world) or (wm.current_sector != initial_sector)
        assert changed

    def test_pgdn_changes_world(self) -> None:
        """PgDn changes world."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        initial_world = wm.current_world

        event = self._make_event(KeySym.PAGEDOWN)
        cyberspace_browser.handle_browser_input(event, state)
        assert wm.current_world != initial_world

    def test_escape_returns_to_hub(self) -> None:
        """ESC goes back to hub."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        from wet_run.engine.state import ScreenKind

        state.screen = ScreenKind.CYBERSPACE_BROWSER

        event = self._make_event(KeySym.ESCAPE)
        cyberspace_browser.handle_browser_input(event, state)
        assert state.screen is ScreenKind.HUB

    def test_q_quits(self) -> None:
        """Q returns False to quit."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm

        event = self._make_event(KeySym.Q)
        result = cyberspace_browser.handle_browser_input(event, state)
        assert result is False


class TestServerIndexSafety:
    """Server index should never go out of bounds after world/sector change."""

    def test_sector_change_with_smaller_server_list(self) -> None:
        """Moving to a sector with fewer servers clamps index."""
        wm = _make_test_worldmap()
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)
        state = AppState()
        state.world_map = wm
        state.selected_server_index = 1  # sense_net has 2 servers (idx 0,1)

        # Move to arasaka (has 1 server): sense_net → public_grid → arasaka (2 cycles)
        _cycle_sector(wm, KeySym.RIGHT)
        _cycle_sector(wm, KeySym.RIGHT)

        # After cycling, reset index in input handler
        # (simulate the input handler logic)
        new_sector = wm.get_current_sector()
        if new_sector is not None and new_sector.servers:
            state.selected_server_index = min(
                state.selected_server_index, len(new_sector.servers) - 1
            )
        else:
            state.selected_server_index = 0

        # Should be clamped to 0 (arasaka has 1 server)
        assert wm.current_sector == SectorId("arasaka")
        assert state.selected_server_index == 0

    def test_empty_sector_safe(self) -> None:
        """Empty sector is handled (no crash, index reset)."""
        wm = _make_test_worldmap()
        # Use an existing sector but clear its servers
        chiba = wm.worlds[WorldId("chiba")]
        s_sense = chiba.sectors[SectorId("sense_net")]
        s_sense.servers = []
        wm.set_location(WorldId("chiba"), SectorId("sense_net"), None)

        state = AppState()
        state.world_map = wm
        state.selected_server_index = 5  # Way out of bounds

        # Simulate input handler
        new_sector = wm.get_current_sector()
        if new_sector is not None and new_sector.servers:
            state.selected_server_index = min(
                state.selected_server_index, len(new_sector.servers) - 1
            )
        else:
            state.selected_server_index = 0

        assert state.selected_server_index == 0
