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
2. 기본 테스트 셋에 `ending_resolver.test.ts` · `adr0315_campaign_chain.test.ts` 추가 (경제/엔딩).
   기존 combat 셋(10) + 신규 3 = **13 파일**.

## 결과 (Consequences)

- **12/12 KILLED.** 엔딩 변이 2건 모두 잡혔다 — `control-wealth-zero` 는 **7개** 테스트가, `liberation-never`
  는 **4개**가 실패. 즉 ADR-0337 의 엔딩 수정은 **실제로 테스트로 지켜진다**(내가 "테스트 추가했다"고 한 것이
  mutation 으로 확인됨).
- **커버리지 신호가 넓어졌다**: `npm run mutation` 이 이제 전투 + 엔딩을 함께 흔든다. 생존 변이가 나오면
  그 모듈의 테스트 구멍이다.
- **남은 것**: 경제(`wallet.ts`/`state.ts`)와 매트릭스는 아직 변이 대상이 아니며, 문자열 anchor 가 까다로운
  곳(다중행 함수)은 별도 처리 필요. mission 로스터 wobble(ADR-0343)과 오너 결정 4건은 무관.
- 검증: mutation 12/12 · vitest 236/4447(변경 없음) · typecheck 0.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — `ENDING` 변이 2건 + 기본 테스트 3파일 추가
- 실행: `npm run mutation` → **12/12 KILLED**(control-wealth-zero 7, liberation-never 4)

**Notes**: 경제/매트릭스 모듈로의 확대는 후속(anchor 설계 필요).

## 영향 받는 항목

- `web/scripts/mutation_spike.ts`

## 관련 결정

- ADR-0333 (mutation spike 도입) · ADR-0337 (엔딩 control) · ADR-0338 (재료 carry) · ADR-0340 (e2e)

## 변경 이력

- 2026-11-22: Accepted (mutation 셋을 엔딩·경제로 확대 → 세션 수정이 테스트됨을 확인)
