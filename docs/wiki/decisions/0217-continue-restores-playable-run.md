# ADR-0217: CONTINUE 가 플레이 가능한 run 을 복원한다 (SaveSlot 이 matrix position 을 보존)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P0 (The Matrix, CONTINUE 복원 후 dead state)
**관련**: [ADR-0209 — idb save backend](./0209-wetrun-web-idb-save-backend.md), [ADR-0210](./0210-combat-vfx-effect-schema.md), [ADR-0215 — graph-directed navigation](./0215-graph-directed-matrix-navigation.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md)

## 컨텍스트 (Context)

CONTINUE 메뉴 옵션이 **죽은, 플레이 불가능한 state** 를 복원하고 있었다.

`slotToGameState` (`web/src/core/state.ts`) 는 `matrix: null` 을 반환하면서 동시에
`runPhase: "matrix"` 를 선언했다. `applyAction` 은 `runPhase === "matrix"` 를 **먼저** 확인하므로
`applyMatrixAction` 이 state 를 소유한다. 그런데 `applyMatrixAction` 의 `confirm` 분기와
movement 분기 **둘 다** `state.matrix != null` 조건으로 gate 되어 있다.
즉 null matrix 상태에서는 모든 input 이 fall through 하고 reducer 는 **동일한 객체** 를 반환한다.
사베를 resume 한 뒤 플레이어는 confirm 도, 이동도 할 수 없었다 (jack out 만 가능).

경현적으로 재현한 결과:

```
SLOT currentNodeIndex present? false
RESTORED runPhase: matrix phase: approach matrix: NULL currentNodeIndex: 0
after confirm:    msg=Resumed from autosave (turn 1)   → no-op (identical object)
after move_south: currentNodeIndex=0                   → no-op (identical object)
```

### 기존 테스트가 이 결함을 놓친 이유 — 둘 다 false positive

- `web/tests/slot_restore.test.ts` 는 `restored.phase === "approach"` 와 `message` 가
  "Resumed" 를 포함하는지만 검사했다. state 가 **actionable** 한지는 검사하지 않았다.
- `web/e2e/continue.spec.ts` 는 `["combat","approach"]).toContain(phase)` 만 검사했다.
  죽은 state 의 `phase` 도 `"approach"` 이므로, "resume → combat" 을 검증한다고 주석에
  적어 놓았음에도 **vacuous** 하게 통과했다.

이것은 property/behavioral verification 이 드러내는 결함 유형이다.
두 테스트 모두 **label** 을 검증했을 뿐 **behavior** 를 검증하지 않았다.

## 고려한 옵션

### Option 1: `slotToGameState` 가 matrix 를 deterministic 하게 재생성 (선택)

- **설명**: `makeInitialState` 가 쓰는 것과 같은 입력으로 matrix 를 다시 생성한다.
  `generateProceduralMatrix(missionGradeOf(mission), missionSeedOf(mission), mission.id)`.
- **장점**:
  - resume 된 run 이 run 시작 시점의 **동일한 matrix** 를 얻는다.
  - 기존 save payload 와 schema version 을 건드리지 않는다.
- **단점**:
  - `currentNodeIndex` 를 별도로 보존하지 않으면 시작 위치로 되돌아간다.
- **Pillar 정합**:
  - P2 (The Matrix): ✅ dead restore path 를 live path 로 되돌린다.

### Option 2: `SaveSlot` 이 matrix 전체를 저장

- **설명**: matrix 그래프 전체를 save payload 에 담는다.
- **장점**: 복원이 완전히 정확하다.
- **단점**: payload 가 크게 늘고, 저장 schema migration 부담이 생긴다.
- **Pillar 정합**: P2 (The Matrix): 정확도는 좋으나 과한 범위.

### Option 3: 현상 유지 (no-op)

- **설명**: `matrix: null` 복원을 그대로 둔다.
- **장점**: 코드 변경 없음.
- **단점**: CONTINUE 가 dead state 를 만든다. 플레이어는 resume 후 아무것도 할 수 없다.
- **Pillar 정합**: 실패.

## 추천 (Recommendation)

**Option 1 + `currentNodeIndex` 선택적 보존** — matrix 는 deterministic 재생성으로 복구하고,
플레이어의 matrix position 은 `SaveSlot` 의 optional field 로 보존한다.
이 조합은 schema migration 없이 CONTINUE 를 실제로 플레이 가능한 상태로 만든다.

## 사용자 결정 (Decision)

[ x ] Option 1 (deterministic matrix regeneration + `currentNodeIndex` persistence) — 코드는 이미 shipped 상태.

## 결정된 내용

1. **`slotToGameState` 가 matrix 를 deterministic 하게 재생성한다.**
   `makeInitialState` 와 같은 입력, 즉
   `generateProceduralMatrix(missionGradeOf(mission), missionSeedOf(mission), mission.id)` 를 쓴다.
   resume 된 run 은 run 이 시작할 때와 동일한 matrix 를 갖는다.
2. **`SaveSlot` 에 OPTIONAL `readonly currentNodeIndex?: number` 가 추가된다.**
   `stateToSaveSlot` 이 이 값을 쓰고, `isSaveSlot` 이 값이 있을 때 finite number 인지 검증한다.
   `slotToGameState` 는 이 값을 소비하고, 값이 없으면 `matrix.startNode` 로 fallback 하므로
   **이 변경 이전에 쓰인 save 도 계속 로드된다.**
   `SaveSlot.version` / `CURRENT_SCHEMA_VERSION` 은 의도적으로 **bump 하지 않는다.**
   optional field 는 backward compatible 이다.
3. **`makeInitialState` 가 shared `missionGradeOf` / `missionSeedOf` helper 로 통합된다.**
   이전에는 동일한 precedence 로 inline extraction 이 중복되어 있었다
   (`matrix_seed ?? seed ?? 42` 그리고 `grade_max ?? grade_min ?? grade ?? 1`).
   이제 fresh run 과 resumed run 의 generation input 이 drift 할 수 없다.
4. **`handleContinue` 가 `launchSelected` 와 같이 `grid: makeGrid(this.layout.cols, this.layout.rows)` 로 맞춘다** (1 line).
5. **Regression test 는 label 이 아니라 BEHAVIOR 를 검증한다.**
   `slotToGameState` 이후 matrix 가 null 이 아니어야 하고, `applyAction(confirm)` 이
   no-op 이 아니어야 한다 (reducer 가 다른 객체를 반환해야 한다),
   `move_south` 가 `currentNodeIndex` 를 바꿔야 하며, `currentNodeIndex` 가
   `stateToSaveSlot` → `slotToGameState` round-trip 을 살아남아야 한다.
   e2e assertion 도 강화되어 restored matrix / `currentNodeIndex` 를 확인하고
   keypress 가 실제로 state 를 바꾸는지 검사한다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/state.ts` — `slotToGameState` 의 matrix 재생성 + `currentNodeIndex` 소비, `stateToSaveSlot` 의 position persistence, `makeInitialState` 의 helper 통합
- `web/src/core/types.ts` — `SaveSlot.currentNodeIndex?: number`
- `web/src/save/storage.ts` — `isSaveSlot` 의 optional field 검증
- `web/src/main.ts` — `handleContinue` 의 grid 정렬 (`launchSelected` 와 동일)
- `web/tests/slot_restore.test.ts` — playability / round-trip regression test +7건
- `web/e2e/continue.spec.ts` — assertion 강화
- Pre-fix 검증: 신규 test 7건 중 6건이 pre-fix `state.ts` 에서 FAIL
  (관측: matrix 는 `expected null not to be null`, no-op confirm 은
  `expected { phase: 'approach', … } not to be { phase: 'approach', … }` —
  동일 객체 반환이 smoking gun)
- 수정 후 gate: `npm test` **125 files / 2935 tests, 0 failures**; `tsc --noEmit` 0 errors; `eslint` 0 errors
- 수정 후 측정: 복원된 matrix 는 `makeInitialState` 의 matrix 와 **동일**,
  `confirm` 은 "No ICE here — move to a node with an encounter." 반환,
  `move_south` 는 0 → 3 이동

**Notes**: e2e spec 은 강화되었으나 **로컬에서는 실행하지 않았다.**
Playwright 는 browser binary 와 live URL 이 필요하다.
따라서 e2e 자체의 green 은 이 ADR 작성 시점에 확인된 사실이 아니다.

## 결과 (Consequences)

### 긍정적 영향

- CONTINUE 가 플레이 가능한 run 을 복원한다.
- matrix position 이 save/restore 를 살아남는다.
- fresh run 과 resumed run 이 동일한 generation input 을 공유함이 증명 가능하다.
- 기존 save 가 계속 로드된다.

### 부정적 영향 / 수용한 비용

- save payload 가 field 하나만큼 늘어난다.
- restore 는 여전히 근사값이다. save 가 `visitedNodes`, `iceRoster`, `statusEffects`,
  `playerCombo`, `skillCooldowns`, `activeMutators` 를 보존하지 않으므로 resume 시 reset 된다.
  이는 **known remaining gap** 이다.

### `handleContinue` grid 정렬에 대한 참고

이 변경은 **zero-behavior-change hardening** 이다.
`state.grid` 의 read site 는 두 곳뿐 (`main.ts:1506`, `main.ts:1519`) 이고,
두 곳 모두 `renderGrid(..., this.layout.cols, this.layout.rows)` 가 `state.grid` 를
**대체한 뒤** 실행된다. resume 된 run 의 matrix 화면은 `renderMatrix(..., layout.cols, layout.rows)`
로 렌더링되며 `state.grid` 를 건드리지 않는다.
즉 저장된 80×50 크기가 실제로 표시된 적은 없었지만, 불일치는 잠재적 상태로 남아 있었다.

### 후속 작업

- 위의 approximate-restore gap (미보존 state field 들) 해소.
- 향후 persistence path 가 추가될 때마다 "복원된 state 가 actionable 인지" 를
  검사하는 shared test helper 도입 검토.

## 영향 받는 항목

- `web/src/core/state.ts` — matrix 재생성, position persistence, helper 통합
- `web/src/core/types.ts` — `SaveSlot` optional field
- `web/src/save/storage.ts` — optional field 검증
- `web/src/main.ts` — `handleContinue` grid 정렬
- `web/tests/slot_restore.test.ts` — behavior regression test
- `web/e2e/continue.spec.ts` — 강화된 assertion

## 관련 결정

- ADR-0209 (idb save backend) — save storage backend
- ADR-0210 (Combat VFX Effect Schema) — 관련 데이터 스키마 결정
- ADR-0215 (graph-directed navigation) — `matrix.startNode` 가 entry index 로 쓰임
- ADR-0216 (derived ICE skill metadata) — sibling ADR, 동일 날짜

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (Option 1, deterministic matrix regeneration + `currentNodeIndex` persistence) — 코드 shipped 상태
