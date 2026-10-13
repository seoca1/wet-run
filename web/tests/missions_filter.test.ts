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

describe("missions_filter: ADR-0213 board isolation", () => {
  it("Sprawl board source excludes every far-grid mission", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const list = Object.values(data) as Mission[];
    const sprawl = filterMissionsByUniverse(list, "sprawl");
    const farGrid = filterMissionsByUniverse(list, "far-grid");
    expect(sprawl.length + farGrid.length).toBe(list.length);
    const sprawlIds = new Set(sprawl.map((m) => m.id));
    const overlap = farGrid.map((m) => m.id).filter((id) => sprawlIds.has(id));
    expect(overlap).toEqual([]);
    expect(farGrid.length).toBe(20);
  });
});
