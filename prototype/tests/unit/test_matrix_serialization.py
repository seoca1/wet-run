"""Tests for matrix graph serialization (to_dict / from_dict)."""

from __future__ import annotations

import pytest

from roguelike_sprawl.matrix.graph import Edge, MatrixGraph, compute_layout
from roguelike_sprawl.matrix.node import (
    AlarmLevel,
    Faction,
    IceKind,
    Node,
    NodeKind,
    ZoneDepth,
)


def _make_node(
    id: str,
    kind: NodeKind = NodeKind.DATA,
    label: str = "Test",
    zone: ZoneDepth = ZoneDepth.SURFACE,
    ice: IceKind = IceKind.NONE,
) -> Node:
    """Helper to create a test Node."""
    return Node(
        id=id,
        kind=kind,
        label=label,
        zone=zone,
        ice=ice,
        alarm=AlarmLevel.LOW,
        faction=Faction.NONE,
    )


def _make_test_graph() -> MatrixGraph:
    """Create a small test graph."""
    entry = _make_node("entry", kind=NodeKind.ENTRY, label="Entry")
    data1 = _make_node("data1", kind=NodeKind.DATA, label="Data 1")
    data2 = _make_node("data2", kind=NodeKind.DATA, label="Data 2")
    ice1 = _make_node("ice1", kind=NodeKind.ICE, label="ICE 1", ice=IceKind.STANDARD)
    exit_node = _make_node("exit", kind=NodeKind.EXIT, label="Exit")

    return MatrixGraph(
        nodes=(entry, data1, data2, ice1, exit_node),
        edges=(
            Edge("entry", "data1"),
            Edge("entry", "data2"),
            Edge("data1", "ice1"),
            Edge("data2", "ice1"),
            Edge("ice1", "exit"),
        ),
        entry_id="entry",
    )


class TestEdgeSerialization:
    """Edge.to_dict / from_dict roundtrip."""

    def test_roundtrip(self) -> None:
        e = Edge("a", "b")
        data = e.to_dict()
        assert data == {"src": "a", "dst": "b"}
        restored = Edge.from_dict(data)
        assert restored.src == "a"
        assert restored.dst == "b"


class TestMatrixSerialization:
    """MatrixGraph.to_dict / from_dict roundtrip."""

    def test_to_dict_has_all_keys(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        assert "nodes" in data
        assert "edges" in data
        assert "entry_id" in data
        assert data["entry_id"] == "entry"

    def test_nodes_serialized_as_list(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) == 5

    def test_edges_serialized_as_list(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        assert isinstance(data["edges"], list)
        assert len(data["edges"]) == 5

    def test_node_fields_preserved(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        # Find the ice1 node
        ice_data = next(n for n in data["nodes"] if n["id"] == "ice1")
        assert ice_data["kind"] == "ice"
        assert ice_data["ice"] == "standard"
        assert ice_data["label"] == "ICE 1"

    def test_roundtrip_preserves_nodes(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        assert len(restored.nodes) == 5
        ids = {n.id for n in restored.nodes}
        assert ids == {"entry", "data1", "data2", "ice1", "exit"}

    def test_roundtrip_preserves_edges(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        assert len(restored.edges) == 5
        edge_pairs = {(e.src, e.dst) for e in restored.edges}
        assert edge_pairs == {
            ("entry", "data1"),
            ("entry", "data2"),
            ("data1", "ice1"),
            ("data2", "ice1"),
            ("ice1", "exit"),
        }

    def test_roundtrip_preserves_node_attributes(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        ice = restored.get("ice1")
        assert ice is not None
        assert ice.kind is NodeKind.ICE
        assert ice.ice is IceKind.STANDARD
        assert ice.label == "ICE 1"
        assert ice.zone is ZoneDepth.SURFACE

    def test_roundtrip_preserves_entry_id(self) -> None:
        graph = _make_test_graph()
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        assert restored.entry_id == "entry"

    def test_roundtrip_preserves_lookup(self) -> None:
        """get() and is_connected() should still work after roundtrip."""
        graph = _make_test_graph()
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        # Test get
        entry = restored.get("entry")
        assert entry is not None
        # Test is_connected
        assert restored.is_connected("entry", "data1")
        assert restored.is_connected("ice1", "exit")
        assert not restored.is_connected("entry", "ice1")  # not directly

    def test_roundtrip_preserves_neighbors(self) -> None:
        """neighbors() should work after roundtrip."""
        graph = _make_test_graph()
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        # entry has 2 neighbors: data1, data2
        nbrs = restored.neighbors("entry")
        assert {n.id for n in nbrs} == {"data1", "data2"}

    def test_layout_after_roundtrip(self) -> None:
        """compute_layout should produce same positions after roundtrip."""
        graph = _make_test_graph()
        original_layout = compute_layout(graph)
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        restored_layout = compute_layout(restored)
        assert original_layout == restored_layout


class TestMatrixSerializationEdgeCases:
    """Edge cases in serialization."""

    def test_empty_graph(self) -> None:
        """Empty graph (only entry, no other nodes)."""
        graph = MatrixGraph(
            nodes=(_make_node("entry", kind=NodeKind.ENTRY, label="Entry"),),
            edges=(),
            entry_id="entry",
        )
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        assert len(restored.nodes) == 1
        assert len(restored.edges) == 0

    def test_graph_with_no_edges(self) -> None:
        graph = MatrixGraph(
            nodes=(
                _make_node("entry", kind=NodeKind.ENTRY, label="Entry"),
                _make_node("data1", kind=NodeKind.DATA, label="Data"),
            ),
            edges=(),
            entry_id="entry",
        )
        data = graph.to_dict()
        restored = MatrixGraph.from_dict(data)
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 0

    def test_corrupted_node_missing_id(self) -> None:
        data = {
            "nodes": [{"kind": "data", "label": "X", "zone": "surface"}],
            "edges": [],
            "entry_id": "",
        }
        with pytest.raises(ValueError, match="Invalid node"):
            MatrixGraph.from_dict(data)  # type: ignore[arg-type]

    def test_corrupted_node_invalid_kind(self) -> None:
        data = {
            "nodes": [{"id": "x", "kind": "INVALID", "label": "X", "zone": "surface"}],
            "edges": [],
            "entry_id": "x",
        }
        with pytest.raises(ValueError, match="Invalid node"):
            MatrixGraph.from_dict(data)  # type: ignore[arg-type]

    def test_invalid_entry_id(self) -> None:
        """Entry id not in nodes — should fail at construction."""
        data = {
            "nodes": [
                {"id": "a", "kind": "entry", "label": "A", "zone": "surface"},
            ],
            "edges": [],
            "entry_id": "nonexistent",
        }
        with pytest.raises(ValueError, match="entry_id"):
            MatrixGraph.from_dict(data)  # type: ignore[arg-type]

    def test_non_dict_node(self) -> None:
        data = {
            "nodes": ["not a dict"],
            "edges": [],
            "entry_id": "",
        }
        with pytest.raises(ValueError, match=r"(?i)invalid node data"):
            MatrixGraph.from_dict(data)  # type: ignore[arg-type]


class TestSaveManagerWithMatrix:
    """SaveManager roundtrip preserves matrix graph."""

    def test_save_and_restore_matrix(self, tmp_path) -> None:
        from roguelike_sprawl.engine import AppState, SaveManager
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission, Rewards
        from roguelike_sprawl.run import Stage, start_run

        # Set up state with matrix
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.MEET_NPC
        state.current_mission = Mission(
            id="first_jack",
            title="Test",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=42,
            zone=ZoneDepth.SURFACE,
            rewards=Rewards(credits=100, materials={}),
        )
        state.matrix = _make_test_graph()
        state.current_node_id = "data1"

        # Save
        manager = SaveManager(save_dir=tmp_path)
        manager.save(1, state)

        # Restore
        new_state = AppState()
        manager.restore_state(1, new_state)

        # Matrix should be preserved
        assert new_state.matrix is not None
        assert len(new_state.matrix.nodes) == 5
        assert new_state.current_node_id == "data1"
        # Test graph operations work
        assert new_state.matrix.is_connected("entry", "data1")

    def test_restore_screen_for_cyberspace_with_matrix(self, tmp_path) -> None:
        from roguelike_sprawl.engine import AppState, SaveManager, ScreenKind
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission, Rewards
        from roguelike_sprawl.run import Stage, start_run

        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.MEET_NPC
        state.current_mission = Mission(
            id="first_jack",
            title="Test",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=42,
            zone=ZoneDepth.SURFACE,
            rewards=Rewards(credits=0, materials={}),
        )
        state.matrix = _make_test_graph()
        state.current_node_id = "entry"

        manager = SaveManager(save_dir=tmp_path)
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        # With matrix restored, should go to MATRIX screen
        assert new_state.screen is ScreenKind.MATRIX

    def test_restore_without_matrix_goes_to_hub(self, tmp_path) -> None:
        from roguelike_sprawl.engine import AppState, SaveManager, ScreenKind
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission, Rewards
        from roguelike_sprawl.run import Stage, start_run

        # Save with matrix
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.MEET_NPC
        state.current_mission = Mission(
            id="first_jack",
            title="Test",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=42,
            zone=ZoneDepth.SURFACE,
            rewards=Rewards(credits=0, materials={}),
        )
        state.matrix = _make_test_graph()
        state.current_node_id = "entry"

        manager = SaveManager(save_dir=tmp_path)
        manager.save(1, state)

        # Manually break the matrix data in the save file
        import json

        path = tmp_path / "slot_1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        # Corrupt the matrix
        data["app_state"]["matrix"]["nodes"] = []
        path.write_text(json.dumps(data), encoding="utf-8")

        new_state = AppState()
        manager.restore_state(1, new_state)
        # Without valid matrix, should go to HUB
        # But the run_state is still MEET_NPC (cyberspace stage)
        # Per logic: HUB since matrix is None
        assert new_state.screen is ScreenKind.HUB

    def test_matrix_layouts_recomputed_on_restore(self, tmp_path) -> None:
        from roguelike_sprawl.engine import AppState, SaveManager
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission, Rewards
        from roguelike_sprawl.run import Stage, start_run

        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.MEET_NPC
        state.current_mission = Mission(
            id="first_jack",
            title="Test",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=42,
            zone=ZoneDepth.SURFACE,
            rewards=Rewards(credits=0, materials={}),
        )
        state.matrix = _make_test_graph()
        state.current_node_id = "entry"

        manager = SaveManager(save_dir=tmp_path)
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        # cyberspace_layouts should be recomputed
        assert new_state.cyberspace_layouts is not None
        assert "entry" in new_state.cyberspace_layouts
        assert "data1" in new_state.cyberspace_layouts
        # Layout positions should be tuples of (col, row)
        pos = new_state.cyberspace_layouts["entry"]
        assert isinstance(pos, tuple)
        assert len(pos) == 2
