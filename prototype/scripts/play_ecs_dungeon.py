"""Phase 4 — ECS Dungeon integration (ecs/dungeon_system).

Phase 4 wires the BSP dungeon (Phase 2) and mission mapper (Phase 3)
into an Entity-Component-System (``ecs/``).  Each room becomes an
``Entity`` with ``RoomTag`` + ``RoomState`` components, and the
``DungeonSystem`` exposes ``on_enter``, ``on_exit``, ``defeat`` hooks
for combat to publish into.

This demo:

1. Generates a BSP dungeon (same as Phase 2).
2. Wraps the graph in a ``DungeonSystem`` and populates ECS entities.
3. Walks the player's first 3 transitions: enter → enter → defeat.
4. Prints the system's cleared/visited lists so the operator can
   verify the ECS state machine.

Run::

    PYTHONPATH=src .venv/bin/python scripts/play_ecs_dungeon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wet_run.ecs.dungeon_system import DungeonSystem  # noqa: E402
from wet_run.ecs.world import World  # noqa: E402
from wet_run.matrix.dungeon_generator import (  # noqa: E402
    ProceduralDungeonGenerator,
)


def main() -> int:
    print("=" * 60)
    print("Phase 4 — ECS Dungeon Integration (DungeonSystem)")
    print("=" * 60)

    gen = ProceduralDungeonGenerator(min_leaf_size=2, room_padding=1)
    graph = gen.generate(seed=7, mission_grade=2, character_ref="veteran")

    world = World()
    sys_ = DungeonSystem(world=world, mission_id="play_ecs_demo")

    n = sys_.populate(graph)
    print(f"[1] populate()                 : {n} entities")
    print(
        f"[2] graph                       : {len(graph.nodes)} rooms, {len(graph.edges)} corridors"
    )

    first_three = [n.id for n in graph.nodes[:3]]
    print(f"[3] simulated walkthrough       : {first_three}")
    for rid in first_three[:2]:
        ent = sys_.on_enter(rid)
        print(f"     on_enter({rid}) → entity {ent.id if ent else '?'}")
    if first_three:
        ent = sys_.defeat(first_three[0])
        print(f"     defeat({first_three[0]})  → entity {ent.id if ent else '?'}")

    print()
    print(f"[4] cleared rooms               : {sys_.cleared_rooms()}")
    print(f"[5] visited rooms               : {sys_.visited_rooms()}")

    print()
    print("*** Phase 4 OK: DungeonSystem populated, walked, defeated ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
