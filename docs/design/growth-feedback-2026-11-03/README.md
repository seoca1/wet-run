# 성장의 순간을 보여준다 (2026-11-03)

[ADR-0261](../../wiki/decisions/0261-growth-moment-is-shown.md) 의 증거다.
오너 요청: "성장에 대한 효과 이벤트나 표시가 있었으면 좋겠어. 재미 요소 중 하나라서 중요해."

## 무엇이 문제였나

ADR-0259 가 카드 보상을 넣었지만 **획득의 순간이 보이지 않았다**:
카드가 즉시 덱에 들어가고 화면이 바로 매트릭스로 넘어갔다 — 소리도, 강조도, 멈춤도 없었다.
HUD 메시지 한 줄(`Took Payload — added to your deck`)이 전부였고, 그마저 지나갔다.

## 바뀐 것 — 3박자

| 박자 | 무엇 | 어디 |
|---|---|---|
| **① 소리** | `SFX_IDS.EQUIP` — 정의·WAV 는 있었지만 **한 번도 재생되지 않던** id. 덱이 커지는 전환이 그것이 이름하는 사건이다 | `combat_sfx.ts` `pickEventSfx` |
| **② 멈춤** | 카드를 고르면 **즉시 이동하지 않는다.** 화면이 획득을 붙잡고 ENTER 를 기다린다 (로그라이크의 "고르고, 진행" 박자) | `takeCardReward` |
| **③ 표시** | 고른 카드는 **밝은 초록 + `ACQUIRED` + 캐럿**, 나머지 둘은 **흐리게**(소진). footer 는 `ENTER: continue` | `renderLootScreen` |

```text
DATA SALVAGE
HP 63/100
+4,075 credits
NEW PROGRAM
> 1 KRAKEN   ACQUIRED     ← 밝은 초록
  2 INSPIRE               ← 흐림 (소진)
  3 DECRYPT               ← 흐림 (소진)
HEAL applied → 78/100
ENTER: continue
```

그리고 **도착지가 성장을 이어받는다** — ENTER 뒤 메시지가
`Took Kraken. Choose an adjacent route — healed to 78/100` 이다.

## 저장 무결성

획득은 선택이므로 유도할 수 없다. `cardRewardTaken` 을 저장 슬롯에 **선택 필드**로 추가했다
(`currentNodeIndex`·`clearedEncounterNodes`·`bypassedEncounterNodes` 와 같은 패턴, version 1 유지).
그래서 저장된 loot 프레임을 다시 열어도 **이미 가져간 카드는 가져갈 수 없다** — 한 전투에 한 장.

제시 목록은 가져간 카드를 **계속 포함**한다(`ownedIds` 가 `cardRewardTaken` 을 되돌린다).
그러지 않으면 하나를 고른 순간 나머지 둘의 자리가 밀려 화면이 흔들린다.

`cardRewardTaken` 은 loot 를 떠날 때 지운다 — 다음 전투의 보상은 새로 시작한다.

## 검증

| 항목 | 결과 |
|---|---|
| vitest | **180 files / 3985 tests passed** (베이스라인 180/3978) — [npm-test.txt](npm-test.txt) |
| typecheck / eslint / build | 0 errors / 0 errors / PASS — [typecheck.txt](typecheck.txt) · [lint.txt](lint.txt) · [build.txt](build.txt) |
| 밸런스 | opening 100.0/100.0/81.4/42.6/36.6/0.0 · PPL 100.0/100.0/99.3/84.1/44.4/27.3 — **동일**(표시·사운드 전용) — [balance-opening.txt](balance-opening.txt) |
| 실플레이(ego-lite) | 제시 → `1` = `runPhase: loot`·`taken: "kraken"`·`"Acquired Kraken"` → ENTER = `matrix`·`taken: null`·`"Took Kraken."` · **console error 0** |
| 3개 레이아웃 캡처 | 그리드 초과 **0** · HUD 초과 **0** (18 케이스) |

### 캡처

| 제시 | 획득 (ADR-0261) | 종결 (보상 없음) |
|---|---|---|
| [80×50](loot-80x50-pair.png) · [60×40](loot-60x40-pair.png) · [40×60](loot-40x60-pair.png) | [80×50](loot-acquired-80x50-pair.png) · [60×40](loot-acquired-60x40-pair.png) · [40×60](loot-acquired-40x60-pair.png) | [80×50](loot-terminal-80x50-pair.png) · [60×40](loot-terminal-60x40-pair.png) · [40×60](loot-terminal-40x60-pair.png) |

## 테스트가 고정한 계약

- `card_reward.test.ts` — 획득 시 **loot 에 머문다**·`cardRewardTaken` 설정·제시 목록 안정·
  **두 번째 획득 거부**·ENTER 가 성장을 이름 붙이고 기억을 지움·미획득 ENTER 는 카드를 이름 붙이지 않음.
- `combat_event_sfx.test.ts` — 덱 증가 → `EQUIP`, 증가 없으면 소리 없음.
- `save_load_roundtrip.test.ts` — `cardRewardTaken` 왕복 보존, 미획득이면 슬롯에 없음.
- `run_screen.test.ts` — `ACQUIRED` 표시, 획득 후 HUD 는 `ENTER: continue`(숫자 미약속).

## 남은 항목 (보고)

1. **하네스가 성장을 모델링하지 않는다** — `balance_sim` 은 loot 를 걷지 않으므로 보상의 힘을 못 잰다.
2. **도착지 배너는 텍스트뿐** — 성장을 더 강조하려면 매트릭스 화면에 배너 밴드가 필요하다.
3. **제시 카드에 tier 가중치 없음** — 초반에 강한 카드가 나올 수 있다.
