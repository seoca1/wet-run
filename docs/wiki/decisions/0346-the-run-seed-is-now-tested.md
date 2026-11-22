# ADR-0346: 런 seed 호출부를 순수 함수로 빼서 테스트했다

**상태**: Accepted (오너: *"응"* — ADR-0345 가 지목한 진짜 구멍)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

ADR-0345 가 매트릭스 mutation 을 돌리며 **진짜 구멍 하나**를 남겼다: `main.ts` 의 런 시작 seed —
`runWalletSeed = seedRunWallet(hoard, Σ 계약 보상)` — 이 **앱 루프 안에 인라인**이라 단위 테스트가
없었다. `main.ts` 는 하네스가 구동하지 않으므로, 이 seed 계산을 변이하면 **SURVIVED** 로 나온다.
즉 ADR-0338 의 seed 부분은 **호출부가 미검증**이었고, 골든(밸런스/장비)도 hoard 를 보지 않는다.

## 결정 (Decision)

**seed 계산을 `wallet.ts` 의 순수 함수로 추출하고 테스트로 고정한다.**

- `contractSeedMaterials(legs, missionRewardMaterials)`:
  - 계약이 있으면 **모든 leg 보상의 합**(`addStacks`),
  - 계약이 없으면 그 미션의 보상.
- `main.ts` 는 이 함수를 호출한다(인라인 reduce 제거).

## 결과 (Consequences)

- **구멍 봉합**: `tests/adr0338_run_seed.test.ts`(신규 4 테스트)가 seed 의 span 을 고정 —
  "계약이면 모든 leg 합", "잭아웃 1프레임은 주조 0", "번 것만 적립".
- **mutation 19/19**: 새 변이 `seed-ignores-contract`(`(acc, leg) => acc`, 계약 무시)를 이 테스트가
  **KILLED**(1개 테스트) — 즉 이제 seed 호출부가 테스트된다.
- **앱 루프 의존 축소**: `main.ts` 가 wallet 수학을 직접 들지 않고 검증된 함수에 위임한다.
- 검증: mutation **19/19** · vitest **237 files / 4451 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/state/wallet.ts` — `contractSeedMaterials` (순수)
- `web/src/main.ts` — 인라인 reduce → 함수 호출
- `web/tests/adr0338_run_seed.test.ts` — 4 테스트
- `web/scripts/mutation_spike.ts` — `seed-ignores-contract` 변이 → KILLED

**Notes**: 남은 앱-루프 전용 로직(예: endRun 의 ownedEquipment 병합)도 같은 방식으로 뺄 수 있다(후속).

## 영향 받는 항목

- `web/src/core/state/wallet.ts` · `web/src/main.ts` · `web/tests/adr0338_run_seed.test.ts`

## 관련 결정

- ADR-0323 (hoard 보존) · ADR-0338 (계약 재료 + seed) · ADR-0345 (매트릭스 mutation, 구멍 지목)

## 변경 이력

- 2026-11-22: Accepted (seed 추출 + 테스트 → 구멍 봉합)
