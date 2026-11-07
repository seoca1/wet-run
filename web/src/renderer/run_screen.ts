import type { GameState } from "../core/types";
import { renderMatrix } from "./matrix";
import { renderEndingScreen, renderLootScreen } from "./ending";
import { jockeyHandle } from "../core/state/jockey";
import type { ScreenView } from "./screen_view";
import { renderGrid } from "./combat_grid";
import { groupStatusByTarget } from "./status_hud";
import { buildHudLines } from "../core/state/state";
import { isTerminalNode } from "../core/state/run_end";
import { burnTarget } from "../core/state/state_actions_phases";
import type { GrowthReveal } from "./growth_reveal";
import { offeredCardIds, rewardProgram } from "../core/state/card_reward";
import { formatRewardOption } from "../core/combat/program_affordance";
import { missionGradeOf } from "../core/combat/ice_scaling";
import {
  BURN_COST,
  LOOT_INTEL_SLOT,
  LOOT_REPAIR_SLOT,
  LOOT_BURN_SLOT,
  LOOT_VENT_SLOT,
  VENT_COST,
  ventHpPrice,
  lootIntelPrice,
  lootRepairAmount,
} from "../core/state/loot_choice";
import { ENDINGS } from "../core/combat/ending_resolver";
import { composeCombatVfx } from "./combat_vfx";
import { composeFloatingDamage, overlayShake } from "./combat_overlay";
import type { ShakeState } from "./screen_shake";
import { renderEncounterDecision } from "./encounter";
import type { MatrixTravelFrame } from "./matrix_travel";

/** The same full-grid dimensions used by matrix, loot, ending and combat views. */
export function runScreenLayout(cols: number, rows: number) {
  return { cols, rows } as const;
}

/**
 * The ending's arc number, for the narrow right-hand HUD.
 *
 * The HUD panel is 10 columns wide at the 40-column layout, so a line has
 * to stay short: the canvas squeezes an over-long line instead of
 * truncating it, and the glyphs overlap. The ending's own name is already
 * on the grid, so the arc number is the part the HUD adds.
 */
export function endingArcLabel(choice: string | null): string {
  const ending = choice ? ENDINGS.find((e) => e.id === choice) : undefined;
  return ending ? `ARC ${ending.arc}` : "ARC ?";
}

/** Compose non-combat run phases, retaining message-derived loot and HUD text.
 * `matrixTravel` is the controller's current traversal frame (visual only). */
export function renderRunScreen(
  state: GameState,
  cols: number,
  rows: number,
  matrixEntryHint = false,
  matrixTravel: MatrixTravelFrame | null = null,
  growth: GrowthReveal | null = null,
): ScreenView | null {
  const layout = runScreenLayout(cols, rows);
  switch (state.runPhase) {
    case "matrix": {
      if (state.encounterDecision)
        return renderEncounterDecision(state, cols, rows);
      const matrix = state.matrix;
      if (!matrix) return null;
      return {
        grid: renderMatrix(
          matrix,
          state.currentNodeIndex,
          state.visitedNodes,
          layout.cols,
          layout.rows,
          state.clearedEncounterNodes?.includes(state.currentNodeIndex)
            ? (state.iceRoster[state.activeIceIndex] ?? null)
            : null,
          state.selectedMatrixNodeIndex ?? null,
          state.clearedEncounterNodes ?? [],
          matrixEntryHint,
          matrixTravel,
          state.bypassedEncounterNodes ?? [],
          state.intelNodes ?? [],
        ),
        hud: [
          "MATRIX",
          "",
          `Node ${state.currentNodeIndex + 1}/${matrix.nodes.length}`,
          // ADR-0262: the arrival note — the board otherwise never shows the
          // growth, so the card is named while the runner is back in play.
          ...(growth?.arrivalLines ?? []),
        ],
      };
    }
    case "ending":
      return {
        grid: renderEndingScreen(state.endingChoice, layout.cols, layout.rows, {
          mission: state.mission.title,
          jockey: jockeyHandle(state.jockeyId),
          hp: state.player.hp,
          maxHp: state.player.maxHp,
          credits: state.player.credits,
          turns: state.turnCount,
        }),
        // The grid already shows the ending's name, so the HUD carries the
        // arc number. The raw id ("arc4_liberation_front", 23 chars) was
        // squeezed by the canvas HUD at the 40-column layout, where the
        // panel is 10 columns wide — the glyphs overlapped and the line
        // was unreadable (ADR-0251 rule 5: the screen must be readable
        // and must say what it means).
        hud: ["ENDING", "", endingArcLabel(state.endingChoice)],
      };
    case "loot": {
      const creditsMatch = state.message.match(/\+(\d[\d,]*)\s+credits/);
      const lootMatch = state.message.match(/Loot:\s*(.+)$/);
      const rewardCredits = creditsMatch
        ? parseInt((creditsMatch[1] ?? "").replace(/,/g, ""), 10)
        : 0;
      const lootText = lootMatch ? `Loot: ${lootMatch[1]}` : "";
      // A terminal node ends the run on confirm — no heal, no route.
      const terminal = isTerminalNode(state);
      // ADR-0259: a non-terminal win offers cards; a terminal one ends the run.
      const takenId = state.cardRewardTaken ?? null;
      const ids = terminal ? [] : offeredCardIds(state);
      // ADR-0282: the loot screen is a spend — programs 1-3, repair 4,
      // credits 5. Built here so the renderer just prints the lines.
      const grade = missionGradeOf(state.mission);
      const offers = ids
        .map((id, i) => {
          const card = rewardProgram(id);
          return card ? formatRewardOption(i + 1, card, id === takenId) : "";
        })
        .filter((line) => line.length > 0);
      const takenIndex = takenId === null ? -1 : ids.indexOf(takenId);
      if (!terminal && takenId === null) {
        const repair = lootRepairAmount(state.player.maxHp, grade);
        const healed = Math.min(state.player.maxHp, state.player.hp + repair);
        offers.push(
          `${LOOT_REPAIR_SLOT} REPAIR          +${repair} HP  → ${healed}/${state.player.maxHp}`,
        );
        // ADR-0287: information, not power. Priced so it competes with a card
        // on a decision, not on a stat.
        const intelPrice = lootIntelPrice(grade);
        offers.push(
          `${LOOT_INTEL_SLOT} INTEL           ${intelPrice}cr — name the routes ahead (spends this stop)`,
        );
        // ADR-0295: the only way back from the trace, priced above what a kill
        // pays so it buys capacity rather than farming it.
        if (state.player.alarm > 0) {
          const ventedNow = Math.min(VENT_COST, state.player.alarm);
          const ventHp = ventHpPrice(state.player.maxHp);
          offers.push(
            `${LOOT_VENT_SLOT} VENT            ${ventHp} HP — clear ${ventedNow} COST → ${state.player.alarm - ventedNow}/100`,
          );
          // ADR-0296: the same capacity bought with growth instead of body.
          const spare = burnTarget(state);
          if (spare) {
            offers.push(
              `${LOOT_BURN_SLOT} BURN            ${spare.id} (T${spare.tier}) — clear ${Math.min(BURN_COST, state.player.alarm)} COST`,
            );
          }
        }
      }
      return {
        grid: renderLootScreen(
          state.player.hp,
          state.player.maxHp,
          layout.cols,
          layout.rows,
          rewardCredits,
          lootText,
          terminal,
          offers,
          takenIndex,
          growth?.lootCommit ?? null,
        ),
        // Only ENTER does anything on the loot screen: `applyLootAction`
        // ignores cancel and the move keys, so promising "↑↓: navigate" or
        // "ESC: back" would be a false affordance (ADR-0251 rule 5). The
        // line is kept short for the HUD panel — the canvas squeezes an
        // over-long line instead of truncating it — and the grid footer
        // carries the full wording.
        hud: [
          "LOOT",
          "",
          terminal
            ? "ENTER: run ends"
            : takenIndex >= 0
              ? "ENTER: continue"
              : offers.length > 0
                ? "1-3: card · 4: repair · 5: intel · 6: vent · 7: burn"
                : "ENTER: route",
        ],
      };
    }
    default:
      return null;
  }
}

/** Build combat's base grid from HP deltas and target-specific status effects. */
export function renderCombatScreen(
  view: {
    readonly state: GameState;
    readonly iceDelta: number | null;
    readonly playerDelta: number | null;
    /** ADR-0251: the touch overlay's program buttons carry the hand (same
     * rows, same facts) and sit over the canvas hand band, so the canvas
     * leaves that band empty instead of drawing text under the buttons. */
    readonly handOnOverlay?: boolean;
  },
  cols: number,
  rows: number,
) {
  const statusGroups = groupStatusByTarget(
    view.state.statusEffects,
    view.state.activeIceIndex,
  );
  const layout = runScreenLayout(cols, rows);
  return renderGrid(
    view.state,
    view.iceDelta,
    view.playerDelta,
    statusGroups,
    layout.cols,
    layout.rows,
    view.handOnOverlay === true,
  );
}

/** Layer VFX, then damage numbers, leaving the stored base grid unchanged. */
export function composeCombatScreen(
  state: GameState,
  reducedMotion: boolean,
): ScreenView & { readonly shake?: ShakeState } {
  const hud = buildHudLines(state);
  if (state.vfxInstances.length === 0) return { grid: state.grid, hud };
  const layout = runScreenLayout(state.grid.width, state.grid.height);
  const composed = composeCombatVfx(
    state.grid,
    state.vfxInstances,
    layout.cols,
    layout.rows,
  );
  return {
    grid: composeFloatingDamage(
      composed,
      state.vfxInstances,
      layout.cols,
      layout.rows,
    ),
    hud,
    shake: overlayShake(state.vfxInstances, reducedMotion),
  };
}
