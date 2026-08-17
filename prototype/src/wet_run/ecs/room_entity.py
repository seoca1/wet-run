"""Phase 4: Room → Entity conversion (ADR-0060).

Each room in the BSP-laid dungeon becomes an ECS-lite entity with
typed components.  This bridges the ``matrix`` graph (immutable
``MatrixGraph``) and the ECS ``World`` (mutable runtime state).

Components attached to each RoomEntity:
    - ``kind``       : ``NodeKind`` (ENTRY / EXIT / DATA / ICE / CONSTRUCT / ROUTER / CORE)
    - ``room_type``  : ``RoomType`` (visual rendering hint)
    - ``x, y``       : grid coordinates (top-left of the room)
    - ``w, h``       : room dimensions (corridor reserve)
    - ``label``      : human-readable label
    - ``cleared``    : bool, False initially (True after mission complete)
    - ``visited``    : bool, False initially (True after on_enter)
    - ``faction``    : ``Faction`` (faction bias)
    - ``ice_kind``   : ``IceKind`` (ICE tier if kind is ICE)
    - ``zone``       : ``ZoneDepth`` (matrix depth)

Separating ``kind`` (gameplay) from ``room_type`` (visual) keeps the
ECS layer independent of the rendering decision.  Most rooms carry
matching pairs (DATA/DATA, ICE/ICE) but the indirection lets us later
swap glyph without rewriting ECS logic.
"""

from __future__ import annotations

from ..matrix.dungeon_generator import RoomType
from ..matrix.node import Faction, IceKind, Node, NodeKind, ZoneDepth
from .entity import Entity

# Component name constants — single source of truth so the system code
# doesn't sprinkle string literals around.
COMP_KIND = "kind"
COMP_ROOM_TYPE = "room_type"
COMP_X = "x"
COMP_Y = "y"
COMP_W = "w"
COMP_H = "h"
COMP_LABEL = "label"
COMP_CLEARED = "cleared"
COMP_VISITED = "visited"
COMP_FACTION = "faction"
COMP_ICE_KIND = "ice_kind"
COMP_ZONE = "zone"


def node_to_entity(
    node: Node,
    *,
    x: int = 0,
    y: int = 0,
    w: int = 1,
    h: int = 1,
) -> Entity:
    """Convert a MatrixGraph ``Node`` to an ECS ``Entity``.

    Args:
        node: A node from the dungeon ``MatrixGraph``.
        x/y/w/h: Grid coordinates and dimensions of the underlying
            room.  Defaults to a 1x1 unit cell when not provided.

    Returns:
        An Entity with all room components attached, ready to be
        added to a ``World``.
    """
    # Map NodeKind → RoomType.  NPC / construct nodes are rendered
    # with the "?" glyph.
    kind_to_room: dict[NodeKind, RoomType] = {
        NodeKind.ENTRY: RoomType.ENTRY,
        NodeKind.EXIT: RoomType.EXIT,
        NodeKind.DATA: RoomType.DATA,
        NodeKind.ICE: RoomType.ICE,
        NodeKind.CONSTRUCT: RoomType.NPC,
        NodeKind.ROUTER: RoomType.ROUTER,
        NodeKind.SYSTEM: RoomType.ROUTER,
        NodeKind.CORE: RoomType.CORE,
    }
    return Entity(
        id=node.id,
        kind=node.kind,
        room_type=kind_to_room[node.kind],
        x=x,
        y=y,
        w=w,
        h=h,
        label=node.label,
        cleared=False,
        visited=False,
        faction=node.faction,
        ice_kind=node.ice,
        zone=node.zone,
    )


def room_to_entity(
    room_id: str,
    room_type: RoomType,
    node_kind: NodeKind,
    label: str,
    *,
    x: int = 0,
    y: int = 0,
    w: int = 1,
    h: int = 1,
    faction: Faction = Faction.NONE,
    ice_kind: IceKind = IceKind.NONE,
    zone: ZoneDepth = ZoneDepth.SURFACE,
) -> Entity:
    """Build an ``Entity`` directly from room components.

    Used when callers have already translated a mission outline into
    ``RoomType`` tokens and want to emit entities without going through
    the full BSP ``MatrixGraph``.
    """
    return Entity(
        id=room_id,
        kind=node_kind,
        room_type=room_type,
        x=x,
        y=y,
        w=w,
        h=h,
        label=label,
        cleared=False,
        visited=False,
        faction=faction,
        ice_kind=ice_kind,
        zone=zone,
    )


__all__ = [
    "COMP_CLEARED",
    "COMP_FACTION",
    "COMP_H",
    "COMP_ICE_KIND",
    "COMP_KIND",
    "COMP_LABEL",
    "COMP_ROOM_TYPE",
    "COMP_VISITED",
    "COMP_W",
    "COMP_X",
    "COMP_Y",
    "COMP_ZONE",
    "node_to_entity",
    "room_to_entity",
]
