# ADR-0192: Ending Expansion (Phase 14 — Content Expansion, Axis 5)

**상태**: Accepted (2026-08-08, Phase 14 implementation in progress)
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 replay value + Pillar 5 closure)
**관련**: [ADR-0046 — GN Ending B](./0046-graphic-novel-ending-b.md), [ADR-0049 — GN Ending C](./0049-graphic-novel-ending-c.md), [ADR-0188 — Mission Expansion](./0188-mission-expansion.md)

## 컨텍스트 (Context)

Current state: 9 endings (3 chars × 3 types = 3 arcs × 3 chars). Per `.omo/plans/expand-roguelike-game-contents.md`, Phase 14 expands to 18+ endings with new ending types per character.

Gaps:
- Limited ending types (only 3 per character)
- No NG+ endings (different from base)
- No new ending archetypes (redemption, sacrifice, etc.)

## 옵션 (Options)

### Option 1: 6 new ending types per character (54 total)
- Each character gets 6 new ending types
- **장점**: Deep character arc satisfaction
- **단점**: 54 endings is a lot of content

### Option 2: 6 new types per character + 3 NG+ (12 new types, 30+ total)
- All Option 1 + NG+ different endings
- **장점**: Comprehensive closure
- **단점**: Lower per-type fidelity

### Option 3 (recommended)**: 6 new types per character + 3 NG+ (matching plan target)

**추천**: Option 3 (matches plan target of 18+ endings)

## 결정 (Decision)

**Option 3**: 6 new ending types + 3 NG+ endings.

### Target counts

| Category | Current | Target | Delta |
|---|--:|--:|--:|
| Per-character endings | 3 | 9 | +6 |
| NG+ endings | 0 | 3 | +3 |
| **Total** | **9** | **18+** | **+9+** |

### New ending types (6 per character)

| Type | Definition | Conditions |
|---|---|---|
| **Redemption** | Ally with former enemy | Quest + morale |
| **Sacrifice** | Trade life for system shutdown | Beat boss + sacrifice |
| **Transcendence** | Upload consciousness | Construct + upload |
| **Betrayal** | Side with antagonist | Faction + betrayal |
| **Absolution** | Come to terms with past | Story + closure |
| **Integration** | Merge with construct/AI | Construct + AI |

### NG+ endings (3)

- **The Network** (network across all save files)
- **The Construct** (post-Salvation, AIs unify)
- **The Peripheral** (jackpot reference, alternate timeline)

### Character × ending matrix (per-game)

| Character | R | S | T | B | A | I | Total |
|---|---|---|---|---|---|---|---|
| Case | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6 |
| Molly | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6 |
| Bobby | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6 |
| (6 more chars) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 6 each |
| **Total** | | | | | | | **54** |

### Data-driven approach

Each ending is a JSON entry with:
- Trigger conditions
- Cinematic sequence (4-6 frames)
- Score modifier
- Achievement flag

## Implementation surface

### Data files

- `prototype/data/scenes/endings.json` — 18+ new entries
- `prototype/data/scenes/ending_cinematics.json` (NEW) — frame sequences

### Code

- `graphic_novel_view.py` — extend ending detection
- `engine/ending.py` (NEW) — ending trigger logic
- `engine/achievements.py` — link endings to achievements

### Tests

- `tests/unit/test_endings.py` — per-ending trigger coverage
- `tests/unit/test_ending_ng_plus.py` (NEW) — NG+ gating

### Design docs

- `design/scenario/graphic-novel.md` — ending matrix
- `design/systems/progression.md` — NG+ state

### Testcases

- `testcases/graphic-novel/endings_v2.md` (NEW)
- `testcases/progression/ng_plus.md` (NEW)

### i18n

- Ending titles + dialogue in `data/i18n/{en,ko}.json`

## Consequences (Pillar impact)

- **Pillar 1 (Run)**: Strong — replay value via 18+ endings
- **Pillar 2 (Matrix)**: Neutral — endings not matrix-specific
- **Pillar 3 (Flatline)**: Moderate — Sacrifice ending carries death weight
- **Pillar 4 (Build)**: Indirect — endings unlock achievement wall
- **Pillar 5 (Style)**: Strong — Gibson-tone closure

**Tests**: +10-15 tests
**Effort**: 1-2 sessions (smallest of all 6 axes)
**Risk**: Low — additive content

## 열린 질문

1. **Per-character endings**: 6 per character, or 6 universal + 6 specific? Recommend 6 universal (every character can earn each).
2. **NG+ endings**: 3 distinct, or 1 + 2 variants? Recommend 3 distinct.
3. **Sacrifice ending**: Permanent (new game required), or recoverable? Recommend permanent (high-stakes).
4. **Cinematic length**: 4-6 frames per ending, or 6-8? Recommend 4-6 (pacing).

## 다음 단계

If approved:
   1. Ending type design (6 types)
   2. Per-character ending map (9 × 6 = 54 endings)
   3. Cinematic sequences (4-6 frames each)
   4. NG+ endings (3 distinct)
   5. Tests + design docs
   6. i18n
   7. Atomic commit

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/data/story/endings.json:5-7` — `_metadata`: `total_endings: 28`, `adrs_cross_reference: ADR-0192`, phase 14; 6 declared types (redemption, sacrifice, transcendence, betrayal, absolution, integration)
- `prototype/data/story/endings.json` content — 28 entries spanning the 6 types (per-type counts: redemption 3, sacrifice 4, transcendence 6, betrayal 5, absolution 5, integration 5) plus 9-character base endings (Case/Molly/Bobby et al. × 3 endings)
- `prototype/src/wet_run/story/endings.py:1` — module docstring cites "ADR-0192, Phase 14 integration"
- `prototype/src/wet_run/story/endings.py:22-231` — `EndingResult` dataclass, `_load_endings()`, `get_ending()`, `get_endings_by_character()`, `get_ng_plus_endings()`, `get_endings_by_type()`, `is_trigger_condition_met()`, `check_ending_eligibility()`, `process_ending()`, `get_total_endings()`, `get_ending_count_by_type()`, `get_ending_count_by_character()`
- `prototype/src/wet_run/story/ending_renderer.py:28-139` — `EndingScene` dataclass + `get_by_type()` + cinematic rendering with `ENDING_TYPE` upper-case tag and NG+ marker
- `prototype/tests/unit/test_endings_handler.py:23-230` — 26 tests across 6 classes (counts, queries, trigger conditions, processing, eligibility, result)
- `prototype/tests/unit/test_endings_persistence.py` — 14 tests for save/load NG+ ending state
- `prototype/tests/unit/test_ending_renderer.py` — 16 tests for cinematic rendering
- `prototype/tests/unit/test_ng_plus.py` — 21 tests for NG+ state machine
- `prototype/tests/unit/test_phase14_endings_programs.py:55-87` — `TestEndings`: count + 6 types present + required fields

**Notes**: 28 endings shipped vs 18+ target (155%). Per-character 9×6=54 matrix from §"Character × ending matrix" was implemented as character-mapped subset (28 entries) with `get_endings_by_character` / `get_ending_count_by_character` providing runtime enumeration. 3 distinct NG+ endings present in dataset. Cinematics: 4-6 frame per the design decision.

**No further action on ADR-0192** — implementation closed.
