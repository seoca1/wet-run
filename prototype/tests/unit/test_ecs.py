"""Tests for the ECS-lite (Entity, World)."""

from __future__ import annotations

import pytest

from wet_run.ecs.entity import Entity
from wet_run.ecs.world import World


def test_entity_creation() -> None:
    e = Entity("e1", hp=10, name="test")
    assert e.id == "e1"
    assert e.get("hp") == 10
    assert e.get("name") == "test"
    assert e.has("hp", "name")
    assert not e.has("hp", "missing")


def test_entity_get_set_remove() -> None:
    e = Entity("e1")
    assert e.get("hp") is None
    e.set("hp", 50)
    assert e.get("hp") == 50
    e.set("hp", 100)
    assert e.get("hp") == 100
    assert e.remove("hp") == 100
    assert e.get("hp") is None


def test_entity_equality() -> None:
    a = Entity("e1", hp=10)
    b = Entity("e1", hp=20)  # same id, different components
    c = Entity("e2", hp=10)
    assert a == b  # same id
    assert a != c
    assert hash(a) == hash(b)


def test_entity_repr() -> None:
    e = Entity("e1", hp=10, name="test")
    r = repr(e)
    assert "Entity" in r
    assert "e1" in r


def test_world_add_remove() -> None:
    w = World()
    e1 = Entity("e1", hp=10)
    e2 = Entity("e2", hp=20)
    w.add(e1)
    w.add(e2)
    assert len(w) == 2
    assert w.get("e1") == e1
    assert w.remove("e1") == e1
    assert w.get("e1") is None
    assert len(w) == 1


def test_world_add_duplicate_raises() -> None:
    w = World()
    w.add(Entity("e1", hp=10))
    with pytest.raises(ValueError, match="already exists"):
        w.add(Entity("e1", hp=20))


def test_world_find_by_components() -> None:
    w = World()
    w.add(Entity("e1", hp=10, pos=(0, 0)))
    w.add(Entity("e2", hp=20, pos=(1, 0)))
    w.add(Entity("e3", hp=30))
    w.add(Entity("e4", pos=(2, 0)))

    hp_results = list(w.find("hp"))
    assert {e.id for e in hp_results} == {"e1", "e2", "e3"}

    pos_results = list(w.find("pos"))
    assert {e.id for e in pos_results} == {"e1", "e2", "e4"}

    both_results = list(w.find("hp", "pos"))
    assert {e.id for e in both_results} == {"e1", "e2"}

    assert w.count("hp") == 3
    assert w.count("pos") == 3
    assert w.count("hp", "pos") == 2


def test_world_iteration_and_contains() -> None:
    w = World()
    w.add(Entity("e1"))
    w.add(Entity("e2"))
    assert "e1" in w
    assert "missing" not in w
    ids = {e.id for e in w}
    assert ids == {"e1", "e2"}


def test_world_clear() -> None:
    w = World()
    w.add(Entity("e1"))
    w.add(Entity("e2"))
    w.clear()
    assert len(w) == 0
