/** Combat / damage / status VFX renderers.
 *
 * Split from combat_vfx.ts per ADR-0110. Owns the hit-flash, damage, and
 * status-glyph effect kinds. Returns null for kinds owned by
 * combat_vfx_render_scene.ts so the dispatcher can fall through.
 */
import type { Grid } from "../core/types.ts";
import { setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";
import type { VfxRenderCtx } from "./combat_vfx_core.ts";

/** Render a combat / damage / status VFX frame, or null if the kind is not
 * handled here (scene / outcome / matrix kinds live in the scene renderer). */
export function renderCombatHitVfx(ctx: VfxRenderCtx, grid: Grid): Grid | null {
  const { instance, cols, rows, t, dur, progress } = ctx;

  switch (instance.kind) {
    case "attack": {
      // Projectile line: moves from startRow → targetRow over ticks.
      const row =
        instance.startRow != null && instance.targetRow != null
          ? Math.round(
              instance.startRow +
                (instance.targetRow - instance.startRow) * progress,
            )
          : rows / 2;
      const col = Math.floor(cols * 0.2 + cols * 0.6 * progress);
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
      grid = setText(
        grid,
        cx - 4,
        Math.floor(rows / 2),
        "+",
        PALETTE.GREEN_NEON,
      );
      grid = setText(
        grid,
        cx - 6,
        Math.floor(rows / 2) - 1,
        "·",
        PALETTE.GREEN_NEON,
      );
      grid = setText(
        grid,
        cx - 2,
        Math.floor(rows / 2) - 1,
        "·",
        PALETTE.GREEN_NEON,
      );
      grid = setText(
        grid,
        cx,
        Math.floor(rows / 2) - 1,
        "+",
        PALETTE.GREEN_NEON,
      );
      if (t === dur - 1) {
        grid = setText(
          grid,
          cx - 5,
          Math.floor(rows / 2) - 2,
          "♥",
          PALETTE.GREEN_NEON,
        );
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
      grid = setText(
        grid,
        cx - 4,
        cy,
        `↑ ${instance.payload} ↑`,
        PALETTE.GREEN_NEON,
      );
      if (t === Math.floor(dur / 2)) {
        grid = setText(grid, cx - 1, cy - 1, "▲", PALETTE.GREEN_NEON);
      }
      return grid;
    }
    case "debuff": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      grid = setText(
        grid,
        cx - 4,
        cy,
        `↓ ${instance.payload} ↓`,
        PALETTE.RED_BRIGHT,
      );
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
      grid = setText(
        grid,
        cx - 6,
        cy - 1,
        stars[t % stars.length] ?? "✦",
        PALETTE.YELLOW_AMBER,
      );
      grid = setText(
        grid,
        cx + 5,
        cy - 1,
        stars[(t + 2) % stars.length] ?? "✦",
        PALETTE.YELLOW_AMBER,
      );
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
      grid = setText(
        grid,
        2,
        1,
        `HIT! -${instance.payload}`,
        PALETTE.RED_BRIGHT,
      );
      return grid;
    }
    case "player_hit": {
      const shakeRow = Math.floor(rows * 0.6);
      const shakeCol = t % 2;
      grid = setText(
        grid,
        2 + shakeCol,
        shakeRow,
        "█▒▒▒[HP CRIT]▒▒▒█",
        PALETTE.RED_BRIGHT,
      );
      grid = setText(grid, 2, 1, "!! DAMAGE !!", PALETTE.RED_BRIGHT);
      return grid;
    }
    case "critical_hit": {
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      const damage = instance.payloadNum ?? 0;
      grid = setText(
        grid,
        cx - 8,
        1,
        `* CRIT! -${damage} *`,
        PALETTE.YELLOW_AMBER,
      );
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
      grid = setText(
        grid,
        statusCol,
        statusRow,
        `[${instance.payload} applied]`,
        PALETTE.YELLOW_AMBER,
      );
      grid = setText(
        grid,
        statusCol,
        statusRow + 1,
        "▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
        PALETTE.YELLOW_AMBER,
      );
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
      grid = setText(
        grid,
        2,
        1,
        `HEAVY -${instance.payloadNum ?? 0}`,
        PALETTE.ORANGE,
      );
      return grid;
    }
    case "pierce": {
      // Arrow passes through target (left → right).
      const cy = Math.floor(rows / 2);
      const col = Math.floor(cols * 0.1 + cols * 0.8 * progress);
      grid = setText(grid, col, cy, "====>", PALETTE.WARM);
      grid = setText(grid, col - 6, cy, "----", PALETTE.GRAY_DARK);
      if (t === Math.floor(dur / 2)) {
        grid = setText(
          grid,
          2,
          1,
          `PIERCE -${instance.payloadNum ?? 0}`,
          PALETTE.YELLOW_AMBER,
        );
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
      grid = setText(
        grid,
        cx - 3 + colOffset,
        cy,
        strikes[Math.min(hit, 2)] ?? "[>",
        PALETTE.DAMAGE_COLOR,
      );
      grid = setText(
        grid,
        cx - 3 + colOffset,
        cy - 1,
        "✦",
        PALETTE.YELLOW_AMBER,
      );
      if (t === dur - 1) {
        grid = setText(
          grid,
          cx - 6,
          cy + 2,
          `-${instance.payloadNum ?? 0} (${instance.payload || "x3"})`,
          PALETTE.YELLOW_AMBER,
        );
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
      grid = setText(
        grid,
        2,
        1,
        `DOT -${instance.payloadNum ?? 0}`,
        PALETTE.ICE_FADE_PURPLE,
      );
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
      grid = setText(
        grid,
        2,
        1,
        `COUNTER -${instance.payloadNum ?? 0}`,
        PALETTE.SHIELD_COLOR,
      );
      return grid;
    }
    case "lifesteal": {
      // Red line from target → self, then heal pulse.
      const cx = Math.floor(cols / 2);
      const cy = Math.floor(rows / 2);
      if (t < dur / 2) {
        const phase = t / (dur / 2);
        const arrowCol = Math.floor(cols * 0.7 - cols * 0.5 * phase);
        grid = setText(grid, arrowCol, cy, "==>", PALETTE.DAMAGE_COLOR);
      } else {
        grid = setText(grid, cx, cy, "+", PALETTE.HEAL_COLOR);
        grid = setText(grid, cx - 2, cy, "·+·", PALETTE.HEAL_COLOR);
      }
      grid = setText(
        grid,
        2,
        1,
        `LIFESTEAL +${instance.payloadNum ?? 0}`,
        PALETTE.MAGENTA_NEON,
      );
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
    default:
      return null;
  }
}
