"""Procedural BSP dungeon generator (ADR-0060 Phase 2).

:class:`ProceduralDungeonGenerator` produces a non-linear dungeon from a
seed, mission grade, and character reference. The same
``(seed, grade, character_ref)`` tuple always yields the same
:class:`MatrixGraph`, enabling deterministic runs and easy regression
testing.

Algorithm:
    1. Choose grid size based on ``mission_grade`` (1-5).
    2. Recursively partition the grid using BSP — each split is
       chosen randomly (horizontal/vertical) and the cut position
       is jittered within the region's interior.
    3. Each leaf places one room, sized relative to the region.
    4. Connect adjacent rooms with L-shaped corridors to form a
       spanning tree, then add extra branches (dead-ends) based on
       character reference.
    5. Promote one endpoint leaf to ENTRY and the leaf farthest
       from entry (within the spanning tree) to EXIT. Mark a few
       rooms as DATA / ICE / NPC based on character_ref.
    6. Return a MatrixGraph with all nodes and bidirectional edges.

Originally part of ``matrix/dungeon_generator.py`` (862 LOC); split into
this sub-module per ADR-0110 (≤ 500 LOC per module).
"""

from __future__ import annotations

import random

from ..graph import MatrixGraph
from ..node import Faction
from . import procedural_bsp, procedural_layout

# Grid size (cols x rows) for each mission grade (1-5).
# Smaller for novice, larger for higher grades.
GRID_BY_GRADE: dict[int, tuple[int, int]] = {
    1: (7, 5),  # 10-12 rooms
    2: (9, 6),  # 14-18 rooms
    3: (11, 7),  # 19-24 rooms
    4: (13, 8),  # 25-30 rooms
    5: (15, 10),  # 35-42 rooms
}


class ProceduralDungeonGenerator:
    """Procedural BSP dungeon generator (Phase 2).

    Produces a non-linear dungeon from a seed, mission grade, and
    character reference.  The same (seed, grade, character_ref) tuple
    always yields the same MatrixGraph, enabling deterministic runs and
    easy regression testing.
    """

    __slots__ = ("min_leaf_size", "room_padding")

    def __init__(
        self,
        min_leaf_size: int = 2,
        room_padding: int = 1,
    ) -> None:
        """Configure BSP leaf size and the room padding inside each region.

        ``min_leaf_size`` controls recursion depth: the smaller this
        value, the more (smaller) rooms.  ``room_padding`` reserves a
        border around each room for corridors to pass through.
        """
        self.min_leaf_size = min_leaf_size
        self.room_padding = room_padding

    def generate(
        self,
        seed: int,
        mission_grade: int = 1,
        character_ref: str = "veteran",
        mission_id: str | None = None,
    ) -> MatrixGraph:
        """Generate a procedural BSP dungeon.

        Args:
            seed: RNG seed; same value + grade + character_ref => same layout.
            mission_grade: 1-5, controls grid size (and thus room count).
            character_ref: ``"novice"`` | ``"veteran"`` | ``"heretic"`` —
                controls dead-end fraction and ICE / NPC density.
            mission_id: optional identifier used to vary the seed slightly
                so different missions with identical (seed, grade) aren't
                identical rooms.

        Returns:
            A ``MatrixGraph`` with ENTRY → ... → EXIT and bidirectional
            corridor edges between rooms.
        """
        # Per-mission RNG (so identical seed + grade yields reproducible
        # results, but mission_id introduces a stable offset).
        effective_seed = seed
        if mission_id is not None:
            effective_seed += hash(mission_id) % 7919
        rng = random.Random(effective_seed)

        grade = max(1, min(5, mission_grade))
        char = character_ref if character_ref in procedural_layout.DEADEND_BY_CHAR else "veteran"
        cols, rows = GRID_BY_GRADE[grade]

        # 1. BSP partition
        root = procedural_bsp.bsp_partition(rng, self.min_leaf_size, 0, 0, cols, rows)

        # 2. Place rooms inside leaf nodes
        procedural_bsp.place_rooms(rng, self.room_padding, root)

        # 3. Collect all rooms with their BSP centers for spanning tree
        leaves = procedural_bsp.collect_leaves(root)
        if len(leaves) < 2:
            # Degenerate (very small grade) — return empty adjacent pair
            return procedural_layout.build_graph([], [], entry_id="entry")

        # 4. Build spanning tree by joining adjacent leaves (L-corridors)
        edges_with_dirs = procedural_layout.connect_adjacent(rng, leaves)

        # 5. Add dead-end branches for character variation
        edges_with_dirs = procedural_layout.add_dead_ends(rng, leaves, edges_with_dirs, char)

        # 6. Assign room types (ENTRY/EXIT/DATA/ICE/NPC) and ids
        rooms = procedural_layout.assign_room_types(rng, leaves, char)

        # 7. Convert to nodes
        nodes = procedural_layout.rooms_to_nodes(rooms, char)

        # 8. Build bidirectional edges
        edges = procedural_layout.build_bidirectional_edges(edges_with_dirs, rooms)

        # 9. Find entry id (always the first room placed, top-left)
        # Leaves are visited in BSP pre-order so the first leaf is the
        # top-left region — perfect for the jack-in point.
        entry_id = leaves[0].room.room_id  # type: ignore[union-attr]

        return MatrixGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
            entry_id=entry_id,
        )

    def decorate_with_outline(
        self,
        graph: MatrixGraph,
        outline: list,  # type: ignore[type-arg]
        character_ref: str = "veteran",
    ) -> MatrixGraph:
        """Re-tag nodes to match a mission RoomType outline.

        Convenience wrapper around
        :func:`wet_run.matrix.dungeon_generator.procedural_layout.decorate_with_outline`.
        """
        return procedural_layout.decorate_with_outline(graph, outline, character_ref)

    @staticmethod
    def _faction_for(character_ref: str) -> Faction:
        """Map a character_ref to its default dungeon faction.

        Kept as a staticmethod on the generator so existing call sites
        and the docstring-coverage audit that introspects
        ``ProceduralDungeonGenerator._faction_for`` continue to work.
        Delegates to the layout helper.
        """
        return procedural_layout.faction_for(character_ref)


__all__ = ["GRID_BY_GRADE", "ProceduralDungeonGenerator"]
