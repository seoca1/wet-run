# ADR-0260: 시작 덱은 고른다 — 알파벳 순을 의도된 5장으로

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 승인 (2026-11-03 "모두 추천대로 해줘")
**우선순위**: P1 (The Flatline — 초반 난이도 곡선, The Build — 죽은 코드 제거)
**관련**: [ADR-0259 — 카드 보상(성장)](./0259-card-reward-growth.md) · [ADR-0256 — 카드 효과 밸런스 재기준선](./0256-card-effects-balance-rebaseline.md) · [ADR-0255 — 카드가 이름대로 동작한다](./0255-card-effects-are-real.md) · [ADR-0229 — grade curve 재기준선](./0229-grade-curve-rebaseline.md)

> **이 ADR은 시작 5장의 구성을 바꾸고, 그에 따른 밸런스 이동을 명시 수용한다**(ADR-0229 §3).
> 카드 효과·리듀서·RNG 는 건드리지 않는다.

## 컨텍스트 (Context)

시작 5장은 `main.ts` 의 `loadDeck` 이 **id 를 알파벳 정렬해 앞 5개**를 골라 만들었다:

```
backdoor, barrier, boost, cloak, decoy
= 공격 1 + 지원 1 + 방어 3
```

**디자인 결정이 아니라 이름의 우연**이다. 카드 효과를 배선한 뒤(ADR-0255) 이 구성의 결과가
드러났다 — 5장 중 4장이 방어/지원 리더를 달고 있어 초반이 매우 단단해졌고, g2·g3 승률이
각각 **100% / 97.5%** 로 올랐다(ADR-0256).

동시에 ADR-0259 이 **런 중 카드 획득**을 가능하게 만들었으므로, 시작 덱에서 빠지는 카드는
더 이상 "죽는" 카드가 아니다 — 보상으로 얻을 수 있다. 그래서 시작 5장을 의도적으로 고를 수 있다.

## 고려한 옵션

### Option 1 — 알파벳 순 유지 (ADR-0256 상태)
초반이 100%/97.5% 로 평평하다. 게임 도입이 "고르는 재미"를 가르치지 못하고, id 이름이
바뀌면 시작 덱이 조용히 바뀐다. **거부.**

### Option 2 — 의도된 5장으로 교체 (선택)

공격 3 + 방어 2, 전부 tier 1-3, 효과가 배선된 카드를 우선. **후보 5개를 실측**해 곡선이
가장 건강한 것을 골랐다:

| 후보 | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---|---|---|---|---|---|
| 알파벳(이전) | 100.0 | 100.0 | 97.5 | 53.4 | 44.1 | 0.3 |
| strike·backdoor·boost·barrier·**cloak** | 100.0 | 100.0 | 80.1 | 39.0 | 25.8 | 0.0 |
| backdoor·hammer·boost·barrier·cloak | 100.0 | 100.0 | 93.5 | 48.5 | 41.0 | 0.7 |
| backdoor·hammer·boost·barrier·decoy | 100.0 | 100.0 | 94.7 | 52.7 | 43.7 | 0.7 |
| **strike·backdoor·boost·barrier·decoy** | 100.0 | 100.0 | **81.4** | **42.6** | **36.6** | 0.0 |

`cloak`(회피 −15%) 대신 `decoy`(다음 타격 50% 흡수)를 고르면 g5 가 25.8 → 36.6 으로 회복된다 —
decoy 의 단일 타격 흡수가 강하기 때문이다. 그 조합이 ADR-0239 기준선(100/88.3/70.5/39.5/36.2/0)
과 가장 가까운 모양을 낸다.

## 사용자 결정 (Decision)

[x] **Option 2** — 의도된 5장:
`strike · backdoor · boost · barrier · decoy` (공격 3 + 방어 2)

## 결과 (Consequences)

### 바뀐 것

- `web/src/core/state/starting_deck.ts` (신규) — `STARTING_DECK_IDS` · `STARTING_DECK_SIZE` ·
  `startingDeck(catalog)`. **게임(`main.ts`)과 밸런스 하네스가 같은 상수를 읽는다** — 측정한 덱이
  플레이한 덱과 어긋날 수 없다.
- `main.ts` — 알파벳 정렬 `loadDeck` 제거.
- `web/scripts/balance_harness.ts` — 복제된 알파벳 로직 제거, 같은 상수 사용.
- **죽은 코드 제거** — `web/src/core/state/starter_deck.ts` 는 카탈로그에 없는 id
  (`strike_a` …)를 담은 8장 정의였고 게임이 쓰지 않았다(테스트 2개만 검증). 삭제하고
  `starting_deck.ts` + 그 테스트로 교체.

### 밸런스 (ADR-0229 §3 명시 수용)

| 곡선 | 이전 | **이후** | 참고 ADR-0239 |
|---|---|---|---|
| opening | 100.0 / 100.0 / 97.5 / 53.4 / 44.1 / 0.3 | **100.0 / 100.0 / 81.4 / 42.6 / 36.6 / 0.0** | 100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0 |
| PPL | 100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3 | **동일** | 100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7 |

PPL 은 `deckForGrade`(grade 별 최강 5장)를 쓰므로 시작 덱 변경의 영향을 받지 않는다.

**수용 근거**: 곡선이 단조 감소하고, g3 이 97.5 → 81.4 로 내려가 "고르는 재미"가 생기며,
g5 가 ADR-0239 수준(36.6 vs 36.2)으로 돌아왔다. g1·g2 가 100% 인 것은 도입 구간이라 의도된
쉬움이다.

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/starting_deck.test.ts` (신규) — 5장, id 유일, 카탈로그에 존재, **알파벳 순이 아님**,
  guard 가 2장 이하, tier ≤ 3, 카탈로그에 없는 id 는 건너뜀.
- `web/tests/boot_init.test.ts` — 시작 덱 계약(부팅 회귀 가드)을 새 모듈로 갱신.
- 밸런스 — [balance-opening.txt](../../design/card-reward-2026-11-03/balance-opening.txt).
- vitest **180 files / 3978 tests passed** · typecheck 0 · eslint 0 errors · build PASS.

**Notes**:

- g2 가 여전히 100% 다. 모든 후보가 그러했다 — 현재 카드 전력에서 g2 는 항상 이긴다.
  낮추려면 카드 전력을 조정해야 하며, 그것은 별도 결정(효과 수치)이다.
- 후보 실측 표는 [증거 README](../../design/card-reward-2026-11-03/README.md) 에 보존했다.

## 열린 질문

- **(a) g2 100%.** 도입 구간으로 의도된 쉬움인가, 조정이 필요한가.
- **(b) `cloak` 의 자리.** 시작 덱에서 빠져 보상으로만 얻어진다. 시작 카드로 되돌릴지는
  곡선과 함께 판단(위 후보 표).

## 영향 받는 항목

- `web/src/core/state/starting_deck.ts` (신규) · `web/src/main.ts` · `web/scripts/balance_harness.ts`
- `web/src/core/state/starter_deck.ts` (삭제) · `web/tests/starter_deck.test.ts` (삭제)
- `web/tests/starting_deck.test.ts` (신규) · `web/tests/boot_init.test.ts` · `web/tests/balance_sim.test.ts`

## 관련 결정

- ADR-0259 (성장 — 빠진 카드를 얻을 수 있게 함) · ADR-0255·0256 (카드 효과와 그 기준선) ·
  ADR-0229 (재기준선 절차) · ADR-0239 (기준선)

## 변경 이력

- 2026-11-03: Draft 작성
- 2026-11-03: Accepted — 오너 승인. 후보 5개 실측 후 구현.
