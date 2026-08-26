# ADR-0199: Wet Run Web MVP (Tier 1)

**상태**: Accepted (2026-08-25; user-directed autonomous build)
**날짜**: 2026-08-25
**결정자**: 사용자 (operator)
**우선순위**: P1 (Browser reach — broadens addressable player base; mobile/web deferred per ADR-0007 now superseded)
**관련**:
- [ADR-0007 — Platform Target (Accepted 2026-06-17)](./0007-platform-target.md) **SUPERSEDED** for web/mobile scope
- [web-version-2026-08-25 implementation plan](../.omo/plans/web-version-2026-08-25.md) (full context)
- [Gamepad controller input (ADR-0197)](./0197-gamepad-controller-input-support.md) — keyboard mapping parity

## 컨텍스트 (Context)

ADR-0007 (Accepted 2026-06-17) explicitly rejected web + mobile:
> "모바일은 Pillar 3과 충돌 (F2P 위험)" / "웹은 매트릭스 톤의 ASCII와 거리"

User reverses this decision (2026-08-25) to expand addressable player base to:
- Steam Deck + Linux desktop browser
- iPad / Android tablet browsers
- Phone browsers (Tier 2 — MVP excludes)

Two perspectives validated the approach:
- **Librarian research** (opus-4.5, 1m43s): 6 web-port approaches; Pyodide not viable (SDL2 C extensions); Pygbag possible but costly rewrite
- **Oracle counter-review** (1h adversarial): rejected Pygbag-first as "procrastination device"; pushed MVP-only with 4-week calendar budget

## 고려한 옵션 (Considered Options)

### Option 1: TypeScript + Canvas2D MVP (RECOMMENDED — adopted)

- **설명**: Browser-native TypeScript; Canvas2D ASCII renderer; static files; ~4 weeks for MVP.
- **장점**:
  - Native browser performance (60fps free; sub-second cold-start)
  - Single artifact (static files) for GitHub Pages + itch.io deployment
  - Reuses existing wet_run/data/ via Python export script
  - No backend, no multiplayer, no auth, no payment — minimal ops
- **단점**:
  - Game logic reimplementation in TypeScript (state machines, ICE-breaking)
  - Gibson tone validation is non-trivial (subtle ANSI shifts, half-block glyphs)
  - 5811 Python tests become obsolete; ~50% don't port
- **Pillar 정합**:
  - P1 (The Run): tier 1 web MVP ships 1 playable mission
  - P2 (The Matrix): Canvas2D renders ICE widget, basic state machine
  - P3 (The Flatline): combat escalation via ICE HP damage
  - P4 (The Build): static JSON export + Vite build pipeline
  - P5 (The Style): Gibson neon palette preserved in palette.ts

### Option 2: Pygbag (Python-in-browser) — REJECTED

- **설명**: Migrate tcod → pygame-ce; package via Pygbag to WebAssembly.
- **Why rejected**: Migrating 48 files × 423 tcod call sites = rewriting the renderer. 4-8 weeks; tests become 50% obsolete. WASM-compiled Python in browser is a compromise; better to commit to native web from day 1.

### Option 3: Hybrid Python backend + JS frontend — REJECTED

- **설명**: Python FastAPI + TypeScript rot.js frontend; multiplayer-ready.
- **Why rejected**: Multiplayer isn't in the design. No design doc, no ADR, no roadmap entry says "we need multiplayer." Hybrid adds network round-trips + auth + reconnection logic + 2 type systems to solve a problem that doesn't exist.

### Option 4: Full port (all 209 missions + i18n + audio + mobile touch) — REJECTED

- **설명**: Direct full-port without MVP scoping.
- **Why rejected**: 6-12 months; calendar time > person-weeks for single maintainer. Risk: shipping a half-broken web version kills the project.

## 추천 (Recommendation)

**Adopt Option 1: TypeScript + Canvas2D MVP.** Implement in 7 atomic commits over ~4 weeks calendar time.

### Scope (Tier 1 MVP — explicit boundaries)

**In MVP**:
- 1 playable mission (first_jack)
- ASCII Canvas2D renderer (Gibson palette, monospace font)
- ICE-breaking combat state machine (1 ICE encounter)
- Save/load via localStorage (schema-versioned)
- Keyboard input (arrow keys + ENTER + SPACE + ESC + Q)
- Static files deployment (GitHub Pages)

**Out of MVP** (Tier 2+ deferral):
- Multiple missions, full campaign (209 missions)
- Multiple bosses, status effects, deck-building roster
- Multiple jockeys, narrative / graphic novel mode
- Audio (Howler.js)
- Mobile touch UI
- Multiplayer, cloud save sync
- Full i18n (English only in MVP)
- Save migration from desktop

### Architecture

```
Game/wet_run-web/                           # New sub-folder in workspace
├── src/
│   ├── core/                                # Game logic (port from wet_run)
│   │   ├── types.ts                         # Shared interfaces (GameState, Mission, Ice, Program)
│   │   ├── state.ts                         # Pure reducer (applyAction)
│   │   └── grid.ts                          # Immutable Grid construction
│   ├── renderer/
│   │   ├── canvas.ts                        # AsciiRenderer (Canvas2D)
│   │   └── palette.ts                       # Gibson neon palette
│   ├── input/
│   │   └── keyboard.ts                      # Keyboard → GameAction
│   ├── save/
│   │   └── storage.ts                       # localStorage round-trip
│   ├── data/                                # Static JSON (exported from wet_run/data/)
│   └── main.ts                              # Entry point
├── tests/                                   # Vitest
├── docs/PLAYTEST.md                          # 3-person playtest protocol
├── scripts/export_web_data.py               # Python → JSON export
├── index.html                               # Entry HTML (Canvas + status overlay)
├── package.json                             # Vite + Vitest + TS
├── tsconfig.json                            # TypeScript strict
├── vite.config.ts                           # Vite bundler + test config
└── vitest.setup.ts                          # localStorage polyfill
```

### Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | TypeScript 5.x | Type safety, modern web standards |
| Bundler | Vite | Fast HMR, simple config |
| Renderer | Canvas2D | Sufficient for ASCII; can upgrade to WebGL later |
| Tests | Vitest | TS-native, fast |
| Data | Static JSON (Python export) | Reuses wet_run/data/ |
| Save | localStorage JSON | No backend needed |
| Distribution | GitHub Pages or itch.io | Free, simple |

### Operational Decisions (operator gate answers)

| Q | Decision |
|---|---|
| Deployment | GitHub Pages (proven pattern in this workspace) |
| Repo structure | Sub-folder (`Game/wet_run-web/`) inside workspace |
| Audio in MVP | Silent (Tier 2 if validated) |
| Save | localStorage JSON (Tier 2: IndexedDB) |
| Distribution scope | MVP only (later: link from `Game/wet_run/dashboard/`) |
| First ICE encounter | first_jack (default Watchdog from `ice_types.json`) |

### 7-Commit Implementation Plan

| # | Commit | Day | LOC |
|---|---|---|---:|
| 1 | Project setup + data export | 1 | ~200 |
| 2 | ASCII Canvas2D renderer | 2-3 | ~300 |
| 3 | Game state types + keyboard input | 4-5 | ~400 |
| 4 | Combat core — IceBreaker state machine port | 6-9 | ~600 |
| 5 | Save/load + win/loss + HUD | 10-11 | ~300 |
| 6 | Polish + 3-person playtest hooks | 12-14 | ~400 |
| 7 | Deploy + ADR-0199 | 15 | (docs) |

**Total**: ~2,200 LOC, 4 weeks calendar, 1 maintainer.

### 5-Step Validation Plan

1. **Day 1 visual render test** (Commit 2): Can Canvas2D render ASCII with Gibson neon feel? If not — stop, redesign.
2. **Day 5 boss fight prototype** (Commit 4): Port 1 boss. Time it. If >3 days — estimate was wrong, recalibrate.
3. **Day 10 playtest with 3 people** (Commit 6): `docs/PLAYTEST.md` protocol. Watch where they get stuck.
4. **Day 12 cold-start measurement**: <3s on cable broadband. (Static JS should be sub-second.)
5. **Day 15 ADR-0199** (this document): Supersede ADR-0007 for web/mobile scope.

## 결과 (Consequences)

### Positive
- Cross-device reach without backend infrastructure
- Sub-second cold-start (static files)
- Gibson neon palette reproducible in Canvas2D
- Reuses wet_run/data/ via Python export (no content duplication)
- 4-week calendar budget realistic for single maintainer

### Negative
- ~2,200 LOC new TypeScript code
- 5811 Python tests remain desktop-only
- Desktop ↔ web save migration not in MVP scope (ADR-0183 §Input Remapping closure incomplete)
- "Gibson tone" validation deferred to playtest — if fails, redesign

### Risks

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| 1 | **Gibson tone loss** in Canvas2D (subtle ANSI shifts, half-blocks, CRT flicker) | M | H | Validate in Commit 2 visual render test; if fails, accept 80% fidelity |
| 2 | **Calendar time** > 4 weeks for single maintainer | H | H | Strict MVP scope; no scope creep; hard deadline |
| 3 | **Save migration** never covered by tests (desktop vs web save schema) | M | M | MVP uses localStorage; cross-device sync explicitly out of scope |
| 4 | **Game state complexity** underestimated | M | M | Port only 1 encounter; reuse data; no multiplayer |
| 5 | **Cross-browser compat** (Safari audio quirks, IndexedDB) | L | M | Tier 1: desktop Chrome/Firefox/Safari 17+; keyboard only |

## Implementation Status (this session, 2026-08-25)

| Step | Status |
|---|---|
| ADR-0199 drafted + Accepted | ✅ 2026-08-25 (autonomous, user-directed) |
| Implementation plan written | ✅ `.omo/plans/web-version-2026-08-25.md` |
| Commit 1: Project setup + data export | ✅ Scaffolding, package.json, tsconfig.json, vite.config.ts, index.html, PWA manifest, export_web_data.py |
| Commit 2: ASCII Canvas2D renderer | ✅ `renderer/canvas.ts` + `palette.ts` (Gibson neon palette) |
| Commit 3: Game state + keyboard input | ✅ `core/types.ts` + `core/grid.ts` + `core/state.ts` + `input/keyboard.ts` |
| Commit 4: Combat core | ✅ IceBreaker state machine (useProgram reduces ICE HP, alarm accumulates) |
| Commit 5: Save/load | ✅ `save/storage.ts` (localStorage JSON + schema versioning) |
| Commit 6: Polish + playtest hooks | ✅ `docs/PLAYTEST.md` (3-person protocol) |
| Commit 7: ADR-0199 (this document) | ✅ |
| 17 unit tests (state + storage) | ✅ All passing |
| TypeScript strict dry-compile | ✅ No errors |
| Vite production build | ✅ 48KB JS (11.5KB gzipped) + 2KB HTML |

### Final Files Touched

| Path | LOC | Action |
|---|---:|---|
| `Game/wet_run-web/package.json` | 32 | NEW |
| `Game/wet_run-web/tsconfig.json` | 21 | NEW |
| `Game/wet_run-web/vite.config.ts` | 17 | NEW |
| `Game/wet_run-web/vitest.setup.ts` | 35 | NEW |
| `Game/wet_run-web/index.html` | 60 | NEW |
| `Game/wet_run-web/public/manifest.json` | 18 | NEW |
| `Game/wet_run-web/README.md` | ~70 | NEW |
| `Game/wet_run-web/scripts/export_web_data.py` | 95 | NEW |
| `Game/wet_run-web/src/core/types.ts` | ~140 | NEW |
| `Game/wet_run-web/src/core/grid.ts` | ~70 | NEW |
| `Game/wet_run-web/src/core/state.ts` | ~165 | NEW |
| `Game/wet_run-web/src/renderer/canvas.ts` | ~85 | NEW |
| `Game/wet_run-web/src/renderer/palette.ts` | ~45 | NEW |
| `Game/wet_run-web/src/input/keyboard.ts` | ~50 | NEW |
| `Game/wet_run-web/src/save/storage.ts` | ~65 | NEW |
| `Game/wet_run-web/src/main.ts` | ~110 | NEW |
| `Game/wet_run-web/tests/state.test.ts` | ~115 | NEW |
| `Game/wet_run-web/tests/storage.test.ts` | ~70 | NEW |
| `Game/wet_run-web/docs/PLAYTEST.md` | ~85 | NEW |
| `Game/wet_run/decisions/0199-wetrun-web-mvp.md` | (this) | NEW |
| `Game/wet_run/decisions/README.md` | +1 line | UPDATED (index entry) |
| **Total** | **~1345** | (TypeScript: ~1,015; Python: ~95; docs: ~235) |

### Supersedes

- **ADR-0007** (Accepted 2026-06-17) for web/mobile scope only. macOS + Windows desktop continues per ADR-0007.

### Deferred (Tier 3+)

- 3-person playtest (validates Tier 1+2 shippable quality)
- Audio via Howler.js (silent per operator gate)
- Full 209-mission campaign
- Status effect VFX
- Multiple bosses / jockeys
- Save migration from desktop
- Full i18n (English-only in MVP)
- Multiplayer / cloud sync
- WebGL renderer upgrade (if Canvas2D insufficient)

---

*Accepted: 2026-08-25. Owner: Sisyphus. Tier 1 MVP built in single session (autonomous). Playtest pending (3-person protocol in docs/PLAYTEST.md).*
