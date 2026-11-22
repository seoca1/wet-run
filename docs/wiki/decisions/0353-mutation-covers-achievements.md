# ADR-0353: mutation 을 achievements(함수형)까지 — 여긴 구멍이 없었다

**상태**: Accepted (오너: *"계속"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

mutation 셋은 상수/구조 중심이었다. **함수형 모듈**로 넓힌다 — `achievements.ts` 의 임계값(centurion 100
회, flawless 50, undefeated 10)은 함수 안의 비교문이라 상수와 다른 anchor 다.

## 결정 (Decision)

**변이 3건 + 테스트 셋 추가.**

- `getProgress("centurion_progress") >= 100 → >= 101`
- `getProgress("flawless_progress") >= 50 → >= 51`
- `getProgress("undefeated_progress") >= 10 → >= 11`
- 기본 셋에 `achievements.test.ts` 추가.

## 결과 (Consequences)

- **39/39 KILLED.**
- **여긴 구멍이 없었다**: `achievements.test.ts` 가 임계를 **동작으로** 고정한다 — centurion 은 90 에서
  `isUnlocked === false`, 100 에서 `true`. 그래서 `>= 100 → >= 101` 변이는 100 지점에서 풀리지 않아
  **즉시 KILLED**(각 1개). 앞선 값-미고정 사례들과 달리, 여기 테스트는 상수를 import 하지 않고 **경계
  동작**을 검사하므로 값이 실제로 잡힌다.
- **교훈의 반대면**: 상수 import 검사는 값 변이에 면역이지만, **경계 동작 검사**는 값을 잡는다. 앞서
  구멍이었던 곳들(쿼터 밴드·BGM 감쇠)은 후자가 없었다.
- 검증: mutation **39/39** · vitest **238 files / 4459 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — `ACHIEVEMENTS` 변이 3 + `achievements.test.ts` 셋 추가
- 실행: `npm run mutation` → **39/39 KILLED**(ach 3건 각 1)

**Notes**: 함수형 모듈은 경계 동작 테스트가 있으면 잘 잡힌다. 남은 모듈(던전 크롤러 로직·허브 등) 후속.

## 영향 받는 항목

- `web/scripts/mutation_spike.ts`

## 관련 결정

- ADR-0349 / 0350 / 0351 / 0352 (값 계약 테스트 — 그 반대면의 대조)

## 변경 이력

- 2026-11-22: Accepted (achievements 확대 → 39/39; 경계 동작이 값을 잡는다)
