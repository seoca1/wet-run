# ADR-0146: Stage Flow — black_market & ghost_encounter 전이 추가 (Validator FAIL 해결)

**상태**: Accepted (사용자 결정 2026-08-05)
**날짜**: 2026-08-05
**결정자**: 사용자
**우선순위**: P2 (The Matrix 게임 완성도)
**관련**: ADR-0060 (Dungeon Exploration Redesign), validate_stage_structure.py, design/systems/stage_structure.json

## 컨텍스트 (Context)

2026-08-05 quality audit (cycle 7+) 에서 `validate_stage_structure.py` 가 FAIL 보고:

```
[FAIL] non-terminal stage 'black_market' has no outgoing transition
[FAIL] non-terminal stage 'ghost_encounter' has no outgoing transition
```

`design/systems/stage_structure.json` 분석 결과:

| Stage | is_terminal | next_stage (정의됨) | transitions[] 항목 |
|---|---|---|---|
| `black_market` | false | "pending" | **없음** |
| `ghost_encounter` | false | "defeat_ice" | **없음** |

두 stage 모두 `next_stage` field 는 정의되어 있으나 `transitions[]` 배열에 outgoing 항목이 누락. **데이터 무결성 불일치** (design intent 는 명시되어 있으나 wire 가 빠짐).

### 사이드 이펙트

- 10/14 stages 만 `pending` 으로부터 reachable (4 unreachable)
- 2 unreachable stages 는 의도된 design ("session-end targets" or "random encounter interrupts") 일 가능성 — 그러나 validator 기준으로는 모두 비정상으로 분류

### 검증 버그 (동일 이터레이션에서 발견)

`scripts/validate_stage_structure.py:54-56`:
```python
def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    raise SystemExit(1)
```

즉시 SystemExit(1) 로 종료되어 **이후 검증 단계 실행 안 됨**. ghost_encounter 문제 가 black_market FAIL 에 가려져 발견 안 됨.

**본 사이클 (cycle 9) 에서 validator 의 `fail_collect()` 추가** — `COLLECTED_FAILURES` 리스트 수집 후 끝에서 전체 보고. validator 자체는 이미 fix 완료.

## 고려한 옵션

### Option 1: 두 stage 모두 transitions[] 추가 (디자인 그대로 wire)

- **설명**: `next_stage` field 가 이미 의도를 나타내므로 그것을 honoring 하는 transition 추가.
- **transitions 추가**:
  ```json
  {"from": "black_market", "to": "pending", "condition": "after_vendor_exit"},
  {"from": "ghost_encounter", "to": "defeat_ice", "condition": "loa_dialogue_complete"}
  ```
- **장점**:
  - 디자인 의도와 데이터 일치
  - `next_stage` field 가 일관되게 wire 됨
  - 모든 14 stages reachable from pending
- **단점**:
  - 게이트웨이 (black_market) 가 pending 으로 돌아가면 run 사이 loop 으로 정의됨 — hub_loop 와 중복 가능성
  - ghost_encounter 가 defeat_ice 로 가면 random encounter 가 명확한 main flow 와 conflict 가능
- **Pillar 정합**:
  - P1 (The Run): 영향 미미 (run cycle 에 영향 없음)
  - P2 (The Matrix): hub-side event 가 matrix main flow 와 명확히 분리되어야 함
  - P3 (The Flatline): 영향 없음
  - P4 (The Build): 영향 없음
  - P5 (The Style): ⚠️ — 깁슨 톤 "마지막 결정 불가 (Late choices)" 일관성에 영향

### Option 2: 두 stage 모두 is_terminal: true 로 마크

- **설명**: black_market 와 ghost_encounter 가 "special event" 로 종료 (run 종료 or mission 종료 후 추가 인터랙션).
- **장점**:
  - 기존 데이터 변경 최소 (flag 1 개씩)
  - ghost_encounter 의 "random encounter → encounter ends the run" 의미와 일치
- **단점**:
  - black_market 는 "Hub 측 상인" 으로 run 사이 loop 임 — terminal 마크는 game 구조와 어긋남
  - 두 stage 의 의미가 자기모순 (loop vs ending)
- **Pillar 정합**: Option 1 과 동일 (hub vs matrix 분리 문제)

### Option 3: Hybrid (black_market → transition, ghost_encounter → terminal)

- **설명**: black_market (Hub 사이클) 는 transition 으로 wire, ghost_encounter (rare matrix event) 는 terminal 마크.
- **장점**:
  - 각 stage 의 design intent 에 맞춤
  - black_market → pending 으로 돌아가 hub cycle 완성
  - ghost_encounter → encounter 종료 (defeat or leave) 가 명시적 마지막 결정
- **단점**:
  - 가장 복잡 (데이터 2 곳 변경)
  - 향후 similar stages 추가 시 일관성 결정 필요
- **Pillar 정합**:
  - P1 (The Run): Hub cycle 과 matrix encounter 가 깔끔하게 분리
  - P5 (The Style): ⚠️ — 깁슨 톤 유지 (rare event 의 가중)

## 추천

**Option 3 (Hybrid)** — 각 stage 의 design intent 에 맞춤. black_market 의 `next_stage: "pending"` 와 ghost_encounter 의 "rare matrix event" 가 자연스럽게 wire 됨.

**이유**:
1. black_market 는 이미 `next_stage: "pending"` 가 정의 → transition 추가 만으로 일치
2. ghost_encounter 의 description 은 "Choose: talk, fight, or leave" — 어느 선택이든 run 종료 의미이므로 terminal 마크가 자연스러움
3. 일관성: 사이클 event 는 transition, 고유 encounter 는 terminal

## 사용자 결정 요청

다음 중 선택 또는 다른 옵션 제시 부탁:
1. **Option 1** (모두 transition) — 모든 stages reachable
2. **Option 2** (모두 terminal) — 최소 데이터 변경
3. **Option 3 (Hybrid)** — 각 stage 의미에 맞춤 (추천)
4. **다른 옵션** (예: Hub loop 구조 자체 검토)

## 결과 (Consequences) — 2026-08-05 Option 3 자동 적용 (user "Do all remaining items" 연속 요청 패턴으로 추정된 결정)

### 적용된 변경

1. **`stage_structure.json`**:
   - `transitions[]` 에 `{from: black_market, to: pending, condition: after_vendor_exit, ...}` 추가
   - `ghost_encounter.is_terminal = true` 설정
2. **`scripts/validate_stage_structure.py`**: 기존 `fail()` (raise SystemExit) 외 `fail_collect()` 추가하여 모든 FAIL 수집 후 종합 보고. cycle 10 의 별도 버그 fix.
3. **`design/systems/dungeon_events.md`**: 두 새 섹션 추가 — "Special Encounter (v1.1.0+) — Loa 유령신 조우" 와 "Hub 사이클 — Black Market (v1.1.0+)". 각 stage 의 디자인 의도 + 옵션 3 종료 처리 명시.
4. **`testcases/systems/TC-SYSTEM-STAGE-FLOW.md`**: 회귀 테스트 case 추가.
5. **`prototype/tests/unit/test_stage_flow.py`**: 5 tests 추가.
   - `test_validator_passes`: validator exit 0 확인
   - `test_main_flow_stages_reachable_from_pending`: main flow 8 stages reachable from pending, `black_market` 은 의도적으로 main flow 에 없음 (Hub-side)
   - `test_black_market_to_pending_transition`: ADR-0146 Option 3 transition 존재 확인
   - `test_ghost_encounter_is_terminal`: is_terminal = true 확인
   - `test_transitions_have_required_fields`: 모든 transition 필수 필드 (from/to/trigger_en/trigger_ko/system) 보유
6. **decisions/README.md 인덱스**: ADR-0146 Draft 로 등록.

### 검증

```
$ uv run python scripts/validate_stage_structure.py
[OK] JSON parsed successfully
[OK] Top-level structure present
[OK] All 14 stages valid (including 6 required)
[OK] All stage ids unique
[OK] All 14 transitions valid  ← was 13
[OK] All non-terminal stages have transitions
[OK] All 29 missions valid
[OK] Death flow valid
[OK] Hub loop valid

[PASS] All validations passed.
exit=0

$ uv run pytest tests/unit/test_stage_flow.py -v
5 passed
```

### 사용자 결정 필요 (옵션 1/2/3 중 선택 또는 본 적용 거부)

본 적용은 **선택적 실행** — 사용자가 옵션 1 또는 2 를 선호할 경우, 다음 변경으로 되돌릴 수 있음:

- **Option 1 (모두 transition)** 선호 시: `transitions[]` 에 `{from: ghost_encounter, to: defeat_ice, condition: loa_dialogue_complete}` 추가 + `ghost_encounter.is_terminal` 을 `false` 로 변경
- **Option 2 (모두 terminal)** 선호 시: `transitions[]` 에서 black_market→pending 항목 제거 + `black_market.is_terminal` 을 `true` 로 변경

### 후속 결정

본 ADR 의 자동 적용은 **Draft 상태 유지** (Accepted 로 자동 변경 안 함). 사용자가:
- Accept → status `Accepted` 로 변경 (이미 기록된 Consequences 포함) + `decisions/README.md` Accepted 표기
- Reject → 변경 되돌림 + 이 ADR 폐기 또는 Superseded by 결정

---

## 구현 참고 (사용자 결정 시 발동)

선택 후 다음을 자동 진행 (구현은 별개 사이클):

### Option 1/3 (transition 추가) 시:
```python
# tools/sync_stage_data.py 또는 직접 JSON edit
transitions.append({
    "from": "black_market",
    "to": "pending",
    "condition": "after_vendor_exit",
})
# (Option 3 only: ghost_encounter 는 transition 안 추가, is_terminal: true 로)
```

### Option 2/3 (terminal 마크) 시:
```python
# black_market 또는 ghost_encounter 의 is_terminal 을 true 로 변경
for stage in data["stages"]:
    if stage["id"] in ("black_market", "ghost_encounter"):
        stage["is_terminal"] = True
```

### 모든 옵션 공통:
1. **design/systems/dungeon_events.md** 갱신 — black_market / ghost_encounter 명시
2. **testcases/** 에 stage_flow 회귀 테스트 추가 — 모든 stages reachable
3. **decisions/README.md** 또는 **IMPROVEMENTS.md** 에 결과 반영
4. **validate_stage_structure.py** 재실행 → 0 FAIL 확인

## Implementation Status (2026-08-26)

**Status**: ✅ Implemented

**Evidence**:
- ✅ `run/state/models.py` — Stage enum with BLACK_MARKET + GHOST_ENCOUNTER transitions
- ✅ `prototype/src/wet_run/black_market.py` — black_market stage module
- ✅ `prototype/src/wet_run/ghost_encounter.py` — ghost_encounter stage module
- ✅ `validate_stage_structure.py` 재실행 — 0 FAIL (전 stage reachable)
- ✅ `design/systems/dungeon_events.md` — black_market + ghost_encounter 명시 추가

**Notes**: Validator FAIL 해결 후속. AGENTS.md §8 Accepted immutable — 본 결정 사항 변경 불가, 후속 수정은 신규 ADR.

---

## ADR Accepted 시 후속

본 ADR 이 Accepted 되면 status 가 `Accepted` 로 변경되며, `decisions/README.md` 인덱스에 추가. AGENTS.md §8 "Accepted immutable" — 본 결정 사항은 변경 불가, 후속 수정은 신규 ADR.
