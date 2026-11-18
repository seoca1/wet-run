# 시스템 설계도 — 2026-11-18

> 목적: 지금까지의 구조를 **눈으로** 보고, **비어 있는 곳**을 한 문서에서 찾는다.
> 범례: **✅ 배선됨** · **🟡 부분** · **❌ 죽음(경로·데이터 없음)**
> 모든 판정은 코드/데이터 근거를 함께 적었다.

---

## 1. 한 런의 흐름 (도면)

```
 MENU
  ├─ NEW RUN ──► JOCKEY SELECT ──► PROLOGUE(GN) ──► MISSION SELECT
  │                                                      │
  │                                          (미션 목록이 계약을 공개)
  │                                                      ▼
  │                                                 BRIEFING ──► PREP(advance)
  │                                                      │         몸 +HP/실드
  │                                                      ▼
  │   ┌───────────────── 미션 1 (계약 다리 1/3) ─────────────────┐
  │   │  MATRIX ──► ENCOUNTER ──► COMBAT ──► LOOT STOP          │
  │   │    │            │            │           │               │
  │   │  이동/우회    BREACH/BYPASS  카드 사용  카드/수리/인텔/   │
  │   │  (보스 게이트)  (60 COST)   (1장=적1페이즈) VENT/BURN/RECOVER
  │   └──────────────────────────────────────────┼──────────────┘
  │                                              ▼
  │                        디브리핑 카드 ──► 다음 작업 카드
  │                                              │
  │                                    ┌─────────┴─────────┐
  │                                    ▼                   ▼
  │                          CONTRACT PREP(advance)   다리 2/3, 3/3
  │                                    │                   │
  │                                    └─────────┬─────────┘
  │                                              ▼
  │                                         ENDING (liberation > control)
  └─ CONTINUE / CRAFT / EQUIPMENT / HALL OF DEAD / HELP / SETTINGS / FAR GRID HUB
```

**한 계약 = 3미션.** 이월: **덱 · 크레딧 · 고유** / 리셋: **HP · COST · 턴 · 보드** (`state/state.ts` `startNextLeg`)

---

## 2. 계층 도면 — 무엇이 어디로 흐르는가

```
┌─ 교전 ──────────────┐   ┌─ 미션 ───────────────┐   ┌─ 계약 ──────────────┐   ┌─ 메타(영속) ─────────┐
│ 성장 없음            │   │ 덱 +카드              │   │ 덱/크레딧/고유 이월   │   │ prep 지갑            │
│ (고정 도구)          │──►│ 크레딧 += 보상         │──►│ advance(몸) 다리마다  │──►│ Far Grid 해금        │
│                     │   │ materials → inventory │   │ HP/COST/보드 리셋     │   │ 업적 28              │
└─────────────────────┘   └───────────┬──────────┘   └─────────────────────┘   │ 완료 미션 기록        │
                                      │                                        └──────────────────────┘
                            ❌ 소비처 없음 (아래 §5)
```

---

## 3. 시스템 배선표

| 시스템 | 상태 | 근거 | 비고 |
| --- | --- | --- | --- |
| 전투(카드/ICE/보스) | ✅ | `combat_engine.ts` · `state_actions_combat.ts` | 보스 4페이즈, armor 감산 |
| SRW 케이스 | 🟡 | `attack_resolution.ts` | **기본 표 0**(ADR-0321) — `cloak` 만 |
| 실피해 표시 | ✅ | `damage_preview.ts` · `combat_grid.ts` | armor `A7` + 피해 범위 |
| 전투 후 회복 | ✅ | `victory.ts` `victoryHealAmount` | floor 50% (ADR-0319) |
| 전리품 정지 | ✅ | `loot_choice.ts` | 8슬롯 |
| 카드 보상 | ✅ | `card_reward.ts` | 3장 · tier 가중 · 고유 1/계약 |
| prep advance | ✅ | `prep.ts` | HP `[0,0,20,70,185,140]` |
| 계약/캠페인 | ✅ | `campaign.ts` | 3미션 |
| 엔딩 | ✅ | `ending_resolver.ts` | liberation > control |
| 서사(브리핑/비트) | ✅ | `event_beats.ts` · `import_briefings.py` | 33미션 |
| 메타(prep 지갑/업적/Far Grid) | ✅ | `prep_wallet.ts` · `achievements.ts` · `far_grid_gate.ts` | |
| **장비(EQUIPMENT)** | 🟡 | `equipment_store.ts` · `main.ts` | **배선됨(ADR-0322)** — 단 **획득 경로 0** |
| **크래프팅** | ❌ | `main.ts:459-461` `makeRecipesFromData({})` | **데이터 자체가 없음** |
| **인포 마켓** | ❌ | `makeInfoMarket({})` | **판매 항목 0** |
| **재료(아이템)** | ❌ | `victory.ts:92` 적립만 | **소비처 0** |
| **아이템 사용** | ❌ | `GameAction` 에 `use_item` 없음 | 소비 아이템 개념 없음 |
| **스탯(장비)** | 🟡 | `equipmentLoadout.totalStats()` | **12개 중 3개만** 읽힘 |
| **플레이어 방어 스탯** | ❌ | `player_mitigation.ts` | shield/evasion 만, **defense 미적용** |
| **세트/웻웨어** | 🟡 | `set_bonus.ts` (loadout 이 호출) · `wetware.ts` | 계산되나 **획득 경로 0** |

---

## 4. 빈 곳 — 우선순위

### ❌ P0-1. 크래프팅: 데이터가 없다
```
main.ts:459   this.recipes   = makeRecipesFromData({});   // raw["recipes"] 없음 → []
main.ts:460   this.materials = makeMaterialsFromData({}); // 정의 0
main.ts:461   this.infoMarket= makeInfoMarket({});        // 판매 0
```
`craftItem()` 은 완성돼 있지만 **레시피가 0개**라 아무것도 제작할 수 없다. `recipes.json` · `materials.json` · `sets.json` 은 **리포 어디에도 없다**(find 결과 0). 크래프팅 화면은 **빈 목록**을 그린다(`crafting_screen.ts:101`).

### ❌ P0-2. 재료: 28종이 쌓이기만 한다
```
ICE 82개가 data_fragment 를 떨군다 … 드롭 아이템 총 28종
victory.ts:92-94  materials[drop.item] += qty   → state.inventory.materials
```
그런데 **소비처가 없다**(레시피 0, 마켓 0, 장비 제작 0). 게다가:
```
main.ts:1663  this.inventory = initial.inventory;   // 런 시작 시 미션 보상으로 '덮어씀'
```
메뉴의 지갑은 **런을 마쳐도 갱신되지 않는다** → 런에서 모은 재료는 **화면 사이에서 증발**한다.

### ❌ P0-3. 장비: 얻을 수 없다
- 카탈로그에 **18종(tier 0~6)** 이 있지만, 장착 경로는 메뉴의 "첫 번째 빈 슬롯 장비"뿐 → **tier-0 기본값만**.
- 드롭 0 · 구매 0 · 제작 0. `DEFAULT_REGISTRY` 밖의 장비는 **도달 불가**.

### ❌ P1-1. 스탯: 계산되지만 읽히지 않는다
`totalStats()` 가 12개 스탯을 합산하는데, **전투가 읽는 것은 3개**:

| 스탯 | 읽히나 | 근거 |
| --- | --- | --- |
| `attackBonus` | ✅ | `state_actions_programs.ts:76` |
| `critBonusPct` | ✅ | 같은 곳 `:107` |
| `damageBonusPct` | ✅ | 같은 곳 `:118` |
| `defense` | ❌ | `equipStats.defense` 소비 0 — 플레이어 방어 단계 없음 |
| `hpBonus` · `shieldBonus` | ❌ | 소비 0 |
| `apBonus` · `apRegenBonusPct` | ❌ | 소비 0 |
| `programPower` | ❌ | 소비 0 |
| `iceResistance` | ❌ | 전투가 `defenderIceResistance: 0` 하드코딩 |
| `grantsSkillId` · `extraEffect` | ❌ | 소비 0 |

### ❌ P1-2. 아이템 사용 개념이 없다
`GameAction` 에 `use_item` 이 없고 소비 아이템도 없다. 드롭은 전부 **재료**다.

### 🟡 P2-1. 성장이 성공 경로가 아니다 (ADR-0322 측정)
이기는 플레이의 덱은 **5장 그대로**(g4 5.02) — 수리 슬롯이 성장을 먹는다.

### 🟡 P2-2. 크래프팅 고리 미확인
런 ↔ 메뉴 사이의 재료/크레딧 순환이 끊겨 있다(P0-2).

---

## 5. 아이템/경제 도면 — source → sink

```
  킬 bounty ─┐
  미션 보상 ─┼─► player.credits ──► (a) 엔딩 조건(control, >5000)  ✅
             │                     └─► (b) prep 지갑(50%)          ✅ (g1/g2 만 사용)
             └─► inventory.credits ─► ❌ 제작(레시피 0)
  킬 드롭(28종) ─► inventory.materials ─► ❌ 소비처 0
  고유(1/계약) ─► 덱                   ✅
  장비(18종) ──► ❌ 획득 경로 0 (tier-0 기본만 장착 가능)
```

**요약**: **들어오는 문은 많은데 나가는 문이 없다.** 크레딧만 두 개의 출구(엔딩·prep 지갑)가 있고, 재료·장비는 **막다른 길**이다.

---

## 6. 대응 제안 (우선순위)

| # | 작업 | 내용 | 왜 |
| --- | --- | --- | --- |
| **1** | **재료 → 장비 제작** | `recipes.json`/`materials.json` 데이터를 만들고 `craftItem` 을 화면에 연결. 드롭 28종을 **장비/프로그램 제작 재료**로 소비 | 나가는 문이 생기고 **장비 축이 살아난다**(P0-1·2·3 동시 해결) |
| **2** | **런 ↔ 메뉴 지갑 연결** | 런 종료 시 `this.inventory` 를 런의 재료/크레딧으로 갱신(지금은 덮어쓰기만) | 모은 것이 증발하지 않는다 |
| **3** | **미사용 스탯 배선** | `defense`(플레이어 피해 감소) · `hpBonus`/`shieldBonus`(최대 HP/실드) 를 실제로 적용 | 장비가 **12개 스탯**을 갖게 된다 — 장비 선택이 의미를 가짐 |
| **4** | **아이템 사용** | 소비 아이템(예: `maas_neuropozyne_dose`)에 `use_item` 액션 | 드롭에 **즉시 쓸 수 있는 것**이 생긴다 |
| **5** | **성장↔난이도 손잡이** | ADR-0322 의 측정 — floor/수리 재설계 | 성장이 성공 경로가 된다 |

> **1~3 이 서로 맞물린다**: 재료가 장비를 만들고(P0), 장비의 스탯이 실제로 전투에 닿으면(P1) 장비 축이 완성된다. 이 셋을 **한 슬라이스**로 묶는 것이 가장 효율적이다.

---

## 7. 한 줄 요약

> **전투·서사·성장의 '입구'는 잘 배선돼 있고, '출구'(크래프팅·아이템·장비 획득)가 통째로 비어 있다. 재료 28종과 장비 18종이 데이터로만 존재하고 게임에서는 막다른 길이다. 장비 스탯 12개 중 9개도 아무도 읽지 않는다.**
