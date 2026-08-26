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

## Scope (Tier 2a — current build)

- **5 playable missions** (first_jack + watchdog_patrol + ono_sendai_repair + construct_market + ghost_signal_origin)
- ASCII Canvas2D renderer (Gibson palette)
- ICE-breaking combat state machine
- **Multi-slot save/load** (4 slots: 1 autosave + 3 manual, with legacy single-slot migration)
- Keyboard input (arrow keys + ENTER + SPACE + ESC)
- **Mobile touch input** (auto-mounts virtual gamepad on `pointer: coarse` devices)
- Silent (no audio — Tier 2b adds Howler.js)
- Desktop browser primary, mobile browser fully playable

## Out of scope (Tier 3+)

- Full 209-mission campaign
- Status effect VFX
- Multiple bosses
- Multiple jockeys
- Save migration from desktop
- Audio (Howler.js)
- Multiplayer / cloud sync
- Full i18n (English only)

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
