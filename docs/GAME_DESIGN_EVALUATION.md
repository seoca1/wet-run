# Wet Run — Game Design Evaluation (2026-10-20)

## Evaluation Framework

12-axis rubric: 7 roguelike-specific + 5 general game design.
Sources: MDA (Hunicke), Game Feel (Swink/Pichlmair), Roguelike design literature,
Koenitz ludonarrative toolbox, Game Accessibility Guidelines, procedural balance research.

| Axis | Question |
|---|---|
| R1 | Difficulty curve — monotonic? Any inversions? |
| R2 | Replayability — multiple runs meaningful? |
| R3 | Risk/reward balance — risky choices pay off? |
| R4 | Meta-progression — permanent growth after death? |
| R5 | Seed variety — different paths each run? |
| R6 | Control responsiveness — player choices matter? |
| R7 | Death weight — is death meaningful? |
| G1 | Story/gameplay integration — does world embed in play? |
| G2 | Tone consistency — original tone preserved? |
| G3 | Learning curve — easy to learn, deep to master? |
| G4 | Audio/visual completeness — can you mute? Is info clear? |
| G5 | Accessibility — playable by diverse players? |

## Results

| Axis | Score | Evidence |
|---|---|---|
| R1 | 🟢 STRONG | Monotonic non-increasing (100→88.8→73→47.4→42.4→0% opener; PPL also monotonic) |
| R2 | 🟢 STRONG | 5 mutators, 28 achievements, 53 missions, 97 ICE types |
| R3 | 🟢 STRONG | deck-building solid; event_matrix merchant events use real program-tier pricing |
| R4 | 🟢 STRONG | death_cycle.ts, HALL_OF_DEAD, faction_reputation |
| R5 | 🟢 STRONG | BSP dungeon, far_grid_gate, 97 ICE × 30 programs |
| R6 | 🟢 STRONG | combat state machine, enemy AI (ice_ai.ts) |
| R7 | 🟢 STRONG | LOW_HP mutator, deceased jockey archive |
| G1 | 🟢 STRONG | 72 GN scenes (9 jockeys × 8), Fiction wiki primary source |
| G2 | 🟢 STRONG | AGENTS.md §4 Sprawl accuracy rules; no Cyberpunk 2077/Shadowrun/D&D borrow |
| G3 | 🟡 PARTIAL | tutorial_mission exists but marked "Tier 5.5+"; 4/6 menu options stub |
| G4 | 🟡 PARTIAL | 12 BGM tracks (phase-aware), 3 SFX only; no volume slider (M toggle only) |
| G5 | 🟡 PARTIAL | colorblind/gamepad ADRs exist; actual application unverified |

**Composite**: 8 strong / 3 partial / 1 issue (down from 7/4/1)

## Issue Re-Check (2026-10-20)

All three previously-flagged issues were verified as **already fixed**:

### 1. Difficulty curve (R1) — ✅ Already fixed
- **Fixed**: 2026-09-24, ADR-0211 + ADR-0212
- `ice_types.json` carries `hp_base` + `hp_per_grade` per ICE
- `parseIce` derives `hp` at load time from those fields
- `iceHpForGrade()` applies runtime cap (`ENCOUNTER_HP_BY_GRADE`)
- Balance harness now reports monotonic non-increasing curve
- **Evidence**: `npm run balance` → opener 100→88.8→73→47.4→42.4→0%

### 2. Status effects (R3/G4) — ✅ Already wired
- **Status**: `status.ts` (249 lines, 13 effects) fully integrated into combat path
- Wiring: `state_actions_programs.ts` — `rollStatusProc` → `applyStatus` → `tickStatus` → `applyTickEffects` → `applyBurnDamage`
- 31 tests cover burn/slow/vulnerable (25 in `status.test.ts`, plus `slow_effect.test.ts`)
- README "Out of scope" line was stale — **removed**

### 3. Event pricing (R3) — ✅ Already implemented
- **Status**: `event_matrix.ts` merchant events use real program tier-based pricing
- No `placeholder pricing` comment remains in codebase

## Data Inventory

| Asset | Count | Source |
|---|---|---|
| Missions | 53 | `src/data/missions.json` (14 fields each) |
| ICE types | 97 | `src/data/ice_types.json` |
| Programs | 30 | `src/data/programs.json` |
| GN scenes | 27 | `src/data/scenes.json` |
| Achievements | 28 | `src/core/achievement_definitions.ts` |
| Mutators | 5 | `src/core/run_mutators.ts` |
| Boss phases | 51 refs | `src/core/boss_phases.ts` |
| Core modules | 62 | `src/core/` |
| Test files | 122 | `web/tests/` |
| Tests passing | 2,902 | vitest run |

## Verification Commands

```bash
cd web
npm test              # 2,902 tests
npm run typecheck     # tsc --noEmit strict
npm run lint          # eslint
npm run build         # tsc + vite build
npm run balance       # win-rate per grade (opener + PPL deck)
python3 ../../scripts/audit_vault.py  # vault lint
```

## Remaining Open Items

| Axis | Issue | Priority |
|---|---|---|
| G3 | tutorial marked "Tier 5.5+" (not yet implemented) | Low |
| G3 | 4/6 menu options are stubs (GRAPHIC_NOVEL, CONTINUE, SETTINGS, CREDITS) | Low |
| G4 | 3 SFX only; no volume slider (M toggle only) | Low |
| G4 | No per-track fade in/out (Howler.fade()) | Low |
| G5 | colorblind/gamepad ADRs exist but actual application unverified | Low |