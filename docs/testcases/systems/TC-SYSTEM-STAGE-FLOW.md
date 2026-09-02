# TC-SYSTEM-STAGE-FLOW: Stage Flow 무결성 검증

**상태**: Active (2026-08-05)
**우선순위**: P2
**작성일**: 2026-08-05
**연결 명세**: `design/systems/stage_structure.json`
**관련 ADR**: ADR-0146 (Stage Flow — Hybrid, Draft)

## 목적 (Purpose)

`validate_stage_structure.py` 가 PASS (exit 0) 임을 검증. 모든 non-terminal stage 에 outgoing transition 이 정의되어 있고, terminal stage 표시가 일관됨.

## 전제 조건 (Preconditions)

- `design/systems/stage_structure.json` 가 최신 상태
- `scripts/validate_stage_structure.py` 가 실행 가능

## 검증 단계 (Steps)

### 자동 검증 (1회)
```bash
uv run python scripts/validate_stage_structure.py
echo "exit=$?"
# expect: exit=0 + "[PASS] All validations passed."
```

### 수동 검증 (Stage 별)

1. **black_market**: Hub-side vendor
   - 다음 단계 = `pending` (after_vendor_exit)
   - is_terminal = false (Hub loop 일부)
   - ✅ `transitions[]` 에 `{from: black_market, to: pending}` 항목 존재
2. **ghost_encounter**: Loa 유령신 조우
   - 다음 단계 = `defeat_ice` (전투 선택 시)
   - is_terminal = **true** (any outcome → encounter 종료)
   - ⚠️ Stage 종료 후 run 자체는 계속
3. **complete**, **death_restart**: Terminal stages
   - is_terminal = true ✓
   - outgoing transition 없음 ✓

## 통과 기준 (Pass Criteria)

- [x] validator exit 0
- [x] validator 출력: "[PASS] All validations passed."
- [x] 14 stages 모두 reachable from `pending`
- [x] 2 terminal stages (complete, death_restart) + 1 terminal encounter (ghost_encounter)
- [x] black_market → pending transition 존재
- [x] 모든 missions.stages 가 valid stage id

## 실패 시 대응

만약 validator FAIL:
1. FAIL 메시지 읽기 (validator 가 모든 collect 후 한 번에 출력)
2. `design/systems/stage_structure.json` 의 해당 stage 또는 transition 수정
3. 본 TC 재실행

## 회귀 테스트

`scripts/validate_stage_structure.py` 가 design 변경 시 자동으로 FAIL → 즉시 알려줌 (CI 통합 시).

## 디자인 의도 (Rationale)

ADR-0146 Option 3 (Hybrid) 의 두 가지 디자인 의도:

1. **`black_market` (Hub 사이클 stage)** = vendor 종료 시 `pending` 으로 정상 복귀. 게임 경제 시스템 [ADR-0015] 과 연결.

2. **`ghost_encounter` (Rare matrix event)** = 깁슨 원작 `Mona Lisa Overdrive` 의 vodoun/Loa 시스템 반영. Select: talk / fight / leave 중 어느 선택이든 encounter 종료로 마크되어 main flow 복귀 (`defeat_ice`).

두 stage 의 의미적 구분 (Hub 순환 vs Matrix encounter termination) 을 데이터 모델이 정확히 표현.
