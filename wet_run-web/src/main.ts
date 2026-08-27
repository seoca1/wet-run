/** Wet Run Web MVP — entry point.
 *
 * Tier 2a (2026-08-25): supports mission select screen (5 missions).
 * Tier 2b (2026-08-26): Howler.js BGM (single track, M to mute).
 * Boots the ASCII renderer, mounts keyboard input, loads MVP game data,
 * and renders the initial frame.
 */
import { AsciiRenderer } from "./renderer/canvas.ts";
import { KeyboardInput } from "./input/keyboard.ts";
import { mountVirtualGamepad, updateProgramRow, isTouchDevice } from "./input/touch.ts";
import { AudioManager, SFX_IDS } from "./audio/manager.ts";
import { MENU_OPTIONS, renderMainMenu, renderStubScreen, type MenuOption } from "./renderer/menu.ts";
import { renderMatrix } from "./renderer/matrix.ts";
import { buildMatrix } from "./core/matrix.ts";
import { renderEndingScreen, renderLootScreen } from "./renderer/ending.ts";
import { composeCombatVfx, tickCombatVfxList } from "./renderer/combat_vfx.ts";
import {
  healthBar,
  healthColor,
  hitFlashColor,
  formatStatusLabel,
  formatStatusGlyph,
  ICE_DEFEAT_ART,
  PLAYER_DEFEAT_ART,
  centerArt,
} from "./renderer/vfx.ts";
import type { GameState, GameAction, GamePhase, Ice, Mission, Program, ScreenKind } from "./core/types.ts";
import { applyAction, buildHudLines, makeInitialState, resolveProgramSelection, slotToGameState, stateToSaveSlot } from "./core/state.ts";
import { makeGrid, setText } from "./core/grid.ts";
import { PALETTE, iceColor } from "./renderer/palette.ts";
import { save as saveToSlot, load as loadFromSlot, hasSave as slotHasSave, getSaveMeta } from "./save/storage.ts";
import { getLayout, watchLayout, type Layout } from "./core/layout.ts";

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
    .map((id) => {
      const p = programs[id];
      if (!p) return undefined;
      // programs.json entries are keyed by id but don't carry id in the
      // value (legacy schema). Inject it so save/load round-trip works.
      return { ...p, id } as Program;
    })
    .filter((p): p is Program => p !== undefined);
}

/** Format a mission for the select screen (Tier 2a). */
function formatMissionOption(mission: Mission, index: number): string {
  const grade = `T${mission.grade_max}`;
  const credits = mission.rewards.credits.toLocaleString();
  return `${index + 1}. ${mission.title}  [${grade} | ${credits}cr]`;
}

/** Render the mission select screen. */
function renderMissionSelect(
  missions: ReadonlyArray<Mission>,
  selected: number,
  cols: number,
  rows: number,
): ReturnType<typeof makeGrid> {
  let grid = makeGrid(cols, rows);
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
  private screen: ScreenKind = "menu";
  private selectedMenuIndex = 0;
  private selectedMission = 0;
  private renderer: AsciiRenderer;
  private input: KeyboardInput;
  private iceTypes: Readonly<Record<string, Ice>>;
  private programs: Readonly<Record<string, Program>>;
  private missions: ReadonlyArray<Mission>;
  private hasSaveCache: boolean = false;
  private saveMetaCache: { missionId: string; turnCount: number; savedAt: string } | null = null;
  private unmountTouch: () => void = () => {};
  private unwatchLayout: () => void = () => {};
  private _lastPhase: GamePhase | null = null;
  private _lastIceHp: number | null = null;
  private _lastPlayerHp: number | null = null;
  private layout: Layout;

  constructor(canvas: HTMLCanvasElement, iceTypes: Readonly<Record<string, Ice>>) {
    this.iceTypes = iceTypes;
    this.programs = programsData as unknown as ProgramsFile;
    this.missions = MISSIONS;
    this.layout = getLayout();
    this.renderer = new AsciiRenderer(canvas, { cellWidth: 8, cellHeight: 16 });
    this.renderer.resizeGrid(this.layout.cols, this.layout.rows, this.layout.hudCols);
    this.input = new KeyboardInput();
    // Refresh CONTINUE option availability on boot (async).
    void this.refreshSaveCache();
    const handler = (action: GameAction): void => {
      // Pre-game screens (menu, mission_select, stub screens) route to handlePreGameInput.
      // In-game screens route through the reducer.
      if (this.screen !== "menu" && this.screen !== "mission_select" && this.state === null) {
        this.handleStubInput(action);
        return;
      }
      if (this.state === null) {
        this.handlePreGameInput(action);
      } else {
        // Resolve select_program (hand index) → use_program (programId) at the boundary.
        const resolved: GameAction = (() => {
          if (this.state === null) return action;
          const r = resolveProgramSelection(this.state, action);
          return r ?? action;
        })();
        const previous = this.state;
        this.state = applyAction(this.state, resolved);
        if (resolved.type === "use_program" && previous.phase === "combat" && this.state.phase === "combat") {
          const iceDelta = this.state.ice.hp - previous.ice.hp;
          if (iceDelta < 0) {
            AudioManager.getInstance().playSfx(SFX_IDS.COMBAT_HIT);
          }
          this._lastIceHp = this.state.ice.hp;
          this._lastPlayerHp = this.state.player.hp;
        }
        this.draw();
      }
    };
    this.input.setHandler(handler);
    this.input.start();
    if (isTouchDevice()) {
      this.unmountTouch = mountVirtualGamepad(handler);
    }
    this.unwatchLayout = watchLayout((next) => {
      this.layout = next;
      this.renderer.resizeGrid(next.cols, next.rows, next.hudCols);
      this.draw();
    });
  }

  private handlePreGameInput(action: GameAction): void {
    // Digit keys 1-9 → menu selection on menu screen (otherwise → combat program select).
    if (action.type === "select_program" && this.screen === "menu") {
      const idx = action.handIndex - 1;
      if (idx >= 0 && idx < MENU_OPTIONS.length) {
        this.selectedMenuIndex = idx;
        this.selectMenuOption(MENU_OPTIONS[idx]?.key);
      }
      return;
    }
    if (this.screen === "menu") {
      if (action.type === "move_south") {
        this.selectedMenuIndex = (this.selectedMenuIndex + 1) % MENU_OPTIONS.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMenuIndex = (this.selectedMenuIndex - 1 + MENU_OPTIONS.length) % MENU_OPTIONS.length;
        this.draw();
      } else if (action.type === "confirm") {
        this.selectMenuOption(MENU_OPTIONS[this.selectedMenuIndex]?.key);
      } else if (action.type === "jack_out" || action.type === "cancel") {
        // No-op: already at top-level menu
        this.draw();
      }
      return;
    }
    if (this.screen === "mission_select") {
      if (action.type === "move_south") {
        this.selectedMission = (this.selectedMission + 1) % MISSIONS.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMission = (this.selectedMission - 1 + MISSIONS.length) % MISSIONS.length;
        this.draw();
      } else if (action.type === "confirm") {
        this.launchSelected();
      } else if (action.type === "jack_out" || action.type === "cancel") {
        this.screen = "menu";
        this.draw();
      }
      return;
    }
  }

  private handleStubInput(action: GameAction): void {
    // Stub screens: ENTER/ESC/Q/CANCEL all return to main menu.
    if (
      action.type === "confirm" ||
      action.type === "cancel" ||
      action.type === "jack_out"
    ) {
      this.screen = "menu";
      this.draw();
    }
  }

  private selectMenuOption(option: MenuOption | undefined): void {
    if (!option) return;
    switch (option) {
      case "new_run":
        this.screen = "mission_select";
        this.draw();
        break;
      case "continue":
        void this.handleContinue();
        break;
      case "graphic_novel":
      case "settings":
      case "credits":
      case "hall_of_dead":
      case "help":
      case "endings":
      case "stats":
        // Stub for now (Tier 5+). Show "Coming soon" screen.
        this.draw();
        break;
    }
  }

  /** Reload hasSave + meta caches from storage. Call after save/load/clear. */
  private async refreshSaveCache(): Promise<void> {
    this.hasSaveCache = await slotHasSave(0);
    this.saveMetaCache = await getSaveMeta(0);
    // Re-draw menu to reflect availability change (if on menu screen).
    if (this.screen === "menu") this.draw();
  }

  /** Load autosave (slot 0) and resume from saved state.
   *
   * Returns silently if no save exists (gated by hasSaveCache). On success,
   * transitions to the in-game state and resets _lastIceHp/_lastPlayerHp
   * so hit-flash VFX doesn't trigger immediately on resume.
   */
  private async handleContinue(): Promise<void> {
    if (!this.hasSaveCache) {
      // No save — show stub message (should be unreachable from menu but safe).
      this.draw();
      return;
    }
    const slot = await loadFromSlot(0);
    if (!slot) {
      // Stale cache: hasSave said true but load failed. Refresh + stub.
      await this.refreshSaveCache();
      this.draw();
      return;
    }
    const fallbackIce = Object.values(this.iceTypes)[0];
    if (!fallbackIce) {
      this.draw();
      return;
    }
    const restored = slotToGameState(slot, this.missions, this.programs, fallbackIce);
    if (!restored) {
      // Mission no longer in catalog or all programs disappeared.
      this.draw();
      return;
    }
    this.state = restored;
    this.screen = "menu"; // game-internal state; main screen renderer picks up state != null
    this._lastIceHp = restored.ice.hp;
    this._lastPlayerHp = restored.player.hp;
    this.draw();
  }

  private launchSelected(): void {
    const mission = MISSIONS[this.selectedMission];
    if (!mission) return;
    const programs = programsData as unknown as ProgramsFile;
    const deck = loadDeck(programs);
    const ice = loadIce(mission, this.iceTypes);
    const initial = makeInitialState(mission, ice, deck);
    // Tier 5.5: pass programs to enable event-matrix (combat/discovery/trap/etc.)
    const matrix = buildMatrix(this.iceTypes, programs);
    this.state = {
      ...initial,
      grid: makeGrid(this.layout.cols, this.layout.rows),
      matrix,
      currentNodeIndex: 0,
      runPhase: "matrix",
      phase: "approach",
    };
    this.draw();
  }

  private autosave(): void {
    if (this.state === null) return;
    // saveToSlot is async (Tier 3 IDB backend). Fire-and-forget: autosave is best-effort.
    saveToSlot(0, stateToSaveSlot(this.state))
      .then(() => {
        // Refresh save metadata so menu reflects current save state.
        void this.refreshSaveCache();
      })
      .catch(() => {
        // Autosave is best-effort; user can manually save later.
      });
  }

  private draw(): void {
    // Tier 5: matrix / loot / ending screens render with a real GameState
    // but their UI is non-combat. Route by runPhase.
    if (this.state !== null && this.state.runPhase === "matrix") {
      updateProgramRow([]);
      const matrix = this.state.matrix;
      if (matrix) {
        this.renderer.render(
          renderMatrix(
            matrix,
            this.state.currentNodeIndex,
            this.state.visitedNodes,
            this.layout.cols,
            this.layout.rows,
            this.state.iceRoster[this.state.activeIceIndex] ?? null,
          ),
          ["MATRIX", "", `Node ${this.state.currentNodeIndex + 1}/${matrix.nodes.length}`],
        );
      }
      return;
    }
    if (this.state !== null && this.state.runPhase === "ending") {
      updateProgramRow([]);
      this.renderer.render(
        renderEndingScreen(this.state.endingChoice, this.layout.cols, this.layout.rows),
        ["ENDING", "", `Choice: ${this.state.endingChoice ?? "?"}`],
      );
      return;
    }
    if (this.state !== null && this.state.runPhase === "loot") {
      updateProgramRow([]);
      this.renderer.render(
        renderLootScreen(
          this.state.player.hp,
          this.state.player.maxHp,
          this.layout.cols,
          this.layout.rows,
        ),
        ["LOOT", "", "ENTER: continue | ESC: jack out"],
      );
      return;
    }
    if (this.state === null) {
      // Pre-game screen routing
      updateProgramRow([]); // hide row outside combat
      if (this.screen === "menu") {
        this.renderer.render(
          renderMainMenu(
            this.selectedMenuIndex,
            this.layout.cols,
            this.layout.rows,
            this.hasSaveCache,
            this.saveMetaCache,
          ),
          [
            "MAIN MENU",
            "",
            `Selected: ${this.selectedMenuIndex + 1}/${MENU_OPTIONS.length}`,
          ],
        );
      } else if (this.screen === "mission_select") {
        this.renderer.render(
          renderMissionSelect(MISSIONS, this.selectedMission, this.layout.cols, this.layout.rows),
          [
            "MISSION SELECT",
            "",
            `Selected: ${this.selectedMission + 1}/${MISSIONS.length}`,
          ],
        );
      } else {
        // Stub screens (graphic_novel, continue, settings, credits, hall_of_dead,
        // help, endings, stats)
        const opt = MENU_OPTIONS[this.selectedMenuIndex];
        const label = opt ? opt.label.toUpperCase() : "WET RUN";
        this.renderer.render(
          renderStubScreen(label, this.layout.cols, this.layout.rows),
          ["STUB", "", "Coming soon — Tier 5+"],
        );
      }
      this.syncPhase("menu");
    } else {
      const previous = this.state;
      const iceDelta = this._lastIceHp !== null ? previous.ice.hp - this._lastIceHp : null;
      const playerDelta = this._lastPlayerHp !== null ? previous.player.hp - this._lastPlayerHp : null;
      const mockStatusEffects = mockStatusEffectsForTurn(previous.turnCount);
      this.state = {
        ...this.state,
        grid: renderGrid(
          this.state,
          iceDelta,
          playerDelta,
          mockStatusEffects,
          this.layout.cols,
          this.layout.rows,
        ),
      };
      this.renderer.render(this.state.grid, buildHudLines(this.state));
      // Tier 5.5: tick + composite VFX overlay.
      this.state = {
        ...this.state,
        vfxInstances: tickCombatVfxList(this.state.vfxInstances),
      };
      if (this.state.vfxInstances.length > 0) {
        const composed = composeCombatVfx(
          this.state.grid,
          this.state.vfxInstances,
          this.layout.cols,
          this.layout.rows,
        );
        this.renderer.render(composed, buildHudLines(this.state));
      }
      updateProgramRow(this.state.phase === "combat" ? this.state.deck : []);
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

  /** Read-only phase accessor for e2e/integration tests. */
  getPhase(): GamePhase | null {
    return this.state?.phase ?? null;
  }

  /** Read-only screen accessor for e2e/integration tests. */
  getScreen(): ScreenKind {
    return this.screen;
  }

  /** External entry point for touch gamepad program buttons.
   * Resolves hand index → programId via resolveProgramSelection, then applies.
   */
  handleProgramButton(handIndex: number): void {
    if (this.state === null) return;
    const action: GameAction = { type: "select_program", handIndex };
    const resolved = resolveProgramSelection(this.state, action);
    if (resolved === null) return;
    const previous = this.state;
    this.state = applyAction(this.state, resolved);
    if (previous.phase === "combat" && this.state.phase === "combat") {
      const iceDelta = this.state.ice.hp - previous.ice.hp;
      if (iceDelta < 0) {
        AudioManager.getInstance().playSfx(SFX_IDS.COMBAT_HIT);
      }
      this._lastIceHp = this.state.ice.hp;
      this._lastPlayerHp = this.state.player.hp;
    }
    this.draw();
  }

  stop(): void {
    this.input.stop();
    this.unmountTouch();
    this.unwatchLayout();
  }
}

function mockStatusEffectsForTurn(turn: number): readonly string[] {
  const pool = ["burn", "stun", "slow", "silence", "vulnerable"];
  const start = turn % pool.length;
  const count = (turn % 3) + 1;
  return pool.slice(start, start + count);
}

function renderGrid(
  state: GameState,
  iceHpDelta: number | null = null,
  playerHpDelta: number | null = null,
  statusEffects: readonly string[] = [],
  cols = 80,
  rows = 50,
) {
  let grid = makeGrid(cols, rows);
  // Layout-relative anchors: ICE block centered horizontally; HUD bars near top-left.
  const iceCol = Math.max(20, Math.floor(cols * 0.45));
  const iceNameCol = iceCol + 1;
  const iceStatusCol = iceCol + Math.min(20, cols - iceCol - 6);
  const turnCol = Math.max(iceNameCol, cols - Math.floor(cols * 0.25));
  const statusArtCol = Math.max(20, Math.floor(cols * 0.45));
  const handRow = Math.max(8, rows - Math.floor(rows * 0.16));
  const artWidth = Math.min(32, cols - statusArtCol - 2);

  grid = setText(grid, 2, 1, `Mission: ${state.mission.title}`, PALETTE.GREEN_NEON);
  grid = setText(grid, 2, 3, state.message, PALETTE.GRAY_LIGHT);

  grid = setText(grid, turnCol, 1, `T${state.turnCount + 1}`, PALETTE.GRAY_LIGHT);

  grid = setText(
    grid,
    2,
    5,
    `P ${healthBar(state.player.hp, state.player.maxHp)} ${state.player.hp}/${state.player.maxHp}`,
    playerHpDelta !== null ? hitFlashColor(playerHpDelta) : healthColor(state.player.hp, state.player.maxHp),
  );

  if (state.phase === "combat" || state.phase === "victory" || state.phase === "defeat") {
    const iceHp = Math.max(0, state.ice.hp);
    const iceRow = Math.floor(rows * 0.44);
    grid = setText(grid, iceCol, iceRow, "[", PALETTE.GRAY_MID);
    grid = setText(grid, iceNameCol, iceRow, state.ice.name.slice(0, 12), iceColor(state.ice.tier));
    const statusSuffix = formatStatusGlyph(statusEffects);
    if (statusSuffix !== "") {
      grid = setText(grid, iceStatusCol, iceRow, statusSuffix, PALETTE.YELLOW_AMBER);
    } else {
      grid = setText(grid, iceStatusCol, iceRow, "]", PALETTE.GRAY_MID);
    }
    grid = setText(
      grid,
      iceCol,
      iceRow + 2,
      `${healthBar(iceHp, 100)} ${iceHp}/100`,
      iceHpDelta !== null ? hitFlashColor(iceHpDelta) : healthColor(iceHp, 100),
    );
  }

  const statusLabel = formatStatusLabel(state.phase);
  if (statusLabel !== "") {
    const statusColor = state.phase === "victory" ? PALETTE.GREEN_NEON : PALETTE.RED_BRIGHT;
    const statusRow = Math.floor(rows * 0.52);
    grid = setText(grid, statusArtCol, statusRow, statusLabel, statusColor);
    if (state.phase === "victory") {
      const art = centerArt(ICE_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= rows) break;
        grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
        y += 1;
      }
    } else if (state.phase === "defeat") {
      const art = centerArt(PLAYER_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= rows) break;
        grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
        y += 1;
      }
    }
  }

  if (state.phase === "combat" && state.deck.length > 0) {
    grid = setText(grid, 2, handRow, "HAND:", PALETTE.YELLOW_AMBER);
    let x = 9;
    for (const p of state.deck) {
      if (x >= cols - 6) break;
      const label = `[${p.id.slice(0, 4)}]`;
      grid = setText(grid, x, handRow, label, PALETTE.CYAN_LIGHT);
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
