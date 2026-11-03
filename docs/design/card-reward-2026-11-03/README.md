# 성장하는 재미 — 카드 보상 · 규칙 고지 · 시작 덱 (2026-11-03)

증거 묶음. 오너 요청 "모두 추천대로 해줘. 성장하는 재미는 중요해."

| ADR | 무엇 | 성격 |
|---|---|---|
| [0260](../../wiki/decisions/0260-starting-deck-is-chosen.md) | 시작 덱을 고른다 (알파벳 순 → 의도) | 밸런스 재기준선 |
| [0259](../../wiki/decisions/0259-card-reward-growth.md) | **전투 승리 후 카드 1장 선택 — 런의 성장** | 신규 메커닉 |
| [0258](../../wiki/decisions/0258-killing-blow-cost-rule-notice.md) | 결정타 COST 면제 규칙을 화면에 알린다 | 표시 전용 |
| (보류) | 좁은 화면 HUD 압축 | 기존 결함, 이번 범위 밖 |

## 이 세션 이전의 문제

1. **성장이 없었다.** 게임은 시작 5장을 주고 끝이었다. 상점 화면(`shop.ts`)은 껍데기
   (`renderShopScreen(_state)` — 인자를 안 씀)이고, 전리품은 재료만 줬다. 카탈로그의 25장은
   **플레이어에게 절대 오지 않는 죽은 콘텐츠**였다.
2. **시작 5장이 우연이었다.** `loadDeck`이 id를 알파벳 정렬해 앞 5개를 골랐다 —
   `backdoor, barrier, boost, cloak, decoy` = 공격 1 + 방어/지원 4. 그래서 초반이 매우 단단했고
   g2·g3 승률이 100% 로 올랐다.
3. **결정타 COST 면제 규칙이 안 보였다.** ADR-0254 가 거짓 예측 표기를 걷어냈지만
   그 자리에 아무것도 넣지 않아, 플레이어는 규칙을 알 수 없었다.

## 바뀐 것

### ③ 카드 보상 (ADR-0259)

비종결 노드에서 이기면 loot 화면이 **카드 3장을 제시**한다. `1`-`3` 로 하나를 골라 덱에 넣는다
(draw pile 에 들어가 다음 손패 순환 때 등장). 터치에서는 같은 3장이 버튼으로 뜬다.
`ENTER` 는 건너뛰고 이동한다.

```text
DATA SALVAGE
HP 61/100
+4,075 credits
NEW PROGRAM
1 PAYLOAD
2 KRAKEN
3 ECHO
HEAL applied → 79/100
1-3: take a card | ENTER: skip
```

제시 카드는 **런의 순수 함수**(mission seed + turn + node)다 — 저장된 loot 화면을 다시 열어도
같은 3장이 나오므로 재시도로 이득을 볼 수 없고, `Math.random` 을 **소비하지 않아** 밸런스
하네스가 영향을 받지 않는다. 이미 가진 카드는 제시하지 않는다.

종결 노드(보스/막다른 길)는 런이 끝나는 곳이라 **보상을 주지 않는다** — 다음 전투가 없다.

### ① 시작 덱 (ADR-0260)

알파벳 순을 **의도된 5장**으로 교체: `strike · backdoor · boost · barrier · decoy`
= 공격 3 + 방어 2, 전부 tier 1-3.

| 곡선 | 이전(알파벳) | **이후(의도)** | 참고: ADR-0239 |
|---|---|---|---|
| opening | 100.0 / 100.0 / 97.5 / 53.4 / 44.1 / 0.3 | **100.0 / 100.0 / 81.4 / 42.6 / 36.6 / 0.0** | 100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0 |
| PPL | 100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3 | **동일** (deckForGrade 는 시작 덱과 무관) | 100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7 |

**후보 5개를 실측해** 곡선이 가장 건강한 것을 골랐다:

| 후보 | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---|---|---|---|---|---|
| 알파벳(이전) | 100.0 | 100.0 | 97.5 | 53.4 | 44.1 | 0.3 |
| strike·backdoor·boost·barrier·**cloak** | 100.0 | 100.0 | 80.1 | 39.0 | 25.8 | 0.0 |
| backdoor·hammer·boost·barrier·cloak | 100.0 | 100.0 | 93.5 | 48.5 | 41.0 | 0.7 |
| backdoor·hammer·boost·barrier·decoy | 100.0 | 100.0 | 94.7 | 52.7 | 43.7 | 0.7 |
| **strike·backdoor·boost·barrier·decoy** | 100.0 | 100.0 | **81.4** | **42.6** | **36.6** | 0.0 |

`cloak` 대신 `decoy` 를 고르면 g5 가 25.8 → 36.6 으로 회복된다(decoy 의 1턴 흡수가 강하다).

### ② 결정타 COST 규칙 (ADR-0258)

- 전투 진입 힌트(런당 1회)에 한 줄 — 40열 레이아웃에도 들어가게 35자
  (`The last-hit program costs no COST.`)
- 승리 메시지에 `(no COST)` — 그 분기가 곧 결정타다

## 캡처 — 3개 레이아웃

*before* = `HEAD` web/src(`git archive`), *after* = 작업 트리.

| loot (보상 있음) | loot (종결, 보상 없음) |
|---|---|
| [80×50](loot-80x50-pair.png) · [60×40](loot-60x40-pair.png) · [40×60](loot-40x60-pair.png) | [80×50](loot-terminal-80x50-pair.png) · [60×40](loot-terminal-60x40-pair.png) · [40×60](loot-terminal-40x60-pair.png) |

폭 검사: **그리드 초과 0, HUD 초과 0** (loot 6개 케이스 전부).

## 검증

| 항목 | 결과 |
|---|---|
| `npx vitest run` | **180 files / 3978 tests passed** (베이스라인 179/3956) — [npm-test.txt](npm-test.txt) |
| `npx tsc --noEmit` | 0 errors — [typecheck.txt](typecheck.txt) |
| `npx eslint src` | 0 errors (기존 warning 1) — [lint.txt](lint.txt) |
| `npm run build` | PASS — [build.txt](build.txt) |
| `npm run balance` (opening) | 100.0 / 100.0 / 81.4 / 42.6 / 36.6 / 0.0 — [balance-opening.txt](balance-opening.txt) |
| `npm run balance -- --deck ppl` | 100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3 — **동일** — [balance-ppl.txt](balance-ppl.txt) |
| 실플레이(ego-lite Chromium) | 전투 승리 → `1` 로 Payload 획득 → `draw: ["payload"]`, `message: "Took Payload — added to your deck"` |

**밸런스 하네스는 loot 를 걷지 않는다** — 카드 보상은 하네스 밖이므로 PPL 곡선이 변하지 않았다.
그만큼 하네스는 실제 런의 성장을 **과소평가**한다(아래 "남은 항목").

## 발견하고 고친 것

- **`resolveProgramSelection` 이 combat 밖에서도 동작했다.** 손패에 카드가 남은 채 이기면,
  loot 화면의 숫자키가 `use_program` 으로 변환되어 보상 선택이 깨졌다. combat 전용으로 제한.
- **터치에 보상 경로가 없었다.** loot 중 프로그램 행이 비워져 모바일 플레이어는 고를 수 없었다.
  같은 3장을 버튼으로 공급(`rewardAffordances` + `handleRewardButton`).
- **죽은 코드 제거.** `state/starter_deck.ts` 는 카탈로그에 없는 id(`strike_a` …)를 담은 8장
  정의였고 게임이 쓰지 않았다(테스트 2개만 검증). `starting_deck.ts` 로 교체.

## 남은 항목 (보고)

1. **HUD 좁은 레이아웃 압축** — 40×60 에서 `> [1] Yakuza Enf HP: 165`(24자)·`Mission: …`(23자)가
   15자 패널에 압축된다. ADR-0254 (c) 그대로, HUD 재설계급이라 보류.
2. **하네스가 성장을 모델링하지 않는다** — `balance_sim` 은 loot 를 걷지 않으므로 카드 보상의
   힘을 재지 않는다. 실제 런은 하네스보다 강해진다. 하네스에 보상 단계를 넣으려면 seed 고정
   시뮬레이션이 필요하다(별도 작업).
3. **나머지 25장의 효과** — 카드 보상으로 이제 **획득 가능**해졌지만, 대부분 평범한 공격이다
   (설계 의도는 `plannedDescription`). 배선하면 이제 의미가 있다.
4. **결정타 COST 0 정책 자체** — 청구로 바꾸려면 리듀서 변경 + 재기준화(오너 결정).
