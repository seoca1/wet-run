import type { GameState } from "../core/types";
import { makeGrid } from "../core/grid";
import {
  ENCOUNTER_VERBS,
  ENCOUNTER_VERB_COSTS,
  encounterRoster,
  bypassBlockReason,
  encounterScanProgram,
  type EncounterVerb,
} from "../core/state/encounter_verbs";
import { drawPanel, screenFrameRect, setInnerText } from "./panel";
import { PALETTE } from "./palette";
import type { ScreenView } from "./screen_view";
import type { DialogueBeat } from "../core/state/event_beats";

/** The verbs that resolve the node or end the run, in arrow order. */
const EXIT_VERBS: readonly EncounterVerb[] = ["BYPASS", "BREACH", "JACK OUT"];

export function renderEncounterDecision(
  state: GameState,
  cols: number,
  rows: number,
  /** ADR-0317 (3b): the ICE's own tagline, once the runner has looked at it.
   * Null for silent ICE, which is most of them, and for an already-heard one. */
  iceVoice: DialogueBeat | null = null,
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
  const bypassBlocked =
    bypassReason !== null || state.player.alarm + costs.bypass > costs.limit;
  const exits = EXIT_VERBS.filter(
    (verb) => verb !== "BYPASS" || !bypassBlocked,
  );
  write(`EXITS: ${exits.join(" · ")}`, PALETTE.CYAN_LIGHT);
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
    const exit = EXIT_VERBS.includes(verb);
    write(
      `${selected ? ">" : " "} ${verb.padEnd(8)} ${exit ? "EXIT" : "INFO"} ${suffix}`.trimEnd(),
      selected
        ? PALETTE.GREEN_NEON
        : exit
          ? PALETTE.CYAN_LIGHT
          : PALETTE.GRAY_LIGHT,
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
  if (iceVoice !== null) {
    // ADR-0317 (3b): the ICE broadcasts once the runner has looked at it. Its
    // identity is what PROBE sells, so the voice waits for the reveal — it
    // never gives that away for free.
    const body: string[] = [];
    for (const line of iceVoice.lines) body.push(...wrapWords(line, width));
    // The footer names the keys that act, so the voice never pushes it off the
    // panel (ADR-0251 rule 5). Reserve the three footer rows plus the blank
    // that separates the voice from them. The worst case is the 60x40 layout
    // with three ICE on the node and Black ICE's three-voice tagline; a tight
    // screen shows what fits rather than losing the footer.
    const capacity = inner.y + inner.height - y - 4;
    const hasSpeaker = iceVoice.speaker.length > 0;
    const bodyRows = Math.max(0, hasSpeaker ? capacity - 1 : capacity);
    if (bodyRows >= 1) {
      if (hasSpeaker) write(iceVoice.speaker, PALETTE.YELLOW_AMBER);
      for (const row of body.slice(0, bodyRows))
        write(row, PALETTE.CYAN_LIGHT);
      y += 1;
    }
  }
  if (state.encounterDecision?.selectedVerb == null)
    write("Nothing selected — press ↓ to pick", PALETTE.YELLOW_AMBER);
  write("↑↓/←→: choose · ENTER/SPACE: act");
  write("ESC: jack out (abandon run)");
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
