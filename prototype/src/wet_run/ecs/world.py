"""ECS-lite world: collection of entities with query helpers."""

from __future__ import annotations

from collections.abc import Iterator

from typing_extensions import override

from .entity import Entity


class World:
    """Container for entities, supports queries by component names."""

    __slots__ = ("_entities",)

    def __init__(self) -> None:
        """Initialize an empty world with no entities."""
        self._entities: dict[str, Entity] = {}

    def add(self, entity: Entity) -> Entity:
        """Add an entity. Raises if id already exists."""
        if entity.id in self._entities:
            raise ValueError(f"Entity id already exists: {entity.id!r}")
        self._entities[entity.id] = entity
        return entity

    def remove(self, entity_id: str) -> Entity | None:
        """Remove and return an entity, or None if absent."""
        return self._entities.pop(entity_id, None)

    def get(self, entity_id: str) -> Entity | None:
        """Get an entity by id, or None if absent."""
        return self._entities.get(entity_id)

    def find(self, *component_names: str) -> Iterator[Entity]:
        """Iterate entities that have all of the given components."""
        if not component_names:
            yield from self._entities.values()
            return
        for entity in self._entities.values():
            if entity.has(*component_names):
                yield entity

    def count(self, *component_names: str) -> int:
        """Count entities that have all of the given components."""
        return sum(1 for _ in self.find(*component_names))

    def clear(self) -> None:
        """Remove all entities."""
        self._entities.clear()

    def __iter__(self) -> Iterator[Entity]:
        """Iterate all entities in insertion order."""
        return iter(self._entities.values())

    def __len__(self) -> int:
        """Return the number of entities in the world."""
        return len(self._entities)

    def __contains__(self, entity_id: object) -> bool:
        """Return True if an entity with the given id is in the world."""
        return entity_id in self._entities

    @override
    def __repr__(self) -> str:
        """Render a debug-friendly representation (entity count)."""
        return f"World({len(self._entities)} entities)"
