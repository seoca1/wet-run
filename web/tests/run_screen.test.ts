import { describe, expect, it } from "vitest";
import {
  composeCombatScreen,
  renderCombatScreen,
  renderRunScreen,
  runScreenLayout,
} from "../src/renderer/run_screen";
import { renderMatrix } from "../src/renderer/matrix";
import { renderEndingScreen, renderLootScreen } from "../src/renderer/ending";
import { offeredCardIds, rewardProgram } from "../src/core/state/card_reward";
import { formatRewardOption } from "../src/core/combat/program_affordance";
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import {
  LOOT_INTEL_SLOT,
  LOOT_REPAIR_SLOT,
  lootIntelPrice,
  lootRepairAmount,
} from "../src/core/state/loot_choice";
import { renderGrid } from "../src/renderer/combat_grid";
import { groupStatusByTarget } from "../src/renderer/status_hud";
import { buildHudLines } from "../src/core/state/state";
import { triggerCombatVfx } from "../src/renderer/combat_vfx";
import { PALETTE } from "../src/renderer/palette";
import { rowText, runState } from "./view_fixtures";

describe("run screen composition", () => {
  it("preserves matrix frame, node HUD and active ICE inputs", () => {
    const state = runState({
      runPhase: "matrix",
      currentNodeIndex: 1,
      visitedNodes: [0, 1],
      clearedEncounterNodes: [1],
    });
    if (!state.matrix) throw new Error("fixture requires a matrix");
    const view = renderRunScreen(state, 80, 50);
    expect(runScreenLayout(80, 50)).toEqual({ cols: 80, rows: 50 });
    expect(view?.grid.cells).toEqual(
      renderMatrix(
        state.matrix,
        1,
        [0, 1],
        80,
        50,
        state.iceRoster[0] ?? null,
        null,
        [1],
      ).cells,
    );
    expect(view?.hud).toEqual([
      "MATRIX",
      "",
      `Node 2/${state.matrix.nodes.length}`,
    ]);
  });

  it("does not draw a replacement when the matrix is absent", () => {
    const state = runState({ runPhase: "matrix", matrix: null });
    expect(renderRunScreen(state, 80, 50)).toBeNull();
  });

  it("preserves ending fallback and the literal question-mark HUD", () => {
    const state = runState({ runPhase: "ending", endingChoice: null });
    const view = renderRunScreen(state, 40, 30);
    // ADR-0269: the ending now carries the run's own numbers, so the expected
    // grid is the same renderer with the same summary -- this assertion is
    // about the null-choice fallback, not about the summary's shape.
    expect(view?.grid.cells).toEqual(
      renderEndingScreen(null, 40, 30, {
        mission: state.mission.title,
        hp: state.player.hp,
        maxHp: state.player.maxHp,
        credits: state.player.credits,
        turns: state.turnCount,
      }).cells,
    );
    expect(view?.hud).toEqual(["ENDING", "", "ARC ?"]);
  });

  it("reports the money the run earned, not the mission's base reward", () => {
    // ADR-0277: fight rewards land in `player.credits` — the number the HUD
    // shows and the save keeps. `inventory.credits` holds the mission's base
    // reward and is only ever spent on crafting. The ending read the second
    // one, so a run that earned 2,300 credits ended on a screen saying 500.
    const state = runState({
      runPhase: "ending",
      endingChoice: "arc1_wage_slave",
    });
    const spent = {
      ...state,
      player: { ...state.player, credits: 2300 },
      inventory: { ...state.inventory, credits: 500 },
    };
    const view = renderRunScreen(spent, 80, 30);
    if (!view) throw new Error("ending screen did not render");
    const text = view.grid.cells.map((_, y) => rowText(view.grid, y)).join("\n");
    expect(text).toContain("2,300cr");
    expect(text).not.toContain("500cr");
  });

  it("keeps the ending HUD line inside the narrow HUD panel", () => {
    // The HUD panel is 10 columns wide at the 40-column layout. The canvas
    // squeezes an over-long HUD line instead of truncating it, so a raw
    // ending id made the glyphs overlap and the line unreadable.
    const state = runState({
      runPhase: "ending",
      endingChoice: "arc4_liberation_front",
    });
    const view = renderRunScreen(state, 40, 30);
    const hud = view?.hud ?? [];
    for (const line of hud) {
      expect(line.length).toBeLessThanOrEqual(9);
    }
    expect(hud.join(" ")).not.toContain("arc4_liberation_front");
  });

  it.each([
    ["Recovered +1,234 credits. Loot: shard x2", 1234, "Loot: shard x2"],
    ["No rewards", 0, ""],
  ] as const)("preserves parsed loot for %s", (message, credits, loot) => {
    const state = runState({ runPhase: "loot", message });
    const view = renderRunScreen(state, 80, 50);
    // ADR-0259: a non-terminal win also offers cards. The controller and the
    // renderer derive the same offer from the same run.
    const offers = offeredCardIds(state)
      .map((id, i) => {
        const card = rewardProgram(id);
        return card ? formatRewardOption(i + 1, card) : "";
      })
      .filter((line) => line.length > 0);
    // ADR-0282: the loot screen is a spend, so the repair and credits options
    // are part of the offer block.
    const grade = missionGradeOf(state.mission);
    const repair = lootRepairAmount(state.player.maxHp, grade);
    offers.push(
      `${LOOT_REPAIR_SLOT} REPAIR          +${repair} HP  → ${Math.min(state.player.maxHp, state.player.hp + repair)}/${state.player.maxHp}`,
    );
    offers.push(
      `${LOOT_INTEL_SLOT} INTEL           ${lootIntelPrice(grade)}cr — name the routes ahead (spends this stop)`,
    );
    expect(view?.grid.cells).toEqual(
      renderLootScreen(
        state.player.hp,
        state.player.maxHp,
        80,
        50,
        credits,
        loot,
        false,
        offers,
      ).cells,
    );
    // Only ENTER and the loot digits do anything on the loot screen:
    // `applyLootAction` ignores cancel and the move keys, so promising them
    // was a false affordance (ADR-0251 rule 5). ADR-0282 adds the repair and
    // credits slots, so the HUD names all three.
    expect(view?.hud).toEqual([
      "LOOT",
      "",
      "1-3: card · 4: repair · 5: intel",
    ]);
  });

  it("shows the taken card as ACQUIRED and waits for ENTER (ADR-0261)", () => {
    const base = runState({ runPhase: "loot", message: "No rewards" });
    const offered = offeredCardIds(base);
    const state = { ...base, cardRewardTaken: offered[0]! };
    const view = renderRunScreen(state, 80, 50);
    const text = view!.grid.cells
      .map((row) => row.map((c) => c?.char ?? " ").join(""))
      .join("\n");
    expect(text).toContain("ACQUIRED");
    // the reward is spent, so the digits are not promised any more
    expect(view?.hud).toEqual(["LOOT", "", "ENTER: continue"]);
    expect(text).not.toContain("1-3: take a card");
  });

  it("offers no card on the terminal node, since the run ends there", () => {
    const state = runState({ runPhase: "loot", message: "No rewards" });
    if (!state.matrix) throw new Error("fixture requires a matrix");
    const terminal = {
      ...state,
      currentNodeIndex: state.matrix.nodes.length - 1,
    };
    const view = renderRunScreen(terminal, 80, 50);
    expect(view?.hud).toEqual(["LOOT", "", "ENTER: run ends"]);
  });

  it("leaves combat routing to the controller", () => {
    expect(renderRunScreen(runState(), 80, 50)).toBeNull();
  });

  it("preserves the full combat grid with HP deltas and grouped status effects", () => {
    const state = runState({
      statusEffects: [
        { kind: "burn", target: "player", remaining: 2, magnitude: 3 },
        {
          kind: "slow",
          target: "ice",
          iceIndex: 0,
          remaining: 3,
          magnitude: 1,
        },
        {
          kind: "silence",
          target: "ice",
          iceIndex: 1,
          remaining: 3,
          magnitude: 1,
        },
      ],
    });
    const grid = renderCombatScreen(
      { state, iceDelta: -7, playerDelta: -3 },
      80,
      50,
    );
    expect(grid.cells).toEqual(
      renderGrid(
        state,
        -7,
        -3,
        groupStatusByTarget(state.statusEffects, state.activeIceIndex),
        80,
        50,
      ).cells,
    );
    expect(grid.cells[1]?.[1]?.char).toBe("╔");
  });

  it("returns the untouched base grid and HUD when no VFX is active", () => {
    const state = runState();
    const view = composeCombatScreen(state, false);
    expect(view.grid).toBe(state.grid);
    expect(view.hud).toEqual(buildHudLines(state));
    expect(view.shake).toBeUndefined();
  });

  it("layers floating damage over VFX without changing the stored grid", () => {
    const state = runState({
      vfxInstances: [
        triggerCombatVfx("player_hit", "", 20, undefined, undefined, 17),
      ],
    });
    const baseCells = state.grid.cells;
    const view = composeCombatScreen(state, true);
    expect(rowText(view.grid, 5).slice(2, 5)).toBe("-17");
    expect(view.grid.cells[5]?.[2]?.fg).toBe(PALETTE.WHITE);
    expect(view.shake).toMatchObject({ x: 0, y: 0 });
    expect(state.grid.cells).toBe(baseCells);
    expect(rowText(state.grid, 5).trim()).toBe("");
  });
});
