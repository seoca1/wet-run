import type { GameState } from "../core/types";
import { makeGrid } from "../core/grid";
import {
  ENCOUNTER_VERBS,
  ENCOUNTER_VERB_COSTS,
  encounterRoster,
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
  write(
    `Node ${state.currentNodeIndex + 1} · ${node?.zone.toUpperCase() ?? ""}`,
    PALETTE.GREEN_NEON,
  );
  write(
    `HP ${state.player.hp}/${state.player.maxHp} · COST ${state.player.alarm}/${costs.limit}`,
  );
  write(`Reward: ${node?.reward.credits ?? 0}cr`);
  y += 1;
  const details = {
    PROBE: "Reveal ICE identity and HP",
    BYPASS: "No fight / no loot / no heal",
    BREACH: "Fight for the full reward",
    "JACK OUT": "Abandon the run (unchanged)",
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
    const blocked = state.player.alarm + price > costs.limit;
    const suffix =
      verb === "PROBE" && state.encounterDecision?.probed
        ? "REVEALED"
        : price > 0
          ? `+${price} COST${blocked ? " BLOCKED" : ""}`
          : "";
    const selected = state.encounterDecision?.selectedVerb === verb;
    write(
      `${selected ? ">" : " "} ${verb} ${suffix}`,
      selected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT,
    );
    write(`  ${details[verb]}`);
    y += 1;
  }
  if (state.encounterDecision?.probed) {
    write("EXACT THREAT", PALETTE.GREEN_NEON);
    for (const ice of encounterRoster(state))
      write(`${ice.id} HP ${ice.hp}/${ice.maxHp}`);
  } else {
    write("Threat hidden — PROBE to reveal");
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
      state.message,
    ],
  };
}
