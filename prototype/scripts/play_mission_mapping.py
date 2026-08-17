"""Phase 3 — Mission → Room mapping (matrix/mission_mapper).

The mission mapper takes the canonical ``data/missions/missions.json``
(29 missions across 15 chapters) and converts each mission into a
small dungeon graph:

- ``missions_to_rooms(missions)`` produces ONE aggregated graph where
  every mission's rooms become nodes connected by a hub corridor.
- ``mission_to_graph(mission)`` produces ONE graph for a single mission.

This demo loads all 29 missions, prints aggregate stats, and runs
``mission_to_graph`` on three representative missions across arcs
(novice / veteran / heretic) so the operator can verify the mapping.

Run::

    PYTHONPATH=src .venv/bin/python scripts/play_mission_mapping.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wet_run.matrix import mission_mapper  # noqa: E402
from wet_run.missions import JobBoard  # noqa: E402


def main() -> int:
    print("=" * 60)
    print("Phase 3 — Mission → Dungeon Room Mapping")
    print("=" * 60)

    board = JobBoard.load(ROOT / "data" / "missions" / "missions.json")
    missions = tuple(board._missions.values())
    print(f"[1] Loaded {len(missions)} missions from missions.json")

    rooms_aggregate = mission_mapper.missions_to_rooms(missions[0])
    print(f"[2] missions_to_rooms({missions[0].id}) : {len(rooms_aggregate)} RoomTypes")

    samples = []
    for arc in ("novice", "veteran", "heretic"):
        hit = next((m for m in missions if arc in m.id.lower()), None)
        if hit is not None:
            samples.append(hit)
    if not samples:
        samples = missions[:3]

    print()
    print(f"[3] Per-mission graphs (sample of {len(samples)}):")
    total_rooms = 0
    for m in samples:
        rooms = mission_mapper.missions_to_rooms(m)
        g = mission_mapper.mission_to_graph(m)
        kinds = sorted({r.value for r in rooms})
        print(
            f"     - {m.id:36s} "
            f"RoomTypes={len(rooms):2d} graph nodes={len(g.nodes):2d} "
            f"corridors={len(g.edges):2d} kinds={kinds}"
        )
        total_rooms += len(g.nodes)

    print()
    print(
        f"[4] aggregate over {len(missions)} missions → "
        f"{sum(len(mission_mapper.mission_to_graph(m).nodes) for m in missions)} "
        f"total graph nodes"
    )

    print()
    print("*** Phase 3 OK: mission→room mapping exercised for all 29 missions ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
