# Wet Run Web — Migration + Active Development

## Executive Summary

Python 프로토타입 (236 파일, 54K LOC) → TypeScript Web 완전 이전 완료.
현재 전투 시스템 고도화 단계 (multi-enemy combat).

**Current State**: 40+ TypeScript files, 997 tests, zero type errors.

## Migration Phases — COMPLETED

### Phase 1: Data Layer Consolidation ✅
**Completed**: missions.json (209), programs.json (30), ice_types.json (97), i18n strings, export scripts

### Phase 2: Core Game Logic ✅
**Completed**: combat_models.ts, combat_engine.ts, boss_phases.ts, status.ts (13 effects), state.ts wiring

| Module | Description | Tests |
|--------|-------------|-------|
| `combat_models.ts` | Combatant, CombatState, Skill, StatusEffect interfaces | — |
| `combat_engine.ts` | Damage calc (variance/crit/weakness/synergy/combo), alarm tick, combo timeout | 31 |
| `boss_phases.ts` | 4-phase transitions, damage multipliers, labels/colors | 29 |
| `status.ts` | 13 status effects (burn, stun, slow, silence, vulnerable, stagger, regen, powered, weakened, bleed, fatigue, confused, terrified) | 8 new |
| `state.ts` | Full wiring — calculateDamage, combo, alarm, bleed/heal integration | 16 |

### Phase 3: Matrix Enhancement ✅
**Completed**: BSP dungeon generation, fog of war, exploration mechanics

| Module | Description | Tests |
|--------|-------------|-------|
| `dungeon.ts` | Public types, Mulberry32 RNG, DungeonGenerator (Phase 1), dungeonToMatrix adapter | 40 |
| `dungeon_bsp.ts` | BspNode, bspPartition, placeRooms, collectLeaves | — |
| `dungeon_layout.ts` | Kruskal MST, dead-ends, room-type assignment, ProceduralDungeonGenerator | — |
| `exploration.ts` | MatrixGraphView, Visibility, ExplorationState, eventForRoomType | 26 |

### Phase 4: Content Systems ✅
**Completed**: crafting, equipment, achievements, run mutators

| Module | Description | Tests |
|--------|-------------|-------|
| `crafting.ts` | 3-tier recipes, material costs, InfoMarket | 71 |
| `equipment.ts` | Gear slots, stat bonuses, equip/unequip, loadout | 132 |
| `achievements.ts` | 28 achievements across 5 categories (combat, exploration, story, mastery, hidden) | 58 |
| `run_mutators.ts` | Run modifier system (8 mutators) | 34 |

### Phase 5: Narrative Systems ✅
**Completed**: graphic novel engine, scene data

| Module | Description | Tests |
|--------|-------------|-------|
| `graphic_novel.ts` | Scene definitions, auto-play, transitions, text utilities | 74 |
| `scenes.json` | 27 scenes (3 characters × 9 scenes) | — |

### Phase 6: Polish & Validation ✅
**Completed**: TypeScript strict mode, 899 tests, no escape hatches

## Technical Verification

### Build
```
npx tsc --noEmit     → 0 errors
npx vitest run       → 997/997 tests pass (47 files)
npx vite build       → 235.94 KB (gzip 53.98 KB)
```

### Code Quality
- No `as any` or `@ts-ignore`
- All tests use deterministic RNG (injected, not Math.random)
- Frozen/immutable data structures throughout
- Python parity verified: damage calc, combo, alarm, boss phases, status effects, enemy AI

### File Count
- **Source files**: ~40 TypeScript files
- **Test files**: 47 test files
- **Data files**: missions.json, programs.json, ice_types.json, effects.json, scenes.json, strings.json
- **Scripts**: export_all.py, export_missions.py

### Phase 7: Integration ✅
**Completed**: Wired crafting, equipment, graphic novel into main.ts game loop

| Task | Status |
|------|--------|
| Wire crafting into main.ts game loop | ✅ Crafting screen, recipes, inventory |
| Wire equipment into main.ts game loop | ✅ Equipment screen, loadout, equip/unequip |
| Wire graphic novel into screen manager | ✅ GN auto-play, dialogue, scene navigation |
| Fix broken inventory.programs combat gate | ✅ Removed (was blocking all combat) |
| Menu options: craft + equipment | ✅ 11 options total |

## Active Development — Combat Systems

### Enemy AI ✅ (2026-09-02)
**Completed**: ICE aggression tiers + personality archetypes + auto-attacks

| Module | Description | Tests |
|--------|-------------|-------|
| `ice_ai.ts` | Aggression tiers (passive/standard/aggressive/boss), personality archetypes (aggressive/defensive/stealth/support), skill selection, stat modifiers | 35 |
| `state.ts` | `processEnemyTurns()` — enemy auto-attacks after player actions, counter-attack window | Updated |
| `types.ts` | `lastEnemyAttackMs` field added to `GameState` | Updated |

**Key mechanics ported from Python**:
- `AGGRESSION_PROBABILITY` — per-tick skill-use chance (ADR-0148)
- `PERSONALITY_SKILL_PREFERENCE` — personality-based skill priority (ADR-0161)
- `getCritBonus()` — aggressive personality +5% crit
- `getAlarmMultiplier()` — stealth personality 0.5x alarm speed
- `shouldDefensiveAct()` — defensive personality HP<50% threshold
- `shouldTargetAlly()` — support personality ally targeting

### Multi-Enemy Combat ✅ (2026-09-02)
**Completed**: Target cycling, roster display, auto-advance on kill

| Module | Description | Tests |
|--------|-------------|-------|
| `state.ts` | `cycleTarget()` — Tab cycles alive enemies; `advanceDeadTarget()` auto-advances on kill | 4 |
| `types.ts` | `cycle_target` action added to `GameAction` union, Tab key mapped | Updated |
| `main.ts` | `renderGrid()` — roster with per-enemy HP bars, `>` target cursor, `[DEAD]` markers | Updated |
| `state.ts` | `buildHudLines()` — roster display with active marker | Updated |
| `multi_enemy.test.ts` | Target cycling, dead-skip, HUD roster, edge cases | 7 |

**Mechanics**:
- Tab key cycles `activeIceIndex` through alive enemies (wraps around)
- Dead enemies skipped automatically; `advanceDeadTarget()` called before damage calc and enemy turns
- Roster renders vertically with 3-row blocks: name + HP bar + status effects (active target only)
- `[DEAD]` marker replaces HP bar for defeated enemies
- HUD right-panel shows all enemies with `>` cursor on active target

### Remaining Combat Tasks ✅
- [x] AoE skill support (target all enemies)
- [x] Boss AI overrides (phase-specific AoE, minion spawn)
- [x] Skill cooldown system (enemy skill cooldowns)
- [x] Personality → skill selection wiring (production hot path)

## Remaining Work

### Tier A — Combat Systems (Priority) ✅
- [x] Enemy AI (aggression tiers, personality, auto-attacks)
- [x] Multi-enemy combat (target switching, roster display)
- [x] Companion system (Dixie auto-attacks, synergy)
- [x] Boss AI overrides (phase-specific AoE, minion spawn)
- [x] Skill cooldown system (enemy skill cooldowns)
- [x] Personality → skill selection wiring (production hot path)

### Tier B — Content & UX ✅
- [x] Python ice_types.json → TS aggression/personality field sync
- [x] Loot/drop system (post-combat item drops)
- [x] Run mutators actual integration (combat/matrix effects)
- [x] Achievement triggers (event-based check & toast)
- [x] Graphic novel save/load

### Tier C — Infrastructure ✅
- [x] lz-string compress/storage test fixes (2 pre-existing failures)
- [x] Bundle optimization (tree-shaking verification)
- [x] PWA service worker (offline play)

## Timeline

- **Phase 1**: ✅ Data Layer
- **Phase 2**: ✅ Core Logic
- **Phase 3**: ✅ Matrix
- **Phase 4**: ✅ Content
- **Phase 5**: ✅ Narrative
- **Phase 6**: ✅ Polish
- **Phase 7**: ✅ Integration
- **Enemy AI**: ✅ Complete
- **Multi-Enemy Combat**: ✅ Complete
- **AoE Skills**: ✅ Complete
- **Boss AI**: ✅ Complete
- **Skill Cooldowns**: ✅ Complete
- **Personality Wiring**: ✅ Complete
- **Companion System**: ✅ Complete
- **ice_types.json Sync**: ✅ Complete
- **Loot System**: ✅ Complete
- **Mutator Integration**: ✅ Complete
- **Achievement Triggers**: ✅ Complete
- **Graphic Novel Save/Load**: ✅ Complete
- **lz-string Test Fixes**: ✅ Complete
- **Bundle Optimization**: ✅ Complete (388KB gzip 112KB)
- **PWA Service Worker**: ✅ Complete

**Total Migration**: Complete (all 7 phases delivered)
**Active Development**: Tier C Infrastructure — ALL COMPLETE
