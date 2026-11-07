# ADR-0285: 전리품에 세 번째 선택지는 없다 — 만들 수 없다는 것을 측정하고 지웠다

**상태**: Accepted
**날짜**: 2026-11-07
**결정자**: 오너 ("c." — ADR-0284 열린 질문 (c): `SALVAGE` 에 다른 보상을 주기)
**우선순위**: P1 (선택의 정직성)
**관련**: [ADR-0282 — 전리품은 지출](./0282-the-loot-stop-is-a-spend.md) · [ADR-0284 — 크레딧이 prep 으로](./0284-credits-reach-prep.md) · [ADR-0283 — prep 은 용량](./0283-prep-is-capacity-not-cards.md) · [ADR-0260 — 시작 덱 큐레이션](./0260-starting-deck-is-chosen.md) · [ADR-0251 — 화면은 사실을 말한다](./0251-the-screen-states-what-happens.md)

> 전리품 다섯 번째 칸은 **두 번 실패했다**: 크레딧(ADR-0282)은 카드·수리보다 싸서 거의 함정이었고,
> ADR-0284 는 그 크레딧에 목적지를 줬지만 **fitted 등급에 얹지 않는** 방식이라 여전히 약했다.
> 세 번째 시도는 **용량**(플랫 maxHp 패치)이었다. 측정은 **지배당한다**고 말했고, 그래서 **칸을 지웠다.**

## 컨텍스트 (Context)

전리품 화면은 `1-3` 프로그램 · `4` 수리 · `5` (크레딧→패치)였다. 1-3 과 4 는 실재하는 가치가 있다:
카드는 **성장**(ADR-0259, 유일한 성장 경로)이고 수리는 **최대 HP 의 50~80%** 다.

## 측정 (Measurement)

플랫 maxHp 패치 `[12, 14, 18, 24, 60, 40]` 를 슬롯 5 에 넣고, 네 정책으로 재봤다
(`npm run survival --seeds 16`, prep=stim):

| 정책 | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---:|---:|---:|---:|---:|---:|
| `card` — 한 번도 안 쓴다 | 100.0 | 75.4 | 44.3 | 33.1 | 9.0 | 4.2 |
| `patch` — 항상 패치 | 100.0 | 96.1 | 53.4 | 35.6 | 6.9 | 0.0 |
| `smart` — 다치면 수리 | 100.0 | 98.0 | **81.8** | **45.6** | **31.9** | **18.8** |
| `mixed` — 건강하면 패치 | 100.0 | 81.3 | 48.9 | 33.1 | 9.0 | 4.2 |

**읽는 법**

1. 패치는 **"안 쓰기"보다는 낫다**(g2 75.4→96.1) — 즉 크레딧처럼 완전한 함정은 아니다.
2. 그러나 **제때의 수리에게 어디서나 지배당한다.** 결정적 비교는 `mixed` 대 `smart` 다:
   건강할 때 패치하는 것이 **훨씬 나쁘다**(g3 48.9 vs 81.8). 이유는 그 loot stop 에서
   **카드를 포기**하기 때문이고, loot stop 에서 **성장이 용량보다 비싸다**(ADR-0260 의 교훈과 같다).
3. 수리는 **최대 HP 의 50~80%**(g5 에서 70%면 100 이상)를 회복하는데, 플랫 패치는 g5 에서 **60** 이다.
   패치를 **비율**로 만들면 STIM prep(최대 HP 증가)과 **복리**되고 여섯 번까지 쌓여 더 나빠진다.

원자료: `docs/design/adr-0285/third-loot-option-spread.txt`.

## 결정 (Decision)

**슬롯을 지운다.** 전리품은 **카드 3장 + 수리**뿐이다.

**지배당하는 선택지는 선택이 아니다.** 남겨 두면 "고를 게 셋"처럼 보이지만 실제로는 **함정의 다른 모양**이고,
화면이 플레이어에게 **거짓 결정**을 제시하는 것이다(ADR-0251 의 정신). 관대해 보이려고 지배당하는 칸을
유지하는 것은 **결정에 대해 거짓말하는 것**이다.

**부수 정리**: prep 스톡파일(ADR-0284)은 이제 **승리가 지급하는 것**에서 적립한다
(`resolveVictory` 가 `totalReward` 의 절반을 적립). 슬롯이 사라져도 크레딧은 다음 런의 prep 에 닿는다.

## 결과 (Consequences)

- **화면이 정직해졌다**: 두 선택지 모두 실제로 값을 가진다.
- **크레딧의 목적지는 유지된다**(승리 적립 → prep 스톡파일).
- **불변**: `SaveSlot` · 리듀서 구조 · RNG · 시계 무변경. 수리·카드 경로는 그대로.
- **되돌린 것**: ADR-0284 의 `SALVAGE` 슬롯과 그 테스트, `LOOT_PATCH_*`, `takeLootPatch`,
  하네스의 `--loot patch|mixed`.

## Implementation Status (2026-11-07)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/state/loot_choice.ts` — 슬롯 5 제거, `lootSlotChoice` 가 `program | repair | null`.
- `web/src/core/state/state_actions_phases.ts` — `takeLootPatch` 제거(수리·카드 유지).
- `web/src/core/combat/victory.ts` — 승리 지급액의 절반을 prep 스톡파일에 적립.
- `web/src/renderer/run_screen.ts` · `ending.ts` — 오퍼 블록과 푸터에서 5번 제거
  (80열 `1-3: card | 4: repair | ENTER: none` · 40열 `1-3 card · 4 repair`).
- `web/tests/loot_choice.test.ts` — "5번은 선택지가 아니다" 로 교체.
- 측정: `docs/design/adr-0285/third-loot-option-spread.txt`.
- vitest **195 files / 4117 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 frozen 0 ·
  story trace 통과.

**Notes**:

- 이 ADR 은 **무엇을 만들지 않은 기록**이다. 세 번 시도한 끝에 슬롯이 사라졌고, 그 근거가
  네 정책의 수치다(`smart` 가 모든 등급에서 최선, `mixed` 가 최악).
- e2e 드라이버는 고칠 필요 없었다 — 화면 수가 변하지 않았다(키 하나가 죽었을 뿐).

## 열린 질문

- **(a) 크레딧의 소비처는 여전히 얇다.** 승리 적립 → prep 스톡파일이 전부이고, 그 스톡파일은
  ADR-0284 에 따라 **fitted 등급에 얹히지 않아** 초반 등급에서만 의미가 있다. 크레딧을 진짜로
  쓰게 하려면 **인런 상점**(`purchaseItem` 호출자 0) 또는 **테이블 재조정**이 필요하다.
- **(b) 엔딩 리졸버의 `control` 조건**이 여전히 `credits > 5000` 이다(ADR-0279 (b)).
  크레딧의 정의가 이 ADR 로 또 한 번 바뀌었으므로 함께 볼 시점이다.

## 변경 이력

- 2026-11-07: Draft → Accepted (오너 "c."). 플랫 패치 측정 → 지배당함 → 슬롯 제거, 스톡파일 적립원 이동.
