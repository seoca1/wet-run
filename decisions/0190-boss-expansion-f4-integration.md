# ADR-0190: Boss Expansion + F.4 Integration (Phase 12 — Content Expansion, Axis 4)

**상태**: Accepted (2026-08-08, Phase 12 implementation in progress)
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 1 climax + Pillar 5 finale)
**관련**: [ADR-0050 — Boss ICE System](./0050-boss-ice-system.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0180 — Boss Expansion v1.3.0+](./0180-boss-expansion.md), [ADR-0187 — Boss Phase 5 Expansion](./0187-boss-phase-5-expansion.md), [.omo/plans/expand-roguelike-game-contents.md](../../../.omo/plans/expand-roguelike-game-contents.md)

## 컨텍스트 (Context)

Current state: 5+ bosses (Wintermute, T-A Prime, Neuromancer, Loa Baron, Black Baron). v1.3.0+ Track F.4 created tier 5 boss profiles in registry only — not yet integrated into combat flow.

Per `.omo/plans/expand-roguelike-game-contents.md`, Phase 12 expands to 8-10 bosses with F.4 integration scope.

Gaps:
- F.4 boss profiles (Neuromancer, Loa Baron, Black Baron) not wired to combat dispatch
- No zone-boss archetype (1 per zone = 6 zone-bosses would give every zone a climax)
- No ascended variants (tier 5 of existing bosses is in registry only)
- No secret boss (post-Salvation endgame)

## 옵션 (Options)

### Option 1: F.4 integration only (3 existing bosses)
- Wire existing tier 5 profiles into combat
- **장점**: Completes existing ADR-0180 scope
- **단점**: No new bosses, no new content

### Option 2: F.4 integration + 6 new zone-bosses (9 total)
- All Option 1 + 6 zone-bosses (one per zone)
- **장점**: Every zone gets a climax
- **단점**: 9 bosses is a lot to design

### Option 3: F.4 integration + 6 zone-bosses + 3 ascended variants + 1 secret (13 total)
- Full scope per plan
- **장점**: Comprehensive endgame
- **단점**: Largest scope, longest effort

**추천**: Option 3 (matches plan target of 8-10 bosses plus F.4)

## 결정 (Decision)

**Option 3**: Full scope. F.4 integration + 6 zone-bosses + 3 ascended + 1 secret.

### Target counts

| Category | Current | Target | Delta |
|---|--:|--:|--:|
| Base bosses | 2 | 2 | 0 |
| Tier 5 bosses (F.4) | 3 (registry only) | 3 (integrated) | +0 (integration) |
| Zone-bosses | 0 | 6 | +6 |
| Ascended variants | 0 | 3 | +3 |
| Secret boss | 0 | 1 | +1 |
| **Total active** | **2** | **13** | **+11** |

### F.4 integration (priority)

3 bosses in `boss_expansion.py` registry need to be wired into combat dispatch:
- **Neuromancer** (tier 5, 6 phases, HP 400) — Sprawl final boss
- **Loa Baron** (tier 4, 4 phases, HP 300) — Vodou construct
- **Black Baron** (tier 3, 4 phases, HP 250) — Corporate villain

Integration: `combat_view_state.py:134` (`build_ice_enemy()`) routes to boss profiles when AI level triggers.

### Zone-bosses (1 per zone)

| Zone | Boss | Theme | Difficulty |
|---|---|---|---|
| Surface | DJ Cyberspace | Local ripper | Normal |
| Mid | Sense/Net Sentinel | Media surveillance | Hard |
| Deep | Hosaka Memory | Corporate vault | Hard |
| Core | Locus Construct | AI fragment | Extreme |
| TA | Tessier Child | Heir-apparent | Extreme |
| Freeside | Orbit Ghost | Orbital phantom | Extreme |

### Ascended variants

- **Wintermute Ascended** (tier 5 Wintermute with 8 phases)
- **T-A Prime Ascended** (tier 5 T-A with construct choir)
- **Neuromancer Ascended** (combine Neuromancer + Wintermute + T-A)

### Secret boss

- **The Peripheral** (post-Salvation, NG+ exclusive) — references Jackpot trilogy

### Boss design principles

- Each boss has a "tell" (1-frame warning before major attack)
- Each boss has a counter-strategy (specific program/augment)
- Boss dialogue: Gibson "I am the interface" / "we are the message"
- HP scaled to Pillar 3 weight (HEAL 15% per ADR-0152)

## Implementation surface

### Code

- `combat/boss_expansion.py` — wire existing 3 profiles into combat dispatch
- `combat/zone_bosses.py` (NEW) — 6 zone-boss profiles
- `combat/ascended_bosses.py` (NEW) — 3 ascended variants
- `combat/secret_boss.py` (NEW) — The Peripheral (post-Salvation)
- `combat/dispatch.py` — extend routing for new bosses

### Data files

- `prototype/data/combat/boss_profiles.json` — extend with 10 new bosses
- `prototype/data/combat/boss_dialogue.json` (NEW) — Gibson-flavored dialogue

### Tests

- `tests/unit/test_boss_f4_integration.py` (NEW) — verify registry dispatch
- `tests/unit/test_zone_bosses.py` (NEW) — per-zone behavior
- `tests/unit/test_ascended_bosses.py` (NEW) — variant behavior
- `tests/unit/test_secret_boss.py` (NEW) — gating + behavior

### Design docs

- `design/systems/combat.md` — boss archetypes + F.4 integration
- `design/systems/missions.md` — endgame mission gating

### Testcases

- `testcases/combat/boss_f4_integration.md` (NEW)
- `testcases/combat/zone_bosses.md` (NEW)
- `testcases/combat/ascended_bosses.md` (NEW)
- `testcases/combat/secret_boss.md` (NEW)

### i18n

- Boss names + dialogue in `data/i18n/{en,ko}.json`

## Consequences (Pillar impact)

- **Pillar 1 (Run)**: Strong — every zone has a climax; endgame content
- **Pillar 2 (Matrix)**: Strong — new boss-themed zones
- **Pillar 3 (Flatline)**: Strong — new death scenarios + Gibson voice
- **Pillar 4 (Build)**: Moderate — programs needed to counter new bosses
- **Pillar 5 (Style)**: Strong — iconic boss dialogue

**Tests**: +25-30 tests
**Effort**: 3-5 sessions (includes F.4 integration)
**Risk**: Medium — F.4 integration may surface bugs in existing flow

## 열린 질문

1. **F.4 integration priority**: Do F.4 bosses replace existing tier 5 slots, or coexist? Recommend coexist (existing registry, new dispatch).
2. **Zone-boss vs zone-progress**: Should zone-boss be required to progress, or optional? Recommend required (zone climax).
3. **Ascended variants**: Unlock conditions (NG+ only, or beat normal first)? Recommend beat normal first.
4. **Secret boss gating**: Just post-Salvation, or NG+ AND post-Salvation? Recommend NG+ AND post-Salvation.

## 다음 단계

If approved:
1. F.4 integration (highest priority — completes existing ADR)
2. Zone-boss design (1 per zone)
3. Ascended variants (3 bosses)
4. Secret boss (post-Salvation)
5. Dialogue content (Gibson voice)
6. Tests + design docs
7. i18n
8. Atomic commit
