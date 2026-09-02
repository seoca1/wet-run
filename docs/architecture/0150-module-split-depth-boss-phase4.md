# ADR-0150: Module Split — `depth.py` (311 LOC) + `boss_phase4.py` (394 LOC)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (모듈 사이즈 정책 준수, ADR-0110 follow-up)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0148 — Combat Depth Expansion](./0148-combat-depth-expansion.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0141 — Additional Module Splits](./0141-additional-module-splits.md)

## 컨텍스트 (Context)

ADR-0110 (모듈 사이즈 정책) 의 권장 한도:

- **250 LOC**: 신규 모듈 권장 한도
- **500 LOC**: PR 거부 기준
- **700-800 LOC**: 1회성/단발성 모듈 예외 허용
- **1000+ LOC**: 신규 ADR 필수 (정당화 + 분할 계획 OR 보유 사유 명시)

**현재 상태** (ADR-0148 + ADR-0149 완료 후):

| 모듈 | LOC | Status | 비고 |
|---|---:|---|---|
| `combat/depth.py` | 311 | ⚠ 124% of 250 ceiling | ADR-0148 |
| `combat/boss_phase4.py` | 394 | ⚠ 157% of 250 ceiling | ADR-0149 |

두 모듈 모두 1-topic cohesive 이지만, ADR-0110 권장 한도 초과. ADR-0148/0149 의 "모듈 사이즈" Consequences 섹션에서 후속 검토로 명시.

**Split 이유**:
1. **Discoverability**: 4 sub-feature (counter/defense/companion/aggression) + 3 sub-feature (mechanics/intro/taunts) 가 1 module 에 몰려 있어, 신규 contributor 가 찾기 어려움.
2. **Test isolation**: `test_combat_depth.py` (41 tests) + `test_boss_phase4.py` (49 tests) 가 1 module 에 의존. 모듈 분리 시 test 도 자연스럽게 분리.
3. **Future extensibility**: Phase 5+ (v1.2.0+) 에서 sub-feature 추가 시 1 module 의 *모든* 함수와 import 가 영향. 분리 시 sub-feature 만 영향.
4. **ADR-0110 정합**: 250 ceiling 준수가 "The Build" 의 Pillar 3.

**기술 제약**:
- 기존 `from wet_run.combat.depth import ...` 사용처 (combat/__init__.py, state.py, test_combat_depth.py, test_construct_companion.py) **backward-compatible** 유지.
- 신규 `depth/` sub-package 의 `__init__.py` 가 모든 symbol re-export.
- `boss_phase4/` sub-package 도 동일 패턴.

## 고려한 옵션

### Option 1: 현 상태 유지 (depth.py + boss_phase4.py 1 module)

- **설명**: 두 module 모두 1-topic cohesive 이므로 분할 불필요. ADR-0110 의 "1000+ LOC" 만 의무, 현재 < 500 이므로 OK.
- **장점**:
  - 변경 범위 최소 — 분할 0.
  - 1-topic cohesive 유지.
- **단점**:
  - ADR-0110 권장 (250) 초과.
  - Discoverability / test isolation 부족.
- **Pillar 정합**:
  - P3 (The Build): 모듈 사이즈 정책 정합 위반 (soft).

### Option 2: depth.py 4-way split + boss_phase4.py 3-way split (권장)

- **설명**: 
  - `depth/` sub-package: `counter.py` + `defense.py` + `companion.py` + `aggression.py` + `__init__.py` (5 files, each < 250)
  - `boss_phase4/` sub-package: `mechanics.py` + `intro.py` + `taunts.py` + `__init__.py` (4 files, each < 250)
- **장점**:
  - ADR-0110 250 ceiling 준수 (7 files, each < 250).
  - Discoverability 향상 (sub-feature 별 module).
  - Test isolation (test_depth_counter, test_depth_defense, ... 분리 가능).
  - Future extensibility (v1.2.0+ sub-feature 추가 시 1 file 만 영향).
- **단점**:
  - 변경 범위 중간 — 9 new files, 2 old files removed, `combat/__init__.py` re-export 갱신, tests 갱신.
  - Total LOC 약간 증가 (각 module 의 docstring + import 로 ~10-15% 증가).
- **Pillar 정합**:
  - P3 (The Build): ADR-0110 250 ceiling 준수.

### Option 3: depth.py 2-way split + boss_phase4.py 2-way split

- **설명**:
  - `depth/` sub-package: `reactive.py` (counter + defense) + `proactive.py` (companion + aggression) + `__init__.py` (3 files)
  - `boss_phase4/` sub-package: `boss_fight.py` (mechanics) + `boss_narrative.py` (intro + taunts) + `__init__.py` (3 files)
- **장점**:
  - 변경 범위 더 작음 (5 new files).
  - 1 module 의 *역할* 기준 분할 (reactive vs proactive).
- **단점**:
  - 각 file 이 여전히 200+ LOC (sub-feature 2-3 묶음).
  - Discoverability 중간 (sub-feature 별 분할이 더 명확).
- **Pillar 정합**:
  - P3: ADR-0110 250 ceiling 준수 (2-3 sub-feature 묶음).

## 추천 (Recommendation)

**Option 2** (depth.py 4-way + boss_phase4.py 3-way).

이유:
1. **Pillar 3 (The Build) 정합**: 7 files 모두 250 ceiling 이하 — ADR-0110 100% 준수.
2. **Discoverability**: sub-feature 별 module — 신규 contributor 가 "counter window" 찾으려면 `depth/counter.py` 만 보면 됨.
3. **Test isolation**: 향후 `test_depth_counter.py` + `test_depth_defense.py` + ... 분리 가능 (현재는 1 file 유지).
4. **Future extensibility**: v1.2.0+ 에서 sub-feature 추가 시 1 file 만 영향 (예: `depth/counter.py` 에 *react_time* parameter 추가).
5. **Backward-compatibility**: `combat/__init__.py` 의 re-export 가 모든 symbol 유지. 기존 `from wet_run.combat.depth import ...` 코드 변경 불필요.
6. **Risk**: 변경 범위 중간 (9 new files, 2 old files removed) 이지만, 순수 리팩토링 (no behavior change) — 1000+ LOC 새 module 0.

## 사용자 결정 (Decision)

[x] Option 2 (depth.py 4-way + boss_phase4.py 3-way) — 사용자 승인 (2026-08-07 "continue" follow-up)
[ ] Option 1 (현 상태 유지)
[ ] Option 3 (2-way split)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. 신규 sub-package: `combat/depth/`

```
combat/depth/
├── __init__.py      (re-exports + dispatch, ~50 LOC)
├── counter.py       (open_counter_window, is_counter_window_open, apply_counter_attack, counter_window_active_and_expired, COUNTER_WINDOW_MS, COUNTER_DAMAGE_MULTIPLIER, COUNTER_STUN_MS, ~50 LOC)
├── defense.py       (apply_wisp, apply_shield_barrier, apply_wardrone, tick_defense_durations, tick_defense_expiry, WISP_SHIELD, WISP_DURATION_MS, SHIELD_BARRIER, WARDRONE_SHIELD, WARDRONE_DURATION_MS, WARDRONE_COUNTER_DMG, WARDRONE_COUNTER_INTERVAL_MS, DefenseProgram, ~120 LOC)
├── companion.py     (dixie_use_skill, dixie_choose_skill, DIXIE_DECOMPILE_*, DIXIE_ICEBREAKER_*, CompanionSkillId, ~100 LOC)
└── aggression.py    (_combatant_aggression, _skill_use_probability, enemy_should_use_skill, AggressionLevel, AGGRESSION_PROBABILITY, ~50 LOC)
```

### 2. 신규 sub-package: `combat/boss_phase4/`

```
combat/boss_phase4/
├── __init__.py      (re-exports + apply_phase4_mechanic dispatch, ~50 LOC)
├── mechanics.py     (should_trigger_phase4, trigger_phase4, apply_personality_drift, apply_family_vote, apply_construct_merge, apply_ground_slam, apply_glitch_burst, Phase4Mechanic, all mechanic constants, ~180 LOC)
├── intro.py         (get_boss_intro, apply_boss_intro_enhancement, BossIntroEnhancement, BOSS_INTRO, ~60 LOC)
└── taunts.py        (pick_death_taunt, apply_death_taunt, DEATH_TAUNTS, _normalize_boss_id, _BOSS_ALIASES, ~60 LOC)
```

### 3. 제거

- `combat/depth.py` → sub-package 로 이동
- `combat/boss_phase4.py` → sub-package 로 이동

### 4. `combat/__init__.py` 갱신

기존 24 re-exports + 신규 sub-package re-exports 유지. backward-compatible.

### 5. Tests 갱신

- `test_combat_depth.py` — `from wet_run.combat.depth import ...` → 변경 없음 (sub-package `__init__.py` 가 re-export).
- `test_boss_phase4.py` — 동일.
- `test_construct_companion.py` — 동일.

### 6. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | 변경 없음 | 기존 test 유지 |
| P2 (The Matrix) | 변경 없음 | 기존 test 유지 |
| P3 (The Build) | ADR-0110 250 ceiling 준수 | 각 file 의 LOC 확인 |
| P4 (The Build) | 변경 없음 | 기존 test 유지 |
| P5 (The Style) | 변경 없음 | 깁슨 어휘 유지 |

## 영향 받는 항목

- `prototype/src/wet_run/combat/depth.py` (removed)
- `prototype/src/wet_run/combat/depth/` (new sub-package, 5 files)
- `prototype/src/wet_run/combat/boss_phase4.py` (removed)
- `prototype/src/wet_run/combat/boss_phase4/` (new sub-package, 4 files)
- `prototype/src/wet_run/combat/__init__.py` (re-export 갱신)
- `prototype/src/wet_run/combat/state.py` (import path 변경 — `depth.counter` import)
- `prototype/src/wet_run/engine/combat_view_state.py` (import path 변경 — `boss_phase4.taunts` import)
- `prototype/tests/unit/test_combat_depth.py` (변경 없음, backward-compat)
- `prototype/tests/unit/test_boss_phase4.py` (변경 없음, backward-compat)
- `prototype/tests/unit/test_construct_companion.py` (변경 없음)
- `log.md` (ADR-0150 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0150 entry)

## 관련 결정

- ADR-0110 — 모듈 사이즈 정책 (250 권장, 1000+ 의무)
- ADR-0141 — Additional Module Splits (matrix_view, combat/state 분할)
- ADR-0142 — graphic_novel_view Split v2 (3-way split)
- ADR-0143 — combat_view Split (4-way split)
- ADR-0144 — combat/effects Data Extraction
- ADR-0145 — combat/effects_vfx 3-way split
- ADR-0148 — Combat Depth Expansion (depth.py 의 원본)
- ADR-0149 — Boss Phase 4 Finale (boss_phase4.py 의 원본)

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/depth/` (sub-package, 6 files) — replaces `combat/depth.py`:
  - `__init__.py:1-98` — re-exports + dispatch
  - `counter.py:1-88` — counter window logic
  - `defense.py:1-147` — Wisp/Shield/Wardrone stackable defense
  - `companion.py:1-135` — Dixie companion skills
  - `aggression.py:1-74` — ICE aggression tier probability
  - `personality.py:1-166` — ICE personality aggregation (extra, post-ADR)
- `prototype/src/wet_run/combat/boss_phase4/` (sub-package, 5 files) — replaces `combat/boss_phase4.py`:
  - `__init__.py:1-94` — re-exports + `apply_phase4_mechanic` dispatch
  - `mechanics.py:1-212` — 5 Phase 4 mechanics
  - `intro.py:1-116` — boss intro enhancement
  - `taunts.py:1-83` — death taunts library
  - `trigger.py:1-83` — trigger logic (extra, post-ADR)
- `prototype/src/wet_run/combat/__init__.py` — re-exports both sub-packages (backward-compat preserved)
- `prototype/tests/unit/test_combat_depth.py:1-501` — 41 tests (unchanged import path)
- `prototype/tests/unit/test_boss_phase4.py:1-495` — 49 tests (unchanged import path)
- `prototype/tests/unit/test_construct_companion.py` — unchanged

**Notes**: All 7 planned files shipped (4 depth + 3 boss_phase4). Two extra files (`depth/personality.py` 166 LOC, `boss_phase4/trigger.py` 83 LOC) added in subsequent work — see ADR-0148 / ADR-0149 Implementation Status notes. Single-file depth.py and boss_phase4.py no longer exist (sub-packages only). All ADR-0110 LOC ceilings met (each file < 250 LOC, maxboss_phase4/mechanics.py 212).

**No further action on ADR-0150** — implementation closed.

## 변경 이력

- 2026-08-07: Draft 작성 (ADR-0148 + ADR-0149 follow-up, A+B+C plan 후속)
- 2026-08-07: Accepted (Option 2, 사용자 "continue" follow-up)
