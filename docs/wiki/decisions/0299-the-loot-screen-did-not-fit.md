# ADR-0299: 전리품 화면은 40열에서 잘렸다 — 값이 잘려나갔다

**상태**: Accepted
**날짜**: 2026-11-08
**결정자**: 오너 ("Continue." — ADR-0298 (c))
**우선순위**: P1 (UI · 정직성)
**관련**: [ADR-0298 — SYPHON](./0298-syphon-a-hot-trace.md) · [ADR-0297 — 조합은 이미 있었다](./0297-the-combination-already-existed.md) · [ADR-0282 — 전리품은 지출](./0282-the-loot-stop-is-a-spend.md) · [ADR-0251 — 화면은 사실을 말한다](./0251-the-screen-states-what-happens.md)

> ADR-0295~0298 이 전리품 화면을 **4칸에서 8칸으로** 키웠고, 줄도 같이 길어졌다. 40열 레이아웃에서
> 실제로 렌더해보니 **글자가 중간에서 잘렸고**, 잘린 부분이 하필 **값(price)** 이었다.

## 측정 (Measurement)

`renderRunScreen(state, 40, 60)` — 흔적 80, HP 150/300:

```
5 INTEL           30cr — name the rout      ← 잘림
6 VENT            120 HP — clear 10 CO      ← 잘림
7 BURN            p1 (T1) — clear 7 CO      ← 잘림
8 SYPHON          10 COST — +75 HP → 2      ← 잘림
```

`+75 HP → 2` 는 **가격이 아니라 오타처럼 보인다.** 그리고 패널 하단 문구는
`1-3: card | 4: repair | 5: intel` — **ADR-0287 이후 늘어난 6·7·8 을 말하지 않는다**(ADR-0251
rule 5 위반: 동작하는 키를 말하지도, 동작하지 않는 키를 약속하지도 않아야 한다).

60열에서도 intel 줄(72자)이 잘린다.

## 결정 (Decision)

1. **좁은 레이아웃(< 76열)은 짧은 형식**을 쓴다. **모든 숫자는 남긴다**:

```
4 REPAIR +210HP → 300/300
5 INTEL 30cr
6 VENT 120HP → 70/100
7 BURN p1(T1) → 7
8 SYPHON 10 → +75HP
```

2. **패널 하단 문구는 호출자가 정한다** — `renderLootScreen(..., hint)`. 화면과 패널이 **같은
   문장**을 쓰므로 어긋날 수 없다.
3. **폭에 맞춰 문구를 줄인다**: 전체 문구가 패널에 안 들어가면 `1-3 card · 4-8 options`.

## 결과 (Consequences)

- **40·60·80 세 레이아웃 모두에서 모든 값이 읽힌다**(실측: 최장 줄 32자 / 42자 / 78자).
- **거짓 어포던스 두 개 제거**: 잘린 가격, 그리고 5번에서 멈춘 하단 문구.
- **불변**: 게임 규칙·곡선·저장 형식. 렌더러의 문자열과 폭 분기만.

## Implementation Status (2026-11-08)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/renderer/run_screen.ts` — `narrow = cols < 76` · 5개 옵션의 짧은 형식 · `lootHintFull`
  가 폭을 넘으면 `1-3 card · 4-N options`.
- `web/src/renderer/ending.ts` — `renderLootScreen(..., hint)`: 패널 하단이 호출자 문구를 쓴다.
- `web/tests/adr0299_loot_fits_the_narrow_panel.test.ts` (5) — 40·60열에서 **가격이 온전**(`70/100`
  포함) · **패널 폭 초과 없음** · 80열에서 긴 문장 유지 + 하단이 8번까지 이름.
- `web/tests/run_screen.test.ts` — 기대값이 같은 `hint` 를 넘기도록 갱신.
- vitest **204 files / 4160 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 ·
  story trace 통과.

**Notes**:

- **e2e 드라이버 수정 불필요** — 입력·화면 수 변화 없음.
- 76열이 경계인 이유: 가장 긴 전체 문구(intel 72자) + 좌우 여백.

## 열린 질문

- **(a) 칸이 더 늘면.** 지금은 8칸이 한 화면에 들어간다. 9칸 이상이면 **두 쪽**(전투 후 정산 /
  현금 지출)으로 나누는 편이 낫고, 그러면 화면 수가 늘어 e2e 드라이버 등록(ADR-0275)이 필요하다.
- **(b) 짧은 형식의 문법.** `7 BURN p1(T1) → 7` 은 숫자 두 개가 붙어 의미가 흐릿하다. `7 BURN p1(T1): -7 COST`
  같은 표기가 나을 수 있으나 40열에서 다시 길어진다.
- **(c) 자동 검사.** 지금은 이 ADR 의 테스트가 세 레이아웃을 지킨다. 새 옵션을 추가할 때 **폭 검사를
  자동으로** 하려면 렌더러가 "너무 긴 줄"을 경고하도록 만들 수 있다.