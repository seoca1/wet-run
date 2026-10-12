/** Scene / outcome / matrix VFX renderers.
 *
 * Split from combat_vfx.ts per ADR-0110. Owns the ICE banner, boss phase,
 * victory / defeat art, and matrix (jack-in / jack-out / room / data) effect
 * kinds. Returns null for kinds owned by combat_vfx_render_combat.ts so the
 * dispatcher can fall through.
 */
import type { Grid } from "../core/types.ts";
import { setText } from "../core/grid.ts";
import { PALETTE, resolveColorHint } from "./palette.ts";
import type { VfxRenderCtx } from "./combat_vfx_core.ts";

/** Render a scene / outcome / matrix VFX frame, or null if the kind is not
 * handled here (combat / damage / status kinds live in the combat renderer). */
export function renderSceneVfx(ctx: VfxRenderCtx, grid: Grid): Grid | null {
  const { instance, cols, rows, t, dur } = ctx;

  switch (instance.kind) {
    case "ice_intro": {
      const cx = Math.floor(cols / 2);
      const iceName = instance.payload || "ICE";
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        1,
        "┌──────────────────┐",
        PALETTE.RED_BRIGHT,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        2,
        `│ INCOMING: ${iceName.padEnd(8)} │`,
        PALETTE.RED_BRIGHT,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        3,
        "└──────────────────┘",
        PALETTE.RED_BRIGHT,
      );
      const scanLines = ["[ scanning... ]", "[ scanning... ]", "[ DETECTED ]"];
      grid = setText(
        grid,
        Math.max(2, cx - 9),
        5,
        scanLines[Math.min(t, 2)] ?? "",
        PALETTE.YELLOW_AMBER,
      );
      return grid;
    }
    case "ice_death": {
      const cx = Math.floor(cols / 2);
      const iceName = instance.payload || "ICE";
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        1,
        `▼ ${iceName} OFFLINE ▼`,
        PALETTE.GRAY_LIGHT,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        3,
        "╔══════════════════╗",
        PALETTE.GRAY_LIGHT,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        4,
        "║   CONNECTION     ║",
        PALETTE.GRAY_LIGHT,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        5,
        "║     SEVERED      ║",
        PALETTE.GRAY_LIGHT,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        6,
        "╚══════════════════╝",
        PALETTE.GRAY_LIGHT,
      );
      return grid;
    }
    case "boss_phase_transition": {
      const phase = (instance.payloadNum ?? 1) as 1 | 2 | 3 | 4;
      const phaseConfig: Record<
        number,
        { color: string; icon: string; label: string; message: string }
      > = {
        1: {
          color: PALETTE.CYAN_LIGHT,
          icon: "⚡",
          label: "PHASE 1",
          message: "Sentinel scanning...",
        },
        2: {
          color: PALETTE.YELLOW_AMBER,
          icon: "▲",
          label: "PHASE 2",
          message: "ICE alert — defenses rising!",
        },
        3: {
          color: PALETTE.RED_BRIGHT,
          icon: "✶",
          label: "PHASE 3",
          message: "ICE enrages — full assault!",
        },
        4: {
          color: PALETTE.MAGENTA_NEON,
          icon: "★",
          label: "PHASE 4",
          message: "Desperation — fatal protocols!",
        },
      };
      const cfg = phaseConfig[phase] ?? phaseConfig[1]!;
      const cx = Math.floor(cols / 2);
      const header = `${cfg.icon} BOSS ${cfg.label} ${cfg.icon}`;
      grid = setText(
        grid,
        Math.max(2, cx - Math.floor(header.length / 2)),
        1,
        header,
        cfg.color,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        3,
        "╔══════════════╗",
        cfg.color,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        4,
        `║ ${cfg.message.padEnd(14)} ║`,
        cfg.color,
      );
      grid = setText(
        grid,
        Math.max(2, cx - 10),
        5,
        "╚══════════════╝",
        cfg.color,
      );
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
      grid = setText(
        grid,
        cx - 5,
        1,
        `* ${star} VICTORY ${star} *`,
        PALETTE.GREEN_NEON,
      );
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
      grid = setText(
        grid,
        Math.floor(cols / 2) - 4,
        Math.floor(rows / 2),
        "JACK IN",
        PALETTE.CYAN_LIGHT,
      );
      return grid;
    }
    case "jackout_whiteout": {
      // Whiteout flash + sparse particles.
      const fade = t === 0 ? PALETTE.HIT_FLASH_COLOR : PALETTE.GRAY_LIGHT;
      grid = setText(
        grid,
        Math.floor(cols / 2) - 4,
        Math.floor(rows / 2),
        "JACK OUT",
        fade,
      );
      if (t === 0) {
        for (let x = 0; x < cols; x += 4) {
          grid = setText(
            grid,
            x,
            Math.floor(rows / 2) - 1,
            "·",
            PALETTE.HIT_FLASH_COLOR,
          );
        }
      } else if (t === 1) {
        for (let x = 0; x < cols; x += 4) {
          grid = setText(
            grid,
            x,
            Math.floor(rows / 2) + 1,
            "·",
            PALETTE.GRAY_LIGHT,
          );
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
        grid = setText(
          grid,
          cx - 6,
          cy - 3,
          "DATA FRAGMENT",
          PALETTE.TIER_GOLD,
        );
      }
      return grid;
    }
    default:
      return null;
  }
}
