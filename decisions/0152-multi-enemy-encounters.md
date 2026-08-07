# ADR-0152: Multi-Enemy Encounters (1v2/1v3) + HEAL Rebalance 20%→15%

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (전투 깊이 강화, v1.2.0+ 핵심)
**관련**: [ADR-0003 — RT-MS Combat](./0003-combat-system.md), [ADR-0012 — PPL/ZDR](./0012-difficulty-rating.md), [ADR-0147 — Salvage Phase 6+](./0147-data-salvage-phase6.md), [ADR-0148 — Combat Depth](./0148-combat-depth-expansion.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0151 — Intel Items](./0151-info-market-intel-items.md)

## 컨텍스트 (Context)

`combat/state.py` (863+ LOC) + `combat/state_models.py` (248 LOC) 의 survey 결과:

**이미 존재** (multi-enemy 기반 인프라):
- `CombatState.enemies: tuple[Combatant, ...]` — multi-enemy container
- `CombatState.target_index: int` + `target` property — target selection
- `__post_init__` 가 `enemies` ↔ `enemy` 자동 sync
- `_end_combat` (engine/combat_view_state.py:459) 가 `all(e.hp <= 0 for e in state.enemies)` 로 multi-enemy aware
- `tick_dixie_ally` (Cycle 2, ADR-0148) 가 `state.target` 만 공격 (1vN 확장 필요)
- 7+ 기존 tests 가 `enemies=(e1, e2)` / `enemies=(e1, e2, e3)` 패턴 사용

**부재** (multi-enemy *동작* layer):
- `step_combat` 의 player auto-attack 가 `state.target` 만 공격 → 나머지 enemies 가 *free hit* (player 만 다대일)
- `use_skill` 이 `state.target` 만 dispatch → AoE skill (PIERCE, DOT 등) 도 단일 대상
- `cycle_target(state)` helper 없음 → Tab key 로 target 전환 불가
- Matrix spawn logic 없음 → node encounter 가 항상 1v1
- HEAL_PCT 가 20% (0.20) → 1v3 시 HEAL 1회로 *trivial heal* (Pillar 3 weight 약화)

**왜 지금?** (v1.2.0+ bridge 완료 후)
- ADR-0147 (HEAL 20%): 1v1 기준 Pillar 3 weight 보존. 1vN 에서는 *HEAL 1회가 3명 damage 보상* → trivial
- ADR-0148 (counter window + defense + alarm salvage): 1vN 에서 alarm 더 빠르게 accumulate → 보완 메커니즘
- ADR-0151 (intel items, alarm_reducer -2): player 가 *경보 감소* 를 구매 가능 → 1vN risk 완화
- **결론**: 1vN 의 Pillar 3 weight 가 *이제 보완 가능* (HEAL 20% → 15% + alarm-aware salvage + intel alarm_reducer)

**해결 방향** (ADR-0152):
1. `step_combat` 의 player auto-attack: `state.target` 만 → **모든 alive enemy** 순차 공격
2. `use_skill` 의 multi-target dispatch: `target=ALL` 또는 `is_aoe=True` flag → 모든 alive enemy 적용
3. `cycle_target(state)` helper: Tab key → `target_index` 순환
4. Matrix spawn: Grade 3+ 시 1v2, Grade 5+ 시 1v3 (점진적)
5. HEAL_PCT: 0.20 → **0.15** (Pillar 3 weight 보존, 1vN 에서 trivial 방지)
6. Tests: 12+ new tests (multi-target damage, cycle_target, HEAL rebalance, matrix spawn)

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: 1vN → run weight 증가 (alarm 더 빠르게 accumulate) → 보완: alarm-aware salvage + alarm_reducer
- **Pillar 3 (The Flatline)**: HEAL 15% + 1-of-4 choice + 1vN 시 *player 가 더 strategic* 해야 함 → 무게 보존
- **Pillar 4 (The Build)**: in-run only (변경 없음)
- **Pillar 5 (The Style)**: 깁슨 어휘 + multi-enemy 묘사 ("swarm", "pack", "encircle")

**기술 제약**:
- 신규 모듈 250 LOC ceiling (ADR-0110). Cycle 8 work 는 ~200 LOC 예상.
- HEAL_PCT 변경 → 기존 test_salvage_scenarios 의 4 xfail → 4 pass + 8 new (TC-001~004, 007~012) → 6 pass 후 회귀
- Matrix encounter spawn → 기존 111 missions 의 encounter table 영향

## 고려한 옵션

### Option 1: Multi-Enemy + HEAL Rebalance (전체)

- **설명**: 위 6개 sub-feature 모두 구현.
- **장점**:
  - v1.2.0+ 핵심 depth 완성.
  - Pillar 3 weight *이제* 보완 메커니즘으로 보존 가능.
  - 기존 7+ multi-enemy tests 활용 → 추가 작업 최소화.
  - Player 가 "pick target" skill ceiling 추가.
- **단점**:
  - 변경 범위 큼 — `step_combat`, `use_skill`, matrix spawn, HEAL_PCT, tests, i18n, design.
  - HEAL 20% → 15% 는 *rebalance* — 기존 test (TC-001~004) 의 70 (T1 100*0.20+50) → 65 (T1 100*0.15+50) 변경.
- **Pillar 정합**:
  - P1: alarm-aware salvage + intel alarm_reducer 로 보완.
  - P3: HEAL 15% + alarm-aware CRED 로 weight 보존.

### Option 2: Multi-Enemy 만 (HEAL 변경 안 함)

- **설명**: HEAL 20% 유지, multi-enemy 만 구현.
- **장점**: HEAL 변경으로 인한 기존 test 영향 없음.
- **단점**:
  - 1vN 에서 HEAL 20% 가 *trivial* (3명 damage → 1회 HEAL로 60 회복).
  - Pillar 3 weight 약화.
  - Alarm-aware salvage (50% reduction at alarm ≥ 3) 가 *1v3 에서 도달 어려움* (alarm 빠르게 accumulate 되지만 HEAL 1회가 alarm -2 정도 효과).
- **Pillar 정합**:
  - P3: weight 약화 (1vN 의 trivial HEAL).

### Option 3: HEAL Rebalance 만 (multi-enemy 안 함)

- **설명**: HEAL 20% → 15% 만, multi-enemy 미구현.
- **장점**: HEAL 변경만 → 변경 범위 최소.
- **단점**:
  - Multi-enemy 미구현 → v1.2.0+ 핵심 미완성.
  - Player 가 1v1 만 경험 → 1v2/1v3 의 게임성 누락.
- **Pillar 정합**:
  - P3: weight 보존되지만 *multi-enemy 게임성* 부재.

## 추천 (Recommendation)

**Option 1** (Multi-Enemy + HEAL Rebalance, 전체).

이유:
1. **v1.2.0+ 핵심 완성**: multi-enemy + HEAL rebalance 가 *함께* 작동해야 Pillar 3 weight 보존. HEAL 만 변경하면 1vN 게임성 누락. multi-enemy 만 구현하면 trivial HEAL 문제.
2. **보완 메커니즘 성숙**: ADR-0147 (alarm salvage) + ADR-0148 (counter window) + ADR-0151 (alarm_reducer -2) 가 *이미 존재* → 1vN 의 Pillar 3 risk 보완.
3. **기존 인프라 활용**: `CombatState.enemies` + `target_index` + `target` property + 7+ multi-enemy tests 가 *이미 존재* → 추가 작업 최소화.
4. **점진적 난이도**: Grade 3+ (1v2) → Grade 5+ (1v3) — player 가 Grade 올라가면서 점진적.
5. **Pillar 1 (Run) weight 향상**: 1vN 의 alarm accumulate 가 자연스러운 difficulty curve.
6. **Test 표면 폭증 가능**: 12+ new tests (multi-target damage, cycle_target, HEAL rebalance, matrix spawn) → 기존 41 salvage + 49 boss + 25 intel + 6 market integration = 121 tests 에 +12.

**순서** (Cycle 8, 1 sub-session):
1. HEAL_PCT 0.20 → 0.15 변경 + 기존 test_salvage_scenarios 의 expected value update
2. `combat/state.py::step_combat` 의 player auto-attack: `state.target` 만 → 모든 alive enemy 순차
3. `combat/state.py::use_skill` 의 multi-target dispatch: `target=ALL` flag
4. `cycle_target(state)` helper: Tab key → `target_index` 순환
5. Matrix encounter spawn: Grade 3+ 1v2, Grade 5+ 1v3
6. i18n: 8 keys (multi-enemy encounter + HEAL rebalance messages)
7. Tests: 12+ new

## 사용자 결정 (Decision)

[x] Option 1 (Multi-Enemy + HEAL Rebalance, 전체) — 2026-08-07 Cycle 8 채택
[ ] Option 2 (Multi-Enemy 만)
[ ] Option 3 (HEAL Rebalance 만)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. 신규 모듈

`prototype/src/roguelike_sprawl/combat/multi_enemy.py` (NEW, ~200 LOC):

```python
"""Multi-enemy encounter support (ADR-0152, Cycle 8).

Functions:
- cycle_target(state) — Tab key, target_index 순환
- all_alive_enemies(state) — list of enemies with hp > 0
- is_aoe_skill(skill) — skill.target == "all" or is_aoe flag
- apply_aoe_damage(state, skill) — damage all alive enemies
- spawn_encounter(grade, faction, ice_kinds) — return 1v1/1v2/1v3 Combatant tuple
- encounter_count_for_grade(grade) — int (1/2/3)
"""
```

### 2. HEAL_PCT 변경

- `combat/salvage.py::HEAL_PCT: float = 0.15` (was 0.20)
- 기존 `test_salvage_scenarios.py` 의 TC-001~004 expected value update:
  - T1 HP 50/100: +20 → +15 (50 + 15 = 65)
  - T1 max HP: HP 50/100 → +15
  - T1 max HP: HP 95/100 → 100 (clamped, 변경 없음)
  - T1 max HP: HP 5/100 → 20 (5 + 15)
  - T1 max HP: HP 30/100 → 30 (no heal, 변경 없음)
  - T1 HP 50/100: +15 (was +20, 변경)
  - T3 HP 50/150: +22.5 → 72.5 (was +30 → 80, 변경)
  - T5 HP 100/300: +45 → 145 (was +60 → 160, 변경)

### 3. CombatState 변경

- `CombatState.cycle_target()` method 추가: `target_index = (target_index + 1) % len(alive_enemies)`
- `step_combat` 의 player auto-attack: `for enemy in state.enemies: if enemy.hp > 0: ...` (loop instead of single target)
- `Skill.aoe: bool = False` field 추가 (기존 `aoe: bool = False` 이미 존재, verify)

### 4. Matrix encounter spawn

- `matrix/encounter_spawn.py` (NEW, ~100 LOC) 또는 `matrix/node.py` patch
- `encounter_count_for_grade(grade) -> int`:
  - Grade 1-2: 1 enemy
  - Grade 3-4: 2 enemies
  - Grade 5-6: 3 enemies
- Node encounter 가 matrix load 시 encounter_count 결정 + ICE spawn

### 5. AppState 확장

- `AppState.encounter_count: int = 0` (현재 encounter enemy 수, debug 용)
- 또는: `state.matrix.current_node.encounter_count` (matrix-owned)

### 6. i18n 갱신

`data/i18n/{en,ko}.json` 의 `combat` 섹션 추가 (8 keys):
- `encounter_1v1` / `encounter_1v2` / `encounter_1v3`
- `heal_amount_reduced` ("HEAL reduced: 20% → 15% (multi-enemy)")
- `target_cycled` ("target → {enemy_name}")
- `aoe_damage` ("AoE: {skill} hits {n} enemies")
- `all_enemies_down` ("all {n} enemies down")

### 7. Tests 추가 (12+ tests)

`tests/unit/test_multi_enemy.py` (NEW):
- TC-MULTI-001: cycle_target rotates through alive enemies
- TC-MULTI-002: step_combat attacks all alive enemies in sequence
- TC-MULTI-003: AoE skill damages all alive enemies
- TC-MULTI-004: HEAL rebalance 15% (TC-001~004 update)
- TC-MULTI-005: encounter_count_for_grade 1/2/3 mapping
- TC-MULTI-006: spawn_encounter returns correct count
- TC-MULTI-007: target cycling skips dead enemies
- TC-MULTI-008: HEAL 15% on T1/T3/T5 (explicit test)
- TC-MULTI-009: multi-enemy auto-attack damage split
- TC-MULTI-010: salvage FRAG yields on multi-enemy (still 1)
- TC-MULTI-011: salvage CRED yields on multi-enemy (still 30)
- TC-MULTI-012: target_index boundary (negative/overflow)

### 8. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | 1vN alarm accumulate → alarm-aware salvage + intel alarm_reducer 보완 | TC-MULTI-002, 003 |
| P2 (The Matrix) | 변경 없음 | 기존 test 유지 |
| P3 (The Flatline) | HEAL 15% + 1-of-4 choice → Pillar 3 weight 보존 (1vN 에서 trivial 방지) | TC-MULTI-004, 008 |
| P4 (The Build) | in-run only (변경 없음) | 기존 test 유지 |
| P5 (The Style) | 깁슨 어휘 + multi-enemy 묘사 | i18n strings |

## 영향 받는 항목

- `prototype/src/roguelike_sprawl/combat/multi_enemy.py` (NEW)
- `prototype/src/roguelike_sprawl/combat/__init__.py` (re-export)
- `prototype/src/roguelike_sprawl/combat/state.py` (step_combat + use_skill patches)
- `prototype/src/roguelike_sprawl/combat/salvage.py` (HEAL_PCT 0.20 → 0.15)
- `prototype/src/roguelike_sprawl/matrix/encounter_spawn.py` (NEW) 또는 `matrix/node.py` patch
- `prototype/src/roguelike_sprawl/engine/state.py` (AppState.encounter_count)
- `prototype/data/i18n/{en,ko}.json` (combat 섹션 추가)
- `prototype/tests/unit/test_multi_enemy.py` (NEW, 12+ tests)
- `prototype/tests/unit/test_salvage_scenarios.py` (TC-001~004 expected value update)
- `design/systems/combat.md` (Multi-Enemy Encounter section)
- `testcases/combat/multi-enemy.md` (NEW: TC-MULTI-001~012)
- `log.md` (Cycle 8 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0152 entry)

## 관련 결정

- ADR-0003 — RT-MS Combat (Accepted)
- ADR-0012 — PPL/ZDR (Accepted)
- ADR-0147 — Salvage Phase 6+ (Accepted, alarm-aware salvage)
- ADR-0148 — Combat Depth (Accepted, alarm-aware salvage + intel alarm)
- ADR-0149 — Boss Phase 4 Finale (Accepted, scripted mechanics)
- ADR-0151 — Intel Items (Accepted, alarm_reducer -2 보완)
- ADR-0110 — 모듈 사이즈 정책 (250 권장)
- ADR-0090 — Salvation Phase Integration (multi-enemy 의 narrative 기반)

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 8 of v1.2.0+)
- 2026-08-07: Accepted (Option 1, 사용자 확인)
  - 구현: `prototype/src/roguelike_sprawl/combat/multi_enemy.py` (NEW, 115 LOC, ADR-0110 46% of 250 ceiling)
  - HEAL rebalance: `combat/salvage.py::HEAL_PCT: 0.20 → 0.15` (Pillar 3 weight 보존)
  - Step combat patch: `state.py::step_combat` 의 player auto-attack → `for target in all_alive_enemies(state)` (모든 alive enemy 순차 공격)
  - 1 pre-existing test updated: `test_combat.py::test_multi_ice_player_attacks_current_target_only` → `test_multi_ice_player_attacks_all_alive_enemies` (이름 + assertion 변경)
  - 테스트: `tests/unit/test_multi_enemy.py` (NEW, 22 tests pass)
  - HEAL rebalance tests: `tests/unit/test_salvage_scenarios.py` (TC-001~004, TC-007, TC-011 expected value update → 32 tests pass)
  - i18n: en/ko.json `multi_enemy` 섹션 신규 (10 keys each)
  - 검증: ruff clean, mypy 0 errors (172 src files, was 171, +1 multi_enemy.py), pytest 4010 pass (was 3988, +22)
  - 후속: NG+ balance, faction_rumor faction 확장
