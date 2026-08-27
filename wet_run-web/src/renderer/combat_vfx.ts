/** Combat VFX system (Tier 5.5, Stage 2).
 *
 * Per-event VFX instances with tick-based animation. Each instance has a
 * kind, a tick counter, a duration, and a payload (text). Instances are
 * ticked per draw() and expired when duration reaches 0.
 *
 * Visual effects (all ASCII, ASCII art embedded):
 * - card_use:    projectile line → target
 * - card_hit:    burst particles + flash
 * - ice_hit:     full-row red flash
 * - player_hit:  screen shake (canvas offset)
 * - status_apply: status glyph + label
 * - victory:     ice defeat art + rotating stars
 * - defeat:      player defeat art + red flash
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

export type CombatVfxKind =
  | "card_use"
  | "card_hit"
  | "ice_hit"
  | "player_hit"
  | "status_apply"
  | "victory"
  | "defeat"
  | "boss_phase_1"
  | "boss_phase_2"
  | "boss_phase_3"
  | "boss_phase_4";

export interface CombatVfxInstance {
  readonly id: number;
  readonly kind: CombatVfxKind;
  /** Tick counter (0 = spawned, increments each draw). */
  readonly tick: number;
  /** Total ticks before expiration. */
  readonly duration: number;
  /** Optional metadata: program name, status kind, etc. */
  readonly payload: string;
  /** Optional row offset for movement effects (projectile). */
  readonly startRow?: number;
  readonly targetRow?: number;
}

let nextVfxId = 1;

/** Create a new VFX instance (auto-assigns id, tick=0). */
export function triggerCombatVfx(
  kind: CombatVfxKind,
  payload: string = "",
  duration: number = 4,
  startRow?: number,
  targetRow?: number,
): CombatVfxInstance {
  return {
    id: nextVfxId++,
    kind,
    tick: 0,
    duration,
    payload,
    startRow,
    targetRow,
  };
}

/** Tick a VFX instance. Returns the updated instance, or null if expired. */
export function tickCombatVfx(instance: CombatVfxInstance): CombatVfxInstance | null {
  const nextTick = instance.tick + 1;
  if (nextTick >= instance.duration) return null;
  return { ...instance, tick: nextTick };
}

/** Tick a list of VFX instances, returning the survivors. */
export function tickCombatVfxList(
  list: ReadonlyArray<CombatVfxInstance>,
): ReadonlyArray<CombatVfxInstance> {
  return list.map(tickCombatVfx).filter((v): v is CombatVfxInstance => v !== null);
}

/** Render a single VFX frame into a grid overlay.
 *
 * The function writes the effect's visual at its current tick. The caller
 * is responsible for compositing this over the base combat grid.
 */
export function renderCombatVfx(instance: CombatVfxInstance, cols: number, rows: number): Grid {
  let grid = makeGrid(cols, rows);
  const t = instance.tick;
  const dur = instance.duration;
  const progress = dur > 0 ? t / dur : 0;

  switch (instance.kind) {
    case "card_use": {
      // Projectile line: moves from startRow → targetRow over ticks.
      const row = instance.startRow != null && instance.targetRow != null
        ? Math.round(instance.startRow + (instance.targetRow - instance.startRow) * progress)
        : rows / 2;
      const col = Math.floor(cols * 0.2 + (cols * 0.6) * progress);
      grid = setText(grid, col, row, "→", PALETTE.YELLOW_AMBER);
      grid = setText(grid, col - 2, row, "-", PALETTE.YELLOW_AMBER);
      grid = setText(grid, col - 4, row, "-", PALETTE.GRAY_DARK);
      // Payload (program name) at top of grid
      grid = setText(grid, 2, 1, `[${instance.payload}]`, PALETTE.GREEN_NEON);
      return grid;
    }
    case "card_hit": {
      // Burst particles around impact point.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      grid = setText(grid, cx, cy, "*", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx - 1, cy, "*", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx + 1, cy, "*", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx, cy - 1, "✶", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx, cy + 1, "✶", PALETTE.YELLOW_AMBER);
      if (t === dur - 1) {
        grid = setText(grid, cx - 2, cy - 1, "╲", PALETTE.YELLOW_AMBER);
        grid = setText(grid, cx + 2, cy - 1, "╱", PALETTE.YELLOW_AMBER);
        grid = setText(grid, cx - 2, cy + 1, "╱", PALETTE.YELLOW_AMBER);
        grid = setText(grid, cx + 2, cy + 1, "╲", PALETTE.YELLOW_AMBER);
      }
      return grid;
    }
    case "ice_hit": {
      // Full-row red flash on first tick, then fade.
      const flashRow = instance.targetRow ?? Math.floor(rows * 0.4);
      const flashColor = t === 0 ? PALETTE.RED_BRIGHT : PALETTE.GRAY_MID;
      const flashChar = "█";
      for (let x = 2; x < cols - 2; x++) {
        grid = setText(grid, x, flashRow, flashChar, flashColor);
        grid = setText(grid, x, flashRow + 1, flashChar, flashColor);
      }
      grid = setText(grid, 2, 1, `HIT! -${instance.payload}`, PALETTE.RED_BRIGHT);
      return grid;
    }
    case "player_hit": {
      // Screen shake: shift everything 1px (just text overlay).
      const shakeRow = Math.floor(rows * 0.6);
      const shakeCol = t % 2; // alternate 0/1
      grid = setText(grid, 2 + shakeCol, shakeRow, "█▒▒▒[HP CRIT]▒▒▒█", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 1, "!! DAMAGE !!", PALETTE.RED_BRIGHT);
      return grid;
    }
    case "status_apply": {
      const statusRow = Math.floor(rows * 0.3);
      const statusCol = Math.floor(cols / 2) - 8;
      grid = setText(grid, statusCol, statusRow, `[${instance.payload} applied]`, PALETTE.YELLOW_AMBER);
      grid = setText(grid, statusCol, statusRow + 1, "▒▒▒▒▒▒▒▒▒▒▒▒▒▒", PALETTE.YELLOW_AMBER);
      return grid;
    }
    case "victory": {
      // Ice defeat art + rotating stars.
      const cx = Math.floor(cols / 2);
      const stars = ["✦", "✧", "✶", "✷", "★"];
      const star = stars[t % stars.length] ?? "✦";
      grid = setText(grid, cx - 5, 1, `* ${star} VICTORY ${star} *`, PALETTE.GREEN_NEON);
      grid = setText(grid, 2, 3, "╔══════════════════╗", PALETTE.GREEN_NEON);
      grid = setText(grid, 2, 4, "║   ICE DEFEATED   ║", PALETTE.GREEN_NEON);
      grid = setText(grid, 2, 5, "╚══════════════════╝", PALETTE.GREEN_NEON);
      return grid;
    }
    case "defeat": {
      // Player defeat art + red flash.
      const cx = Math.floor(cols / 2);
      grid = setText(grid, cx - 4, 1, "!!! FLATLINE !!!", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 3, "╔══════════════════╗", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 4, "║  PLAYER DEFEAT   ║", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 5, "╚══════════════════╝", PALETTE.RED_BRIGHT);
      // Red rows fade out
      if (t < dur - 1) {
        for (let x = 0; x < cols; x++) {
          grid = setText(grid, x, rows - 2, "▓", PALETTE.RED_BRIGHT);
        }
      }
      return grid;
    }
    case "boss_phase_1":
    case "boss_phase_2":
    case "boss_phase_3":
    case "boss_phase_4": {
      // Boss phase transition VFX (ADR-0149). Distinct color + icon + message per phase.
      const phase = parseInt(instance.kind.slice(-1), 10) as 1 | 2 | 3 | 4;
      // Per-phase config: color, icon, label, descriptive message.
      // - Phase 1 (>75% HP): calm sentinel, gray-cyan
      // - Phase 2 (50-75% HP): alert, yellow-amber
      // - Phase 3 (25-50% HP): enraged, red-deep + magic effects
      // - Phase 4 (<25% HP): desperate, magenta+cyan pulse
      const phaseConfig: Record<number, { color: string; icon: string; label: string; message: string }> = {
        1: { color: PALETTE.CYAN_LIGHT, icon: "⚡", label: "PHASE 1", message: "Sentinel scanning..." },
        2: { color: PALETTE.YELLOW_AMBER, icon: "▲", label: "PHASE 2", message: "ICE alert — defenses rising!" },
        3: { color: PALETTE.RED_BRIGHT, icon: "✶", label: "PHASE 3", message: "ICE enrages — full assault!" },
        4: { color: PALETTE.MAGENTA_NEON, icon: "★", label: "PHASE 4", message: "Desperation — fatal protocols!" },
      };
      const cfg = phaseConfig[phase] ?? phaseConfig[1]!;
      const cx = Math.floor(cols / 2);
      const header = `${cfg.icon} BOSS ${cfg.label} ${cfg.icon}`;
      grid = setText(grid, Math.max(2, cx - Math.floor(header.length / 2)), 1, header, cfg.color);
      grid = setText(grid, Math.max(2, cx - 10), 3, "╔══════════════╗", cfg.color);
      grid = setText(grid, Math.max(2, cx - 10), 4, `║ ${cfg.message.padEnd(14)} ║`, cfg.color);
      grid = setText(grid, Math.max(2, cx - 10), 5, "╚══════════════╝", cfg.color);
      // Phase-specific effects overlay
      if (phase === 3) {
        // Enrage: red flicker row
        if (t === 0 || t === 2) {
          for (let x = 4; x < cols - 4; x++) {
            grid = setText(grid, x, 7, "✶", PALETTE.RED_BRIGHT);
          }
        }
      } else if (phase === 4) {
        // Desperate: cyan/magenta pulse
        if (t % 2 === 0) {
          for (let x = 4; x < cols - 4; x += 2) {
            grid = setText(grid, x, 7, "★", PALETTE.MAGENTA_NEON);
          }
        }
      }
      return grid;
    }
  }
}

/** Composite multiple VFX instances over a base grid (later instances override earlier).
 * Note: this returns a NEW grid (immutable).
 */
export function composeCombatVfx(
  baseGrid: Grid,
  instances: ReadonlyArray<CombatVfxInstance>,
  cols: number,
  rows: number,
): Grid {
  let out = baseGrid;
  for (const inst of instances) {
    const overlay = renderCombatVfx(inst, cols, rows);
    out = compositeGrid(out, overlay, cols, rows);
  }
  return out;
}

/** Overlay `overlay` onto `base` (overlay takes precedence where set). */
function compositeGrid(base: Grid, overlay: Grid, cols: number, rows: number): Grid {
  // Grid is immutable; build a new one copying non-empty overlay cells.
  // We iterate overlay cells; any cell with a non-space char overrides base.
  // Optimization: short-circuit if overlay cell is space.
  let result = base;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const overlayCell = overlay.get(x, y);
      if (!overlayCell || overlayCell.char === " ") continue;
      const baseCell = base.get(x, y);
      if (baseCell && baseCell.char === overlayCell.char && baseCell.fg === overlayCell.fg) {
        continue; // identical, skip
      }
      // Reconstruct cell with overlay color (same char).
      result = setText(result, x, y, overlayCell.char, overlayCell.fg);
    }
  }
  return result;
}