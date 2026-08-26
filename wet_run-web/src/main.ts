/** Wet Run Web MVP — entry point.
 *
 * Tier 2a (2026-08-25): supports mission select screen (5 missions).
 * Tier 2b (2026-08-26): Howler.js BGM (single track, M to mute).
 * Boots the ASCII renderer, mounts keyboard input, loads MVP game data,
 * and renders the initial frame.
 */
import { AsciiRenderer } from "./renderer/canvas.ts";
import { KeyboardInput } from "./input/keyboard.ts";
import { mountVirtualGamepad, isTouchDevice } from "./input/touch.ts";
import { AudioManager, SFX_IDS } from "./audio/manager.ts";
import { healthBar, healthColor, formatStatusLabel } from "./renderer/vfx.ts";
import type { GameState, GameAction, GamePhase, Ice, Mission, Program } from "./core/types.ts";
import { applyAction, buildHudLines, makeInitialState, stateToSaveSlot } from "./core/state.ts";
import { makeGrid, setText } from "./core/grid.ts";
import { PALETTE, iceColor } from "./renderer/palette.ts";
import { save as saveToSlot } from "./save/storage.ts";

import missionsData from "./data/missions.json" with { type: "json" };
import programsData from "./data/programs.json" with { type: "json" };
import iceTypesData from "./data/ice_types.json" with { type: "json" };

type MissionsFile = Readonly<Record<string, Mission>>;
type ProgramsFile = Readonly<Record<string, Program>>;

/** Mission catalog (Tier 2a: 5 curated). */
const MISSIONS: ReadonlyArray<Mission> = Object.values(missionsData as MissionsFile);

/** Pick the ICE type best matched to the mission's `ice_id` (fallback: first). */
function loadIce(mission: Mission, iceTypes: Readonly<Record<string, Ice>>): Ice {
  const keys = Object.keys(iceTypes);
  const preferred = (mission as { ice_id?: string }).ice_id;
  if (preferred && preferred in iceTypes) {
    const ice = iceTypes[preferred];
    if (ice) return ice;
  }
  const first = keys[0];
  if (!first) throw new Error("No ICE types in ice_types.json");
  const fallback = iceTypes[first];
  if (!fallback) throw new Error("ICE entry empty");
  return fallback;
}

/** Build the first 5 programs for the deck (deterministic order from program id). */
function loadDeck(programs: Readonly<Record<string, Program>>, count = 5): ReadonlyArray<Program> {
  const ids = Object.keys(programs)
    .sort()
    .slice(0, count);
  return ids
    .map((id) => programs[id])
    .filter((p): p is Program => p !== undefined);
}

/** Format a mission for the select screen (Tier 2a). */
function formatMissionOption(mission: Mission, index: number): string {
  const grade = `T${mission.grade_max}`;
  const credits = mission.rewards.credits.toLocaleString();
  return `${index + 1}. ${mission.title}  [${grade} | ${credits}cr]`;
}

/** Render the mission select screen. */
function renderMissionSelect(missions: ReadonlyArray<Mission>, selected: number): ReturnType<typeof makeGrid> {
  let grid = makeGrid(80, 50);
  grid = setText(grid, 2, 1, "WET RUN — Select Mission", PALETTE.GREEN_NEON);
  grid = setText(grid, 2, 3, "ENTER: launch | ESC: quit | Arrow keys: navigate", PALETTE.GRAY_LIGHT);
  let y = 6;
  for (let i = 0; i < missions.length; i++) {
    const m = missions[i];
    if (!m) continue;
    const isSelected = i === selected;
    const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const marker = isSelected ? "▸" : " ";
    grid = setText(grid, 4, y, `${marker} ${formatMissionOption(m, i)}`, fg);
    y += 1;
  }
  return grid;
}

class Game {
  private state: GameState | null = null;
  private renderer: AsciiRenderer;
  private input: KeyboardInput;
  private selectedMission = 0;
  private iceTypes: Readonly<Record<string, Ice>>;
  private unmountTouch: () => void = () => {};
  private _lastPhase: GamePhase | null = null;

  constructor(canvas: HTMLCanvasElement, iceTypes: Readonly<Record<string, Ice>>) {
    this.iceTypes = iceTypes;
    this.renderer = new AsciiRenderer(canvas, { cellWidth: 8, cellHeight: 16 });
    this.renderer.resizeGrid(80, 50, 28);
    this.input = new KeyboardInput();
    const handler = (action: GameAction): void => {
      if (this.state === null) {
        this.handleMenuInput(action);
      } else {
        this.state = applyAction(this.state, action);
        this.draw();
      }
    };
    this.input.setHandler(handler);
    this.input.start();
    // Tier 2c: auto-mount virtual gamepad on touch devices.
    if (isTouchDevice()) {
      this.unmountTouch = mountVirtualGamepad(handler);
    }
  }

  private handleMenuInput(action: GameAction): void {
    if (action.type === "move_south") {
      this.selectedMission = (this.selectedMission + 1) % MISSIONS.length;
      this.draw();
    } else if (action.type === "move_north") {
      this.selectedMission = (this.selectedMission - 1 + MISSIONS.length) % MISSIONS.length;
      this.draw();
    } else if (action.type === "confirm") {
      this.launchSelected();
    } else if (action.type === "jack_out" || action.type === "cancel") {
      this.draw();
    }
  }

  private launchSelected(): void {
    const mission = MISSIONS[this.selectedMission];
    if (!mission) return;
    const programs = programsData as unknown as ProgramsFile;
    const deck = loadDeck(programs);
    const ice = loadIce(mission, this.iceTypes);
    const initial = makeInitialState(mission, ice, deck);
    this.state = { ...initial, grid: makeGrid(80, 50) };
    this.draw();
  }

  private autosave(): void {
    if (this.state === null) return;
    try {
      saveToSlot(0, stateToSaveSlot(this.state));
    } catch {
      // Autosave is best-effort; user can manually save later.
    }
  }

  private draw(): void {
    if (this.state === null) {
      this.renderer.render(renderMissionSelect(MISSIONS, this.selectedMission), [
        "MISSION SELECT",
        "",
        `Selected: ${this.selectedMission + 1}/${MISSIONS.length}`,
      ]);
      this.syncPhase("menu");
    } else {
      this.state = { ...this.state, grid: renderGrid(this.state) };
      this.renderer.render(this.state.grid, buildHudLines(this.state));
      // Autosave on every state change (cheap; localStorage write).
      this.autosave();
      this.syncPhase(this.state.phase);
    }
  }

  private syncPhase(current: GamePhase): void {
    if (this._lastPhase === current) return;
    const previous = this._lastPhase;
    this._lastPhase = current;
    const audio = AudioManager.getInstance();
    audio.playPhase(current);
    if (current === "victory" && previous !== "victory") {
      audio.playSfx(SFX_IDS.VICTORY);
    } else if (current === "defeat" && previous !== "defeat") {
      audio.playSfx(SFX_IDS.DEFEAT);
    } else if (current === "exit") {
      audio.stopAllSfx();
    }
  }

  start(): void {
    this.draw();
  }

  stop(): void {
    this.input.stop();
    this.unmountTouch();
  }
}

function renderGrid(state: GameState) {
  let grid = makeGrid(80, 50);
  grid = setText(grid, 2, 1, `Mission: ${state.mission.title}`, PALETTE.GREEN_NEON);
  grid = setText(grid, 2, 3, state.message, PALETTE.GRAY_LIGHT);

  grid = setText(grid, 60, 1, `T${state.turnCount + 1}`, PALETTE.GRAY_LIGHT);

  grid = setText(
    grid,
    2,
    5,
    `P ${healthBar(state.player.hp, state.player.maxHp)} ${state.player.hp}/${state.player.maxHp}`,
    healthColor(state.player.hp, state.player.maxHp),
  );

  if (state.phase === "combat" || state.phase === "victory" || state.phase === "defeat") {
    const iceHp = Math.max(0, state.ice.hp);
    grid = setText(grid, 36, 22, "[", PALETTE.GRAY_MID);
    grid = setText(grid, 37, 22, state.ice.name.slice(0, 12), iceColor(state.ice.tier));
    grid = setText(grid, 50, 22, "]", PALETTE.GRAY_MID);
    grid = setText(
      grid,
      36,
      24,
      `${healthBar(iceHp, 100)} ${iceHp}/100`,
      healthColor(iceHp, 100),
    );
  }

  const statusLabel = formatStatusLabel(state.phase);
  if (statusLabel !== "") {
    const statusColor = state.phase === "victory" ? PALETTE.GREEN_NEON : PALETTE.RED_BRIGHT;
    grid = setText(grid, 36, 26, statusLabel, statusColor);
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

function boot(): void {
  const loading = document.getElementById("loading");
  const canvas = document.getElementById("game-canvas");
  if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
    console.error("Canvas element not found");
    return;
  }

  let game: Game;
  try {
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    game = new Game(canvas, iceTypes);
  } catch (err) {
    console.error("Failed to boot Wet Run:", err);
    if (loading) loading.textContent = `Error: ${(err as Error).message}`;
    return;
  }

  if (loading) loading.style.display = "none";
  game.start();
  (window as unknown as { wetrun: Game }).wetrun = game;

  const audio = AudioManager.getInstance();
  AudioManager.unlockOnFirstGesture(() => {
    audio.play();
  });
  document.addEventListener("keydown", (ev: KeyboardEvent) => {
    if (ev.key === "m" || ev.key === "M") {
      const muted = audio.toggleMute();
      console.info(`[audio] BGM ${muted ? "muted" : "unmuted"} (M to toggle)`);
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
