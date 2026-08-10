# ADR-0189: ICE Type Expansion (Phase 12 — Content Expansion, Axis 2)

**상태**: Accepted (2026-08-08, Phase 12 implementation in progress)
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 3 combat variety + Pillar 5 atmosphere)
**관련**: [ADR-0005 — Cyberspace Representation](./0005-cyberspace-representation.md), [ADR-0148 — Combat Depth Expansion](./0148-combat-depth-expansion.md), [ADR-0188 — Mission Expansion](./0188-mission-expansion.md)

## 컨텍스트 (Context)

Current state: 41 ICE types across 6 archetypes (Standard/Watchdog/Black/Goliath/Construct/Construct-proxy). Per `.omo/plans/expand-roguelike-game-contents.md`, Phase 12 expands to 60+ ICE types with faction-specific designs and cyberspace hazards.

Gaps:
- No faction-specific ICE (faction currently affects dialogue, not combat)
- No variant tiers (ascended, corrupted, defensive)
- No cyberspace hazards (non-ICE obstacles)

## 옵션 (Options)

### Option 1: Faction-specific ICE only (25 new)
- 5 factions × 5 types each = 25 new ICE
- **장점**: Strong faction identity, narrative coherence
- **단점**: No hazards, no variant system

### Option 2: Faction ICE + variants + hazards (19+ new)
- 25 faction ICE + 10 variants + 5 hazards = 40 new
- **장점**: Comprehensive variety
- **단점**: 3 different subsystems to design

### Option 3: Variants + hazards only (15 new)
- 10 variants + 5 hazards = 15 new
- **장점**: Smaller scope, faster
- **단점**: No faction-specific identity

**추천**: Option 2 (comprehensive coverage, complements Axis 4 boss expansion)

## 결정 (Decision)

**Option 2**: Faction ICE + variants + hazards.

### Target counts

| Category | Current | Target | Delta |
|---|--:|--:|--:|
| Base archetypes | 6 | 6 | 0 |
| Faction-specific | 0 | 25 | +25 |
| Variant tiers | 0 | 10 | +10 |
| Cyberspace hazards | 0 | 5 | +5 |
| **Total** | **41** | **60+** | **+19+** |

### Faction-ICE mapping

| Faction | Personality | ICE type | Behavior |
|---|---|---|---|
| Hosaka | Corporate | Analyst | Medium defense, alert propagation |
| Sense/Net | Media | Spin | Information warfare, alibi |
| Yakuza | Enforcement | Brute | High offense, brutality |
| T-A | Construct | Daemon | High HP, multi-phase |
| Loa | Vodou | Loa | Status effects, malware |

### Variant tiers

- **Ascended** (5 ICE): tier 5 versions of existing archetypes
- **Corrupted** (3 ICE): glitchy, unpredictable behavior
- **Defensive** (2 ICE): shield-first tactics

### Cyberspace hazards

- **Antivirus Sweep**: periodic node damage (avoid by moving)
- **Trace Route**: spawns ICE if player stays in one node too long
- **Data Corruption**: reduces program effectiveness
- **System Lag**: slows player actions
- **Blackout**: temporary node lockout

## Implementation surface

### Data files

- `prototype/data/combat/ice_types.json` — 40+ new entries
- `prototype/data/combat/ice_faction_map.json` (NEW) — faction → ICE mapping
- `prototype/data/combat/ice_variants.json` (NEW) — variant tier specs
- `prototype/data/combat/cyberspace_hazards.json` (NEW) — hazard definitions

### Code

- `combat/ice.py` — extend `IceType` registry
- `combat/ice_faction.py` (NEW) — faction-ICE binding
- `combat/ice_variants.py` (NEW) — variant tier logic
- `combat/cyberspace_hazards.py` (NEW) — hazard system

### Tests

- `tests/unit/test_ice_faction.py` (NEW) — per-faction coverage
- `tests/unit/test_ice_variants.py` (NEW) — variant behavior
- `tests/unit/test_cyberspace_hazards.py` (NEW) — hazard triggers

### Design docs

- `design/systems/combat.md` — new ICE archetypes
- `design/systems/hacking.md` — cyberspace hazards

### Testcases

- `testcases/combat/ice_faction.md` (NEW)
- `testcases/combat/ice_variants.md` (NEW)
- `testcases/combat/cyberspace_hazards.md` (NEW)

### i18n

- New ICE names + descriptions in `data/i18n/{en,ko}.json`

## Consequences (Pillar impact)

- **Pillar 1 (Run)**: Indirect — faction ICE tied to faction reputation
- **Pillar 2 (Matrix)**: Strong — cyberspace hazards add new dimension
- **Pillar 3 (Flatline)**: Strong — more ICE variety = varied death scenarios
- **Pillar 4 (Build)**: Indirect — new programs needed to counter new ICE
- **Pillar 5 (Style)**: Strong — faction-specific Gibson-flavored encounters

**Tests**: +15-20 tests
**Effort**: 2-3 sessions
**Risk**: Low — additive only

## 열린 질문

1. **Faction ticker ratio**: 5 per faction, or 5-3-3-3-3 (T-A bigger)? Recommend 5-5-5-5-5 for parity.
2. **Variant tier design**: Soft stat boosts, or new mechanics? Recommend mechanics (e.g., Corrupted has random behavior).
3. **Hazard frequency**: Encounter rate per zone? Recommend 1-2 per zone per run.
4. **Balance**: Does adding 19 new ICE affect HEAL cycle weight (Pillar 3)? Recommend counter-check during integration.

## 다음 단계

If approved:
1. Faction-ICE mapping finalized
2. Data files drafted (1 faction first, then scale)
3. Code integration
4. Tests + design docs
5. i18n
6. Atomic commit
