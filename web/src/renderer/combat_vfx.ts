/** Combat VFX system (Tier 5.5 + Tier 5.6 + Tier 6 effect schema).
 *
 * Per-event VFX instances with tick-based animation. Each instance has a
 * kind, a tick counter, a duration, and a payload (text). Instances are
 * ticked per draw() and expired when duration reaches 0.
 *
 * Effect kinds are the canonical taxonomy shared with the Python prototype
 * (see prototype/data/effects.json + ADR-0210). The schema is exported via
 * scripts/export_effects.py and consumed via src/data/effects.d.ts.
 *
 * Tier 6 (this commit) adds 12 v2 effects (8 skill + 4 matrix) backported
 * from Python's effects_vfx_animations.py + effects_vfx_compose.py.
 *
 * Visual effects (all ASCII, ASCII art embedded):
 * - attack:                projectile line → target (Tier 5.5)
 * - heavy_attack:          charge→slam→shockwave (Tier 6)
 * - pierce:                arrow passes through target (Tier 6)
 * - multi_hit:             3 quick strikes (Tier 6)
 * - dot:                   toxic particles around target (Tier 6)
 * - shield:                shield block glyph + bracket (Tier 5.6)
 * - heal:                  +HP rising text + green particle (Tier 5.6)
 * - regen:                 gentle pulse of + signs (Tier 6)
 * - buff / debuff:         up/down arrow + label (Tier 5.6)
 * - stun:                  status glyph + stars (Tier 5.6)
 * - counter:               shield bash returning damage (Tier 6)
 * - lifesteal:             red line target→self + heal (Tier 6)
 * - detect:                scanning reticle (Tier 6)
 * - ice_hit:               full-row red flash (Tier 5.5)
 * - player_hit:            screen shake (canvas offset) (Tier 5.5)
 * - critical_hit:          larger damage + CRIT tag (Tier 5.6)
 * - status_apply:          status glyph + label (Tier 5.5)
 * - ice_intro:             ICE-typed ASCII banner (Tier 5.6)
 * - ice_death:             ICE-typed ASCII defeat banner (Tier 5.6)
 * - boss_phase_transition: payload-driven phase 1..4 VFX (Tier 5.6)
 * - victory:               ice defeat art + rotating stars (Tier 5.5)
 * - defeat:                player defeat art + red flash (Tier 5.5)
 * - jackin_glitch:         cyan glitch particles (Tier 6 matrix)
 * - jackout_whiteout:      whiteout flash + particles (Tier 6 matrix)
 * - room_flash:            brief color flash on room entry (Tier 6 matrix)
 * - data_acquired:         gold particle burst + flash (Tier 6 matrix)
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE, resolveColorHint } from "./palette.ts";

export type CombatVfxKind =
  | "attack"
  | "heavy_attack"
  | "pierce"
  | "multi_hit"
  | "dot"
  | "shield"
  | "heal"
  | "regen"
  | "buff"
  | "debuff"
  | "stun"
  | "counter"
  | "lifesteal"
  | "detect"
  | "ice_hit"
  | "player_hit"
  | "critical_hit"
  | "status_apply"
  | "ice_intro"
  | "ice_death"
  | "boss_phase_transition"
  | "victory"
  | "defeat"
  | "jackin_glitch"
  | "jackout_whiteout"
  | "room_flash"
  | "data_acquired";

export interface CombatVfxInstance {
  readonly id: number;
  readonly kind: CombatVfxKind;
  /** Tick counter (0 = spawned, increments each draw). Derived from elapsedMs / WEB_TICK_MS. */
  readonly tick: number;
  /** Total ticks before expiration. Derived from durationMs / WEB_TICK_MS at spawn. */
  readonly duration: number;
  /** Total lifetime in milliseconds (canonical, derived from schema's duration_ms). */
  readonly durationMs: number;
  /** Wall-clock elapsed time in ms since spawn. Drives ms-precise expiry. */
  readonly elapsedMs: number;
  /** Optional metadata: program name, status kind, ice type, etc. */
  readonly payload: string;
  /** Numeric metadata: damage amount, boss phase, etc. Parsed as needed. */
  readonly payloadNum?: number;
  /** Optional row offset for movement effects (projectile). */
  readonly startRow?: number;
  readonly targetRow?: number;
}

/** Web frame budget (ms per tick). 16ms ≈ 60fps. */
export const WEB_TICK_MS = 16;

let nextVfxId = 1;

/** Create a new VFX instance (auto-assigns id, tick=0, elapsedMs=0). */
export function triggerCombatVfx(
  kind: CombatVfxKind,
  payload: string = "",
  duration: number = 4,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): CombatVfxInstance {
  const durationMs = Math.max(0, duration) * WEB_TICK_MS;
  return {
    id: nextVfxId++,
    kind,
    tick: 0,
    duration,
    durationMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** Create a VFX instance with explicit ms duration (ADR-0210 canonical).
 *
 * Use this when you have the schema's duration_ms value and want ms-precise
 * expiry. The `tick` and `duration` fields are derived for backward-compat
 * with the renderer switch (which reads tick to interpolate animation).
 */
export function triggerCombatVfxMs(
  kind: CombatVfxKind,
  payload: string = "",
  durationMs: number = 80,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): CombatVfxInstance {
  const clampedMs = Math.max(0, durationMs);
  const tickDuration = Math.ceil(clampedMs / WEB_TICK_MS);
  return {
    id: nextVfxId++,
    kind,
    tick: 0,
    duration: tickDuration,
    durationMs: clampedMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** Advance a VFX instance by `deltaMs` real-world milliseconds.
 *
 * Returns the updated instance, or null if it has reached its duration.
 * The `tick` field is derived from elapsedMs (floor(elapsedMs / WEB_TICK_MS))
 * so renderers stay frame-aligned.
 *
 * Tier 7: ms-precise expiry replaces the legacy tick-based advance.
 * Falls back to duration-based expiry when durationMs is 0 (legacy path).
 */
export function advanceVfxBy(instance: CombatVfxInstance, deltaMs: number): CombatVfxInstance | null {
  if (deltaMs < 0) return instance;
  const elapsedMs = instance.elapsedMs + deltaMs;
  // ms-precise expiry: drop when wall-clock exceeds durationMs.
  if (instance.durationMs > 0 && elapsedMs >= instance.durationMs) {
    return null;
  }
  // Legacy tick-based expiry (only if durationMs was unset = 0).
  const tick = Math.floor(elapsedMs / WEB_TICK_MS);
  if (instance.durationMs === 0 && tick >= instance.duration) {
    return null;
  }
  return { ...instance, elapsedMs, tick };
}

/** Tick a VFX instance. Returns the updated instance, or null if expired.
 *
 * Legacy API — increments tick by 1. Prefer advanceVfxBy(instance, deltaMs)
 * for ms-precise timing. Kept for backward compatibility with existing
 * call sites that don't have a deltaMs (e.g., headless test loops).
 */
export function tickCombatVfx(instance: CombatVfxInstance): CombatVfxInstance | null {
  return advanceVfxBy(instance, WEB_TICK_MS);
}

/** Advance a list of VFX instances by deltaMs. Returns survivors. */
export function advanceVfxListBy(
  list: ReadonlyArray<CombatVfxInstance>,
  deltaMs: number,
): ReadonlyArray<CombatVfxInstance> {
  return list
    .map((v) => advanceVfxBy(v, deltaMs))
    .filter((v): v is CombatVfxInstance => v !== null);
}

/** Tick a list of VFX instances by one tick (legacy API). */
export function tickCombatVfxList(
  list: ReadonlyArray<CombatVfxInstance>,
): ReadonlyArray<CombatVfxInstance> {
  return advanceVfxListBy(list, WEB_TICK_MS);
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
    case "attack": {
      // Projectile line: moves from startRow → targetRow over ticks.
      const row = instance.startRow != null && instance.targetRow != null
        ? Math.round(instance.startRow + (instance.targetRow - instance.startRow) * progress)
        : rows / 2;
      const col = Math.floor(cols * 0.2 + (cols * 0.6) * progress);
      grid = setText(grid, col, row, "→", PALETTE.YELLOW_AMBER);
      grid = setText(grid, col - 2, row, "-", PALETTE.YELLOW_AMBER);
      grid = setText(grid, col - 4, row, "-", PALETTE.GRAY_DARK);
      grid = setText(grid, 2, 1, `[${instance.payload}]`, PALETTE.GREEN_NEON);
      return grid;
    }
    case "heal": {
      const cx = Math.floor(cols / 2);
      const amount = instance.payloadNum ?? 0;
      grid = setText(grid, cx - 8, 1, `+${amount} HP`, PALETTE.GREEN_NEON);
      grid = setText(grid, cx - 4, Math.floor(rows / 2), "+", PALETTE.GREEN_NEON);
      grid = setText(grid, cx - 6, Math.floor(rows / 2) - 1, "·", PALETTE.GREEN_NEON);
      grid = setText(grid, cx - 2, Math.floor(rows / 2) - 1, "·", PALETTE.GREEN_NEON);
      grid = setText(grid, cx, Math.floor(rows / 2) - 1, "+", PALETTE.GREEN_NEON);
      if (t === dur - 1) {
        grid = setText(grid, cx - 5, Math.floor(rows / 2) - 2, "♥", PALETTE.GREEN_NEON);
      }
      return grid;
    }
    case "shield": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      grid = setText(grid, cx - 5, cy, "[▓▓▓▓▓▓▓▓▓▓]", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx - 2, cy - 1, "❖", PALETTE.YELLOW_AMBER);
      return grid;
    }
    case "buff": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      grid = setText(grid, cx - 4, cy, `↑ ${instance.payload} ↑`, PALETTE.GREEN_NEON);
      if (t === Math.floor(dur / 2)) {
        grid = setText(grid, cx - 1, cy - 1, "▲", PALETTE.GREEN_NEON);
      }
      return grid;
    }
    case "debuff": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      grid = setText(grid, cx - 4, cy, `↓ ${instance.payload} ↓`, PALETTE.RED_BRIGHT);
      if (t === Math.floor(dur / 2)) {
        grid = setText(grid, cx - 1, cy - 1, "▼", PALETTE.RED_BRIGHT);
      }
      return grid;
    }
    case "stun": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      grid = setText(grid, cx - 2, cy, "✦ STUN ✦", PALETTE.YELLOW_AMBER);
      const stars = ["✦", "✧", "✶", "✷"];
      grid = setText(grid, cx - 6, cy - 1, stars[t % stars.length] ?? "✦", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx + 5, cy - 1, stars[(t + 2) % stars.length] ?? "✦", PALETTE.YELLOW_AMBER);
      return grid;
    }
    case "ice_hit": {
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
      const shakeRow = Math.floor(rows * 0.6);
      const shakeCol = t % 2;
      grid = setText(grid, 2 + shakeCol, shakeRow, "█▒▒▒[HP CRIT]▒▒▒█", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 1, "!! DAMAGE !!", PALETTE.RED_BRIGHT);
      return grid;
    }
    case "critical_hit": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const damage = instance.payloadNum ?? 0;
      grid = setText(grid, cx - 8, 1, `* CRIT! -${damage} *`, PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx, cy, "✦", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx - 1, cy, "✶", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx + 1, cy, "✶", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx, cy - 1, "✷", PALETTE.YELLOW_AMBER);
      grid = setText(grid, cx, cy + 1, "✷", PALETTE.YELLOW_AMBER);
      if (t === dur - 1) {
        grid = setText(grid, cx - 2, cy - 1, "✸", PALETTE.YELLOW_AMBER);
        grid = setText(grid, cx + 2, cy - 1, "✸", PALETTE.YELLOW_AMBER);
        grid = setText(grid, cx - 2, cy + 1, "✸", PALETTE.YELLOW_AMBER);
        grid = setText(grid, cx + 2, cy + 1, "✸", PALETTE.YELLOW_AMBER);
      }
      return grid;
    }
    case "status_apply": {
      const statusRow = Math.floor(rows * 0.3);
      const statusCol = Math.floor(cols / 2) - 8;
      grid = setText(grid, statusCol, statusRow, `[${instance.payload} applied]`, PALETTE.YELLOW_AMBER);
      grid = setText(grid, statusCol, statusRow + 1, "▒▒▒▒▒▒▒▒▒▒▒▒▒▒", PALETTE.YELLOW_AMBER);
      return grid;
    }
    case "ice_intro": {
      const cx = Math.floor(cols / 2);
      const iceName = instance.payload || "ICE";
      grid = setText(grid, Math.max(2, cx - 10), 1, "┌──────────────────┐", PALETTE.RED_BRIGHT);
      grid = setText(grid, Math.max(2, cx - 10), 2, `│ INCOMING: ${iceName.padEnd(8)} │`, PALETTE.RED_BRIGHT);
      grid = setText(grid, Math.max(2, cx - 10), 3, "└──────────────────┘", PALETTE.RED_BRIGHT);
      const scanLines = ["[ scanning... ]", "[ scanning... ]", "[ DETECTED ]"];
      grid = setText(grid, Math.max(2, cx - 9), 5, scanLines[Math.min(t, 2)] ?? "", PALETTE.YELLOW_AMBER);
      return grid;
    }
    case "ice_death": {
      const cx = Math.floor(cols / 2);
      const iceName = instance.payload || "ICE";
      grid = setText(grid, Math.max(2, cx - 10), 1, `▼ ${iceName} OFFLINE ▼`, PALETTE.GRAY_LIGHT);
      grid = setText(grid, Math.max(2, cx - 10), 3, "╔══════════════════╗", PALETTE.GRAY_LIGHT);
      grid = setText(grid, Math.max(2, cx - 10), 4, "║   CONNECTION     ║", PALETTE.GRAY_LIGHT);
      grid = setText(grid, Math.max(2, cx - 10), 5, "║     SEVERED      ║", PALETTE.GRAY_LIGHT);
      grid = setText(grid, Math.max(2, cx - 10), 6, "╚══════════════════╝", PALETTE.GRAY_LIGHT);
      return grid;
    }
    case "boss_phase_transition": {
      const phase = (instance.payloadNum ?? 1) as 1 | 2 | 3 | 4;
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
      if (phase === 3) {
        if (t === 0 || t === 2) {
          for (let x = 4; x < cols - 4; x++) {
            grid = setText(grid, x, 7, "✶", PALETTE.RED_BRIGHT);
          }
        }
      } else if (phase === 4) {
        if (t % 2 === 0) {
          for (let x = 4; x < cols - 4; x += 2) {
            grid = setText(grid, x, 7, "★", PALETTE.MAGENTA_NEON);
          }
        }
      }
      return grid;
    }
    case "victory": {
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
      const cx = Math.floor(cols / 2);
      grid = setText(grid, cx - 4, 1, "!!! FLATLINE !!!", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 3, "╔══════════════════╗", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 4, "║  PLAYER DEFEAT   ║", PALETTE.RED_BRIGHT);
      grid = setText(grid, 2, 5, "╚══════════════════╝", PALETTE.RED_BRIGHT);
      if (t < dur - 1) {
        for (let x = 0; x < cols; x++) {
          grid = setText(grid, x, rows - 2, "▓", PALETTE.RED_BRIGHT);
        }
      }
      return grid;
    }
    case "heavy_attack": {
      // Charge → slam → shockwave (longer duration than attack).
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const chargeFrame = Math.floor(t / (dur / 4));
      if (chargeFrame <= 1) {
        grid = setText(grid, cx - 4, cy, "<===", PALETTE.BUFF_COLOR);
      } else if (chargeFrame === 2) {
        grid = setText(grid, cx - 5, cy, "<=====", PALETTE.ORANGE);
      } else {
        grid = setText(grid, cx - 5, cy, "*SLAM*", PALETTE.RED_BRIGHT);
        for (let x = 4; x < cols - 4; x += 3) {
          grid = setText(grid, x, cy + 2, "·", PALETTE.MAGENTA_NEON);
        }
      }
      grid = setText(grid, 2, 1, `HEAVY -${instance.payloadNum ?? 0}`, PALETTE.ORANGE);
      return grid;
    }
    case "pierce": {
      // Arrow passes through target (left → right).
      const cy = Math.floor(rows / 2);
      const col = Math.floor(cols * 0.1 + (cols * 0.8) * progress);
      grid = setText(grid, col, cy, "====>", PALETTE.WARM);
      grid = setText(grid, col - 6, cy, "----", PALETTE.GRAY_DARK);
      if (t === Math.floor(dur / 2)) {
        grid = setText(grid, 2, 1, `PIERCE -${instance.payloadNum ?? 0}`, PALETTE.YELLOW_AMBER);
      }
      return grid;
    }
    case "multi_hit": {
      // 3 quick strikes with staggered columns.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const hit = Math.floor(t / (dur / 3));
      const strikes = ["[>", "[>>", "[>>>"];
      const colOffset = hit * 2;
      grid = setText(grid, cx - 3 + colOffset, cy, strikes[Math.min(hit, 2)] ?? "[>", PALETTE.DAMAGE_COLOR);
      grid = setText(grid, cx - 3 + colOffset, cy - 1, "✦", PALETTE.YELLOW_AMBER);
      if (t === dur - 1) {
        grid = setText(grid, cx - 6, cy + 2, `-${instance.payloadNum ?? 0} (${instance.payload || "x3"})`, PALETTE.YELLOW_AMBER);
      }
      return grid;
    }
    case "dot": {
      // Toxic particles around target — pulsing dots.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const ringRadius = 3 + Math.floor(t / (dur / 4));
      const chars = ["·", "•", "·"];
      const ch = chars[t % chars.length] ?? "·";
      for (let i = 0; i < 6; i++) {
        const angle = (Math.PI * 2 * i) / 6 + t * 0.3;
        const dx = Math.round(cx + Math.cos(angle) * ringRadius);
        const dy = Math.round(cy + Math.sin(angle) * ringRadius);
        if (dx >= 0 && dx < cols && dy >= 0 && dy < rows) {
          grid = setText(grid, dx, dy, ch, PALETTE.ICE_FADE_PURPLE);
        }
      }
      grid = setText(grid, cx - 2, cy, "(•)", PALETTE.ICE_FADE_PURPLE);
      grid = setText(grid, 2, 1, `DOT -${instance.payloadNum ?? 0}`, PALETTE.ICE_FADE_PURPLE);
      return grid;
    }
    case "regen": {
      // Gentle pulse of plus signs (heal-over-time tick).
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const pulse = t % 2 === 0 ? "+" : "·";
      grid = setText(grid, cx, cy, pulse, PALETTE.ICE_GREEN_BRIGHT);
      grid = setText(grid, cx - 2, cy, `·${pulse}·`, PALETTE.ICE_GREEN_BRIGHT);
      grid = setText(grid, cx + 2, cy, `·${pulse}·`, PALETTE.ICE_GREEN_BRIGHT);
      grid = setText(grid, cx, cy - 1, pulse, PALETTE.ICE_GREEN_BRIGHT);
      grid = setText(grid, cx, cy + 1, pulse, PALETTE.ICE_GREEN_BRIGHT);
      return grid;
    }
    case "counter": {
      // Shield bash returning damage.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const flipFrame = t < dur / 2;
      if (flipFrame) {
        grid = setText(grid, cx - 3, cy, "❖<<", PALETTE.SHIELD_COLOR);
      } else {
        grid = setText(grid, cx - 3, cy, ">>❖", PALETTE.DAMAGE_COLOR);
      }
      grid = setText(grid, 2, 1, `COUNTER -${instance.payloadNum ?? 0}`, PALETTE.SHIELD_COLOR);
      return grid;
    }
    case "lifesteal": {
      // Red line from target → self, then heal pulse.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      if (t < dur / 2) {
        const phase = t / (dur / 2);
        const arrowCol = Math.floor(cols * 0.7 - (cols * 0.5) * phase);
        grid = setText(grid, arrowCol, cy, "==>", PALETTE.DAMAGE_COLOR);
      } else {
        grid = setText(grid, cx, cy, "+", PALETTE.HEAL_COLOR);
        grid = setText(grid, cx - 2, cy, "·+·", PALETTE.HEAL_COLOR);
      }
      grid = setText(grid, 2, 1, `LIFESTEAL +${instance.payloadNum ?? 0}`, PALETTE.MAGENTA_NEON);
      return grid;
    }
    case "detect": {
      // Scanning reticle — pulsing bracket pattern.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const bracket = t < dur / 2 ? "[<·>]" : "[<!>]";
      grid = setText(grid, cx - 3, cy, bracket, PALETTE.SHIELD_COLOR);
      grid = setText(grid, cx - 3, cy - 1, "·", PALETTE.CYAN_LIGHT);
      grid = setText(grid, cx - 3, cy + 1, "·", PALETTE.CYAN_LIGHT);
      if (t === dur - 1) {
        grid = setText(grid, cx - 3, cy - 3, "REVEALED", PALETTE.YELLOW_AMBER);
      }
      return grid;
    }
    case "jackin_glitch": {
      // Cyan glitch particles spread across grid.
      const glitchChars = ["▓", "▒", "░", "+", "·", "/", "\\"];
      const seedCount = 18;
      for (let i = 0; i < seedCount; i++) {
        const ch = glitchChars[(i + t) % glitchChars.length] ?? "·";
        const x = (i * 7 + t * 13) % cols;
        const y = (i * 11 + t * 17) % rows;
        grid = setText(grid, x, y, ch, PALETTE.ICE_CYAN_DIM);
      }
      grid = setText(grid, Math.floor(cols / 2) - 4, Math.floor(rows / 2), "JACK IN", PALETTE.CYAN_LIGHT);
      return grid;
    }
    case "jackout_whiteout": {
      // Whiteout flash + sparse particles.
      const fade = t === 0 ? PALETTE.HIT_FLASH_COLOR : PALETTE.GRAY_LIGHT;
      grid = setText(grid, Math.floor(cols / 2) - 4, Math.floor(rows / 2), "JACK OUT", fade);
      if (t === 0) {
        for (let x = 0; x < cols; x += 4) {
          grid = setText(grid, x, Math.floor(rows / 2) - 1, "·", PALETTE.HIT_FLASH_COLOR);
        }
      } else if (t === 1) {
        for (let x = 0; x < cols; x += 4) {
          grid = setText(grid, x, Math.floor(rows / 2) + 1, "·", PALETTE.GRAY_LIGHT);
        }
      }
      return grid;
    }
    case "room_flash": {
      // Brief color flash on room entry — fades over duration.
      const flashColor = resolveColorHint(instance.payload || "OLIVE");
      const intensity = Math.max(0, 1 - t / dur);
      if (intensity > 0.5) {
        for (let x = 0; x < cols; x += 6) {
          for (let y = 0; y < rows; y += 4) {
            grid = setText(grid, x, y, "+", flashColor);
          }
        }
      }
      return grid;
    }
    case "data_acquired": {
      // Gold particle burst + flash + text.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const goldChars = ["$", "·", "+", "·"];
      const burst = 14;
      for (let i = 0; i < burst; i++) {
        const angle = (Math.PI * 2 * i) / burst;
        const radius = 2 + t;
        const dx = Math.round(cx + Math.cos(angle) * radius);
        const dy = Math.round(cy + Math.sin(angle) * radius);
        const ch = goldChars[i % goldChars.length] ?? "$";
        if (dx >= 0 && dx < cols && dy >= 0 && dy < rows) {
          grid = setText(grid, dx, dy, ch, PALETTE.TIER_GOLD);
        }
      }
      if (t < 2) {
        grid = setText(grid, cx - 6, cy - 3, "DATA FRAGMENT", PALETTE.TIER_GOLD);
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
  let result = base;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const overlayCell = overlay.get(x, y);
      if (!overlayCell || overlayCell.char === " ") continue;
      const baseCell = base.get(x, y);
      if (baseCell && baseCell.char === overlayCell.char && baseCell.fg === overlayCell.fg) {
        continue;
      }
      result = setText(result, x, y, overlayCell.char, overlayCell.fg);
    }
  }
  return result;
}
