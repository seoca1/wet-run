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

## Scope (MVP Tier 1)

- 1 playable mission (first_jack)
- ASCII Canvas2D renderer (Gibson palette)
- ICE-breaking combat state machine
- Save/load via localStorage
- Keyboard input (arrow keys + ENTER + SPACE + ESC)
- Silent (no audio in Tier 1; Tier 2 adds Howler.js)
- Desktop browser primary (mobile browser works; touch UI is Tier 2)

## Out of MVP scope (Tier 2+)

- Multiple missions, full campaign
- Status effect VFX
- Multiple bosses
- Multiple jockeys
- Save migration from desktop
- Mobile touch UI
- Audio (Howler.js)
- Multiplayer / cloud sync
- Full i18n (English only in MVP)

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
