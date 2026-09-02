# ADR-0015: Material & Crafting System (재료 & 제작)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0008 (Progression), ADR-0010 (i18n), ADR-0013 (Events), ADR-0014 (Data Salvage)

## 컨텍스트

사용자 결정 (2026-06-18):
> "전투 승리의 보상으로 아이템 또는 재료 수집 요소를 넣고 싶어. 가상의 소프트웨어 재료들을 단계별로 조합하는 구조를 만들고 최종 완성품이 아이템이나 스킬을 구성하거나 구입하거나 획득하는 요소로 설계해줘."

요구:
- 전투 승리 보상에 *재료* 추가
- 단계별 조합 (Tier 0 → Tier 1 → Tier 2)
- 최종 완성품: 아이템, 스킬 (program), 또는 구매/획득
- 깁슨 톤의 *가상 소프트웨어 재료*

## 고려한 옵션

### Option 1: 4-tier 시스템 (원료 → 정제 → 부품 → 완성) — **기각**

4 단계 (Raw → Refined → Component → Final). 깊지만 정제 단계가 자키에게 *지루*할 수 있음.

### Option 2: 3-tier 시스템 (원료 → 부품 → 완성) — **선택**

3 단계 (Raw → Component → Final). 사용자 선택 (2026-06-18).

### Option 3: 2-tier 시스템 (재료 → 완성) — **기각**

너무 단순. 조합 깊이 부족. Pillar 4 (The Build) 약화.

## 사용자 결정

[x] **Option 2: 3-tier 시스템** (2026-06-18)
[x] **5종 원료 (ice_shard, data_fragment, rom_echo, wetware_chip, biosoft_agent)** (2026-06-18)

## 결정

### 3-Tier 구조

```
Tier 0 — Raw Material (5종)
  ↓ (2-3개 조합)
Tier 1 — Component (4종)
  ↓ (+ tier upgrade)
Tier 2 — Final Product (Program / Item / Construct)
```

### Tier 0: 원료 (Raw Materials)

전투 / 이벤트에서 드롭. 5종, 깁슨 어휘.

| ID | 이름 | 설명 | 드롭 소스 | 희귀도 |
| --- | --- | --- | --- | --- |
| `ice_shard` | ICE Shard | 격파된 ICE의 잔여 데이터. 손에 들면 글리치함. | combat.ice.standard, combat.ice.watchdog | common |
| `data_fragment` | Data Fragment | 추출한 데이터의 잔해. 부분적으로 손상됨. | combat, data nodes, story events | common |
| `rom_echo` | ROM Echo | construct의 기억 조각. 들으면 목소리가 들림. | construct nodes, story events (Dixie, Loa) | uncommon |
| `wetware_chip` | Wetware Chip | 바이오-소프트웨어 부품. 신경과 직접 연결. | story events, rare drops | rare |
| `biosoft_agent` | Biosoft Agent | 살아있는 소프트웨어. 유기적 코드. | construct encounters, high-tier events | rare |

### Tier 1: 부품 (Components)

2-3개 원료 조합. 4종.

| ID | 이름 | 레시피 | 용도 |
| --- | --- | --- | --- |
| `combat_module` | Combat Module | `ice_shard` × 2 + `data_fragment` × 1 | program base |
| `construct_shard` | Construct Shard | `rom_echo` × 1 + `biosoft_agent` × 1 | construct fragment base |
| `wetware_data` | Wetware Data | `data_fragment` × 2 + `wetware_chip` × 1 | item base |
| `ice_construct` | ICE Construct | `ice_shard` × 3 + `rom_echo` × 1 | Black ICE-class program |

### Tier 2: 완성품 (Final Products)

부품 + tier upgrade. 3가지 카테고리.

**Programs** (메뉴 스킬, ADR-0003):
```
combat_module × 1 + upgrade(T1) → T1 Program (Wisp-tier)
combat_module × 2 + upgrade(T2) → T2 Program (Hammer-tier)
combat_module × 3 + upgrade(T3) → T3 Program (Goliath-tier)
combat_module × 4 + upgrade(T4) → T4 Program
combat_module × 5 + upgrade(T5) → T5 Program (Kraken-tier)
```

**Items** (장비, ADR-0008):
```
wetware_data × 1 + upgrade(T1) → T1 Item (basic)
wetware_data × 2 + upgrade(T2) → T2 Item
... (T1~T5)
```

**Constructs** (메타 진행, ADR-0006):
```
construct_shard × 3 → Construct Fragment (런 내)
construct_shard × 5 (across runs) → Construct unlock (메타)
```

**Special Programs** (Black ICE-class, ADR-0012):
```
ice_construct + upgrade(T3) → Black ICE-tier program (T3~T4)
```

### 대체 경로: Info Market (CRED 구매)

`ADR-0014 (Data Salvage)`의 CRED 사용처. 픽서 construct의 *Info Market* (Hub에 표시).

- CRED + 가격 → 즉시 아이템 / program / 정보 구매
- 가격은 티어에 비례: T1 = 100, T2 = 300, T3 = 800, T4 = 2000, T5 = 5000
- CRED 드롭: combat, data nodes, story events
- *조합*과 *구매*는 *상호 보완* — 한쪽이 다른 쪽을 대체하지 않음

## 결과 (Consequences)

### Pillar 정합

- **P1 (The Run)**: 한 런 = 재료 수집 + 조합 + 구매. 무게 유지.
- **P2 (The Matrix)**: 재료는 매트릭스 안의 데이터. Pillar 2 정합.
- **P3 (The Flatline)**: 자키 사망 = 수집한 재료 일부 손실 (Pillar 3 유지, *전부는 아님*).
- **P4 (The Build)**: *가장 직접적인* Pillar 4 표현. unlock + 조합 + 구매.
- **P5 (The Style)**: ICE Shard, ROM Echo, Biosoft — 깁슨 어휘.

### 데이터 주도 (ADR-0010)

모든 재료 / 레시피는 JSON:
- `data/crafting/materials.json` — 원료 + 부품 정의
- `data/crafting/recipes.json` — 조합 레시피
- `data/crafting/upgrades.json` — tier upgrade 정의
- `data/crafting/market.json` — Info Market 가격표

### 기존 ADR 영향

- **ADR-0008 (Progression)**: Tier 시스템 강화. 재료 → 부품 → 완성품 = 새로운 진행 경로.
- **ADR-0014 (Data Salvage)**: FRAG → 재료로 구체화. CRED → Info Market 구매처.
- **ADR-0013 (Events)**: 이벤트 보상 = 재료 (rom_echo, wetware_chip, biosoft_agent).
- **ADR-0006 (Run structure)**: 사망 시 재료 손실 정책 (Pillar 3) — 결정 필요.

### 디자인 영향

- **`design/systems/crafting.md`** (신규) — 제작 시스템 명세
- **`design/systems/economy.md`** (향후) — CRED / Info Market
- **`design/systems/inventory.md`** (향후) — 인벤토리 시스템
- **`testcases/systems/crafting.md`** (신규) — TC-CRAFT-001~010

### 구현 영향 (Phase 6+)

- `crafting/materials.py` — `Material`, `MaterialRegistry`
- `crafting/recipes.py` — `Recipe`, `RecipeBook`, `craft(player, recipe_id)`
- `crafting/inventory.py` — `Inventory` (런 내 재료 보유)
- `crafting/market.py` — `InfoMarket`, `purchase(player, item_id)`
- `engine/hub.py` 확장 — Hub에 Crafting / Info Market 메뉴
- `engine/matrix_view.py` 확장 — 전투 승리 시 드롭 표시

### Phase 5 범위

- **데이터만**: JSON 파일 + ADR
- **UI 없음**: Crafting/Market 화면은 Phase 6+

### Phase 6+ 범위

- Crafting UI (Hub)
- Info Market UI (Hub)
- 전투 승리 시 드롭 표시
- 사망 시 재료 손실 정책
- 조합 자동화 (recipes.json 기반)
- 구매/인벤토리

### 향후 결정

- 사망 시 재료 손실 정책 (전부? 일부? 랜덤?)
- CRED 드롭 확률 / 양
- 조합 비용 (시간 / AP / 픽서 수수료?)
- 레시피 발견 (일부 숨김? 또는 전부 표시?)
- Info Market 가격 변동 (시간 / faction 호감도)
- Tier upgrade 토큰 (드롭? 구매? 보상?)

## 영향 받는 항목

- `design/systems/crafting.md` (신규)
- `design/GDD.md` (decided + core systems)
- `decisions/0008-progression-system.md` (Tier 시스템 강화)
- `decisions/0013-story-events.md` (이벤트 보상 = 재료)
- `decisions/0014-data-salvage.md` (CRED → Market)
- `testcases/systems/crafting.md` (신규)
- `data/crafting/*.json` (신규)

## 관련 결정

- ADR-0008 (Accepted, Revised) — Item Tier
- ADR-0010 (Accepted) — i18n / 데이터 주도
- ADR-0013 (Accepted) — Story Events
- ADR-0014 (Accepted) — Data Salvage

## 변경 이력

- 2026-06-18: Draft 작성
- 2026-06-18: 사용자 결정 (Option 2: 3-tier, 5종 원료)

### Auto-conversion Confirmation (2026-08-05)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `crafting/` 패키지 2 .py 모듈 + `data/crafting/{materials,recipes}.json` (845B). 3-tier 재료 시스템 (5 raw → 4 components → final) — ADR-0015 설계와 일치. Info Market 통합 (`engine/hub.py` 4-패널).

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
