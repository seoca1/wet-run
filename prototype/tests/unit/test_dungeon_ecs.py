"""Phase 4 tests: Room → Entity conversion + DungeonSystem lifecycle."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.ecs.dungeon_system import DungeonSystem, attach_dungeon_to_state
from wet_run.ecs.entity import Entity
from wet_run.ecs.room_entity import (
    COMP_CLEARED,
    COMP_H,
    COMP_ICE_KIND,
    COMP_KIND,
    COMP_LABEL,
    COMP_ROOM_TYPE,
    COMP_VISITED,
    COMP_W,
    COMP_X,
    COMP_Y,
    COMP_ZONE,
    node_to_entity,
    room_to_entity,
)
from wet_run.ecs.world import World
from wet_run.matrix import Edge, IceKind, MatrixGraph, Node, NodeKind, ZoneDepth
from wet_run.matrix.dungeon_generator import RoomType

# ============================================================================
# Helpers
# ============================================================================


def _make_graph() -> MatrixGraph:
    nodes = (
        Node(
            id="r0",
            label="Jack-in",
            kind=NodeKind.ENTRY,
            zone=ZoneDepth.SURFACE,
            ice=IceKind.NONE,
        ),
        Node(
            id="r1",
            label="Data Vault",
            kind=NodeKind.DATA,
            zone=ZoneDepth.SURFACE,
            ice=IceKind.NONE,
        ),
        Node(
            id="r2",
            label="ICE Patrol",
            kind=NodeKind.ICE,
            zone=ZoneDepth.MID,
            ice=IceKind.STANDARD,
        ),
        Node(
            id="r3",
            label="Exit Gate",
            kind=NodeKind.EXIT,
            zone=ZoneDepth.CORE,
            ice=IceKind.NONE,
        ),
    )
    edges = (
        Edge(src="r0", dst="r1"),
        Edge(src="r1", dst="r2"),
        Edge(src="r2", dst="r3"),
    )
    return MatrixGraph(nodes=nodes, edges=edges, entry_id="r0")


# ============================================================================
# node_to_entity / room_to_entity
# ============================================================================


class TestNodeToEntity:
    def test_creates_entity_with_components(self) -> None:
        node = Node(
            id="r1",
            label="Vault",
            kind=NodeKind.DATA,
            zone=ZoneDepth.SURFACE,
            ice=IceKind.NONE,
        )
        entity = node_to_entity(node, x=2, y=3, w=4, h=5)
        assert isinstance(entity, Entity)
        assert entity.id == "r1"
        assert entity.get(COMP_KIND) is NodeKind.DATA
        assert entity.get(COMP_LABEL) == "Vault"
        assert entity.get(COMP_W) == 4
        assert entity.get(COMP_H) == 5
        assert entity.get(COMP_X) == 2
        assert entity.get(COMP_Y) == 3
        assert entity.get(COMP_VISITED) is False
        assert entity.get(COMP_CLEARED) is False

    def test_kind_to_room_type_mapping(self) -> None:
        cases = (
            (NodeKind.ENTRY, RoomType.ENTRY),
            (NodeKind.EXIT, RoomType.EXIT),
            (NodeKind.DATA, RoomType.DATA),
            (NodeKind.ICE, RoomType.ICE),
            (NodeKind.CONSTRUCT, RoomType.NPC),
            (NodeKind.ROUTER, RoomType.ROUTER),
            (NodeKind.CORE, RoomType.CORE),
            (NodeKind.SYSTEM, RoomType.ROUTER),
        )
        for node_kind, expected_room in cases:
            ice = IceKind.STANDARD if node_kind is NodeKind.ICE else IceKind.NONE
            node = Node(
                id="x",
                label="x",
                kind=node_kind,
                zone=ZoneDepth.SURFACE,
                ice=ice,
            )
            entity = node_to_entity(node)
            assert entity.get(COMP_ROOM_TYPE) is expected_room, (
                f"{node_kind} should map to {expected_room}"
            )

    def test_ice_kind_propagates(self) -> None:
        node = Node(
            id="r1",
            label="Hostile",
            kind=NodeKind.ICE,
            zone=ZoneDepth.MID,
            ice=IceKind.BLACK,
        )
        entity = node_to_entity(node)
        assert entity.get(COMP_ICE_KIND) is IceKind.BLACK
        assert entity.get(COMP_ZONE) is ZoneDepth.MID


class TestRoomToEntity:
    def test_explicit_components(self) -> None:
        entity = room_to_entity(
            room_id="custom",
            room_type=RoomType.DATA,
            node_kind=NodeKind.DATA,
            label="Data Cache",
            x=1,
            y=2,
            w=3,
            h=4,
        )
        assert entity.id == "custom"
        assert entity.get(COMP_KIND) is NodeKind.DATA
        assert entity.get(COMP_ROOM_TYPE) is RoomType.DATA
        assert entity.get(COMP_LABEL) == "Data Cache"
        assert entity.get(COMP_X) == 1
        assert entity.get(COMP_VISITED) is False


# ============================================================================
# DungeonSystem populate
# ============================================================================


class TestPopulate:
    def test_populate_adds_all_nodes(self) -> None:
        world = World()
        system = DungeonSystem(world)
        graph = _make_graph()
        added = system.populate(graph)
        assert added == 4
        assert len(world) == 4

    def test_populate_clears_old_entities(self) -> None:
        world = World()
        system = DungeonSystem(world)
        graph = _make_graph()
        system.populate(graph)
        # Populate again with the same graph — should remain 4 entities.
        system.populate(graph)
        assert len(world) == 4

    def test_populate_preserves_non_dungeon_entities(self) -> None:
        """Entities without a ``kind`` component should be untouched."""
        world = World()
        # Pretend some other system already added a "player" entity.
        player = Entity("player", hp=100)
        world.add(player)

        system = DungeonSystem(world)
        system.populate(_make_graph())
        assert world.get("player") is not None
        assert world.count("kind") == 4


# ============================================================================
# DungeonSystem lifecycle
# ============================================================================


class TestLifecycle:
    def test_on_enter_marks_visited(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        assert system.is_visited("r0") is False
        system.on_enter("r0")
        assert system.is_visited("r0") is True

    def test_on_enter_returns_entity(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        entity = system.on_enter("r1")
        assert entity is not None
        assert entity.id == "r1"
        assert entity.get(COMP_VISITED) is True

    def test_on_enter_unknown_id_returns_none(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        assert system.on_enter("missing") is None

    def test_defeat_marks_cleared(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        system.on_enter("r2")
        system.defeat("r2")
        assert system.is_cleared("r2") is True

    def test_defeat_idempotent(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        system.defeat("r2")
        # Second call should not fire hooks again.
        counter = []
        system.add_clear_hook(lambda e: counter.append(e.id))
        system.defeat("r2")
        assert counter == []  # already cleared, hook skipped

    def test_cleared_rooms_returns_ids(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        system.defeat("r1")
        system.defeat("r2")
        cleared = set(system.cleared_rooms())
        assert cleared == {"r1", "r2"}

    def test_visited_rooms_returns_ids(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        system.on_enter("r0")
        system.on_enter("r1")
        visited = set(system.visited_rooms())
        assert visited == {"r0", "r1"}


# ============================================================================
# Hooks
# ============================================================================


class TestHooks:
    def test_enter_hook_fires(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        fired = []
        system.add_enter_hook(lambda e: fired.append(e.id))
        system.on_enter("r1")
        assert fired == ["r1"]

    def test_exit_hook_fires(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        fired = []
        system.add_exit_hook(lambda e: fired.append(e.id))
        system.on_exit("r1")
        assert fired == ["r1"]

    def test_clear_hook_fires_once(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        fired = []
        system.add_clear_hook(lambda e: fired.append(e.id))
        system.defeat("r1")
        system.defeat("r1")
        system.defeat("r2")
        assert fired == ["r1", "r2"]

    def test_multiple_enter_hooks_all_fire(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        a, b = [], []
        system.add_enter_hook(lambda e: a.append(e.id))
        system.add_enter_hook(lambda e: b.append(e.id))
        system.on_enter("r0")
        assert a == ["r0"]
        assert b == ["r0"]

    def test_hook_receives_entity_with_visited_true(self) -> None:
        world = World()
        system = DungeonSystem(world)
        system.populate(_make_graph())
        captured: list[bool] = []
        system.add_enter_hook(lambda e: captured.append(e.get(COMP_VISITED)))
        system.on_enter("r0")
        # Hook fires AFTER ``visited`` is set to True.
        assert captured == [True]


# ============================================================================
# attach_dungeon_to_state
# ============================================================================


class TestAttachHelper:
    def test_returns_system_and_metadata(self) -> None:
        world = World()
        graph = _make_graph()
        system, meta = attach_dungeon_to_state(world, graph, mission_id="m1")
        assert isinstance(system, DungeonSystem)
        assert meta["room_count"] == 4
        assert len(world) == 4
        assert system.mission_id() == "m1"


# ============================================================================
# Integration with mission_to_graph
# ============================================================================


class TestMissionToECSIntegration:
    """End-to-end: mission → outline → BSP → ECS."""

    def test_full_pipeline(self) -> None:
        from wet_run.matrix.mission_mapper import mission_to_graph
        from wet_run.missions.mission import Mission, Objective

        m = Mission(
            id="first_jack",
            title="First Jack-In",
            fixer="finn",
            arc=3,
            grade_min=3,
            grade_max=3,
            matrix_seed=42,
            zone=ZoneDepth.SURFACE,
            objective="Extract data from ICE vault.",
            primary_objective=Objective(type="extract_data", count=1),
        )
        graph = mission_to_graph(m, "veteran")
        world = World()
        system = DungeonSystem(world, mission_id=m.id)
        added = system.populate(graph)

        # Same number of nodes as graph.
        assert added == len(graph.nodes)
        assert world.count(COMP_KIND) == len(graph.nodes)
        # Entry and Exit are wired correctly.
        entry_entity = world.get(graph.entry_id)
        assert entry_entity is not None
        assert entry_entity.get(COMP_KIND) is NodeKind.ENTRY
        exit_count = sum(1 for e in world.find(COMP_KIND) if e.get(COMP_KIND) is NodeKind.EXIT)
        assert exit_count == 1

    def test_clear_data_room_via_system(self) -> None:
        from wet_run.matrix.mission_mapper import mission_to_graph
        from wet_run.missions.mission import Mission, Objective

        m = Mission(
            id="data_run",
            title="Data Run",
            fixer="finn",
            arc=3,
            grade_min=3,
            grade_max=3,
            matrix_seed=99,
            zone=ZoneDepth.SURFACE,
            objective="Extract data fragment.",
            primary_objective=Objective(type="extract_data", count=1),
        )
        graph = mission_to_graph(m, "veteran")
        world = World()
        system = DungeonSystem(world, mission_id=m.id)
        system.populate(graph)

        data_rooms = [e for e in world.find(COMP_KIND) if e.get(COMP_KIND) is NodeKind.DATA]
        assert len(data_rooms) >= 1

        # Clear the first data room.
        first_data = data_rooms[0]
        system.on_enter(first_data.id)
        system.defeat(first_data.id)
        assert system.is_cleared(first_data.id)
