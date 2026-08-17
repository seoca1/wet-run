"""Tests for the procedural matrix generator (ADR-0005)."""

from __future__ import annotations

from wet_run.matrix.generator import MatrixGenerator
from wet_run.matrix.node import NodeKind


def test_generator_grade_1_small_graph() -> None:
    gen = MatrixGenerator()
    g = gen.generate(seed=42, mission_grade=1)
    # 5-7 nodes expected
    assert 5 <= len(g) <= 7
    # Exactly one entry
    entries = [n for n in g if n.kind is NodeKind.ENTRY]
    assert len(entries) == 1
    # At least one exit
    assert g.exits(), "graph must have at least one exit"
    # At least one ICE
    ice = [n for n in g if n.kind is NodeKind.ICE]
    assert len(ice) >= 1


def test_generator_deterministic_same_seed() -> None:
    gen = MatrixGenerator()
    g1 = gen.generate(seed=42, mission_grade=1)
    g2 = gen.generate(seed=42, mission_grade=1)
    assert len(g1) == len(g2)
    assert {n.id for n in g1} == {n.id for n in g2}
    assert {(e.src, e.dst) for e in g1.edges} == {(e.src, e.dst) for e in g2.edges}


def test_generator_different_seeds_yield_different_graphs() -> None:
    gen = MatrixGenerator()
    g1 = gen.generate(seed=42, mission_grade=1)
    g2 = gen.generate(seed=99, mission_grade=1)
    # At least one structural difference (node count or edges)
    same = len(g1) == len(g2) and {(e.src, e.dst) for e in g1.edges} == {
        (e.src, e.dst) for e in g2.edges
    }
    assert not same


def test_generator_entry_is_reachable() -> None:
    """BFS from entry should reach every node (graph is connected)."""
    gen = MatrixGenerator()
    g = gen.generate(seed=7, mission_grade=1)
    visited = {g.entry_id}
    frontier = [g.entry_id]
    while frontier:
        nid = frontier.pop()
        for nbr in g.neighbors(nid):
            if nbr.id not in visited:
                visited.add(nbr.id)
                frontier.append(nbr.id)
    assert visited == {n.id for n in g}


def test_generator_all_nodes_in_surface_zone() -> None:
    """Phase 5: grade-1 missions are Surface only."""
    from wet_run.matrix.node import ZoneDepth

    gen = MatrixGenerator()
    g = gen.generate(seed=1, mission_grade=1)
    for n in g:
        assert n.zone is ZoneDepth.SURFACE
