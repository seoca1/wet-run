# ADR-0337: 표시되는 엔딩에 control이 없다 — 중간 leg는 삼켜진다

**상태**: Accepted (오너: *"위임할게. 후속 진행해줘"* — 검증 보고 P1 "엔딩 게이트")
**날짜**: 2026-11-19
**결정자**: 사용자
**우선순위**: P1 (엔딩 · 검증)

## 컨텍스트 (Context)

전수 검증(2026-11-19)이 **P1 = "제어(control) 엔딩 죽은 분기(0/53)"** 로 올렸다. 근거는
`npm run endings` 의 `control endings actually resolved: 0/53`. 게이트를 재조정하려 파고들었더니
**두 번 틀릴 뻔했다** — 측정 도구가 두 단계로 오도했다.

## 측정 (Measurement)

**1) `npm run endings` 는 오도한다.** 그 도구는 `missionsCompleted` 를 **1로 고정**하고 **시드도 하나**만
돈다(ADR-0279의 단일-미션 질문용). 그래서 `liberation`(>=3)은 구조적으로 꺼지고 `control`은 표본이 없다.

**2) `campaign` per-leg 판정도 오도한다.** 게임은 매 미션 완료마다 `resolveEnding` 을 부르지만
(`state_actions_phases.ts:274`), `state.ts:196-202` 가 **계약이 계속되면 그 엔딩을 다음 leg로 덮어쓴다**
(`startNextLeg`). leg1/leg2 의 판정은 **삼켜져** 플레이어에게 보이지 않는다. per-leg 판정을 세어보면
control 이 **41.5%**(472/1137)로 "가장 흔한" 것처럼 보이지만, **그건 표시되는 엔딩이 아니다.**

**3) 표시되는 엔딩(최종 leg + 사망)만 세면** (20 시드 × 33 미션 = 660 계약):

| 표시 엔딩 | n | 비율 |
|---|---:|---:|
| sacrifice (사망) | 348 | 52.7% |
| liberation (완주) | 312 | 47.3% |
| **control** | **0** | **0%** |

→ **control 은 실제로 표시되지 않는다.** 최종 leg 만 표시되는데 그때는 항상 `missionsCompleted>=3`
→ liberation. ADR-0318 의 "control 은 계약을 끝내지 않고 부유하게 끝난 런" 주장은 **거짓**이었다 —
살아서 계약을 못 끝내는 런이 없기 때문(죽으면 sacrifice).

## 결정 (Decision)

**표시되는 최종 엔딩에서 control 을 되살린다 — 초고부 완주가 지배를 산다.**

`ending_resolver.ts` 에 상수를 하나 두고, `missionsCompleted>=3`(liberation) **앞에** 검사한다:

```ts
export const CONTROL_WEALTH = 18000; // ≈ 완주 계약 종료 크레딧 p90 (p50 10705 · p90 17650 · max 29355)
if (ctx.credits > CONTROL_WEALTH) return control;   // 초고부 완주
if (ctx.missionsCompleted >= 3) return liberation;  // 보통 완주
if (ctx.credits > 5000) return control;             // (레거시/계약 밖 런)
```

ADR-0314("부가 지배를 산다")와 ADR-0318("완주가 최고조")을 **둘 다** 존중한다: 대부분의 완주는
liberation, **가장 부유한 완주(~p90)** 만 control.

## 결과 (Consequences)

- **표시 엔딩 분포가 3분류로 살아난다** (660 계약): sacrifice 52.7% · liberation 44.4% ·
  **control 2.9%**(완주 계약의 6.1%). 임계값은 상수 하나로 조절 가능(15000→16.5%, 16000→14.2%,
  17000→7.6%, 18000→2.9% — 완주 크레딧 분포가 급격해 민감).
- **측정 도구 정정**: `campaign_survival.ts` 가 **표시되는 엔딩**(최종 leg + 사망)만 세고, 완주 크레딧
  분위수를 출력한다. `ending_distribution.ts` 는 단일-미션 경고를 단다.
- **거짓 결함 2건 제거**: "control 0/53 (도구 오독)" 과 "control 41.5% (삼켜진 판정)" 를 모두 바로잡음.
- **남은 열린 질문**: `status_quo` 는 여전히 계약 플레이에서 표시되지 않는다(레거시/계약 밖 런 전용).
  정리(제거 또는 조건 부여)는 별도 결정.
- 검증: `npm run campaign` 표시 엔딩 표 · `ending_resolver.test.ts`(ADR-0337 경계 테스트) ·
  typecheck 0 · 엔딩 테스트 70 pass.

## Implementation Status (2026-11-19)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/combat/ending_resolver.ts` — `CONTROL_WEALTH = 18000` + 초고부 완주 → control 분기
- `web/tests/ending_resolver.test.ts` — `ADR-0337` 경계 테스트
- `web/scripts/campaign_survival.ts` — 표시 엔딩(최종 leg+사망) 분포 + 완주 크레딧 분위수
- `web/scripts/ending_distribution.ts` — 단일-미션 경고
- 측정: control 19/660 = 2.9% (완주 계약의 6.1%)

**Notes**: 임계값 18000 은 오너 튜닝 대상(측정 표 제공). `status_quo` 미표시는 열린 질문.

## 영향 받는 항목

- `web/src/core/combat/ending_resolver.ts`, `web/tests/ending_resolver.test.ts`
- `web/scripts/campaign_survival.ts`, `web/scripts/ending_distribution.ts`
- `docs/design/verification-framework.md`

## 관련 결정

- ADR-0279 (해석기가 `player.credits` 를 읽는다) · ADR-0314 (부가 지배를 산다) ·
  ADR-0315 (런은 계약이다) · ADR-0318 (완주가 최고조) · ADR-0336 (검증 후속)

## 변경 이력

- 2026-11-19: Accepted (P1 엔딩 재조정 — 표시 엔딩에 control 복원 · 측정 도구 정정)
