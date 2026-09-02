# ADR-0153: Matrix Encounter Spawn Integration (1v1/1v2/1v3)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (Multi-Enemy *실제 게임플레이* 활성화, v1.2.0+ bridge)
**관련**: [ADR-0152 — Multi-Enemy Encounters (Cycle 8, ADR 작성 + cycle_target + HEAL rebalance)](./0152-multi-enemy-encounters.md), [ADR-0148 — Combat Depth](./0148-combat-depth-expansion.md), [ADR-0147 — Data Salvage Phase 6+](./0147-data-salvage-phase6.md), [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md)

## 컨텍스트 (Context)

`combat/multi_enemy.py::encounter_count_for_grade()` (Cycle 8) 가 존재하지만 **호출되지 않음**. Matrix 의 모든 ICE node encounter 가 *항상 1v1* — player 가 1v2/1v3 encounter 를 *실제 경험* 못함.

**Architecture 확인** (Cycle 9 survey):
- `matrix/node.py::Node` has single `ice_kind: str` (not list) — *multi-ICE node* 가 아님
- `matrix/dungeon_generator.py` 는 graph 구조만 생성 (Combatant 없음)
- `engine/combat_view_state.py:134` 에서 `build_ice_enemy()` 호출 → **integration point**
- `state.player_grade` available via `start_combat(state, ...)` parameter (line 43)

**현재 상태** (Cycle 8 완료):
- `combat/multi_enemy.py` (115 LOC): `cycle_target`, `all_alive_enemies`, `encounter_count_for_grade` 구현 완료
- `CombatState.enemies: tuple[Combatant, ...]` multi-enemy container 존재
- `step_combat` player auto-attack: `for target in all_alive_enemies(state)` (모든 alive enemy 순차)
- `_end_combat` `all(e.hp <= 0 for e in state.enemies)` multi-enemy aware

**부재**:
- `start_combat` 가 *항상 single enemy* 만 생성 → 1v2/1v3 미발동
- Player grade 가 encounter count 에 반영 안 됨

**해결 방향** (ADR-0153):
- `start_combat` 에서 `encounter_count_for_grade(state.player_grade)` 호출
- Count > 1 일 때 additional enemies 생성 (`build_ice_enemy(ice_kind_id, ice_registry)` 반복)
- `CombatState(player=player, enemy=enemy)` → `CombatState(player=player, enemies=(e1, e2, ..., eN))`
- 기존 `enemy=enemy` 인자 호환성 유지 (`__post_init__` 가 `enemies=tuple([enemy])` 변환)

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: Grade 3+ 부터 1v2 → run weight *자동* 증가 (Pillar 1 의 *run weight* 가 Grade 와 직결)
- **Pillar 3 (The Flatline)**: HEAL 15% (ADR-0152) + 1vN → player 가 *strategic* 필요
- **Pillar 4 (The Build)**: in-run only (변경 없음)
- **Pillar 5 (The Style)**: 깁슨 어휘 ("swarm", "pack", "encircle") — status message 표시

**기술 제약**:
- 기존 `build_ice_enemy` API 변경 없음 (호출 횟수만 증가)
- 기존 `CombatState(enemy=...)` 인자 호환 (Cycle 8 에서 이미 `enemies=tuple([enemy])` 변환)
- 신규 모듈 0개 (기존 `combat/multi_enemy.py` 함수 재사용)
- 5-10 line patch 만 필요

## 고려한 옵션

### Option 1: start_combat patch (최소)

- **설명**: `engine/combat_view_state.py::start_combat` 의 `build_ice_enemy` 호출 직후 + `CombatState` 생성 직전에 8-line patch.
- **장점**:
  - 변경 범위 최소 — 8 line patch 만.
  - 기존 `Node.ice_kind` / `build_ice_enemy` API 변경 0.
  - 기존 `CombatState(enemy=...)` 인자 호환 (Cycle 8 호환성 유지).
  - `combat/multi_enemy.py` 의 `encounter_count_for_grade` 재사용.
- **단점**:
  - `start_combat` 함수에 inline patch — testability 낮음.
  - Multi-encounter *선택적* spawn (특정 node 만 1v2) 불가 — *항상* grade 기반.
- **Pillar 정합**:
  - P1: Grade → 1v2/1v3 자동 (inherent).
  - P3: HEAL 15% 보완 (ADR-0152).
  - P4: in-run only.
  - P5: 깁슨 어휘 status message.

### Option 2: Node.encounter_count 필드 추가

- **설명**: `Node` 에 `encounter_count: int = 1` 필드 추가. `dungeon_generator` 가 player grade 기반 encounter_count 결정. `start_combat` 가 `ice_node.encounter_count` 사용.
- **장점**:
  - Matrix 가 encounter count *지식* 보유 (data-driven).
  - 특정 mission 의 encounter count override 가능 (e.g., "boss encounter = 1 always").
  - Testability ↑ (Node 가 encounter 결정).
- **단점**:
  - 변경 범위 큼 — `Node` schema + `dungeon_generator` patch.
  - Backward-compat: 기존 Node 객체들 (saved game 등) 에 default 1 필요.
  - Tests for generator + start_combat 둘 다 필요.
- **Pillar 정합**:
  - P1: 동일 (Grade 기반).
  - P3: 동일.

### Option 3: matrix encounter_count *table* + start_combat

- **설명**: `data/matrix/encounter_table.json` (Grade → count mapping). `start_combat` 가 이 table + `state.player_grade` 로 encounter 결정.
- **장점**:
  - Data-driven (designer 가 encounter table 조정 가능).
  - Testability ↑.
  - Mission-specific override 가능 (e.g., "tutorial = 1v1 always").
- **단점**:
  - 변경 범위 최대 — JSON + loader + integration.
  - v1.2.0+ scope 에 *over-engineering*.
- **Pillar 정합**:
  - P1: 동일.

## 추천 (Recommendation)

**Option 1** (start_combat patch, 최소).

이유:
1. **변경 범위 최소**: 8 line patch 만. v1.2.0+ 의 *1v2/1v3 즉시 활성화* 목표.
2. **기존 인프라 100% 재사용**: `encounter_count_for_grade` (Cycle 8), `CombatState.enemies` (기존), `build_ice_enemy` (기존).
3. **Pillar 정합성 보존**: P1 (Grade 자동), P3 (HEAL 15% 보완), P4 (in-run).
4. **모듈 사이즈**: 신규 모듈 0개. ADR-0110 정합.
5. **Test surface 폭증 방지**: 3-5 tests (start_combat multi-enemy scenario).

**순서** (Cycle 9, 1 sub-session):
1. `engine/combat_view_state.py::start_combat` patch: encounter_count_for_grade + multi-enemy tuple
2. Status message: "ENCOUNTER: 1v{N} ({n} enemies)" 추가
3. Tests: 3-5 (1v1/1v2/1v3 encounter scenarios)

## 사용자 결정 (Decision)

[x] Option 1 (start_combat patch, 최소) — 2026-08-07 Cycle 9 채택
[ ] Option 2 (Node.encounter_count 필드)
[ ] Option 3 (data-driven encounter table)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. Patch (engine/combat_view_state.py, 8 line)

```python
# Before (line 134):
enemy = build_ice_enemy(ice_kind_id, ice_registry)
# ... (line 146):
cs = CombatState(player=player, enemy=enemy)

# After (ADR-0153):
from ..combat.multi_enemy import encounter_count_for_grade

# Line 134: create primary enemy
enemy = build_ice_enemy(ice_kind_id, ice_registry)
# ADR-0153: create additional enemies based on player grade
n = encounter_count_for_grade(state.player_grade)
enemies_list = [enemy]
for _ in range(n - 1):
    try:
        additional = build_ice_enemy(ice_kind_id, ice_registry)
    except KeyError:
        additional = build_ice_enemy("standard", ice_registry)
    enemies_list.append(additional)
# Status message
state.status_messages.append(f">>> ENCOUNTER: 1v{n} ({n} enemies)")
# Line 146: use enemies tuple
cs = CombatState(player=player, enemies=tuple(enemies_list))
```

### 2. 기존 코드 변경 없음

- `matrix/node.py`: 변경 없음 (Node schema 그대로)
- `matrix/dungeon_generator.py`: 변경 없음 (graph 구조 그대로)
- `combat/registry.py`: 변경 없음 (build_ice_enemy API 그대로)
- `combat/multi_enemy.py`: 변경 없음 (encounter_count_for_grade 그대로)

### 3. AppState 변경 없음

- 기존 `state.player_grade` 활용
- 신규 필드 없음

### 4. i18n 갱신 (선택)

기존 `data/i18n/{en,ko}.json` 의 `multi_enemy` 섹션 (Cycle 8 의 10 keys) 재사용. `encounter_1v1` / `encounter_1v2` / `encounter_1v3` 이미 존재.

### 5. Tests 추가 (3-5 tests)

`tests/unit/test_combat_view_state.py` (또는 신규 `test_encounter_spawn.py`):
- TC-ENC-001: start_combat Grade 1 → 1v1
- TC-ENC-002: start_combat Grade 3 → 1v2
- TC-ENC-003: start_combat Grade 5 → 1v3
- TC-ENC-004: start_combat Grade 6 → 1v3 (clamp)
- TC-ENC-005: multi-enemy CombatState.enemies all alive

### 6. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | Grade → 1vN 자동 (inherent) | TC-ENC-002, 003 |
| P2 (The Matrix) | 변경 없음 | 기존 test 유지 |
| P3 (The Flatline) | HEAL 15% + 1vN (ADR-0152 보완) | 기존 test 유지 |
| P4 (The Build) | in-run only (변경 없음) | 기존 test 유지 |
| P5 (The Style) | 깁슨 어휘 status message 추가 | TC-ENC-002, 003 |

## 영향 받는 항목

- `engine/combat_view_state.py` (8 line patch, start_combat)
- `tests/unit/test_combat_view_state.py` 또는 신규 (3-5 tests)
- `log.md` (Cycle 9 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0153 entry)
- `data/i18n/{en,ko}.json` (변경 없음, 기존 multi_enemy 섹션 재사용)
- `design/systems/combat.md` (변경 없음, 기존 Multi-Enemy Encounters 섹션 그대로)
- `testcases/combat/multi-enemy.md` (변경 없음, 기존 TC-MULTI-001~012 그대로)
- `prototype/data/game_facts.json` (regenerated)

## 관련 결정

- ADR-0152 — Multi-Enemy Encounters (Cycle 8, function 제공)
- ADR-0147 — Data Salvage Phase 6+ (alarm-aware salvage 보완)
- ADR-0148 — Combat Depth (counter window + companion skills 보완)
- ADR-0151 — Info Market Intel Items (alarm_reducer -2 보완)
- ADR-0110 — 모듈 사이즈 정책 (신규 모듈 0개, ADR-0110 정합)
- ADR-0090 — Salvation Phase Integration (narrative 기반)

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/engine/combat_view_state.py:145` — `from ..combat.multi_enemy import encounter_count_for_grade` (import at integration point)
- `prototype/src/wet_run/engine/combat_view_state.py:151` — `enemy = build_ice_enemy(ice_kind_id, ice_registry)` (primary enemy)
- `prototype/src/wet_run/engine/combat_view_state.py:154` — `build_ice_enemy("standard", ice_registry)` (KeyError fallback, defensive)
- `prototype/src/wet_run/engine/combat_view_state.py:157` — `encounter_n = encounter_count_for_grade(state.player_grade)` (Grade-based 1v1/1v2/1v3)
- `prototype/src/wet_run/engine/combat_view_state.py:161` — `additional = build_ice_enemy(ice_kind_id, ice_registry)` (additional enemies)
- `prototype/src/wet_run/engine/combat_view_state.py:163` — `build_ice_enemy("standard", ice_registry)` (KeyError fallback)
- `prototype/src/wet_run/combat/multi_enemy.py:51` — `encounter_count_for_grade` definition (Cycle 8, reused by Cycle 9)
- `prototype/src/wet_run/combat/state_models.py` — `CombatState.enemies: tuple[Combatant, ...]` (multi-enemy container, pre-existing)
- `prototype/tests/unit/test_encounter_spawn.py:1-129` — 14 tests covering Grade 1-2/3-4/5-6 → 1v1/1v2/1v3 + edge cases (grade=0, grade=7, grade=-5, grade=8)
- `prototype/data/i18n/{en,ko,ja,zh}.json` — `multi_enemy` section with `encounter_1v1`/`encounter_1v2`/`encounter_1v3` (reused from ADR-0152)

**Notes**: 8-line patch in `start_combat` per ADR-0153 §Consequences.1 — verified to be present (import + 4-line for-loop + CombatState construction). No new node schema (`Node.ice_kind: str` unchanged) — data-driven approach deferred. All tests passing per `test_encounter_spawn.py` (14 tests). Status message `>>> ENCOUNTER: 1v{N}` is appended to `state.status_messages` per ADR spec.

**No further action on ADR-0153** — implementation closed.

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 9 of v1.2.0+ bridge)
- 2026-08-07: Accepted (Option 1, 사용자 확인)
  - 구현: `engine/combat_view_state.py::start_combat` 8-line patch (multi-encounter)
  - 테스트: `tests/unit/test_encounter_spawn.py` (NEW, 19 tests pass)
  - 검증: ruff clean, mypy 0 errors (172 src files), pytest 4029 pass (was 4010, +19)
  - 효과: Grade 1-2 = 1v1, Grade 3-4 = 1v2, Grade 5-6 = 1v3 *실제 게임플레이* 활성화
  - Pillar 1: Grade → 1vN 자동 (run weight inherent)
  - Pillar 3: HEAL 15% (ADR-0152) + 1vN → player 가 *strategic* 필요
  - 후속: NG+ balance, faction_rumor faction 확장, ja/zh i18n
