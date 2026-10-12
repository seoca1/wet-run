import { describe, it, expect } from "vitest";
import { ProceduralDungeonGenerator } from "../src/core/dungeon_layout.ts";

/** ADR-0213 Pillar 2 (P2 The Matrix): dungeon-pool separation.
 *
 * Layout RNG = mulberry32(matrix_seed + mission-id hash)
 * (`applyMissionIdSeed` in dungeon_layout.ts), so every mission id owns an
 * independent topology stream. Far Grid missions can never share a dungeon
 * with Sprawl missions — including the pre-existing matrix_seed dupes
 * ({555, 7, 444}), which differ by mission id.
 */
describe("dungeon-pool separation (ADR-0213 P2)", () => {
  const gen = new ProceduralDungeonGenerator();

  function signature(missionId: string, seed: number): string {
    const g = gen.generate(seed, 2, "veteran", missionId);
    return g.rooms
      .map((r) => `${r.id}:${r.x},${r.y},${r.w},${r.h}`)
      .join("|");
  }

  it("same seed + different mission ids yield different dungeons", () => {
    const a = signature("ice_run", 7);
    const b = signature("sally_returns_arc3", 7);
    expect(a).not.toBe(b);
  });

  it("far-grid mission never shares topology with a sprawl mission", () => {
    const sprawl = signature("black_ice_dream", 202616);
    const farGrid = signature("mailmans_last_letter", 202616);
    expect(farGrid).not.toBe(sprawl);
  });

  it("same mission id + same seed is deterministic", () => {
    expect(signature("warren_meadow", 202613)).toBe(
      signature("warren_meadow", 202613),
    );
  });

  it("null mission id falls back to raw seed", () => {
    const g = gen.generate(42, 1, "veteran", null);
    expect(g.rooms.length).toBeGreaterThan(0);
  });
});
