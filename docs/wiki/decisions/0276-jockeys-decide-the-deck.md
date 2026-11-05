# ADR-0276: 자키는 런의 시작 덱을 정한다 — 그리고 그 덱은 측정된다

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("자키가 런에 실제 영향" → "계속.")
**우선순위**: P1 (게임플레이 · 밸런스) · P2 (측정 가능성)
**관련**: [ADR-0274 — 런은 자키의 것이다](./0274-the-run-belongs-to-someone.md) · [ADR-0260 — 시작 덱 큐레이션](./0260-starting-deck-is-chosen.md) · [ADR-0255 — 프로그램 효과](./0255-card-effects-are-real.md) · [ADR-0251 — 텍스트는 화면이 하는 일을 말한다](./0251-truthful-program-affordance-and-combat-integrity-rules.md)

> ADR-0274 는 자키가 **누구인지**만 말하게 했다(런 인트로·엔딩 요약, 표시 전용). 이 ADR 은 자키가
> **어떻게 플레이되는지**를 정하게 한다 — 시작 덱을 자키별로 나눈다. 이 계열 작업에서 **처음으로 밸런스에 닿는**
> 변경이라, 세 덱을 전부 같은 곡선으로 측정하고 나서 확정했다.

## 컨텍스트 (Context)

ADR-0260 은 시작 덱을 "알파벳 앞 다섯 개"(우연히 공격 1 + 방어/지원 4) 에서 **큐레이션된 다섯 장**
(`strike, backdoor, boost, barrier, decoy`) 으로 바꿨다. 이후 그 다섯 장은 자키와 무관하게 고정이었다.

측정에 앞서 리듀서의 실제 구조를 확인했다.

- **데미지 경로는 하나**: 모든 프로그램이 `tier * 5` (ADR-0255, `program_effects.ts`).
- **실제 효과가 배선된 프로그램은 다섯 개뿐**: `backdoor`(관통 2) · `barrier`(실드 2, 2턴) ·
  `boost`(강화 +2, 2턴) · `cloak`(회피) · `decoy`(1턴 50%). 나머지는 **평타**이며, 설계된 효과는
  `plannedDescription` 에만 남아 있다.
- 따라서 CASE 덱은 이미 **다섯 효과 중 네 개**를 쥐고 있다.

## 결정 (Decision)

### 1) 시작 덱을 자키별로 나눈다 (`JOCKEY_DECK_IDS`)

```ts
novice:  STARTING_DECK_IDS,                                   // = [strike, backdoor, boost, barrier, decoy]
veteran: ["strike", "backdoor", "exploit", "barrier", "decoy"],
heretic: ["strike", "exploit", "virus", "surge", "decoy"],
```

- `startingDeck(catalog, jockeyId?)` · `startingDeckIds(jockeyId?)` 가 자키 덱을 해석하고,
  모르는 id 는 큐레이션 덱으로 **폴백**한다(데이터 편집이 부팅을 깨지 않게).
- `main.ts` 의 `launchSelected` 가 `startingDeck(programs, JOCKEYS[selectedJockey]?.id ?? null)` 로
  덱을 깐다.
- **하네스와 게임이 같은 표를 읽는다** — 측정한 덱과 플레이한 덱이 어긋날 수 없다.

### 2) 곡선을 측정하고 나서 확정한다 (측정이 결정을 바꿨다)

| grade | missions | CASE | SIL | KAS | PPL(참조) |
|------:|---------:|-----:|----:|----:|----------:|
| 3 | 11 | 78.4% | 83.8% | 78.6% | 99.3% |
| 4 | 10 | 38.9% | 44.5% | 38.8% | 84.1% |
| 5 | 9  | 33.4% | 38.3% | 33.2% | 44.4% |

(1·2·6 등급은 세 덱 모두 100.0/100.0/0.0 — 덱과 무관하게 너무 쉽거나 불가능해서, 차이는 3~5 등급에 산다.)
원자료·후보 측정: `docs/design/jockey-decks-2026-11-04/`.

**측정이 초안을 바꿨다.**

- **첫 KAS 덱은 함정이었다.** `strike, backdoor, virus, surge, decoy` 는 `boost`(강화)와
  `barrier`(실드) 를 `virus`/`surge`(같은 tier 의 **평타**) 로 바꾼 것 — 효과 두 개를 버리고 숫자를
  못 얻었다. 측정값 **3등급 72.4%**, 기본 덱(78.4%)보다 **5점 낮다.** 선택지가 함정이면 안 되므로 기각.
- **tier 상향만이 평타 경로가 보상하는 교환**이다. SIL 의 한 장 교체(`boost` t2 → `exploit` t3) 는
  3등급에서 약 **+5점**(78.4 → 83.8)을 사고, 덱의 성격을 바꾸지 않는다.
- 그래서 KAS 는 **방어를 버리는 대신 tier 로** 공격성을 산다: `strike, exploit, virus, surge, decoy`
  (때리는 네 장 + 안 때리는 한 장). **CASE 와 동급**(3등급 78.6 vs 78.4)이면서 형태가 다르다 —
  의도한 **수평 교환**(같은 힘, 다른 느낌)이고 함정이 아니다.

### 3) 하네스에 임의 덱 측정을 추가한다 (`--deck-ids`)

```
npm run balance -- --deck veteran            # SIL 곡선
npm run balance -- --deck-ids strike,exploit,virus,surge,decoy   # 후보 측정
```

후보를 **출시 전에** 같은 곡선으로 채점하기 위한 것이다(위 첫 KAS 덱이 이 도구로 기각됐다).
`--runs 50` 으로 스캔하고 `100` 으로 확정한다.

## 결과 (Consequences)

- **자키가 이제 런에 영향을 준다**: 이름(ADR-0274) + 시작 덱(이 ADR). 프롤로그 → 자키 → 미션 → 런이
  서사와 플레이 **양쪽**에서 이어진다.
- **선택지의 질이 균형 잡혔다**: 세 덱 모두 3등급 78~84% 대에 있고, 함정이 없다.
- **측정 가능성**: 자키 덱이 단일 표에 있고 하네스가 그 표를 읽으므로, 덱 편집은 곡선으로 검증된다.

### 발견 — 덱의 정체성은 지금 'tier' 뿐이다

배선된 효과가 다섯 개뿐이라, 자키는 **숫자로만** 달라질 수 있다(공격 tier). 자키가 **종류로** 달라지려면
(`KAS` 는 태우고 `SIL` 은 뚫는다) `plannedDescription` 의 효과를 실제로 배선해야 한다 — 열린 질문 (a).

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/state/starting_deck.ts` — `JOCKEY_DECK_IDS` · `startingDeckIds` · `startingDeck(catalog, jockeyId?)`.
- `web/src/main.ts` — `launchSelected` 가 자키 덱을 깐다.
- `web/scripts/balance_harness.ts` — `--deck veteran|heretic` + `--deck-ids a,b,c,d,e`.
- `web/tests/jockey_deck.test.ts` (6) — 자키별 덱 존재, 5장·중복 없음, **ADR-0260 형태**(press ≥ 3, blunt ≥ 1),
  서로 다름, 카탈로그 해석·미지 id 폴백, `main.ts` 소스 배선.
- **실브라우저**: `NEW RUN → (CASE|SIL|KAS) → 미션 → 발사` 후 `window.wetrun.state.deck` 이 각자 덱 —
  `novice=[strike,backdoor,boost,barrier,decoy]` · `veteran=[strike,backdoor,exploit,barrier,decoy]` ·
  `heretic=[strike,exploit,virus,surge,decoy]`.
- 곡선 (100 runs/mission, `docs/design/jockey-decks-2026-11-04/`): CASE `100.0/100.0/78.4/38.9/33.4/0.0` ·
  SIL `100.0/100.0/83.8/44.5/38.3/0.0` · KAS `100.0/100.0/78.6/38.8/33.2/0.0`.
- vitest **188 files / 4056 tests** · tsc 0 · eslint 0 errors · build PASS · `check_doc_claims.py` · `check_no_novel_prose.py` exit 0.

**Notes**:

- `SaveSlot.version` 은 **1 유지** — 덱은 저장 스키마가 아니라 매 런 시작 시 결정된다(저장된 `deckIds` 는 전투 중 덱).
- 세 덱 모두 ADR-0260 형태를 지킨다: 대다수가 공격, **방어 최소 1**. C10(전부 공격)은 2등급에서 무너져 기각됐다.
- SIL 은 의도적으로 소폭 상향(+5점대)이다 — "그녀는 해봤다"는 소개와 맞춘다.
- **2026-11-04 (ADR-0277): 열린 질문 (a) 종료.** `exploit` 을 실제로 배선했고(방어도 50% 무시),
  그 카드가 생기면서 큐레이션 덱만 유일하게 그 카드가 없어 3등급에서 SIL 보다 8.1점 낮아졌다.
  ADR-0276 이 스스로 정한 ±5%p 기준을 넘겼으므로 큐레이션 덱은 `backdoor` → `exploit` 으로 교체됐다.
  이 문서의 곡선은 ADR-0277 의 측정으로 대체된다
  (`docs/design/jockey-identity-2026-11-04/balance-*.txt`). 결정 본문은 그대로다.

## 열린 질문

- **(a) 덱이 종류로 달라지려면** `plannedDescription` 의 효과(virus=도트, surge=속공 등)를 배선해야 한다.
  지금은 tier 로만 다르다.
- **(b) 자키 선택 ↔ 프롤로그 체인.** 프롤로그는 여전히 `novice` 체인으로 시작한다(ADR-0274 b).
- **(c) 등급 6 이 세 덱 모두 0.0%.** 덱 문제가 아니라 등급 6 자체가 (PPL 로도 27.3%) 미완성이다.
- **(d) 줄 단위 소개.** 선택 화면의 소개문은 아직 덱을 언급하지 않는다. 넣을지는 화면 예산 문제.

## 영향 받는 항목

- `web/src/core/state/starting_deck.ts` · `web/src/main.ts` · `web/scripts/balance_harness.ts` ·
  `web/tests/jockey_deck.test.ts` · `docs/design/jockey-decks-2026-11-04/`

## 관련 결정

- ADR-0274 (자키 = 이름) · ADR-0260 (시작 덱 큐레이션 — 이 ADR 이 그 위에 자키 축을 얹는다) ·
  ADR-0255 (프로그램 효과 — 배선된 5개가 이 ADR 의 제약) · ADR-0251 (텍스트/메커니즘 일치)

## 변경 이력

- 2026-11-04: 오너 "계속." → 자키별 시작 덱 · 후보 8종 측정 · 함정 덱(KAS 초안) 기각 · 실브라우저 확인.
