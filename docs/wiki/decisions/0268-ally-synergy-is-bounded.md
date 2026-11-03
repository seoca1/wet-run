# ADR-0268: 동료가 전투를 대신하지 않게 — Dixie 콤보 상한

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("그래." — 끝까지 완주 검증 후 권고 1번 승인)
**우선순위**: P1 (전투 주체성 / 밸런스)
**관련**: [ADR-0266 — COST 상한 턴 패스](./0266-cost-cap-turn-pass.md) · [ADR-0256 — 카드 효과 밸런스 재기준선](./0256-card-effects-balance-rebaseline.md) · [ADR-0260 — 시작 덱](./0260-starting-deck-is-chosen.md) · [ADR-0239 — 밸런스 곡선 기준선](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0265 — 소크 하네스](./0265-combat-freeze-at-the-cost-cap.md)

> **플레이어가 관객이었다.** 실제 완주 로그에서 Dixie 는 `11 → 35 → 68 → 80 → 92 dmg` 인데
> 같은 시점 카드는 `4~17 dmg` 였다. 원인은 `Dixie = 8 + playerCombo × 3` 인데 **콤보가 런 내내
> 리셋되지 않기** 때문이다 — 콤보 체계 자체는 **6에서 끝나도록 설계**돼 있다.

## 컨텍스트 (Context)

측정(실제 빌드·실제 키 완주, `docs/design/ending-run-2026-11-04/story-trace.txt`):

```
[4]  >>> Dixie attacks: 11 dmg     ← combo 1
[19] >>> Dixie attacks: 35 dmg
[41] >>> Dixie attacks: 68 dmg
[52] >>> Dixie attacks: 80 dmg
[61] >>> Dixie attacks: 92 dmg
     Strike → 6 dmg · Boost → 4 dmg · Kraken → 17 dmg
```

코드 사실:

| 사실 | 근거 |
|---|---|
| `Dixie 데미지 = DIXIE_BASE_DAMAGE(8) + playerCombo × DIXIE_SYNERGY_BONUS(3)` | `processDixieTurn` |
| **콤보는 런 내내 누적** — 전투 진입(`openArrivalEncounter`)이 리셋하지 않는다 | 리셋은 `makeInitialState`/복원뿐 |
| 콤보 체계는 **6에서 끝난다** — `COMBO_BONUSES` 의 마지막 키가 6(×3.0), 7 이상은 `?? 1.0` 로 폴백 | `combat_engine.ts` |
| 즉 **7 이상 콤보는 카드 피해에 아무 이득이 없는데**, Dixie 만 계속 강해졌다 | 위 두 사실의 결합 |

부작용: ADR-0266 의 **COST 상한 패스**와 만나면, 상한에서는 카드를 못 쓰므로 **패스만 가능**하고
패스는 턴을 넘겨 Dixie 를 계속 공격시킨다 → **상한 도달 13런이 전부 완주**(= 가만히 있어도 이김).

## 결정 (Decision)

**Dixie 의 시너지를 콤보 체계가 정의한 상한에서 자른다.**

```ts
/** 콤보 피해표가 정의하는 상한: COMBO_BONUSES 는 6에서 끝나고, 그 위는 배율이 1.0 으로 폴백한다. */
export const MAX_COMBO = Math.max(...Object.keys(COMBO_BONUSES).map(Number)); // 6

export function dixieDamage(combo: number): number {
  return DIXIE_BASE_DAMAGE + Math.min(combo, MAX_COMBO) * DIXIE_SYNERGY_BONUS;
}
```

- **카드 피해 배율은 무변경** — 손대지 않는다.
- **콤보를 리셋하지 않는다**(최소 변경): 상한이 걸리면 런 내내 누적돼도 Dixie 는 26 에서 멈춘다.
  리셋은 의미상 더 깔끔하지만 전투 진입 경로를 건드리는 별도 결정이다(열린 질문 a).
- 순수 함수 `dixieDamage` 로 분리해 **공식이 테스트 가능**해졌다(이전엔 리듀서 내부 인라인).

## 결과 (Consequences)

- **Dixie 최대 26** (이전: combo 28 에서 92, 사실상 무한). 플레이어 카드(4~17)와 같은 자릿수가 된다.
- **패스가 무료 승리 버튼이 아니게 된다** — 상한에서 가만히 있으면 동료가 26 씩 때리는 동안 적이 때린다.
  상한은 여전히 "예산 소진"이고, 결판은 전투가 낸다.
- **밸런스 재기준선**(`npm run balance`, 큐레이션 시작 덱):

| grade | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 이전 | 100.0 | 100.0 | **81.4** | **42.6** | **36.6** | 0.0 |
| 이후 | 100.0 | 100.0 | **78.4** | **38.9** | **33.4** | 0.0 |

- **PPL 덱은 불변**(`100.0/100.0/99.3/84.1/44.4/27.3`) — 강한 덱은 전투가 짧아 콤보가 상한에 닿지 않는다.
- **불변식 테스트 덱**(알파벳 5장)은 g3 만 `97.5 → 97.2`.
- 곡선 **단조 감소 유지**, g6 여전히 치명적.

### 불변

- 카드 피해·콤보 배율·`COMBO_BONUSES`·`processDixieTurn` 의 호출 조건(2플레이어턴마다) 무변경.
- COST 상한 패스(ADR-0266)·죽음 retire(ADR-0264)·문서 검사기(ADR-0267) 무변경.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/combat/state_actions_combat.ts` — `MAX_COMBO` · `dixieDamage()` · `processDixieTurn` 이 그것을 사용.
- `web/tests/dixie_combo_cap.test.ts` (3) — 상한값 6, combo 0/1/6 공식, **7·12·28·60 이 모두 26**.
- `web/tests/balance_sim.test.ts` — 기준선 갱신(이유를 주석에 명시).
- `npm run balance` 재측정: 위 표. `npm run balance -- --deck ppl`: 불변.
- **소크 재측정**(`random` 53셀, 상한 후): **완주 53/53 · 정지 0**, 그중 **17런이 COST 상한 도달**하고
  **17런 전부 완주**. 즉 상한은 이제 **생존 가능한 상태**이고(동료 최대 26), 정지는 없다.
  기록: `docs/design/ending-run-2026-11-04/report-dixie-cap.json`.
- vitest **183 files / 4024 tests** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 상한이 걸려도 **콤보 표시/판정은 그대로**다(전투 내 6콤보 보상도 그대로).
- 이 변경으로 ADR-0266 (e) 의 "패스가 무료 승리 버튼"이 해소된다.

## 열린 질문

- **(a) 콤보를 전투 단위로 리셋할 것인가.** 지금은 런 내내 누적이고, 상한 덕분에 피해는 안전하다.
  의미상 "새 전투 = 새 콤보"가 맞다면 `openArrivalEncounter` 에서 0 으로. 다만 카드 배율이 6 위에서
  1.0 으로 폴백하는 이상 동작도 함께 정리해야 한다(별도 ADR).
- **(b) 6 위 콤보 폴백.** `COMBO_BONUSES[combo] ?? 1.0` 은 "콤보가 높을수록 약해지는" 구간을 만든다.
  상한(6)에서 멈추거나, 표를 확장하거나, 명시적으로 리셋해야 한다.
- **(c) 동료의 정체성.** Dixie 가 매 턴 8~26 을 넣는 것이 "동료"인지 "자동 포탑"인지는 연출의 문제다
  (엔딩 완주 감사의 서사 항목 5건 중 2번).

## 영향 받는 항목

- `web/src/core/combat/state_actions_combat.ts` · `web/tests/dixie_combo_cap.test.ts` (신규) ·
  `web/tests/balance_sim.test.ts` (기준선)

## 관련 결정

- ADR-0266 (COST 상한 패스 — 이 ADR 이 그 부작용을 닫는다) · ADR-0256/0260 (밸런스 기준선) ·
  ADR-0265 (소크 하네스 — 상한 도달률을 재는 도구)

## 변경 이력

- 2026-11-04: 엔딩 완주 감사에서 발견 → 오너 승인("그래.") → 상한 구현 · 재기준선.