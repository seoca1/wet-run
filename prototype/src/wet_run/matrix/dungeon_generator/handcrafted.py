"""Hand-crafted Phase 1 dungeon layout (ADR-0060 Phase 1).

This module preserves the original 7x5 layout generator for backward
compatibility with tests that assert on the exact nodes/edges of that
layout. The recommended generator is now
:class:`wet_run.matrix.dungeon_generator.procedural.ProceduralDungeonGenerator`.

Originally part of ``matrix/dungeon_generator.py`` (862 LOC); split into
this sub-module per ADR-0110 (≤ 500 LOC per module).
"""

from __future__ import annotations

from ..graph import Edge, MatrixGraph
from ..node import Faction, IceKind, Node, NodeKind, ZoneDepth
from .models import Room, RoomType


class DungeonGenerator:
    """Generates a 2D grid-based dungeon with rooms.

    Phase 1 hand-crafted 7x5 layout.  Kept for backwards compatibility
    with tests that assert on the exact nodes/edges of this layout.
    Phase 2 (``ProceduralDungeonGenerator``) is the recommended path.
    """

    __slots__ = ()

    def generate(self, seed: int, mission_grade: int = 1) -> MatrixGraph:
        """Generate a dungeon-style MatrixGraph.

        Grid: 5x4 (cols x rows) — 4-directional layout
        Every room (except EXT) has exits in all 4 cardinal directions.
        Path: Entry(R2,C0) → Dixie(R1,C2) → Data(R1,C3) →绕ICE→ Exit(R2,C4)
        """
        # Layout is deterministic; seed reserved for future random variations
        del seed

        # 5 columns x 4 rows grid (col=x, row=y)
        # Row 0 (top):    (0,0)R (1,0)R (2,0)ICE (3,0)R (4,0)R
        # Row 1 (mid):    (0,1)R (1,1)R (2,1)NPC (3,1)DATA (4,1)R
        # Row 2 (bot):    (0,2)ENT(1,2)R (2,2)R (3,2)R (4,2)EXT
        # Row 3 (btm2):   (0,3)R (1,3)R (2,3)R (3,3)R (4,3)R
        layout: list[tuple[str, int, int, RoomType, str]] = [
            # Row 0
            ("r00", 0, 0, RoomType.ROUTER, "Comms Relay"),
            ("r10", 1, 0, RoomType.ROUTER, "Router"),
            ("ice", 2, 0, RoomType.ICE, "ICE Barrier"),
            ("r30", 3, 0, RoomType.ROUTER, "Junction"),
            ("r40", 4, 0, RoomType.ROUTER, "Gateway"),
            # Row 1
            ("r01", 0, 1, RoomType.ROUTER, "Buffer"),
            ("r11", 1, 1, RoomType.ROUTER, "Hub"),
            ("npc_dixie", 2, 1, RoomType.NPC, "Dixie Flatline"),
            ("data", 3, 1, RoomType.DATA, "Data Vault"),
            ("r41", 4, 1, RoomType.ROUTER, "Node"),
            # Row 2
            ("entry", 0, 2, RoomType.ENTRY, "Entry"),
            ("r12", 1, 2, RoomType.ROUTER, "Corridor"),
            ("r22", 2, 2, RoomType.ROUTER, "Intersect"),
            ("r32", 3, 2, RoomType.ROUTER, "Access Point"),
            ("exit", 4, 2, RoomType.EXIT, "Exit"),
            # Row 3
            ("r03", 0, 3, RoomType.ROUTER, "Sublevel"),
            ("r13", 1, 3, RoomType.ROUTER, "Underpass"),
            ("r23", 2, 3, RoomType.ROUTER, "Deep Core"),
            ("r33", 3, 3, RoomType.ROUTER, "Archive"),
            ("r43", 4, 3, RoomType.ROUTER, "Terminal"),
        ]

        rooms: list[Room] = [
            Room(id=room_id, x=x, y=y, room_type=room_type, label=label)
            for room_id, x, y, room_type, label in layout
        ]

        # Define connections — every room connects to its 4 cardinal neighbors
        # (x,y) connects to (x±1,y) and (x,y±1) where those rooms exist
        def edge_pairs() -> list[Edge]:
            """Build bidirectional Edge list from cardinal-adjacent rooms."""
            pairs: list[tuple[str, str]] = []
            ids_at: dict[tuple[int, int], str] = {(r.x, r.y): r.id for r in rooms}
            for r in rooms:
                for dx, dy in [(1, 0), (0, 1)]:  # only forward pairs (reverse added below)
                    neighbor = ids_at.get((r.x + dx, r.y + dy))
                    if neighbor:
                        pairs.append((r.id, neighbor))
            # Add reverse edges (graph is undirected)
            result: list[Edge] = []
            for a, b in pairs:
                result.append(Edge(a, b))
                result.append(Edge(b, a))
            return result

        edges: list[Edge] = edge_pairs()

        # Convert rooms to Nodes
        faction = Faction.SENSE_NET
        nodes: list[Node] = []

        for room in rooms:
            if room.room_type is RoomType.ENTRY:
                node_kind = NodeKind.ENTRY
                ice_kind = IceKind.NONE
            elif room.room_type is RoomType.EXIT:
                node_kind = NodeKind.EXIT
                ice_kind = IceKind.NONE
            elif room.room_type is RoomType.DATA:
                node_kind = NodeKind.DATA
                ice_kind = IceKind.NONE
            elif room.room_type is RoomType.ICE:
                node_kind = NodeKind.ICE
                ice_kind = IceKind.STANDARD
            elif room.room_type is RoomType.NPC:
                node_kind = NodeKind.CONSTRUCT
                ice_kind = IceKind.NONE
            else:
                node_kind = NodeKind.ROUTER
                ice_kind = IceKind.NONE

            node = Node(
                id=room.id,
                kind=node_kind,
                label=room.label,
                zone=ZoneDepth.SURFACE,
                ice=ice_kind,
                faction=faction,
                x=room.x,
                y=room.y,
            )
            nodes.append(node)

        return MatrixGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
            entry_id="entry",
        )


__all__ = ["DungeonGenerator"]
