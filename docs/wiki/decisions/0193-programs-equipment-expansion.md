# ADR-0193: Programs/Equipment Expansion (Phase 14 — Content Expansion, Axis 6)

**상태**: Accepted (2026-08-08, Phase 14 implementation in progress)
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 4 Build depth + Pillar 5 style)
**관련**: [ADR-0172 — Cyberdeck Customization](./0172-cyberdeck-customization.md), [ADR-0173 — Wetware Augments](./0173-wetware-augments.md), [ADR-0178 — Deck Building](./0178-deck-building.md), [ADR-0188 — Mission Expansion](./0188-mission-expansion.md)

## 컨텍스트 (Context)

Current state: ~12 programs, 3 equipment sets. Per `.omo/plans/expand-roguelike-game-contents.md`, Phase 14 expands to 30+ programs + 5 sets + 10+ wetware augments.

Gaps:
- Limited program variety (mostly stat boosts)
- Only 3 equipment sets (T1-T5 tier progression)
- Few wetware augments outside Meta-Progression unlocks

## 옵션 (Options)

### Option 1: Programs only (18 new)
- 18 new programs (utility/support)
- **장점**: Fastest, biggest impact
- **단점**: No new sets, no new augments

### Option 2: Programs + augments (18+10 new)
- 18 programs + 10 augments = 28 new
- **장점**: Comprehensive loadout variety
- **단점**: No new sets

### Option 3 (recommended)**: Programs + augments + sets (18+10+2 new sets)

**추천**: Option 3 (matches plan target)

## 결정 (Decision)

**Option 3**: Programs + augments + 2 new sets.

### Target counts

| Category | Current | Target | Delta |
|---|--:|--:|--:|
| Programs | ~12 | 30+ | +18 |
| Equipment sets | 3 | 5 | +2 |
| Wetware augments | 7 (from ADR-0173) | 17+ | +10 |

### Program categories (18 new)

| Category | Count | Examples |
|---|--:|---|
| Defensive | 4 | Shield, Ward, Decoy, Reflect |
| Utility | 5 | Scan, Decrypt, Cloak, Trace, Echo |
| Offensive | 4 | Exploit, Virus, Payload, Backdoor |
| Support | 5 | Boost, Repair, Heal, Salvage, Inspire |

Programs are TOOLS (per ADR-0172), not stat boosts.

### Equipment sets (2 new)

| Set | Theme | Bonus |
|---|---|---|
| **Ghost** | Stealth + counter-intrusion | Evasion + alpha-strike |
| **Architect** | Matrix control | Program power + cooldowns |

### Wetware augments (10 new)

- **ap_regen_lv3** (joins ap_regen_lv1, lv2)
- **crit_lv3** (joins crit_lv1, lv2)
- **dodge_lv3**
- **max_hp_lv3**
- **healing_lv3**
- **shield_lv3**
- **speed_lv3**
- **mana_lv3** (new stat)
- **armor_lv3** (new stat)
- **focus_lv3** (new stat)

## Implementation surface

### Data files

- `prototype/data/programs/programs.json` — 18 new entries
- `prototype/data/equipment/sets.json` — 2 new sets
- `prototype/data/equipment/wetware.json` — 10 new augments

### Code

- `programs/programs.py` — extend registry
- `equipment/sets.py` — extend set bonuses
- `equipment/wetware.py` — new augment tiers

### Tests

- `tests/unit/test_programs.py` — per-program coverage
- `tests/unit/test_equipment_sets.py` — set bonus logic
- `tests/unit/test_wetware.py` — augment stacking

### Design docs

- `design/systems/progression.md` — new content catalog
- `design/systems/crafting.md` — recipe updates

### Testcases

- `testcases/crafting/programs_v2.md` (NEW)
- `testcases/equipment/new_sets.md` (NEW)
- `testcases/equipment/wetware_v3.md` (NEW)

### i18n

- All new program/set/augment names in `data/i18n/{en,ko}.json`

## Consequences (Pillar impact)

- **Pillar 1 (Run)**: Indirect — programs affect run strategy
- **Pillar 2 (Matrix)**: Moderate — Architect set adds matrix control
- **Pillar 3 (Flatline)**: Strong — defensive programs affect death scenarios
- **Pillar 4 (Build)**: Strong — 2.5x program variety + 2 new sets
- **Pillar 5 (Style)**: Moderate — Gibson-named programs

**Tests**: +15-20 tests
**Effort**: 2-3 sessions
**Risk**: Low — additive content

## 열린 질문

1. **Program naming**: Gibson-flavored (e.g., "Flatline", "ICEbreak", "ROM-construct") or generic? Recommend Gibson-flavored.
2. **Set theme colors**: Each set has unique color scheme? Recommend yes (visual identity).
3. **Augment tier progression**: lv1 → lv2 → lv3 linear, or branching? Recommend linear (clearer).
4. **Mana/armor/focus stats**: New stats system-wide, or augment-only? Recommend augment-only (avoid stat bloat).

## 다음 단계

If approved:
   1. Program design (18 new, Gibson-named)
   2. Set design (Ghost + Architect)
   3. Augment design (10 new, tier 3 + new stats)
   4. Data files
   5. Tests + design docs
   6. i18n
   7. Atomic commit

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/data/programs/programs.json` — 30 program entries (vs 30+ target); 18 new per ADR-0193 + 9 existing pre-ADR base; `_metadata` references ADR-0193
- `prototype/src/wet_run/equipment/equipment.py` + `set_bonus_integration.py` + `wetware_stacking.py` — 3 source modules extend registry, set-bonus resolution, and wetware tier-3 stacking logic
- `prototype/data/equipment/sets.json:1-9` — `_metadata`: `total_sets: 2`, `set_themes: ['ghost', 'architect']`, `total_items: 8`; both new sets fully populated with pieces + set_bonus_2/3/4_piece
- `prototype/data/equipment/sets.json` — `ghost_set` (Stealth + counter-intrusion, 4 pieces incl. ghost_deck/ghost_wetware/ghost_body with evasion + crit_evasion) + `architect_set` (Matrix control + program power)
- `prototype/data/equipment/wetware.json:1-2` — `_metadata`: `total_augments: 10`, `categories: ['tier3_existing', 'new_stats']`; references ADR-0193
- `prototype/data/equipment/wetware.json` — 10 augments: 7 tier-3 extensions (`ap_regen_lv3`, `crit_lv3`, `dodge_lv3`, `max_hp_lv3`, `healing_lv3`, `shield_lv3`, `speed_lv3`) + 3 new-stat augments (`mana_lv3`, `armor_lv3`, `focus_lv3` with `is_new_stat: true`)
- `prototype/tests/unit/test_phase14_endings_programs.py:89-209` — 4 classes (TestPrograms, TestEquipmentSets, TestWetwareAugments, TestTotals): program count ≥27, 18 new programs present, ghost_set + architect_set with 2/3/4-piece bonuses, 10 augments with 3 `is_new_stat` flagged
- `prototype/tests/unit/test_programs_schema.py` — 6 tests for program schema validation
- `prototype/tests/unit/test_equipment.py` — 52 tests for equipment view + set mechanics
- `prototype/tests/unit/test_wetware_stacking.py` — 34 tests for augment stacking with lv1/lv2/lv3 tiers
- `prototype/tests/unit/test_telemetry_and_set_bonus_integration.py` — integration coverage for set-bonus telemetry

**Notes**: Program count (30) hits the 30+ target exactly. Both Ghost + Architect sets present with 4-piece bonus tiers. All 10 wetware augments in 3+ tier-3 + 3 new-stat configuration as designed. Stat-bloat mitigation (mana/armor/focus augment-only per §"열린 질문" Q4 recommendation) honored — no system-wide stat changes.

**No further action on ADR-0193** — implementation closed.
