# ADR-0261: 성장의 순간을 보여준다 — 획득 3박자

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 요청 ("성장에 대한 효과 이벤트나 표시가 있었으면 좋겠어. 재미 요소 중 하나라서 중요해")
**우선순위**: P1 (The Run — 런 안 성장의 재미, The Style — 피드백)
**관련**: [ADR-0259 — 카드 보상(성장)](./0259-card-reward-growth.md) · [ADR-0260 — 시작 덱](./0260-starting-deck-is-chosen.md) · [ADR-0251 — 어포던스 진실성 §5](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0185 — 세이브 마이그레이션](./0185-save-migration-v2.md)

> **이 ADR은 ADR-0259 의 보상에 피드백을 붙인다.** 획득 순간에 소리·멈춤·표시를 주고, 그 선택을
> 저장해 한 전투에 한 장을 넘지 못하게 한다. 밸런스·RNG·게임 메커닉은 무변경.

## 컨텍스트 (Context)

ADR-0259 가 카드 보상을 넣었지만 **획득의 순간이 보이지 않았다**.

- 카드는 즉시 덱에 들어가고 화면은 바로 매트릭스로 넘어갔다.
- 소리 없음. 시각 강조 없음. 멈춤 없음.
- 남는 것은 HUD 메시지 한 줄(`Took Payload — added to your deck`)뿐이었고, 그것도 지나갔다.

"성장하는 재미"는 오너가 명시적으로 중요하다고 한 요소인데, 정작 성장의 순간이 사건으로서
존재하지 않았다. 보상이 **발생은 하는데 느껴지지 않았다.**

또 하나: 획득이 transition 과 동시에 일어나면, 플레이어가 **무엇을 얻었는지 놓칠 수 있다** —
특히 여러 장을 빠르게 넘길 때.

## 고려한 옵션

### Option 1: 소리만 (최소)
`pickEventSfx` 에 "덱 증가 → `EQUIP`" 한 줄. 즉시 전환이라 시각 강조는 불가.
싸지만 "느껴지는" 정도가 약하다 — 사용자가 요청한 "표시"가 없다.

### Option 2: 소리 + 획득 3박자 (선택)
**① 소리**(`EQUIP`) · **② 멈춤**(고르면 이동하지 않고 ENTER 대기) · **③ 표시**(고른 카드 강조 +
`ACQUIRED`, 나머지 흐림, footer `ENTER: continue`). 그리고 도착지 메시지가 성장을 이어받는다.

### Option 3: 애니메이션/타이머 기반 연출
자동 전환·트윈 등. **금지 영역**이다 — ADR-0251 §"이건 짓지 마라" 가 "리듀서 안의 추가
오디오/DOM/벽시계 부작용", "입력 락", "애니메이션 큐"를 명시적으로 배제한다.

**결정: Option 2.** 벽시계도 입력 락도 없이, 플레이어의 ENTER 가 박자를 만든다.

## 사용자 결정 (Decision)

[x] **Option 2** — 소리 + 획득 3박자

## 결과 (Consequences)

### 3박자

| 박자 | 내용 |
|---|---|
| **소리** | `SFX_IDS.EQUIP` — 정의·WAV 는 있는데 **한 번도 재생되지 않던** id(built-but-unwired). 덱이 커지는 전환이 그것이 이름하는 사건이다 |
| **멈춤** | `takeCardReward` 가 **더 이상 `continueToMatrix` 를 호출하지 않는다.** 획득 상태로 머물고 ENTER 가 진행한다 |
| **표시** | 고른 카드 `> 1 KRAKEN  ACQUIRED`(밝은 초록) · 나머지 둘 흐림(소진) · footer `ENTER: continue` |

도착지 메시지: `Took Kraken. Choose an adjacent route — healed to 78/100` — 성장이 화면과 함께
사라지지 않는다.

### 저장 무결성 (ADR-0261 이 만든 제약)

획득은 **플레이어의 선택**이라 유도할 수 없다. 그래서 `cardRewardTaken` 을 저장 슬롯에
**선택 필드**로 추가했다(`currentNodeIndex`·`clearedEncounterNodes`·`bypassedEncounterNodes` 와 같은
패턴, `version` 1 유지). 저장된 loot 프레임을 다시 열어도 **이미 가져간 카드는 다시 못 가져간다.**

**제시 목록 안정성**: `ownedIds` 가 `cardRewardTaken` 을 되돌려 제시 목록에 남긴다.
그러지 않으면 하나를 고른 순간 나머지 둘의 자리가 밀려 화면이 흔들린다.

**정리**: `cardRewardTaken` 은 loot 를 떠날 때(`continueToMatrix`) `null` 로 지운다.

> ADR-0259 는 "새 영속 필드 없음"을 설계 제약으로 삼았다. 이 ADR 은 **획득 박자를 위해 그 제약을
> 한 필드만큼 푼다** — 대가는 선택 필드 1개 + 검증 1줄이고, 이득은 저장 무결성과 재현 가능한 화면이다.

### 불변

- **밸런스 byte-identical** — opening `100.0 / 100.0 / 81.4 / 42.6 / 36.6 / 0.0`,
  PPL `100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3`. 표시·사운드 전용.
- `version` 1 유지 — 구 슬롯은 필드가 없어도 로드된다(`?? null`).
- ADR-0259 의 결정(보상 로직·순수 함수·RNG 0)·ADR-0260·ADR-0243 무변경.
- 벽시계·입력 락·애니메이션 큐 없음(ADR-0251 §"이건 짓지 마라" 준수).

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/card_reward.test.ts` — 획득 시 loot 에 머묾·`cardRewardTaken` 설정·목록 안정·
  두 번째 획득 거부·ENTER 가 성장을 이름 붙이고 기억을 지움.
- `web/tests/combat_event_sfx.test.ts` — 덱 증가 → `EQUIP`, 증가 없으면 소리 없음.
- `web/tests/save_load_roundtrip.test.ts` — `cardRewardTaken` 왕복 보존.
- `web/tests/run_screen.test.ts` — `ACQUIRED` 표시, 획득 후 `ENTER: continue`.
- 3개 레이아웃 캡처(18 케이스, 그리드/HUD 초과 0) —
  [growth-feedback-2026-11-03](../../design/growth-feedback-2026-11-03/README.md).
- 실플레이(ego-lite Chromium) — 제시 → `1` = `loot`·`taken: "kraken"`·`"Acquired Kraken"` →
  ENTER = `matrix`·`taken: null`·`"Took Kraken."`, console error 0.
- vitest **180 files / 3985 tests passed** · typecheck 0 · eslint 0 errors · build PASS.

**Notes**:

- 획득에 ENTER 한 번이 추가된다. 이는 의도된 박자다(로그라이크의 "고르고, 진행") —
  벽시계로 자동 진행하면 ADR-0251 이 금지한 영역에 들어간다.
- 도착지 강조는 아직 메시지 텍스트뿐이다(아래 열린 질문).

## 열린 질문

- **(a) 도착지 배너.** 성장을 더 강조하려면 매트릭스 화면에 배너 밴드가 필요하다(별도 슬라이스).
- **(b) 하네스 모델링.** `balance_sim` 이 loot 를 걷지 않아 보상의 힘을 재지 못한다(ADR-0259 (b)).
- **(c) tier 가중치.** 제시 카드를 초반에 낮은 tier 로 기울일지.

## 영향 받는 항목

- `web/src/core/types.ts` — `GameState.cardRewardTaken` · `SaveSlot.cardRewardTaken`
- `web/src/core/state/card_reward.ts` — `ownedIds` 가 taken 을 되돌림
- `web/src/core/state/state_actions_phases.ts` — `takeCardReward` (머묾) · `continueToMatrix` (정리·메시지)
- `web/src/core/combat/combat_sfx.ts` — 덱 증가 → `EQUIP`
- `web/src/core/combat/program_affordance.ts` — `formatRewardOption(taken)`
- `web/src/renderer/ending.ts` · `run_screen.ts` — 획득 강조
- `web/src/core/state/state.ts` · `web/src/save/storage.ts` — 저장/복원/검증

## 관련 결정

- ADR-0259 (보상 — 이 ADR 이 그 피드백이다) · ADR-0260 (시작 덱) · ADR-0251 (규칙 5 + 금지 목록) ·
  ADR-0185 (세이브 마이그레이션)

## 변경 이력

- 2026-11-03: Draft 작성
- 2026-11-03: Accepted — 오너 요청. 구현 완료.
