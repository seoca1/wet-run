import type { GameState } from "../core/types";
import { makeGrid } from "../core/grid";
import {
  ENCOUNTER_VERBS,
  ENCOUNTER_VERB_COSTS,
  encounterRoster,
  bypassBlockReason,
  encounterScanProgram,
} from "../core/state/encounter_verbs";
import { drawPanel, screenFrameRect, setInnerText } from "./panel";
import { PALETTE } from "./palette";
import type { ScreenView } from "./screen_view";

export function renderEncounterDecision(
  state: GameState,
  cols: number,
  rows: number,
): ScreenView {
  const panel = drawPanel(
    makeGrid(cols, rows),
    screenFrameRect({ width: cols, height: rows }),
    { title: "ENCOUNTER" },
  );
  let grid = panel.grid;
  const inner = panel.inner;
  const x = inner.x + 1;
  let y = inner.y + 1;
  const width = inner.width - 2;
  const write = (text: string, color = PALETTE.GRAY_LIGHT): void => {
    for (let offset = 0; offset < Math.max(1, text.length); offset += width) {
      grid = setInnerText(
        grid,
        inner,
        x,
        y++,
        text.slice(offset, offset + width),
        color,
      );
    }
  };
  const node = state.matrix?.nodes[state.currentNodeIndex];
  const costs = ENCOUNTER_VERB_COSTS;
  const bypassReason = bypassBlockReason(state);
  const scanProgram = encounterScanProgram(state);
  write(
    `Node ${state.currentNodeIndex + 1} · ${node?.zone.toUpperCase() ?? ""}`,
    PALETTE.GREEN_NEON,
  );
  write("ICE blocks travel until resolved", PALETTE.YELLOW_AMBER);
  write(
    `HP ${state.player.hp}/${state.player.maxHp} · COST ${state.player.alarm}/${costs.limit}`,
  );
  write(`Reward: ${node?.reward.credits ?? 0}cr`);
  y += 1;
  const details = {
    PROBE: "Reveal ICE identity and HP",
    BYPASS: bypassReason ?? "No fight / no loot / no heal",
    BREACH: "Fight for the full reward",
    "JACK OUT": "Abandon the run (unchanged)",
    SCAN: state.encounterDecision?.probed
      ? "Threat already revealed; no payment"
      : scanProgram
        ? `Discard ${scanProgram.name} (T${scanProgram.tier})`
        : "Requires utility program in hand",
  } as const;
  for (const verb of ENCOUNTER_VERBS) {
    const price =
      verb === "PROBE"
        ? state.encounterDecision?.probed
          ? 0
          : costs.probe
        : verb === "BYPASS"
          ? costs.bypass
          : 0;
    const blocked =
      (verb === "BYPASS" && bypassReason !== null) ||
      state.player.alarm + price > costs.limit;
    const suffix =
      (verb === "PROBE" || verb === "SCAN") && state.encounterDecision?.probed
        ? "REVEALED"
        : verb === "SCAN"
          ? scanProgram
            ? "PROGRAM"
            : "NO UTILITY IN HAND"
          : price > 0
            ? `+${price} COST${blocked ? " BLOCKED" : ""}`
            : "";
    const selected = state.encounterDecision?.selectedVerb === verb;
    write(
      `${selected ? ">" : " "} ${verb} ${suffix}`,
      selected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT,
    );
    write(`  ${details[verb]}`);
    if (verb === "SCAN") write("  Reveal ICE; lose combat card");
    y += 1;
  }
  if (state.encounterDecision?.probed) {
    write("EXACT THREAT", PALETTE.GREEN_NEON);
    for (const ice of encounterRoster(state))
      write(`${ice.id} HP ${ice.hp}/${ice.maxHp}`);
  } else {
    write("Threat hidden — PROBE or SCAN");
  }
  y += 1;
  write("↑↓/←→: choose · ENTER/SPACE: act");
  return {
    grid,
    hud: [
      "ENCOUNTER",
      `COST ${state.player.alarm}/${costs.limit}`,
      `TRACE ${state.alarmLevel}/5`,
      "",
      ...wrapWords(state.message, HUD_TEXT_COLS),
    ],
  };
}

/** The narrowest HUD in use (the 40x60 preset's 16 columns, one reserved by
 * drawHud). The canvas squeezes a longer line rather than wrapping it. */
const HUD_TEXT_COLS = 15;

function wrapWords(text: string, width: number): string[] {
  const lines: string[] = [];
  for (const word of text.split(" ")) {
    const last = lines.length - 1;
    const line = lines[last];
    if (line !== undefined && line.length + 1 + word.length <= width)
      lines[last] = `${line} ${word}`;
    else lines.push(word);
  }
  return lines;
}
