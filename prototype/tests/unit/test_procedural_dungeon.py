"""Tests for the procedural BSP dungeon generator (ADR-0060 Phase 2).

Covers:
    - Reproducibility: same (seed, grade, char, mission_id) => same graph
    - Variation: different seeds => different graphs
    - Grade scaling: grade 1-5 monotonically increase node count
    - Character variation: dead-end fraction grows novice -> heretic
    - Mission id variation: same seed but different mission_id => different graphs
    - ENTRY / EXIT are exactly one node each
    - Result is a connected spanning tree (every node reachable from entry)
    - Backwards compatibility: original DungeonGenerator returns same layout
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.matrix import (  # noqa: E402
    MatrixGraph,
    NodeKind,
)
from wet_run.matrix.dungeon_generator import (  # noqa: E402
    DungeonGenerator,
    ProceduralDungeonGenerator,
)

# ============================================================================
# Helpers
# ============================================================================


def _hash_graph(
    graph: MatrixGraph,
) -> tuple[tuple[tuple[str, str, str], ...], tuple[tuple[str, str], ...]]:
    """Stable hash of a graph (sorted nodes + sorted edges)."""
    node_sig = tuple(sorted((n.id, n.kind.value, n.ice.value) for n in graph.nodes))
    edge_sig = tuple(sorted((e.src, e.dst) for e in graph.edges))
    return (node_sig, edge_sig)


def _bfs_reachable(graph: MatrixGraph, start: str) -> set[str]:
    """Return set of node ids reachable from ``start`` via BFS."""
    visited: set[str] = set()
    queue: list[str] = [start]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        node = graph.get(current)
        if node is None:
            continue
        for neighbor in graph.neighbors(current):
            if neighbor.id not in visited:
                queue.append(neighbor.id)
    return visited


# ============================================================================
# Reproducibility
# ============================================================================


class TestReproducibility:
    def test_same_seed_same_graph(self) -> None:
        g = ProceduralDungeonGenerator()
        a = g.generate(seed=42, mission_grade=3, character_ref="novice", mission_id="m1")
        b = g.generate(seed=42, mission_grade=3, character_ref="novice", mission_id="m1")
        assert _hash_graph(a) == _hash_graph(b)

    def test_same_seed_different_character_ref_differs(self) -> None:
        g = ProceduralDungeonGenerator()
        a = g.generate(seed=42, mission_grade=3, character_ref="novice", mission_id="m1")
        b = g.generate(seed=42, mission_grade=3, character_ref="heretic", mission_id="m1")
        # Edges may differ because dead-end branches differ by char.
        assert (len(a.edges), len(a.nodes)) != (len(b.edges), len(b.nodes)) or _hash_graph(
            a
        ) != _hash_graph(b)

    def test_different_seed_different_graph(self) -> None:
        g = ProceduralDungeonGenerator()
        a = g.generate(seed=42, mission_grade=3, character_ref="novice")
        b = g.generate(seed=100, mission_grade=3, character_ref="novice")
        # Edges differ for at least one pair (BSP partition changes).
        a_edges = {(e.src, e.dst) for e in a.edges}
        b_edges = {(e.src, e.dst) for e in b.edges}
        assert a_edges != b_edges

    def test_different_mission_id_same_seed_differ(self) -> None:
        g = ProceduralDungeonGenerator()
        a = g.generate(seed=42, mission_grade=3, character_ref="novice", mission_id="mission_A")
        b = g.generate(seed=42, mission_grade=3, character_ref="novice", mission_id="mission_B")
        # Different mission_id seeds the RNG differently; edges should diverge.
        a_edges = {(e.src, e.dst) for e in a.edges}
        b_edges = {(e.src, e.dst) for e in b.edges}
        assert a_edges != b_edges


# ============================================================================
# Grade scaling
# ============================================================================


class TestGradeScaling:
    def test_grade_1_small(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=1, character_ref="novice")
        # Grade 1 = 7x5 grid → at least 2 leaves (entry + exit minimum).
        assert 2 <= len(graph.nodes) <= 12

    def test_grade_5_larger(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=5, character_ref="novice")
        # Grade 5 = 15x10 grid → many leaves.
        assert len(graph.nodes) >= 25

    def test_monotonic_node_count(self) -> None:
        """Higher grades yield >= nodes than lower grades (with same seed)."""
        g = ProceduralDungeonGenerator()
        counts = [
            len(g.generate(seed=42, mission_grade=grade, character_ref="novice").nodes)
            for grade in range(1, 6)
        ]
        for prev, nxt in zip(counts, counts[1:]):
            assert nxt >= prev, (
                f"grade {counts.index(prev) + 1} ({prev}) > grade {counts.index(nxt) + 1} ({nxt})"
            )


# ============================================================================
# Character variation (dead-end fraction)
# ============================================================================


class TestCharacterVariation:
    def test_novice_fewer_dead_ends_than_heretic(self) -> None:
        """Novice yields fewer edges than heretic for the same seed/grade."""
        g = ProceduralDungeonGenerator()
        novice = g.generate(seed=42, mission_grade=3, character_ref="novice")
        heretic = g.generate(seed=42, mission_grade=3, character_ref="heretic")
        # Dead-end fraction is higher for heretic, so edge count should be
        # greater-or-equal (allowing for randomness inside character).
        assert len(heretic.edges) >= len(novice.edges)

    def test_default_character_veteran(self) -> None:
        """Unknown character_ref falls back to veteran (no crash)."""
        g = ProceduralDungeonGenerator()
        # Should not raise even though 'unknown' is not in the lookup.
        graph = g.generate(seed=42, mission_grade=3, character_ref="unknown_char")
        assert len(graph.nodes) >= 2


# ============================================================================
# Structural invariants
# ============================================================================


class TestStructural:
    def test_exactly_one_entry_node(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        entry_count = sum(1 for n in graph.nodes if n.kind is NodeKind.ENTRY)
        assert entry_count == 1

    def test_exactly_one_exit_node(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        exit_count = sum(1 for n in graph.nodes if n.kind is NodeKind.EXIT)
        assert exit_count == 1

    def test_entry_id_is_set(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        assert graph.entry_id is not None
        assert graph.get(graph.entry_id) is not None
        assert graph.get(graph.entry_id).kind is NodeKind.ENTRY  # type: ignore[union-attr]

    def test_graph_is_connected(self) -> None:
        """Every node must be reachable from the entry via BFS."""
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        reachable = _bfs_reachable(graph, graph.entry_id)
        all_ids = {n.id for n in graph.nodes}
        assert reachable == all_ids, f"unreachable: {all_ids - reachable}"

    def test_no_self_loops(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        for edge in graph.edges:
            assert edge.src != edge.dst

    def test_no_duplicate_edges(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        edges_set = {(e.src, e.dst) for e in graph.edges}
        # Bidirectional edges deduplicated by build_bidirectional_edges.
        for src, dst in edges_set:
            assert (dst, src) not in edges_set or dst <= src

    def test_all_edge_endpoints_exist(self) -> None:
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran")
        node_ids = {n.id for n in graph.nodes}
        for edge in graph.edges:
            assert edge.src in node_ids, f"dangling src: {edge.src}"
            assert edge.dst in node_ids, f"dangling dst: {edge.dst}"


# ============================================================================
# Grade clamping and odd inputs
# ============================================================================


class TestEdgeCases:
    def test_grade_clamped_high(self) -> None:
        g = ProceduralDungeonGenerator()
        # Grade 7 should clamp to grade 5.
        clamped = g.generate(seed=42, mission_grade=7, character_ref="veteran")
        normal = g.generate(seed=42, mission_grade=5, character_ref="veteran")
        assert len(clamped.nodes) == len(normal.nodes)

    def test_grade_clamped_low(self) -> None:
        g = ProceduralDungeonGenerator()
        # Grade 0 should clamp to grade 1.
        clamped = g.generate(seed=42, mission_grade=0, character_ref="veteran")
        normal = g.generate(seed=42, mission_grade=1, character_ref="veteran")
        assert len(clamped.nodes) == len(normal.nodes)

    def test_unknown_mission_id_none_safe(self) -> None:
        """Passing mission_id=None should not raise."""
        g = ProceduralDungeonGenerator()
        graph = g.generate(seed=42, mission_grade=3, character_ref="veteran", mission_id=None)
        assert len(graph.nodes) >= 2


# ============================================================================
# Backwards compatibility — original DungeonGenerator
# ============================================================================


class TestOriginalDungeonGenerator:
    def test_returns_twenty_nodes(self) -> None:
        g = DungeonGenerator()
        graph = g.generate(seed=42, mission_grade=1)
        # 5x4 grid layout: 20 rooms (all 4-directional connectivity)
        assert len(graph.nodes) == 20

    def test_seed_ignored_deterministic(self) -> None:
        g = DungeonGenerator()
        a = g.generate(seed=1, mission_grade=1)
        b = g.generate(seed=42, mission_grade=1)
        assert _hash_graph(a) == _hash_graph(b)

    def test_entry_is_entry_node(self) -> None:
        g = DungeonGenerator()
        graph = g.generate(seed=42, mission_grade=1)
        entry = graph.get(graph.entry_id)
        assert entry is not None
        assert entry.kind is NodeKind.ENTRY


# ============================================================================
# Configuration
# ============================================================================


class TestGeneratorConfiguration:
    def test_custom_min_leaf_size(self) -> None:
        """Higher min_leaf_size yields fewer rooms (less splitting)."""
        coarse = ProceduralDungeonGenerator(min_leaf_size=4)
        fine = ProceduralDungeonGenerator(min_leaf_size=2)
        coarse_graph = coarse.generate(seed=42, mission_grade=3, character_ref="veteran")
        fine_graph = fine.generate(seed=42, mission_grade=3, character_ref="veteran")
        # Coarse should have <= leaves than fine.
        assert len(coarse_graph.nodes) <= len(fine_graph.nodes)
