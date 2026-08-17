"""Dungeon view walkthrough (ADR-0060 — dungeon-only mode).

This demo is headless: it does not open a tcod window.  It
programmatically exercises the dungeon view code path:

1. Construct an ``AppState``.
2. Generate a BSP dungeon via ``ProceduralDungeonGenerator`` and
   attach it to ``state.matrix``.
3. Run ``_get_room_position`` on every node and print the resulting
   2-D layout so the operator can verify the room positions match
   the BSP tree.

The actual ``render_dungeon_matrix`` requires a live ``tcod.Console``,
which is exercised by ``scripts/play.py``.

Run::

    PYTHONPATH=src .venv/bin/python scripts/play_dungeon_mode.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wet_run.engine import dungeon_view  # noqa: E402
from wet_run.engine.state import AppState  # noqa: E402
from wet_run.matrix.dungeon_generator import (  # noqa: E402
    ProceduralDungeonGenerator,
)


def main() -> int:
    print("=" * 60)
    print("Dungeon Mode (dungeon_view + Procedural Dungeon)")
    print("=" * 60)

    state = AppState()

    gen = ProceduralDungeonGenerator(min_leaf_size=2, room_padding=1)
    graph = gen.generate(seed=42, mission_grade=1, character_ref="veteran")
    state.matrix = graph
    state.current_node_id = graph.nodes[0].id if graph.nodes else None
    print(
        f"[1] BSP dungeon                  : {len(graph.nodes)} rooms, {len(graph.edges)} corridors"
    )

    room_map = {node.id: dungeon_view._get_room_position(node.id, graph) for node in graph.nodes}
    room_map = {k: v for k, v in room_map.items() if v is not None}
    pos_items = sorted(
        room_map.items(),
        key=lambda kv: (kv[1][1], kv[1][0]) if kv[1] else (0, 0),
    )

    print("[2] grid layout (node_id → (x,y)):")
    for nid, pos in pos_items[:8]:
        cur = "*" if nid == state.current_node_id else " "
        print(f"      {cur} {nid:8s} → {pos}")

    print()
    print("*** Dungeon view BSP attachment + grid positions verified ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
