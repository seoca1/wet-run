# wetrun-web — Browser MVP of Wet Run

> **Tier 1 MVP** of the wet_run browser version per ADR-0199 (proposed).

Browser-native TypeScript implementation of the deck-building ICE-breaking core.
Renders Gibson-flavored ASCII in Canvas2D. Save to localStorage. Static files
for GitHub Pages or itch.io deployment.

## Quick start

```bash
# 1. Export game data from wet_run Python (read-only)
python3 scripts/export_web_data.py

# 2. Install deps (npm/pnpm/yarn)
npm install

# 3. Dev server
npm run dev

# 4. Build for production
npm run build
# Output: dist/ (static files)
```

## Scope (Tier 4 — current build)

- **30 playable missions** (Tier 1-5, surface/mid/deep/core/aftermath/soho zones)
- ASCII Canvas2D renderer (Gibson palette)
- ICE-breaking combat state machine
- **Multi-slot save/load** (4 slots: 1 autosave + 3 manual, with legacy single-slot migration)
- Keyboard input (arrow keys + ENTER + SPACE + ESC)
- **Mobile touch input** (auto-mounts virtual gamepad on `pointer: coarse` devices)
- **BGM audio** (Howler.js, phase-aware 5 tracks: chiba/sense_net/matrix_rain/broadcast/industrial, M to mute)
- **SFX** (Tier 4: combat_hit, victory, defeat — one-shot on phase transition + use_program)
- **Animation VFX** (Tier 4: hit flash color on HP delta, ICE/Player defeat ASCII art)
- **Status effect glyphs** (Tier 4: 5 effects [B/S/L/M/V] = burn/stun/slow/silence/vulnerable)
- **ICE types** (30 curated, T1-T4 Gibson-flavor: watchdog, spider, loa_priest, black, goliath, etc.)
- Desktop browser primary, mobile browser fully playable

## Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Navigate mission select |
| Enter / Space | Confirm / launch mission |
| Escape | Cancel / back |
| Q | Jack out |
| **M** | **Mute / unmute BGM + SFX** (Tier 2b / Tier 4) |

## Out of scope (Tier 5+)

- Full 209-mission campaign
- Status effect VFX
- Multiple bosses
- Multiple jockeys
- Save migration from desktop
- Multiplayer / cloud sync
- Full i18n (English only)

## Out of scope (Tier 4+ / Tier 5 candidates)

- Status effects state machine integration (currently mock data)
- Animation timing (hit flash duration + interpolation)
- Volume slider UI (M key toggle only, no slider)
- SFX expansion (combat_block, combat_skill_*, movement_*)
- Per-track fade in/out (Howler.fade())

See [implementation plan](Game/wet_run/.omo/plans/web-version-2026-08-25.md) for full context.

ADR-0199 (web MVP) is being drafted alongside this MVP implementation.

## Architecture

```
src/
├── core/          # Game logic (port from wet_run Python)
│   ├── combat.ts  # ICE-breaking state machine
│   ├── deck.ts    # Program draw logic
│   └── types.ts   # Shared interfaces
├── renderer/      # Canvas2D ASCII renderer
│   ├── canvas.ts
│   ├── palette.ts
│   └── fonts.ts
├── input/         # Keyboard input → game actions
├── data/          # Static JSON (exported from wet_run Python)
├── save/          # localStorage persistence
└── main.ts        # Entry point
```

## Build / CI

- `npm run dev` — local dev server (Vite HMR)
- `npm run build` — production bundle → `dist/`
- `npm run test` — Vitest unit tests
- `npm run lint` — ESLint TypeScript check
- `npm run export-data` — regenerate static JSON from wet_run Python

Deployment target: GitHub Pages (free, proven pattern in this workspace).

## License

Same as wet_run parent project: MIT.
