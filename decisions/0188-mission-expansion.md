# ADR-0188: Mission Expansion (Phase 11 — Content Expansion, Axis 1)

**상태**: Accepted (2026-08-08, user explicit "Begin Phase 11")
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 1 run variety)
**관련**: [ADR-0017 — Mission-Material Integration](./0017-mission-material-integration.md), [ADR-0061 — Novel Integration Architecture](./0061-novel-integration-architecture.md), [ADR-0152 — Multi-Enemy Encounters](./0152-multi-enemy-encounters.md), [.omo/plans/expand-roguelike-game-contents.md](../../../.omo/plans/expand-roguelike-game-contents.md)
**선행 작업**: `.omo/plans/expand-roguelike-game-contents.md` (Phase 11–14 plan)

## 컨텍스트 (Context)

Current state: 111 missions across 6 zones (Surface/Mid/Deep/Core/TA/Freeside). Per `.omo/plans/expand-roguelike-game-contents.md`, Phase 11 expands to 200+ missions with new types, chains, and dynamic selection.

Gaps identified:
- Zone distribution uneven (TA zone under-served; details TBD via zone analysis)
- 6 mission types (per ADR-0017); no investigation/defense/dual-objective variants
- No mission chains (single missions only; no multi-stage storylines)
- Random mission selection is static (no weighted/dynamic rules)

Track Phase 11 of the Content Expansion plan addresses these gaps via **additive mission content** — no system rewrites, no new mechanics.

## 옵션 (Options)

### Option 1: All-in-one master ADR (1 ADR covers all 6 axes)
- **장점**: Single decision document, atomic scope
- **단점**: Too broad; user reviews 200+ missions in one go
- **추천**: ❌ — Too coarse-grained

### Option 2: Per-axis ADRs (6 separate ADRs, 0188-0193)
- **장점**: One feature per ADR — matches existing pattern (ADR-0180, ADR-0187)
- **단점**: 6 ADRs to review; 6 commits
- **추천**: ✅ (this ADR is Option 2, Axis 1)

### Option 3: Per-phase ADRs (4 ADRs, one per phase)
- **장점**: Phase-scoped review
- **단점**: One ADR can be 100+ lines; harder to read
- **추천**: ❌ — Phase 11 alone is 4-6 sessions of work

## 결정 (Decision)

**Option 2**: Per-axis ADRs. This is Axis 1 (Mission Expansion).

### Target counts

| Metric | Current | Target | Delta |
|---|--:|--:|--:|
| Total missions | 111 | 200+ | +89 |
| Zone distribution | uneven | balanced (≥25/zone) | TBD |
| Mission types | 6 | 11 | +5 |
| Mission chains | 0 | 8 | +8 |
| Endgame missions | 0 | 11 | +11 |

### New mission types

- **Investigation**: multi-stage, no combat (gather intel, deliver)
- **Defense**: defend a node from waves (no extraction, just survival)
- **Dual-objective**: two simultaneous goals (e.g., extract + protect NPC)
- **Extraction**: high-risk, high-reward (timer + combat)
- **Infiltration**: stealth-required (avoid ICE, not engage)

### Mission chains

8 chains of 3-5 missions each (24-40 missions total in chains):
- 3 chain archetypes: faction-driven, character-driven, story-driven
- Chains unlock mid-game (after 3-5 missions completed)
- Each chain has a unique reward (program, augment, deck)

### Zone distribution (initial target)

| Zone | Current | Target | Delta |
|---|--:|--:|--:|
| Surface | ~25 | 35+ | +10 |
| Mid | ~25 | 35+ | +10 |
| Deep | ~20 | 35+ | +15 |
| Core | ~15 | 30+ | +15 |
| TA | ~15 | 35+ | +20 |
| Freeside | ~11 | 30+ | +19 |

(TBD: actual zone distribution analysis happens as first step)

### Random/dynamic selection

- 19 new random mission rules (zone-specific, faction-specific, time-of-day)
- Weighted selection (rare missions harder to trigger; high-value)
- Conditional missions (appear only after specific story events)

### Endgame (Phase 6 NG+)

- 11 post-Salvation missions (NG+ exclusive)
- Boss rush chains (5 missions, escalating bosses)
- Endgame-only construct allies

## Scope boundaries (must NOT)

- **No new mechanics**: existing mission system + types only (no new combat, matrix, or progression)
- **No system rewrites**: extend existing `missions.json` schema, don't replace
- **No upstream mods**: Fiction wiki stays untouched
- **No Cyberpunk 2077 / Shadowrun / D&D tone**
- **No auto-commit**: explicit user authorization per AGENTS.md §8

## Implementation surface

### Data files

- `prototype/data/missions/missions.json` — 89+ new entries
- `prototype/data/missions/<zone>/*.json` — optional per-zone files (if schema extends)

### Schema additions (additive)

```python
# mission type extensibility
class MissionType(str, Enum):
    # Existing 6
    EXTRACTION = "extraction"
    RETRIEVAL = "retrieval"
    INFILTRATION = "infiltration"  # existing
    SABOTAGE = "sabotage"
    ESPIONAGE = "espionage"
    COURIER = "courier"
    # New 5 (this ADR)
    INVESTIGATION = "investigation"  # NEW
    DEFENSE = "defense"              # NEW
    DUAL_OBJECTIVE = "dual_objective"  # NEW
    EXTRACTION_V2 = "extraction_v2"  # high-risk variant
    STEALTH = "stealth"              # NEW (renamed from infiltration?)

# Mission chain
@dataclass(frozen=True, slots=True)
class MissionChain:
    id: str
    name: str
    missions: tuple[str, ...]  # mission IDs in order
    unlock_condition: str
    reward: RewardSpec
```

### Code

- `missions/missions.py` — extend `MissionRegistry` for new types
- `missions/chains.py` (NEW) — chain progression logic
- `missions/random.py` (NEW) — weighted random selection
- `missions/endgame.py` (NEW) — NG+ mission gating

### Tests

- `tests/unit/test_missions.py` — coverage for new types
- `tests/unit/test_mission_chains.py` (NEW) — chain progression
- `tests/unit/test_mission_random.py` (NEW) — weighted selection

### Design docs

- `design/systems/missions.md` — update with new types + chains
- `design/systems/procgen.md` — update with random selection rules
- `design/GDD.md` — update Open Questions section

### Testcases

- `testcases/missions/investigation.md` (NEW)
- `testcases/missions/defense.md` (NEW)
- `testcases/missions/dual_objective.md` (NEW)
- `testcases/missions/chains.md` (NEW)
- `testcases/missions/zone_balance.md` (NEW)

### i18n

- `data/i18n/{en,ko}.json` — mission names, descriptions, chain names
- New keys: `mission_type_{investigation,defense,dual_objective,extraction_v2,stealth}`

## Consequences (Pillar impact)

**Pillar 1 (The Run)**: Significant — replayability via 89+ new missions, 5 new types, 8 chains
**Pillar 2 (The Matrix)**: Neutral — all missions run in cyberspace (existing)
**Pillar 3 (The Flatline)**: Neutral — no new combat mechanics (uses existing PPL/ZDR)
**Pillar 4 (The Build)**: Indirect — new chains unlock new programs/augments
**Pillar 5 (The Style)**: Moderate — new mission types enable more Gibson-flavored scenarios

**Tests**: +30-40 tests covering new types, chains, random selection, NG+ gating
**Effort**: 4-6 sessions (estimated)
**Risk**: Low — additive only, existing 4513 tests must pass

## 열린 질문 (Open Questions)

1. **Mission type names**: "stealth" vs "infiltration" (current name)? Recommend "stealth" for clearer player mental model.
2. **Chain unlock timing**: After 3 missions or 5? Recommend 3 (faster progression).
3. **Random mission weighting**: Where does the weight come from? Recommend initial stats +0.1 per completion (self-balancing).
4. **Zone distribution**: Are proposed targets (35/35/35/30/35/30) appropriate, or adjust?
5. **Endgame missions**: 11 specific missions, or 1 chain + 10 random? Recommend 1 chain + 10 random.

## 다음 단계 (Next Steps)

If user **approves**:
1. Zone distribution analysis (TBD current counts)
2. Mission type taxonomy finalized (resolve Q1)
3. Data files drafted (start with 1 zone, then scale)
4. Design doc updates
5. Tests + i18n
6. Atomic commit (per roguelike_sprawl AGENTS.md §3.2 workflow)

If user **adjusts**:
- Resolve open questions
- Update target counts
- Revise phasing

If user **rejects**:
- This ADR goes to Superseded (or remains Draft)
- No mission expansion this phase
- Move to Axis 2 (ICE types) or end content expansion
