# ADR-0347: 런 종료 장비 병합도 순수 함수로 빼서 테스트했다

**상태**: Accepted (오너: *"응"* — ADR-0346 의 후속: 앱-루프 잔여 로직)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

ADR-0346 이 런 시작 seed 를 순수 함수로 빼며 "남은 앱-루프 전용 로직(예: `endRun` 의 장비 병합)도
같은 방식으로 뺄 수 있다"고 남겼다. `endRun` 은 런이 끝날 때(잭아웃·엔딩·플랫라인) 살베이지한 장비를
소유 목록에 병합하는데, **그 for-루프가 `main.ts` 안**이라 단위 테스트가 없었다.

## 결정 (Decision)

**병합을 `owned_equipment.ts` 의 순수 함수로 추출한다.**

- `mergeDroppedEquipment(owned, droppedIds)`: 런의 드롭을 소유 집합에 접는다.
- `ownEquipment` 와 마찬가지로 **새로 추가된 게 없으면 같은 레코드를 반환** → 호출자가 쓰기를 건너뛴다.
- `main.ts` 의 `endRun` 은 이 함수를 호출한다.

## 결과 (Consequences)

- **구멍 봉합**: `owned_equipment.test.ts` 에 3 테스트 추가 — "드롭은 모두 소유가 된다", "새 게 없으면
  같은 참조를 돌려준다(쓰기 skip)", "드롭 순서와 무관".
- **mutation 20/20**: 새 변이 `drops-ignored`(루프가 아무것도 안 함)를 이 테스트가 **KILLED**(1개).
- **앱 루프가 얇아졌다**: `endRun` 이 장비 수학을 직접 들지 않고 검증된 함수에 위임.
- 검증: mutation **20/20** · vitest **237 files / 4454 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/state/owned_equipment.ts` — `mergeDroppedEquipment` (순수)
- `web/src/main.ts` — `endRun` 이 함수 호출
- `web/tests/owned_equipment.test.ts` — 3 테스트 추가
- `web/scripts/mutation_spike.ts` — `drops-ignored` 변이 → KILLED

**Notes**: `main.ts` 의 남은 앱-루프 로직(예: 세이브 슬롯 결정)도 같은 방식으로 뺄 수 있다(선택).

## 영향 받는 항목

- `web/src/core/state/owned_equipment.ts` · `web/src/main.ts` · `web/tests/owned_equipment.test.ts`

## 관련 결정

- ADR-0325 (장비 소유) · ADR-0329 (드롭 경로) · ADR-0346 (런 seed 추출) · ADR-0345 (구멍 지목)

## 변경 이력

- 2026-11-22: Accepted (런 종료 장비 병합 추출 + 테스트 → 앱-루프 구멍 봉합)
