"""Phase 4: Dungeon ECS system (ADR-0060).

A thin ECS-lite system over the dungeon.  Bridges the matrix graph
(``MatrixGraph``) and the world (``World``) by tracking room lifecycle
events: enter, exit, clear, defeat.

Public API:
    - ``DungeonSystem(world, mission_id)``: top-level system object.
    - ``system.populate(graph)``: add every node in the graph as a
      Room Entity in the world.
    - ``system.on_enter(room_id)``: mark visited, fire callbacks.
    - ``system.on_exit(room_id)``: mark exit (used for backtracking
      statistics, if the caller wishes to track that).
    - ``system.defeat(room_id)``: mark ICE/data cleared.
    - ``system.is_cleared(room_id)``: query helper.

Subscribers (set via ``on_enter`` / ``on_exit`` as callable hooks) are
called with the entity so the UI layer can pull glyph, label, faction
etc. without re-querying the world.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from typing_extensions import override

from ..matrix.graph import MatrixGraph
from .entity import Entity
from .room_entity import (
    COMP_CLEARED,
    COMP_VISITED,
    node_to_entity,
)
from .world import World


class DungeonSystem:
    """Tracks per-room state during a cyberspace run.

    Lifecycle:
        populate(graph)    # world gains one Entity per node
        on_enter(room_id)  # marks visited, calls hooks
        defeat(room_id)    # marks cleared (ICE / data collected)
        on_exit(room_id)   # marks exit (caller tracks backtrack count)
    """

    __slots__ = (
        "_world",
        "_mission_id",
        "_on_enter_hooks",
        "_on_exit_hooks",
        "_on_clear_hooks",
    )

    def __init__(self, world: World, mission_id: str = "") -> None:
        """Bind the system to a ``World`` and tag it with the current mission.

        ``mission_id`` is a label only — it surfaces in ``__repr__`` and
        through ``mission_id()`` so save logs and debug output can
        distinguish concurrent dungeons. Hook lists are empty by default;
        call ``add_*_hook`` to subscribe.
        """
        self._world: World = world
        self._mission_id: str = mission_id
        self._on_enter_hooks: list[Callable[[Entity], None]] = []
        self._on_exit_hooks: list[Callable[[Entity], None]] = []
        self._on_clear_hooks: list[Callable[[Entity], None]] = []

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def populate(self, graph: MatrixGraph) -> int:
        """Add every node in ``graph`` to the world as a Room Entity.

        Idempotent: calling twice replaces any prior dungeon entities
        in the world.  Returns the number of entities added.
        """
        self._clear_dungeon_entities()
        for node in graph.nodes:
            # x/y/w/h default to a unit cell; the renderer can
            # cross-reference this with the BSP leaves later.
            self._world.add(node_to_entity(node))
        return self._world.count("kind")

    def _clear_dungeon_entities(self) -> None:
        """Remove any dungeon-style entities (those with a ``kind`` component)
        from the world before repopulating."""
        for entity in list(self._world._entities.values()):
            if entity.has("kind"):
                self._world.remove(entity.id)

    # ------------------------------------------------------------------
    # Event hooks
    # ------------------------------------------------------------------

    def add_enter_hook(self, hook: Callable[[Entity], None]) -> None:
        """Register a callback fired on each room entry."""
        self._on_enter_hooks.append(hook)

    def add_exit_hook(self, hook: Callable[[Entity], None]) -> None:
        """Register a callback fired on each room exit."""
        self._on_exit_hooks.append(hook)

    def add_clear_hook(self, hook: Callable[[Entity], None]) -> None:
        """Register a callback fired when a room is cleared."""
        self._on_clear_hooks.append(hook)

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    def on_enter(self, room_id: str) -> Entity | None:
        """Mark room ``room_id`` as visited and fire enter hooks.

        Returns the entity (or None if the id is not in the world).
        Calling twice on the same room is a no-op for ``visited`` but
        still fires hooks (callers can debounce).
        """
        entity = self._world.get(room_id)
        if entity is None:
            return None
        entity.set(COMP_VISITED, True)
        for hook in self._on_enter_hooks:
            hook(entity)
        return entity

    def on_exit(self, room_id: str) -> Entity | None:
        """Mark room ``room_id`` as left and fire exit hooks."""
        entity = self._world.get(room_id)
        if entity is None:
            return None
        for hook in self._on_exit_hooks:
            hook(entity)
        return entity

    def defeat(self, room_id: str) -> Entity | None:
        """Mark an ICE / data room as cleared by combat / pickup.

        Idempotent.  Sets ``cleared`` to True and fires clear hooks.
        """
        entity = self._world.get(room_id)
        if entity is None:
            return None
        if entity.get(COMP_CLEARED):
            return entity  # already cleared, no double-event
        entity.set(COMP_CLEARED, True)
        for hook in self._on_clear_hooks:
            hook(entity)
        return entity

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def is_cleared(self, room_id: str) -> bool:
        """True if the room has been cleared (ICE defeated / data extracted)."""
        entity = self._world.get(room_id)
        if entity is None:
            return False
        return bool(entity.get(COMP_CLEARED))

    def is_visited(self, room_id: str) -> bool:
        """True if the room has been entered at least once."""
        entity = self._world.get(room_id)
        if entity is None:
            return False
        return bool(entity.get(COMP_VISITED))

    def cleared_rooms(self) -> list[str]:
        """Return ids of all rooms marked cleared."""
        return [e.id for e in self._world.find(COMP_CLEARED) if e.get(COMP_CLEARED)]

    def visited_rooms(self) -> list[str]:
        """Return ids of all rooms marked visited."""
        return [e.id for e in self._world.find(COMP_VISITED) if e.get(COMP_VISITED)]

    def mission_id(self) -> str:
        """Return the mission label passed to ``__init__`` (empty string if none)."""
        return self._mission_id

    @override
    def __repr__(self) -> str:
        """Compact debug summary: mission tag, entity count, visited/cleared totals."""
        cleared = len(self.cleared_rooms())
        visited = len(self.visited_rooms())
        return (
            f"DungeonSystem(mission={self._mission_id!r}, "
            f"entities={self._world.count('kind')}, "
            f"visited={visited}, cleared={cleared})"
        )


def attach_dungeon_to_state(
    world: World,
    graph: MatrixGraph,
    mission_id: str,
) -> tuple[DungeonSystem, Any]:
    """Convenience helper: build a system and populate it.

    Returns the system plus a small bundle so the UI layer can read
    counts from a single object.
    """
    system = DungeonSystem(world, mission_id=mission_id)
    count = system.populate(graph)
    return system, {"room_count": count}


__all__ = [
    "DungeonSystem",
    "attach_dungeon_to_state",
]
