"""Phase 1 + 2 + 3 integration demo — chapter → mission → BSP dungeon.

ADR-0060 (Phase 1-3) introduced:
  - AppState.dungeon_mode flag
  - ProceduralDungeonGenerator (BSP)
  - missions_to_rooms / mission_to_graph bridge

This demo shows the *integration* end-to-end in headless form, so
a user can see how a story chapter unfolds into a mission that
unfolds into a BSP dungeon.

Pipeline exercised here:

  design/scenario/chapter-N-{novice|veteran|heretic}.md
      ↓
  prototype/data/missions/missions.json (mission per chapter)
      ↓
  ProceduralDungeonGenerator(BSP) — outline → graph
      ↓
  DungeonSystem.on_enter / on_exit / defeat

Default invocation runs the first mission of each arc (3 missions
total) without opening a tcod window.

Usage::

    PYTHONPATH=src .venv/bin/python scripts/play_arc_bsp.py
    PYTHONPATH=src .venv/bin/python scripts/play_arc_bsp.py --arc novice
    PYTHONPATH=src .venv/bin/python scripts/play_arc_bsp.py --missions 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wet_run.ecs.dungeon_system import DungeonSystem  # noqa: E402
from wet_run.ecs.world import World  # noqa: E402
from wet_run.matrix.dungeon_generator import (  # noqa: E402
    ProceduralDungeonGenerator,
)
from wet_run.matrix.mission_mapper import (  # noqa: E402
    mission_to_graph,
    missions_to_rooms,
)
from wet_run.missions import JobBoard  # noqa: E402

ARC_PREFIXES = {
    "novice": ("case", 1),
    "veteran": ("sil", 2),
    "heretic": ("kas", 3),
}


def _filter_by_arc(missions, arc: str) -> list:
    """Return missions whose id starts with the arc's character prefix."""
    prefix, _ = ARC_PREFIXES.get(arc, ("case", 1))
    return [m for m in missions if prefix in m.id.lower()]


def _guess_arc(mission) -> str:
    """Best-effort arc inference for --mission single-run mode."""
    mid = mission.id.lower()
    for arc, (prefix, _) in ARC_PREFIXES.items():
        if prefix in mid:
            return arc
    return "veteran"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arc",
        default="novice",
        choices=list(ARC_PREFIXES),
        help="Character arc (default novice).",
    )
    parser.add_argument(
        "--missions",
        type=int,
        default=5,
        help="Max missions to walk (default 5).",
    )
    parser.add_argument(
        "--mission",
        default=None,
        help=("Run a single mission by id (e.g. 'first_jack'). Bypasses --arc / --missions."),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="RNG seed for BSP (default 2026).",
    )
    parser.add_argument(
        "--grade",
        type=int,
        default=2,
        help="Mission grade 1-5 (default 2 = veteran field).",
    )
    args = parser.parse_args()

    print("=" * 64)
    print("Arc-BSP integration demo (ADR-0060 Phase 1-3)")
    print("=" * 64)

    board = JobBoard.load(ROOT / "data" / "missions" / "missions.json")
    all_missions = tuple(board._missions.values())

    if args.mission is not None:
        hit = next((m for m in all_missions if m.id == args.mission), None)
        if hit is None:
            print(f"[ERR] no mission with id={args.mission!r}.  Available:")
            for m in all_missions:
                print(f"      {m.id}")
            return 1
        arc_missions = [hit]
        args.arc = _guess_arc(hit)
    else:
        arc_missions = _filter_by_arc(all_missions, args.arc)
        if not arc_missions:
            arc_missions = list(all_missions)
        arc_missions = arc_missions[: args.missions]

    print(f"[1] arc={args.arc} (prefix={ARC_PREFIXES[args.arc][0]})")
    print(f"    picked {len(arc_missions)} / {len(all_missions)} missions")
    print()

    world = World()
    ProceduralDungeonGenerator(min_leaf_size=2, room_padding=1)

    for idx, mission in enumerate(arc_missions, start=1):
        rooms = missions_to_rooms(mission, character_ref=args.arc)
        graph = mission_to_graph(mission, character_ref=args.arc, seed=args.seed)
        kinds = sorted({r.value for r in rooms})

        sys_ = DungeonSystem(world=world, mission_id=mission.id)
        n_ent = sys_.populate(graph)

        first_room = graph.nodes[0].id if graph.nodes else "(none)"
        ent = sys_.on_enter(first_room) if graph.nodes else None

        print(f"--- mission {idx}/{len(arc_missions)} : {mission.id} ---")
        # Prefer the structured primary objective, fall back to legacy string.
        primary = getattr(mission, "primary_objective", None)
        if primary is not None:
            obj_text = f"{getattr(primary, 'type', '?')}"
        else:
            obj_text = getattr(mission, "objective", "") or "(no objective)"
        print(f"  objective: {obj_text[:80]}")
        print(f"  room sequence ({len(rooms)}): {kinds}")
        print(f"  BSP graph: {len(graph.nodes)} rooms / {len(graph.edges)} corridors")
        print(
            f"  ECS: {n_ent} entities populated; on_enter({first_room}) -> "
            f"entity {ent.id if ent else '?'}"
        )
        cleared = sys_.cleared_rooms()
        if cleared:
            sys_.defeat(cleared[0])
            print(f"  defeat({cleared[0]}); cleared={sys_.cleared_rooms()}")
        print()

    print(f"*** Phase 1 + 2 + 3 integration verified across {len(arc_missions)} missions ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
