import { writeFileSync } from 'node:fs';
import { PALETTE, applyPaletteMode } from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/renderer/palette.ts';
const lum = (hex: string) => { const n = parseInt(hex.slice(1), 16); const c = [16, 8, 0].map(s => ((n >> s) & 255) / 255).map(v => v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
const ratio = (a: string, b: string) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return Math.round(((x + 0.05) / (y + 0.05)) * 100) / 100; };
const out = [];
for (const mode of ['none', 'deuteranopia', 'protanopia', 'tritanopia'] as const) for (const hc of [false, true]) {
  applyPaletteMode(mode, hc);
  out.push({ mode, highContrast: hc, background: PALETTE.BACKGROUND, ratios: {
    'gate line, nothing-selected prompt, matrix footer (YELLOW_AMBER on BACKGROUND)': ratio(PALETTE.YELLOW_AMBER, PALETTE.BACKGROUND),
    'HUD arrival message (GREEN_NEON on BACKGROUND)': ratio(PALETTE.GREEN_NEON, PALETTE.BACKGROUND),
    'INFO verb rows + details + hints (GRAY_LIGHT on BACKGROUND)': ratio(PALETTE.GRAY_LIGHT, PALETTE.BACKGROUND), 'EXIT verb rows + EXITS line (CYAN_LIGHT on BACKGROUND)': ratio(PALETTE.CYAN_LIGHT, PALETTE.BACKGROUND), 'selected verb row (GREEN_NEON on BACKGROUND)': ratio(PALETTE.GREEN_NEON, PALETTE.BACKGROUND),
  } });
}
applyPaletteMode('none', false);
writeFileSync('/Users/emilio/projects/opencodework/Game/wet_run/docs/design/matrix-encounter-escape-2026-11-01/contrast.json', JSON.stringify(out, null, 2));
console.log(JSON.stringify(out.map(o => [o.mode, o.highContrast, Object.values(o.ratios)])));
