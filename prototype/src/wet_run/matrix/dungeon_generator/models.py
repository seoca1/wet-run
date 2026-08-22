"""Shared data shapes for the dungeon generator package (ADR-0110 split).

Public dataclasses used by both the hand-crafted layout and the
procedural BSP generator:

    RoomType  — visual type of room (StrEnum, 8 values).
    Room      — a placed room in the dungeon grid.
    _BspRoom  — internal room placement record for BSP leaves.
    _BspNode  — recursive BSP partition node with identity-based
                hash/equality (slots=True disables the synthesized
                versions).

Originally part of ``matrix/dungeon_generator.py`` (862 LOC); split into
this sub-module per ADR-0110 (≤ 500 LOC per module).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from typing_extensions import override


class RoomType(StrEnum):
    """Visual type of room for rendering."""

    EMPTY = "empty"
    ENTRY = "entry"
    EXIT = "exit"
    DATA = "data"
    ICE = "ice"
    NPC = "npc"
    ROUTER = "router"
    CORE = "core"
    DEAD_END = "dead_end"


@dataclass
class Room:
    """A room in the dungeon grid."""

    id: str
    x: int
    y: int
    room_type: RoomType
    label: str
    description: str = ""


@dataclass(slots=True)
class _BspRoom:
    """Internal room placement for BSP partitioning."""

    x: int  # top-left x of room (inclusive)
    y: int  # top-left y of room (inclusive)
    w: int  # room width (cells)
    h: int  # room height (cells)
    room_id: str  # assigned when converted to Node


@dataclass(slots=True)
class _BspNode:
    """Recursive BSP partition."""

    x: int  # region x0
    y: int  # region y0
    w: int  # region width
    h: int  # region height
    left: _BspNode | None = None
    right: _BspNode | None = None
    room: _BspRoom | None = None  # leaf only

    # Identity-based hash/equality so instances are deduplicated by id()
    # when used as dict keys or sorted.  Required because @dataclass(slots=True)
    # disables synthesized __eq__/__hash__ on slotted classes.
    @override
    def __hash__(self) -> int:
        """Identity-based hash; required because ``slots=True`` disables the synthesized version."""
        return id(self)

    @override
    def __eq__(self, other: object) -> bool:
        """Identity-based equality; only equal to itself."""
        return self is other

    def __lt__(self, other: object) -> bool:
        """Identity-based ordering for use in ``heapq`` / sorted containers."""
        return id(self) < id(other) if isinstance(other, _BspNode) else NotImplemented

    @property
    def is_leaf(self) -> bool:
        """True if this node has no children (i.e. holds a room)."""
        return self.left is None and self.right is None

    def center(self) -> tuple[int, int]:
        """Center coordinate of the leaf's room (or region if no room)."""
        if self.room is not None:
            return (self.room.x + self.room.w // 2, self.room.y + self.room.h // 2)
        return (self.x + self.w // 2, self.y + self.h // 2)


__all__ = [
    "Room",
    "RoomType",
    "_BspNode",
    "_BspRoom",
]
