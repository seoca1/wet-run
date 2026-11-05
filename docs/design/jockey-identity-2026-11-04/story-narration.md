# 첫 잭인 — CASE의 한 런을 이야기로 읽기

> 이 글은 `story-trace.txt` 를 **서사로 옮긴 것**이다. 괄호 안은 트레이스에 실제로 찍힌 값
> (HP/COST/ICE/크레딧)이고, 인용문은 화면에 실제로 뜬 문장이다.
> 트레이스는 **메시지나 단계가 바뀔 때만** 한 줄을 남기므로, 몇 번의 입력은 한 줄로 접혀 있다.
> 런: CASE(자키 0) · `First Jack`(arc 1, surface, fixer finn) · 15 스텝 · 7 턴 · 엔딩 `arc1_wage_slave`.

---

## 0. 잭인 전 — 두 개의 온도

자키 선택 화면에서 CASE를 고른다. 소개 문구는 이렇게 말한다.

> **CASE** — "New hands. Old reflexes. The deck is already warm."

미션을 고르고 잭인하면, arc 1의 인트로가 화면을 덮는다.

> **FIRST JACK**
> "The deck is cold in your hands."
> "The matrix opens like a door somebody paid for, and somebody is already inside."

덱은 방금 **따뜻하다**고 했는데, 문이 열리자 **차갑다**. 이 모순은 아래에서 다시 언급한다.

## 1. 문이 막혔다 — BREACH

`First Jack`. finn이 준 일이고, 기본 보상은 500 크레딧, 목표는 데모 파일 하나다.
CASE는 node 0에 서 있다. 손패는 다섯 장 — `strike`, `exploit`, `boost`, `barrier`, `decoy`.
COST는 0. 앞쪽 노드에 ICE 하나가 보인다 (ICE 35).

한 칸 이동하자 길이 막힌다.

> "Travel blocked. BREACH: fight. BYPASS: 60 COST (once per run). JACK OUT: abandon run."

우회로는 60 COST를 요구하고, 그 우회는 런당 한 번뿐이다. CASE는 돈을 아끼고 **BREACH**를 고른다.
문을 여는 대신, 문 앞에 서 있는 것을 상대하기로.

> "Entering mid... (1 ICE)"

## 2. 첫 전투 — Wisp

> "Combat vs ICE — Wisp"

Wisp는 35 HP, 방어도 0, 기술 없음. 이름처럼 잡히지 않는 대신 단단하지 않다.
CASE가 `exploit` 을 쓴다. 이 카드는 **방어도의 절반을 무시하는** t3 공격인데, Wisp의 방어도가 0이라
이번엔 그 특권이 아무 값도 하지 않는다 — 그냥 15 피해짜리 카드다. 실제로는 28이 들어가 ICE가 7로 떨어진다 (ICE 35 → 7).

그런데 그 턴의 로그에 남은 첫 줄은 CASE의 공격이 아니다.

> ">>> Dixie attacks: 11 dmg"

Dixie가 먼저 때린다. Wisp가 되받아 CASE를 4만큼 긁는다 (HP 100 → 96).
그리고 Wisp는 죽는다 — 마지막 일격은 트레이스에서 승리 메시지에 접혀 있다.

> "ICE — Wisp defeated! (no COST) +625 credits Loot: ice_shardx1"

## 3. 전리품 — 625 크레딧, 그리고 Scan

전투 보상은 625 크레딧(미션 기본 500 + 노드 보상)과 `ice_shard` 하나.
그 위에 카드 제안이 뜬다.

> "Acquired Scan — press ENTER to continue"

CASE는 Scan을 받는다.

> "Took Scan. Choose an adjacent route — healed to 100/100"

여기서 런의 **성장**이 일어난다. 문제는 이 성장이 이 런에서 **한 번도 손에 들어오지 않는다**는 것이다
(아래 결함 1). Scan은 드로우 파일에 들어가고, 이 런은 손패가 비기 전에 끝난다.

## 4. 표면으로, 다시 막힌 문

node 1에서 node 3으로 나간다.

> "Moved to surface — ↑↓ picks the next route"

한 칸 더, node 5. 또 막혔다. 이번에는 우회도 막혀 있다.

> "Travel blocked. BREACH: fight. BYPASS: blocked here. JACK OUT: abandon run."

선택지가 하나로 줄었다. 다시 BREACH.

> "Entering core-deep... (1 ICE)"

미션 구역은 `surface` 인데 화면은 `mid`, `core-deep` 를 말한다 (아래 결함 5).

## 5. 두 번째 전투 — 같은 이름

> "Combat vs ICE — Wisp"

또 Wisp다. 같은 35 HP, 같은 이름, 같은 기술 없음. 한 미션에 ICE 노드가 둘인데 둘 다 같은 타입이 나왔다.

CASE의 손패는 이제 세 장이다 — `strike`, `boost`, `decoy`. 첫 전투가 손패를 다 쓰기 전에 끝났고,
**손패는 전투 사이에 다시 채워지지 않는다** (아래 결함 2). 방금 받은 Scan도, 새로 뽑힐 카드도 없다.

> ">>> Dixie attacks: 17 dmg"

Dixie가 17을 넣는다. 콤보가 쌓였기 때문이다. ICE가 4로 떨어지고, CASE가 마무리한다.

> "ICE — Wisp defeated! (no COST) +1675 credits Loot: combat_modulex2, data_fragmentx3"

## 6. 엔딩 — Wage Slave

> **Wage Slave** / 노동 노예
> "You survived. Nothing changed."
> 살아남았다. 아무것도 바뀌지 않았다.

요약 줄은 이렇게 남는다.

> **CASE — First Jack**
> HP 100/100 · 2,300cr · 7 turns

첫 잭인. 두 번의 교전. 2,300 크레딧. 체력은 만피. 그리고 아무것도 바뀌지 않았다.

---

# 검증 — 이 이야기가 그럴듯한가

## 결론부터

**골격은 그럴듯하고, 중간이 비어 있다.**

- **arc 1의 약속과 엔딩이 정확히 맞는다.** "첫 잭인 → 돈을 받는다 → 아무것도 바뀌지 않는다"는
  arc 1의 정의 그 자체다. `Wage Slave` 는 이 런에 **틀린 엔딩이 아니다**. 오히려 가장 정확한 엔딩이다.
- **수치가 서사와 어긋나지 않는다.** 2,300 크레딧은 실제로 번 돈이고(625 + 1675), 7턴은 실제 턴 수이며,
  화면에 뜨는 값과 트레이스가 일치한다. (이 값은 이번에 고쳤다 — 전에는 미션 기본 보상인 500cr이 떴다.)
- **끊김은 없다.** 15스텝 동안 입력이 먹히지 않는 지점이 없었고, 엔딩에서 타이틀로 정상 복귀했고,
  세이브 슬롯도 은퇴했다. 소크 하네스(3런)도 정지 0.

**그런데 이야기로서는 중간이 얇다.** 두 교전이 **같은 적**이고, 런의 유일한 성장(Scan)이
**손에 들어오지 않으며**, 두 전투 모두 **로그의 첫 줄이 Dixie의 공격**이다. 그래서 "내가 첫 잭인을
뚫었다"보다 "Dixie가 뚫고 나는 따라갔다"로 읽힌다.

## 점수 (주관, 근거는 위)

| 축 | 점수 | 근거 |
|---|---:|---|
| 프레임(인트로 → 엔딩) | 8/10 | arc 1의 주제와 엔딩이 맞고, 요약 수치가 정직하다 |
| 전투 서사 | 4/10 | 같은 적 2회, 방어도 0이라 `exploit` 의 정체성이 안 보인다 |
| 성장 체감 | 2/10 | 받은 카드가 이 런에서 한 번도 등장하지 않는다 |
| 인과 | 6/10 | 이동 → 차단 → BREACH → 전리품 → 엔딩의 연결은 매끄럽다 |

## 발견한 결함 (심각한 순)

1. **받은 카드가 런에서 한 번도 나오지 않는다.** `Scan` 을 받았지만 드로우 파일로 들어가고,
   손패가 비기 전에 런이 끝나서 한 번도 뽑히지 않는다. 화면은 "Acquired Scan" 이라고 약속하고
   런은 그 약속을 지키지 않는다. **성장이 이 게임의 재미라면 이건 P1이다.**
2. **손패가 전투 사이에 초기화되지 않는다.** 첫 전투를 2장 써서 끝냈기 때문에 두 번째 전투는 3장으로 시작한다.
   정지로 이어지진 않지만(전투 중 손패가 비면 리필된다), 교전마다 난이도가 달라지고 결함 1의 원인이다.
3. **한 미션의 두 ICE가 같은 타입이다.** 둘 다 `Wisp`(35 HP, 방어도 0). 미션 안에서 적 다양성이 없다.
4. **톤 충돌.** 자키 소개는 "The deck is already warm", arc 1 인트로는 "The deck is cold in your hands."
   둘 다 덱의 온도를 말하는데 반대다. 의도된 아이러니라면 한쪽을 그렇게 읽히게 써야 한다.
5. **구역 이름 불일치.** 미션 zone은 `surface` 인데 진입 메시지는 `Entering mid...`, `Entering core-deep...`.
6. **전리품 표기.** `Loot: ice_shardx1` 에 공백이 없고, 다른 줄은 `combat_modulex2, data_fragmentx3` 로
   쉼표를 쓴다. 같은 화면 안에서 형식이 둘이다.
7. **동료가 전투 로그의 첫 줄을 가져간다.** 두 전투 모두 `>>> Dixie attacks` 가 먼저 찍히고
   (11, 17 피해), CASE의 타격은 그 뒤에 온다. 수치상으로는 CASE의 `exploit` 한 방(28)이 더 크지만,
   로그를 읽는 순서에서는 동료가 먼저다. "첫 잭인"의 주인공이 누구인지가 흐려진다.
8. **HP가 정보를 담지 않는다.** 전리품이 매 노드에서 만피로 회복시켜 엔딩은 항상 100/100이다.
   그래서 엔딩의 HP는 읽을 것이 없고, 리졸버의 `hp > 75%` 조건도 항상 참이다
   (ADR-0277 열린 질문 (c)에 이미 기록).

## 먼저 고칠 것 (추천)

1. **전투 시작 시 손패를 채운다** — 결함 1과 2를 동시에 고친다. 받은 카드가 다음 교전 첫 손패에 들어오고,
   교전마다 같은 조건에서 시작한다. 밸런스 변경이므로 `npm run balance` 로 재측정이 필요하다.
2. **미션 안에서 ICE 타입을 중복 없이 뽑는다** — 결함 3. 서사 밀도가 가장 싸게 오른다.
3. **문구 정리** — 결함 4·5·6. 밸런스 무관, 테스트로 고정 가능.

---

## 이 검증에서 실제로 확인한 것 (기계적)

- 실브라우저 · 실제 키 입력만 사용(`wetrun.state` 무기록) · `npm run story`.
- 15 스텝, 정지 0, 엔딩 `arc1_wage_slave` 도달, 타이틀 복귀, 세이브 슬롯 은퇴.
- 스크린샷: `00-jockey-select.png`, `01-run-intro.png`, `02-combat.png`, `03-loot.png`, `04-ending.png`.
- 엔딩 요약 크레딧 수정 확인: `CASE — First Jack / HP 100/100 · 2,300cr · 7 turns`.
- 소크 하네스 3런: `completed` 3, `frozen` 0.

---

# 정정 및 재측정 (2026-11-05, ADR-0278)

위 서사와 결함 목록을 그대로 두되, **틀린 것 셋을 정정**하고 **고친 것과 새로 찾은 것을 기록**한다.
아래 재측정은 트레이스 캡처를 고친 뒤(`message` 만이 아니라 `combatLog` 전체를 남긴다)
`STORY_MISSION=9 npm run story` 를 다시 돌린 결과다. 결함 7 이 애초에 **캡처 손실**이었던 이유가 여기 있다.

## 정정 — 결함 5·7·8 은 오탐이었다

| # | 원래 주장 | 실제 |
|---|---|---|
| 5 | 미션 zone `surface` 인데 `Entering mid` 는 불일치다 | **오탐.** 미션 zone(`surface`)과 **노드** zone(`mid`/`core-deep`)은 다른 축이다. 노드 zone 은 `ZONE_BY_NODE_INDEX` 가 정하고, 미션 zone 은 미션 메타다. 화면은 노드가 말하는 대로 말한다. |
| 7 | Dixie 가 전투 로그의 첫 줄을 가져간다 | **오탐.** `combatLog` 는 **최신 우선 4줄**을 HUD 에 보여준다. 트레이스가 `message`(가장 최신 한 줄)만 캡처해서, 카드 타격이 사라지고 Dixie 의 줄만 남은 것처럼 보였다. 캡처를 고치자 `Exploit → 14 dmg` 가 Dixie 앞에 그대로 있다. |
| 8 | 전리품이 매 노드에서 만피로 회복시킨다 | **부분 오탐.** 회복은 **최대 HP 의 15%** 다(`continueToMatrix`). 이 런은 96/100 이라 15% 회복(15)이 4 를 덮어 만피가 됐을 뿐이다. 다만 "엔딩 HP 가 정보를 담지 않는다"는 관찰 자체는 남는다 — 별도 측정 필요. |

## 고친 결함 (ADR-0278)

| # | 결함 | 수정 | 회귀 테스트 |
|---|---|---|---|
| 1 | 받은 카드가 런에서 한 번도 안 나온다 | 전리품 화면을 닫을 때 손패를 `handSize` 까지 채운다(`combat/hand.ts`), 보상 카드는 드로우 파일 **맨 위**에 얹는다 | `adr0278_playthrough_fixes.test.ts` |
| 2 | 손패가 전투 사이에 초기화되지 않는다 | 결함 1 과 같은 수정. 리필 지점을 **BREACH 가 아니라 전리품**에 둬서, SCAN 으로 쓴 카드는 그 전투 동안 계속 빠져 있다(ADR-0247 비용 유지) | `encounter_programs.test.ts` |
| 3 | 한 미션의 두 ICE 가 같은 타입이다 | 각 ICE 방이 등급 밴드의 **다음 슬롯**을 받는다(`seed + iceOrdinal * 7`) | `adr0278_playthrough_fixes.test.ts` |
| 4 | 자키 소개와 arc 1 인트로의 톤 충돌 | 태그라인을 `New hands. Old reflexes. The deck remembers.` 로 | `jockey_deck.test.ts` |
| 6 | 전리품 표기 불일치(`ice_shardx1`) | `${item} x${qty}` | `state_actions_programs` 메시지 |

## 이번 재측정에서 **새로** 찾은 결함

트레이스 재생에서 드러났고, 둘 다 고쳤다.

1. **전투가 상대의 이름을 말하지 않는다.** `state.ice` 는 런의 **기준 ICE**(미션이 처음 만나는 상대)라,
   보스 방도 `Combat vs ICE — Wisp`, 승리도 `ICE — Wisp defeated!` 라고 말했다 — 실제 상대는
   **wintermute**(armor 8, tier 4)였다. 로스터가 카탈로그를 보게 되면서(§고친 결함 3 과 같은 뿌리)
   이름도 로스터에서 읽게 고쳤다(`combat/roster.ts`).
2. **승패 지점이 보상을 정했다.** 마지막 ICE 를 **카드가** 잡으면 전리품·업적·진영 점수가 전부 들어왔고,
   **Dixie 가** 잡으면 크레딧만 들어왔다. 보스의 전리품(`combat_module x2` 등)과 `boss_slayer`(1,000cr)는
   카드가 막타를 친 런에만 존재했다. 이제 킬이 일어난 지점에서 적립한다(`combat/victory.ts`).
   남는 차이는 하나뿐 — ADR-0258 의 `(no COST)` 는 **막타를 친 카드**의 것이므로 동료 킬은 주장하지 않는다.

## 아직 안 고친 것 (오너 결정 필요)

**미션 기본 보상이 교전마다 지급된다.** `mission.rewards.credits + node.reward.credits` 가
**모든 교전 승리**에 더해진다. 이 런의 미션 보상은 500 인데, 두 번의 교전에서 500 이 **두 번** 들어갔다
(625 = 500 + 75 + 50, 1675 = 500 + 175 + 1000). 미션 선택 화면은 `First Jack [T1 | 500cr]` 이라고
**500 을 약속**한다 — 전리품 회복량 오탐과 같은 "화면이 약속한 것과 게임이 하는 것" 계열이다.
2026-11-02 트레이스에서도 같은 모양이 보인다(`cr=4500` → `+6100`, 두 번).

경제 변경이라 ADR-0278 범위 밖으로 두고 오너 결정으로 남긴다 (권고: 미션 보상은 **엔딩에서 한 번**,
교전 승리는 **노드 보상만**).

