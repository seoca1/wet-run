import type { Mission } from "./types.ts";

export function filterMissionsByUniverse(
  missions: ReadonlyArray<Mission>,
  universe: "sprawl" | "far-grid",
): ReadonlyArray<Mission> {
  return Object.freeze(
    missions.filter((m) => (m.source_universe ?? "sprawl") === universe),
  );
}
