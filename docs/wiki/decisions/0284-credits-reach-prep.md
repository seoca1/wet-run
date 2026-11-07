# ADR-0284: 크레딧이 prep 으로 간다 — 그리고 곡선이 상한을 정한다

**상태**: Accepted
**날짜**: 2026-11-07
**결정자**: 오너 ("응.")
**우선순위**: P2 (경제 연결) · P1 (곡선 보호)
**관련**: [ADR-0283 — prep 은 용량이다](./0283-prep-is-capacity-not-cards.md) · [ADR-0282 — 전리품은 지출](./0282-the-loot-stop-is-a-spend.md) · [ADR-0279 — 지갑 매핑](./0279-the-run-states-its-earnings.md) · [ADR-0252 — 런 종료 시 슬롯 은퇴](./0252-run-end-and-save-timing.md) · [ADR-0275 — 화면은 자기 입력을 소유한다](./0275-screens-own-their-input.md)

> ADR-0282 의 전리품 `SALVAGE` 칸은 크레딧을 `player.credits`(런 원장)에 넣었는데,
> **prep 예산은 미션 보상에서 파생**되므로(ADR-0283) 크레딧으로 살 수 있는 것이 없었다 —
> 카드나 수리보다 **엄격히 나쁜** 칸이었다. 이 ADR 은 그 크레딧에 **다음 런의 prep** 이라는
> 목적지를 준다. 그리고 **목적지의 상한을 곡선이 정한다**는 것을 측정으로 확인했다.

## 컨텍스트 (Context)

ADR-0283 의 두 테이블(`PREP_HP_BY_GRADE` · `PREP_SHIELD_BY_GRADE`)은 **목표 곡선에 맞춰
fitted** 되어 있다. 즉 **여유가 없다.** 그 위에 어떤 보너스를 얹든 등급이 목표에서 벗어난다.

## 결정 (Decision)

### 1) SALVAGE 수입의 절반이 **영속 스톡파일**로 간다

`core/state/prep_wallet.ts` — localStorage 키 `wetrun_prep_wallet` (far-grid unlock ·
completion record 와 같은 패턴; **`SaveSlot` 밖**이므로 저장 스키마 무변경).
`PREP_WALLET_BANK_SHARE = 0.5`.

### 2) 스톡파일은 **fitted 등급에 얹지 않는다**

`prepWalletContribution(tableValue, balance, floor)`:
- `tableValue > 0` → **0**. 그 등급은 목표에 맞춰져 있고, 보태면 벗어난다.
- `tableValue === 0` → `min(balance, floor)` — 즉 **advance 가 아무것도 주지 않는 등급**을
  채운다("nothing offered" 가 있던 자리).

### 3) 사용하면 **소비된다**

prep 을 쓸 때 스톡파일의 몫을 차감한다(`spendPrepWallet`). 영구 보너스가 아니라 **비축**이다.

### 4) 화면은 출처를 밝힌다

`prep` 화면이 `advance + N cr banked` 를 말하고, 각 옵션이 `+X (N banked)` 로
**미션이 준 것과 스톡파일이 준 것**을 구분한다(ADR-0251 규칙 5).

## 측정 — 상한을 정한 것은 곡선이다

`npm run survival --seeds 16 --loot smart --prep stim`:

| 스톡파일 share | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---:|---:|---:|---:|---:|---:|
| **0.5** (첫 시도) wallet 0 | 100.0 | 98.0 | 81.8 | 45.6 | 31.9 | 18.8 |
| **0.5** wallet 500 | 100.0 | 100.0 | 83.5 | 60.6 | **51.4** | **29.2** |
| **0** (채택) wallet 0 | 100.0 | 98.0 | 81.8 | 45.6 | 31.9 | 18.8 |
| **0** wallet 500 | 100.0 | 100.0 | 79.0 | 45.0 | 31.9 | 18.8 |

**share 0.5 는 곡선을 깼다** — g5 **+19.5pp**, g6 **+10.4pp**. ADR-0283 이 맞춘 곡선이
무너진다. **share 0 은 fitted 등급을 그대로 둔다**(g4–g6 동일, g2 만 소폭).

원자료: `docs/design/adr-0284/credit-to-prep-spread.txt`.

## 결과 (Consequences)

- **크레딧이 막다른 길이 아니게 됐다** — 초반 등급에서 스톡파일이 "nothing offered" 를
  채운다.
- **fitted 곡선은 그대로다** — 스톡파일이 얹히지 않으므로 ADR-0283 의 목표가 유지된다.
- **불변**: `SaveSlot` 무변경(별도 localStorage 키) · 리듀서는 `addPrepWallet` 호출만 추가 ·
  RNG·시계 무접촉.

## Implementation Status (2026-11-07)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/state/prep_wallet.ts` — `readPrepWallet` · `addPrepWallet` · `spendPrepWallet` ·
  `prepWalletContribution` · `PREP_WALLET_BANK_SHARE` (신규).
- `web/src/core/state/prep.ts` — `prepWalletUse` · `prepGrantFor` · `applyPrep(state, choice, wallet)`.
- `web/src/core/state/state_actions_phases.ts` — `takeLootCredits` 가 절반을 적립.
- `web/src/renderer/prep.ts` — `wallet` · `fromWallet` 표시.
- `web/src/main.ts` — 화면에서 잔액 읽기, ENTER 에서 차감 후 `applyPrep`.
- `web/tests/prep_wallet.test.ts` (7).
- 하네스: `npm run survival -- --wallet N` (측정 전용).
- vitest **195 files / 4117 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 frozen 0 ·
  story trace 통과.

**Notes**:

- **스톡파일은 현재 곡선-안전하고, 그래서 약하다.** `SALVAGE` 는 카드·수리보다 여전히
  열등하다("거의 함정"이 완전히 해소되지는 않았다). 이건 실패가 아니라 **측정된 상한**이다.
- e2e 드라이버는 이번엔 고칠 필요가 없었다 — 화면 수가 그대로였기 때문(`prep` 재사용).

## 열린 질문

- **(a) 테이블을 낮추고 스톡파일이 그 차이를 메우게 할 것인가 — 이게 `SALVAGE` 를 살리는
  유일한 길이다.** 그러면 **돌아온 러너가 신규보다 쉽게** 플레이한다(메타 진행). fitted 테이블을
  낮추고 스톡파일로 목표를 되찾는 **재조정**이 필요하며, "신규는 더 어렵게, 숙련은 지금만큼" 이
  이 게임에 맞는지가 결정이다. **측정 근거**: share 0.5 에서 g5 +19.5pp / g6 +10.4pp.
- **(b) 스톡파일의 상한.** 지금은 등급별 floor(HP 15 / 실드 30)뿐이다. 초반 등급에서 이게
  충분한지, 아니면 "nothing offered" 가 사라지는 것 자체가 목적인지는 별개 질문이다.
- **(c) `SALVAGE` 에 다른 보상을 줄 것인가.** 크레딧 대신 즉시 용량 보너스(예: 소형 패치) 같은
  세 번째 길. 그러면 곡선 재조정 없이도 경쟁력이 생긴다.

## 변경 이력

- 2026-11-07: Draft → Accepted (오너 "응."). 크레딧 → prep 스톡파일, share 0 으로 곡선 보호.
