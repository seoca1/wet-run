"""ECS-lite entity: a dict of components."""

from __future__ import annotations

from typing import Any

from typing_extensions import override


class Entity:
    """An entity is identified by id and holds a dict of components.

    Components are arbitrary Python objects attached by name.
    This is the "ECS-lite" pattern (ADR-0004): no strict component
    classes, just typed dicts. Trades strict type safety for
    flexibility and Pythonic simplicity.
    """

    __slots__ = ("id", "components")

    def __init__(self, id: str, **components: Any) -> None:  # noqa: A002
        """Create an entity with an id and optional initial components."""
        self.id = id
        self.components = dict(components)

    def get(self, name: str) -> Any:
        """Get a component by name, or None if absent."""
        return self.components.get(name)

    def set(self, name: str, value: Any) -> None:
        """Set a component value (overwrites if exists)."""
        self.components[name] = value

    def has(self, *names: str) -> bool:
        """Return True if entity has all of the given component names."""
        return all(name in self.components for name in names)

    def remove(self, name: str) -> Any:
        """Remove and return a component, or None if absent."""
        return self.components.pop(name, None)

    @override
    def __repr__(self) -> str:
        """Render a debug-friendly representation (id + component type names)."""
        comps = ", ".join(f"{k}={type(v).__name__}" for k, v in self.components.items())
        return f"Entity(id={self.id!r}, {comps})"

    @override
    def __eq__(self, other: object) -> bool:
        """Two entities are equal iff their ids match (component-agnostic)."""
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    @override
    def __hash__(self) -> int:
        """Hash by id; matches equality semantics for set/dict usage."""
        return hash(self.id)
