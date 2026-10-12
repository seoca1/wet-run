import { describe, expect, it } from "vitest";
import type { Mission } from "../src/core/types.ts";
import { filterMissionsByUniverse } from "../src/core/missions_filter";

function makeMission(
  id: string,
  source_universe?: "sprawl" | "far-grid",
): Mission {
  return {
    id,
    title: id,
    fixer: "finn",
    arc: 1,
    zone: "surface",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 0, materials: {} },
    source_universe,
  };
}

describe("missions_filter: filterMissionsByUniverse", () => {
  it("returns only matching missions", () => {
    const missions = [
      makeMission("a", "sprawl"),
      makeMission("b", "far-grid"),
      makeMission("c", "far-grid"),
    ];
    const result = filterMissionsByUniverse(missions, "far-grid");
    expect(result.map((m) => m.id)).toEqual(["b", "c"]);
  });

  it("returns empty array when nothing matches", () => {
    const missions = [makeMission("a", "sprawl")];
    expect(filterMissionsByUniverse(missions, "far-grid")).toEqual([]);
  });

  it("treats missing source_universe as sprawl", () => {
    const missions = [makeMission("a"), makeMission("b", "far-grid")];
    expect(
      filterMissionsByUniverse(missions, "sprawl").map((m) => m.id),
    ).toEqual(["a"]);
    expect(
      filterMissionsByUniverse(missions, "far-grid").map((m) => m.id),
    ).toEqual(["b"]);
  });

  it("returns a frozen array", () => {
    const result = filterMissionsByUniverse([makeMission("a")], "sprawl");
    expect(Object.isFrozen(result)).toBe(true);
  });
});
