# Wet Run — UI Intuition Evaluation (2026-10-24)

## Method
- 10-axis rubric: R1-R4 (retro roguelike UI), U1-U3 (modern UX), A1-A3 (accessibility)
- Code review: `web/src/renderer/menu_main.ts`, `matrix.ts`, `hud.ts`, `canvas.ts`, `touch.ts`, `main.ts`
- Live verification: Playwright E2E on desktop + mobile-portrait-chromium

## Results: 7 Strong / 2 Partial / 1 Issue

### Strong (7)

**R1 — ASCII grid legibility**: monospace `JetBrains Mono` at 12-16px/cell, DPR scaling, `textBaseline: top`. Zero text clipping.

**R2 — Color discipline**: 14-color Gibson palette (neon green/amber/cyan on near-black). HP bar gradient (cyan→green), alarm amber→red threshold at 50%/75%. No color-only information.

**R3 — Consistent navigation**: `▸` marker + `[N]` numbering across menu/mission-select/matrix. Same convention in all 3 screens. Footer always `ESC: back` / `↑↓: navigate | ENTER: launch`.

**R4 — Combat HUD**: 1-line status bar (HP/ALM/CR/CB/BOSS PHASE). Conditional rendering — combo only when >1, boss phase only when active. Overflow guard prevents HUD clipping.

**U1 — Immediate feedback**: stub screens show `[ Coming soon — Tier 5+ ]` for deferred options. Status message line for locked selections. Loading text on boot.

**U2 — Responsive layout**: 3 breakpoints (compact 40×60 / standard 50×80 / landscape 80×50). Auto-switch on `orientationchange`/`resize`. Mobile gamepad auto-mounts on `pointer: coarse`.

**A1 — Input redundancy**: keyboard (arrows/enter/1-9) + gamepad + touch all wired. Same `GameAction` type flows through all three input paths.

### Partial (2)

**U3 — Visual hierarchy**: menu uses `[N]` prefix + `▸` marker + color shift. But mission-select drops the `[N]` prefix (uses `1. ` instead) and matrix drops numbering entirely (uses `[i]` bracket). Inconsistent numbering convention across screens.

**A2 — Screen reader support**: no `role`/`aria-label` attributes on canvas (canvas is a game, not a widget — acceptable). But stub screens and error states have no textual alternative for screen readers.

### Issue (1)

**A3 — Touch target sizing**: virtual gamepad buttons are 1×1 grid cell (8×16px CSS). Below WCAG 44×44px minimum for touch targets. On a 393×851 phone screen, the D-pad is ~32×48px total (4 cells) — the individual arrow buttons are effectively 8px wide. Fingers miss.

**Fix**: increase gamepad cell size on touch (compact breakpoint uses 12×20px cells → 48×80px D-pad), or add touch padding around buttons.

## Verification

```
Mobile E2E:  40/40 passed (Pixel 5, 393×851)
Desktop E2E: 36/36 passed
touch_input: 4 passed (mobile) / 4 skipped (desktop)
```

## Decision

A3 (touch target size) is the only actionable issue. U3 (numbering inconsistency) is cosmetic — fix only if time permits. A2 (screen reader) is out of scope for an ASCII canvas game.