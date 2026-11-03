/** ADR-0251 slice B — sound ids that existed but were never dispatched.
 *
 * Each id is wired only to the real transition it names. `credit_spend` has
 * no in-game event (nothing lowers `player.credits`; `purchaseItem` has no
 * caller), so it stays unwired and must never be picked.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { pickEventSfx, pickTransitionSfx } from "../src/core/combat/combat_sfx";
import { SFX_IDS } from "../src/audio/manager";
import { makeInitialState } from "../src/core/state/state";
import type { GameState, Ice, Mission } from "../src/core/types";

const MISSION: Mission = {
  id: "sfx",
  title: "SFX",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 10, materials: {} },
};
const ICE: Ice = { id: "i", name: "ICE", hp: 100, armor: 0, tier: 1 };

function base(over: Partial<GameState> = {}): GameState {
  const s = makeInitialState(MISSION, ICE, []);
  return {
    ...s,
    iceRoster: [ICE],
    phase: "combat",
    runPhase: "combat",
    ...over,
  };
}
const withPlayer = (
  s: GameState,
  p: Partial<GameState["player"]>,
): GameState => ({
  ...s,
  player: { ...s.player, ...p },
});

describe("pickEventSfx", () => {
  it("a program joins the deck → equip (ADR-0261 growth)", () => {
    const prev = base();
    const card = {
      id: "payload",
      name: "Payload",
      tier: 3,
      cost: 4,
      effect: "attack",
      description: "d",
      aoe: false,
    };
    const next = base({
      inventory: { ...prev.inventory, programs: [card] },
    });
    expect(pickEventSfx(prev, next)).toContain(SFX_IDS.EQUIP);
  });

  it("does not sound equip when the deck did not grow", () => {
    const prev = base();
    expect(pickEventSfx(prev, prev)).not.toContain(SFX_IDS.EQUIP);
  });

  it("boss phase transition → phase_change", () => {
    const prev = base({ bossPhase: 1 });
    expect(pickEventSfx(prev, { ...prev, bossPhase: 2 })).toContain(
      SFX_IDS.PHASE_CHANGE,
    );
  });

  it("entering a boss fight → boss_intro (not phase_change)", () => {
    const prev = base({ runPhase: "matrix", phase: "approach", bossPhase: 0 });
    const next = base({ runPhase: "combat", phase: "approach", bossPhase: 1 });
    const ids = pickEventSfx(prev, next);
    expect(ids).toContain(SFX_IDS.BOSS_INTRO);
    expect(ids).not.toContain(SFX_IDS.PHASE_CHANGE);
  });

  it("entering an ordinary fight is not a boss intro", () => {
    const prev = base({ runPhase: "matrix", phase: "approach" });
    const next = base({ runPhase: "combat", phase: "approach", bossPhase: 0 });
    expect(pickEventSfx(prev, next)).not.toContain(SFX_IDS.BOSS_INTRO);
  });

  it("credits rise → credit_gain", () => {
    const prev = base();
    expect(pickEventSfx(prev, withPlayer(prev, { credits: 60 }))).toContain(
      SFX_IDS.CREDIT_GAIN,
    );
  });

  it("materials rise → loot_drop", () => {
    const prev = base();
    const next: GameState = {
      ...prev,
      inventory: { ...prev.inventory, materials: { ice_shard: 1 } },
    };
    expect(pickEventSfx(prev, next)).toContain(SFX_IDS.LOOT_DROP);
  });

  it("player HP rises → heal", () => {
    const prev = withPlayer(base({ runPhase: "loot" }), { hp: 40 });
    expect(pickEventSfx(prev, withPlayer(prev, { hp: 55 }))).toContain(
      SFX_IDS.HEAL,
    );
  });

  it("a restart from a flatline is not a heal", () => {
    const prev = withPlayer(base({ runPhase: "dead", phase: "defeat" }), {
      hp: 0,
    });
    expect(pickEventSfx(prev, withPlayer(prev, { hp: 100 }))).not.toContain(
      SFX_IDS.HEAL,
    );
  });

  it("player HP reaches 0 → death; jacking out is not a death", () => {
    const prev = withPlayer(base(), { hp: 12 });
    expect(
      pickEventSfx(
        prev,
        withPlayer({ ...prev, phase: "defeat", runPhase: "dead" }, { hp: 0 }),
      ),
    ).toContain(SFX_IDS.DEATH);
    expect(
      pickEventSfx(prev, { ...prev, phase: "defeat", runPhase: "dead" }),
    ).not.toContain(SFX_IDS.DEATH);
  });

  it("nothing changed → silence; credit_spend is never picked", () => {
    const prev = base();
    expect(pickEventSfx(prev, prev)).toEqual([]);
    const spent = withPlayer(prev, { credits: -5 });
    expect(pickEventSfx(prev, spent)).not.toContain(SFX_IDS.CREDIT_SPEND);
  });

  it("pickTransitionSfx = combat layers + event ids, without duplicates", () => {
    const prev = withPlayer(base(), { hp: 12 });
    const next = withPlayer(prev, { hp: 0 });
    const ids = pickTransitionSfx(prev, next);
    expect(ids).toContain(SFX_IDS.DAMAGE);
    expect(ids).toContain(SFX_IDS.DEATH);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("dispatch sites", () => {
  const mainSource = readFileSync(
    fileURLToPath(new URL("../src/main.ts", import.meta.url)),
    "utf8",
  ).replace(/\s+/g, "");

  it("both the key handler and the touch program buttons use the full picker", () => {
    const uses =
      mainSource.match(/pickTransitionSfx\(previous,nextState\)/g) ?? [];
    expect(uses).toHaveLength(2);
    expect(mainSource).not.toContain("pickCombatSfxLayers(previous,nextState)");
  });

  it("the dead boss-phase VICTORY branch is gone (phase_change replaces it)", () => {
    expect(mainSource).not.toContain(
      "previous.bossPhase>0&&this.state.bossPhase>previous.bossPhase){manager.playSfx(audio.SFX_IDS.VICTORY)",
    );
  });
});
