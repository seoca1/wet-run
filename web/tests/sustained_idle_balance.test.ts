import { expect, it } from "vitest";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import { runSuite } from "../scripts/balance_sim";
import missionsJson from "../src/data/missions.json";
import iceTypesJson from "../src/data/ice_types.json";
import programsJson from "../src/data/programs.json";

it("keeps the opening curve non-increasing when every turn includes sustained idle", () => {
  // Given: the canonical CLI population and seeds, not rounded display rates.
  const missions = loadMissionsCatalog(missionsJson);
  const iceCatalog = loadIceCatalog(iceTypesJson);
  const programs = loadProgramsCatalog(programsJson);
  const deck = Object.keys(programs)
    .sort()
    .slice(0, 5)
    .flatMap((id) => programs[id] ?? []);

  // When
  const rates = [1, 2, 3, 4, 5, 6].map((grade) => {
    const bucket = missions.filter((mission) => (mission.grade ?? 1) === grade);
    const wins = bucket.reduce(
      (sum, mission) =>
        sum +
        runSuite(mission, iceCatalog, deck, 100, 1, undefined, 10_000).wins,
      0,
    );
    return wins / (bucket.length * 100);
  });

  // Then
  for (let index = 1; index < rates.length; index++) {
    expect(rates[index], `g${index} >= g${index + 1}`).toBeLessThanOrEqual(
      rates[index - 1],
    );
  }
}, 60_000);
