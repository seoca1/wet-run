# ADR-0344: 내 수정이 테스트되는가 — mutation 셋을 엔딩·경제 모듈로 넓혔다

**상태**: Accepted (오너: *"응. 위임할게"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

검증 프레임워크(ADR-0333)의 mutation spike 는 **`combat_engine.ts` 상수만** 흔들었다(10 변이).
이번 세션에 **엔딩·경제 코드를 바꿨는데**(ADR-0337 control 게이트, ADR-0338 재료 carry), 그 변경이
**테스트로 지켜지는지**는 어디에도 없었다 — "테스트가 있으면 초록"이지 "그 테스트가 이 변경을 잡는가"는
측정되지 않았다.

## 결정 (Decision)

**mutation 셋을 이번 세션에 바꾼 모듈로 넓힌다.**

1. `ending_resolver.ts` 변이 2건 추가:
   - `CONTROL_WEALTH = 18000 → 0` (모든 완주가 control 이 됨)
   - `missionsCompleted >= 3 → >= 4` (liberation 이 3다리 계약에서 안 뜸)
2. 기본 테스트 셋에 `ending_resolver.test.ts` · `adr0315_campaign_chain.test.ts` · `adr0323_the_hoard_outlives_the_run.test.ts` 추가.
3. **경제 모듈 변이 3건 추가**(같은 세션의 ADR-0323/0338):
   - `wallet.ts` `mergeRunIntoWallet`: seed 감산을 덧셈으로 (`-` → `+`, 주조)
   - `wallet.ts` `earnedMaterials`: seed 감산 제거 (`- 0`, 보상을 획득으로)
   - `state.ts` `startNextLeg`: 재료 carry 제거(다음 leg 가 이전 재료를 버림)

## 결과 (Consequences)

- **15/15 KILLED.** 엔딩 변이 2건과 경제 변이 3건이 모두 잡혔다 — `control-wealth-zero` **7개**,
  `liberation-never` **4개**, `merge-mints-seed` **2개**, `earned-keeps-seed` **2개**,
  `carry-drops-materials` **1개** 테스트가 실패. 즉 ADR-0337(엔딩)·ADR-0323/0338(경제)의 수정이
  **실제로 테스트로 지켜진다**.
- **커버리지 신호가 넓어졌다**: `npm run mutation` 이 이제 전투 + 엔딩 + 경제를 함께 흔든다.
- **남은 것**: 매트릭스 모듈은 아직 변이 대상이 아니다. `main.ts`(런 시작 seed)는 앱 루프라 단위 테스트가
  없어 변이하면 SURVIVED 로 나올 것이다(별도 계측 필요). mission 로스터 wobble(ADR-0343)과 오너 결정 4건은 무관.
- 검증: mutation **15/15** · vitest 236/4447(변경 없음) · typecheck 0.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — `ENDING` 변이 2 + `WALLET`/`STATE` 변이 3, 기본 테스트 4파일 추가
- 실행: `npm run mutation` → **15/15 KILLED**(ending 7·4, economy 2·2·1)

**Notes**: 매트릭스 모듈 확대는 후속. `main.ts` 는 단위 테스트가 없어 변이 시 SURVIVED 예상(별도 계측).

## 영향 받는 항목

- `web/scripts/mutation_spike.ts`

## 관련 결정

- ADR-0333 (mutation spike 도입) · ADR-0337 (엔딩 control) · ADR-0338 (재료 carry) · ADR-0340 (e2e)

## 변경 이력

- 2026-11-22: Accepted (mutation 셋을 엔딩·경제로 확대 → 세션 수정이 테스트됨을 확인)
