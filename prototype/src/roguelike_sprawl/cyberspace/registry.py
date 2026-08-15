"""World registry: load and manage World/Sector/Server hierarchy."""

from __future__ import annotations

import json
from pathlib import Path

from .world import Sector, SectorId, Server, World, WorldId, WorldMap


class WorldRegistry:
    """Registry for loading and accessing the world hierarchy."""

    def __init__(self, world_map: WorldMap | None = None) -> None:
        """Initialize the registry; pass an existing ``WorldMap`` or start with an empty one."""
        self.world_map = world_map or WorldMap()

    @classmethod
    def load(cls, path: Path) -> WorldRegistry:
        """Load world hierarchy from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Worlds file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        world_map = WorldMap()
        registry = cls(world_map)

        for world_id, world_data in data.get("worlds", {}).items():
            world = World(
                id=WorldId(world_id),
                name=world_data["name"],
                description=world_data["description"],
            )

            for sector_id, sector_data in world_data.get("sectors", {}).items():
                sector = Sector(
                    id=SectorId(sector_id),
                    name=sector_data["name"],
                    description=sector_data["description"],
                )

                for server_data in sector_data.get("servers", []):
                    server = Server(
                        id=server_data["id"],
                        name=server_data["name"],
                        sector=SectorId(sector_id),
                        difficulty=server_data["difficulty"],
                        description=server_data["description"],
                        mission_id=server_data.get("mission_id"),
                    )
                    sector.servers.append(server)

                world.add_sector(sector)

            registry.world_map.add_world(world)

        return registry

    def get_world(self, world_id: WorldId) -> World | None:
        """Get a world by ID."""
        return self.world_map.worlds.get(world_id)

    def get_server_by_mission(self, mission_id: str) -> tuple[WorldId, SectorId, Server] | None:
        """Find a server that hosts a given mission."""
        for world in self.world_map.worlds.values():
            for sector in world.sectors.values():
                for server in sector.servers:
                    if server.mission_id == mission_id:
                        return (world.id, sector.id, server)
        return None
