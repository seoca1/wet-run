/** Wet Run Web MVP — entry point.
 *
 * Boots the ASCII renderer, mounts keyboard input, loads MVP game data,
 * and renders the initial frame.
 */
import { AsciiRenderer } from "./renderer/canvas.ts";
import { KeyboardInput } from "./input/keyboard.ts";
import type { GameState, GameAction, Ice, Mission, Program } from "./core/types.ts";
import { applyAction, buildHudLines, makeInitialState } from "./core/state.ts";
import { makeGrid, setText } from "./core/grid.ts";
import { PALETTE, iceColor } from "./renderer/palette.ts";

import missionsData from "./data/missions.json" with { type: "json" };
import programsData from "./data/programs.json" with { type: "json" };
import iceTypesData from "./data/ice_types.json" with { type: "json" };

const MVP_MISSION_ID = "first_jack";

function loadMission(): Mission {
  const data = missionsData as unknown as Record<string, Mission>;
  const mission = data[MVP_MISSION_ID];
  if (!mission) throw new Error(`MVP mission '${MVP_MISSION_ID}' not found in missions.json`);
  return mission;
}

function loadIce(): Ice {
  // ice_types.json is keyed by ICE id; pick the first entry as MVP default.
  const data = iceTypesData as unknown as Record<string, Ice>;
  const firstKey = Object.keys(data)[0];
  if (!firstKey) throw new Error("No ICE types in ice_types.json");
  const ice = data[firstKey];
  if (!ice) throw new Error("ICE entry empty");
  return ice;
}

function loadDeck(): ReadonlyArray<Program> {
  const data = programsData as unknown as Record<string, Program>;
  const ids = Object.keys(data).slice(0, 5);
  return ids
    .map((id) => data[id])
    .filter((p): p is Program => p !== undefined);
}

function renderGrid(state: GameState) {
  let grid = makeGrid(80, 50);
  grid = setText(grid, 2, 1, `Mission: ${state.mission.title}`, PALETTE.GREEN_NEON);
  grid = setText(grid, 2, 3, state.message, PALETTE.GRAY_LIGHT);

  if (state.phase === "combat" || state.phase === "victory" || state.phase === "defeat") {
    grid = setText(grid, 36, 22, "[", PALETTE.GRAY_MID);
    grid = setText(grid, 37, 22, state.ice.name.slice(0, 12), iceColor(state.ice.tier));
    grid = setText(grid, 50, 22, "]", PALETTE.GRAY_MID);
    grid = setText(grid, 36, 24, `HP: ${state.ice.hp}`, PALETTE.RED_BRIGHT);
  }

  if (state.phase === "combat" && state.deck.length > 0) {
    grid = setText(grid, 2, 42, "HAND:", PALETTE.YELLOW_AMBER);
    let x = 9;
    for (const p of state.deck) {
      const label = `[${p.id.slice(0, 4)}]`;
      grid = setText(grid, x, 42, label, PALETTE.CYAN_LIGHT);
      x += label.length + 1;
    }
  }
  return grid;
}

class Game {
  private state: GameState;
  private renderer: AsciiRenderer;
  private input: KeyboardInput;

  constructor(canvas: HTMLCanvasElement, mission: Mission, ice: Ice, deck: ReadonlyArray<Program>) {
    this.state = { ...makeInitialState(mission, ice, deck), grid: makeGrid(80, 50) };
    this.renderer = new AsciiRenderer(canvas, { cellWidth: 8, cellHeight: 16 });
    this.renderer.resizeGrid(80, 50, 28);
    this.input = new KeyboardInput();
    this.input.setHandler((action: GameAction) => {
      this.state = applyAction(this.state, action);
      this.draw();
    });
    this.input.start();
  }

  private draw(): void {
    const nextGrid = renderGrid(this.state);
    this.renderer.render(nextGrid, buildHudLines(this.state));
  }

  start(): void {
    this.draw();
  }

  stop(): void {
    this.input.stop();
  }
}

function boot(): void {
  const loading = document.getElementById("loading");
  const canvas = document.getElementById("game-canvas");
  if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
    console.error("Canvas element not found");
    return;
  }

  let game: Game;
  try {
    game = new Game(canvas, loadMission(), loadIce(), loadDeck());
  } catch (err) {
    console.error("Failed to boot Wet Run:", err);
    if (loading) loading.textContent = `Error: ${(err as Error).message}`;
    return;
  }

  if (loading) loading.style.display = "none";
  game.start();
  (window as unknown as { wetrun: Game }).wetrun = game;
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
