"""Tests for cyberspace.world — World / Sector / Server / WorldMap dataclasses.

Coverage target for src/wet_run/cyberspace/world.py.
Pure data model — no tcd / event / threading dependencies.
"""

from __future__ import annotations

from wet_run.cyberspace.world import (
    Sector,
    SectorId,
    Server,
    World,
    WorldId,
    WorldMap,
)


def _server(
    server_id: str = "sv1", name: str = "Alpha", sector: SectorId = SectorId.HOSAKA
) -> Server:
    return Server(id=server_id, name=name, sector=sector, difficulty=5, description="")


def _sector(
    sector_id: SectorId = SectorId.HOSAKA, name: str = "Hosaka", servers: list[Server] | None = None
) -> Sector:
    return Sector(id=sector_id, name=name, description="", servers=servers or [])


def _world(
    world_id: WorldId = WorldId.CHIBA,
    name: str = "Chiba",
    sectors: dict[SectorId, Sector] | None = None,
) -> World:
    return World(id=world_id, name=name, description="", sectors=sectors or {})


# ----------------------------------------------------------------------------
# Sector
# ----------------------------------------------------------------------------


class TestSectorGetServer:
    def test_get_server_returns_matching(self):
        servers = [_server("sv1"), _server("sv2")]
        sector = _sector(servers=servers)
        result = sector.get_server("sv2")
        assert result is not None
        assert result.id == "sv2"

    def test_get_server_returns_none_for_missing(self):
        sector = _sector(servers=[_server("sv1")])
        assert sector.get_server("not-present") is None

    def test_empty_sector_get_server(self):
        sector = _sector(servers=[])
        assert sector.get_server("anything") is None


# ----------------------------------------------------------------------------
# World
# ----------------------------------------------------------------------------


class TestWorldAddSector:
    def test_add_sector_to_world(self):
        world = _world()
        sector = _sector(SectorId.HOSAKA, "Hosaka")
        world.add_sector(sector)
        assert SectorId.HOSAKA in world.sectors
        assert world.sectors[SectorId.HOSAKA] is sector

    def test_add_sector_overwrites(self):
        world = _world()
        sector1 = _sector(SectorId.HOSAKA, "First")
        sector2 = _sector(SectorId.HOSAKA, "Second")
        world.add_sector(sector1)
        world.add_sector(sector2)
        assert world.sectors[SectorId.HOSAKA].name == "Second"


class TestWorldGetSector:
    def test_get_existing_sector(self):
        sector = _sector(SectorId.HOSAKA, "Hosaka")
        world = _world(sectors={SectorId.HOSAKA: sector})
        result = world.get_sector(SectorId.HOSAKA)
        assert result is sector

    def test_get_missing_sector_returns_none(self):
        world = _world()
        assert world.get_sector(SectorId.MAAS) is None


class TestWorldAllServers:
    def test_empty_world_returns_empty(self):
        world = _world()
        assert world.all_servers() == []

    def test_single_sector(self):
        servers = [_server("sv1"), _server("sv2")]
        sector = _sector(servers=servers)
        world = _world(sectors={SectorId.HOSAKA: sector})
        result = world.all_servers()
        assert len(result) == 2
        assert {s.id for s in result} == {"sv1", "sv2"}

    def test_multiple_sectors(self):
        sector1 = _sector(SectorId.HOSAKA, "Hosaka", [_server("h1"), _server("h2")])
        sector2 = _sector(SectorId.MAAS, "Maas", [_server("m1")])
        world = _world(sectors={SectorId.HOSAKA: sector1, SectorId.MAAS: sector2})
        result = world.all_servers()
        assert len(result) == 3
        assert {s.id for s in result} == {"h1", "h2", "m1"}

    def test_empty_sector_ignored(self):
        sector1 = _sector(SectorId.HOSAKA, "Hosaka", [_server("h1")])
        sector2 = _sector(SectorId.MAAS, "Maas", [])
        world = _world(sectors={SectorId.HOSAKA: sector1, SectorId.MAAS: sector2})
        result = world.all_servers()
        assert len(result) == 1


# ----------------------------------------------------------------------------
# WorldMap
# ----------------------------------------------------------------------------


class TestWorldMapAddWorld:
    def test_add_world(self):
        wm = WorldMap()
        world = _world()
        wm.add_world(world)
        assert wm.worlds[WorldId.CHIBA] is world

    def test_first_add_sets_current(self):
        wm = WorldMap()
        world = _world()
        wm.add_world(world)
        assert wm.current_world == world.id

    def test_subsequent_add_doesnt_change_current(self):
        wm = WorldMap()
        first = _world(WorldId.CHIBA, "First")
        second = _world(WorldId.NIGHT_CITY, "Second")
        wm.add_world(first)
        wm.add_world(second)
        assert wm.current_world == WorldId.CHIBA


class TestWorldMapGetCurrent:
    def test_empty_returns_none_world(self):
        wm = WorldMap()
        assert wm.get_current_world() is None

    def test_returns_added_world(self):
        wm = WorldMap()
        world = _world()
        wm.add_world(world)
        assert wm.get_current_world() is world

    def test_get_current_sector_requires_sector_set(self):
        wm = WorldMap()
        world = _world()
        wm.add_world(world)
        assert wm.get_current_sector() is None

    def test_get_current_sector_with_sector(self):
        wm = WorldMap()
        sector = _sector(SectorId.HOSAKA, "Hosaka")
        world = _world(sectors={SectorId.HOSAKA: sector})
        wm.add_world(world)
        wm.current_sector = SectorId.HOSAKA
        result = wm.get_current_sector()
        assert result is sector

    def test_get_current_server_requires_server_set(self):
        wm = WorldMap()
        world = _world()
        wm.add_world(world)
        assert wm.get_current_server() is None

    def test_get_current_server_with_chain(self):
        wm = WorldMap()
        server = _server("sv1")
        sector = _sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _world(sectors={SectorId.HOSAKA: sector})
        wm.add_world(world)
        wm.current_sector = SectorId.HOSAKA
        wm.current_server = "sv1"
        result = wm.get_current_server()
        assert result is server

    def test_get_current_server_wrong_id(self):
        wm = WorldMap()
        server = _server("sv1")
        sector = _sector(SectorId.HOSAKA, "Hosaka", [server])
        world = _world(sectors={SectorId.HOSAKA: sector})
        wm.add_world(world)
        wm.current_sector = SectorId.HOSAKA
        wm.current_server = "missing"
        assert wm.get_current_server() is None


class TestWorldMapSetLocation:
    def test_set_location_to_world_sector(self):
        wm = WorldMap()
        sector = _sector(SectorId.HOSAKA, "Hosaka")
        world = _world(sectors={SectorId.HOSAKA: sector})
        wm.add_world(world)
        wm.set_location(WorldId.CHIBA, SectorId.HOSAKA)
        assert wm.current_world == WorldId.CHIBA
        assert wm.current_sector == SectorId.HOSAKA
        assert wm.current_server is None

    def test_set_location_with_server(self):
        wm = WorldMap()
        wm.set_location(WorldId.CHIBA, SectorId.HOSAKA, server="sv1")
        assert wm.current_server == "sv1"

    def test_set_location_overwrites_previous(self):
        wm = WorldMap()
        wm.set_location(WorldId.CHIBA, SectorId.HOSAKA, server="sv1")
        wm.set_location(WorldId.NIGHT_CITY, SectorId.MAAS, server="sv2")
        assert wm.current_world == WorldId.NIGHT_CITY
        assert wm.current_sector == SectorId.MAAS
        assert wm.current_server == "sv2"
