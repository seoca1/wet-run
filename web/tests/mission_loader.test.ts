import { describe, it, expect } from "vitest";
import { loadMissions, getMissionById } from "../src/core/state.ts";

describe("mission loader functions", () => {
  it("loadMissions returns all missions", () => {
    const missions = loadMissions();
    expect(missions.length).toBe(33);
    expect(missions[0]).toHaveProperty("id");
    expect(missions[0]).toHaveProperty("title");
  });

  it("getMissionById returns correct mission", () => {
    const mission = getMissionById("first_jack");
    expect(mission).toBeDefined();
    expect(mission?.id).toBe("first_jack");
    expect(mission?.title).toBeTruthy();
  });

  it("getMissionById returns undefined for missing mission", () => {
    const mission = getMissionById("nonexistent_mission_xyz");
    expect(mission).toBeUndefined();
  });

  it("all loaded missions have required fields", () => {
    const missions = loadMissions();
    for (const mission of missions) {
      expect(mission.id).toBeTruthy();
      expect(mission.title).toBeTruthy();
      expect(mission.fixer).toBeTruthy();
      expect(mission.arc).toBeGreaterThanOrEqual(1);
      expect(mission.zone).toBeTruthy();
      expect(mission.rewards).toBeDefined();
      expect(mission.rewards.credits).toBeGreaterThanOrEqual(0);
    }
  });
});
