"""Dungeon-style matrix generator (ADR-0060).

Generates a 2D grid-based dungeon with rooms connected by corridors.
Uses a BFS-based layout algorithm for clean cardinal direction movement.

Phase 2 adds :class:`ProceduralDungeonGenerator` which uses a
Binary Space Partitioning (BSP) algorithm to produce seed-determined
non-linear dungeon layouts.  Mission grade (1-5) and character reference
(novice/veteran/heretic) configure layout parameters.  Layouts are
reproducible: the same seed, grade, and character_ref always yield the
same matrix.

The original :class:`DungeonGenerator` (hand-crafted 7x5 layout) is kept
for backwards compatibility with existing tests.

Cohesion split (ADR-0110):
    models.py         — RoomType, Room, _BspRoom, _BspNode.
    handcrafted.py    — DungeonGenerator (Phase 1, 7x5 layout).
    procedural_bsp.py — BSP tree partitioning helpers.
    procedural_layout.py — spanning tree + room type assignment.
    procedural.py     — ProceduralDungeonGenerator (Phase 2 BSP algorithm).

Originally a single ``matrix/dungeon_generator.py`` (862 LOC); split into
this sub-package per ADR-0110 (≤ 500 LOC per module).
"""

from __future__ import annotations

from .handcrafted import DungeonGenerator
from .models import Room, RoomType, _BspNode, _BspRoom
from .procedural import GRID_BY_GRADE, ProceduralDungeonGenerator

__all__ = [
    # Models
    "Room",
    "RoomType",
    "_BspNode",
    "_BspRoom",
    # Phase 1
    "DungeonGenerator",
    # Phase 2
    "GRID_BY_GRADE",
    "ProceduralDungeonGenerator",
]
