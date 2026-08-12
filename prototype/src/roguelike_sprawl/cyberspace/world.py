"""Hierarchical cyberspace model.

Architecture:
  World → Sectors → Servers → Nodes

A World contains multiple Sectors.
A Sector contains multiple Servers.
A Server contains multiple Nodes (the explorable graph).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from typing_extensions import override


class WorldId(StrEnum):
    """Major locations in the Sprawl."""

    CHIBA = "chiba"  # Chiba City (Neuromancer)
    NIGHT_CITY = "night_city"  # Night City
    FREESIDE = "freeside"  # Freeside (Count Zero)
    LO_TEK = "lo_tek"  # Lo Tek territory


class SectorId(StrEnum):
    """Major systems / ISPs / Corporations."""

    SENSE_NET = "sense_net"
    HOSAKA = "hosaka"
    MAAS = "maas"
    ARASAKA = "arasaka"
    MILITECH = "militech"
    PUBLIC_GRID = "public_grid"  # The public Matrix backbone


@dataclass
class Server:
    """A single host system that the player can jack into.

    Each server has:
    - id: unique identifier
    - name: display name
    - sector: which sector it belongs to
    - difficulty: PPL/ZDR rating
    - description: flavor text
    - mission_id: optional mission reference
    """

    id: str
    name: str
    sector: SectorId
    difficulty: int  # 1-10
    description: str
    mission_id: str | None = None  # If this server is a mission target

    @override
    def __repr__(self) -> str:
        return f"Server({self.id}: {self.name})"


@dataclass
class Sector:
    """A collection of related servers (corporation, ISP)."""

    id: SectorId
    name: str
    description: str
    servers: list[Server] = field(default_factory=list)

    def get_server(self, server_id: str) -> Server | None:
        """Get a server by ID."""
        for server in self.servers:
            if server.id == server_id:
                return server
        return None


@dataclass
class World:
    """A major geographic/digital region containing sectors.

    The top-level container for exploration. Multiple worlds exist
    (Chiba, Night City, etc.) and the player can travel between them.
    """

    id: WorldId
    name: str
    description: str
    sectors: dict[SectorId, Sector] = field(default_factory=dict)

    def add_sector(self, sector: Sector) -> None:
        """Add a sector to this world."""
        self.sectors[sector.id] = sector

    def get_sector(self, sector_id: SectorId) -> Sector | None:
        """Get a sector by ID."""
        return self.sectors.get(sector_id)

    def all_servers(self) -> list[Server]:
        """Get all servers across all sectors."""
        servers = []
        for sector in self.sectors.values():
            servers.extend(sector.servers)
        return servers


@dataclass
class WorldMap:
    """Collection of worlds the player can access.

    The global cyberspace: multiple worlds, each with multiple sectors,
    each with multiple servers.
    """

    worlds: dict[WorldId, World] = field(default_factory=dict)
    current_world: WorldId | None = None
    current_sector: SectorId | None = None
    current_server: str | None = None

    def add_world(self, world: World) -> None:
        """Add a world to the map."""
        self.worlds[world.id] = world
        if self.current_world is None:
            self.current_world = world.id

    def get_current_world(self) -> World | None:
        """Get the current world."""
        if self.current_world is None:
            return None
        return self.worlds.get(self.current_world)

    def get_current_sector(self) -> Sector | None:
        """Get the current sector."""
        world = self.get_current_world()
        if world is None or self.current_sector is None:
            return None
        return world.get_sector(self.current_sector)

    def get_current_server(self) -> Server | None:
        """Get the current server."""
        sector = self.get_current_sector()
        if sector is None or self.current_server is None:
            return None
        return sector.get_server(self.current_server)

    def set_location(
        self,
        world: WorldId,
        sector: SectorId,
        server: str | None = None,
    ) -> None:
        """Set the current location."""
        self.current_world = world
        self.current_sector = sector
        self.current_server = server
