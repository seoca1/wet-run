# System: Crafting (제작 — 재료 & 조합)

> **상위 결정**: `../../decisions/0015-crafting-system.md` (Accepted, Draft)
> **관련**: ADR-0008 (Progression), ADR-0010 (i18n), ADR-0013 (Events), ADR-0014 (Data Salvage)

## 목적

전투 승리 / 이벤트 / 매트릭스 탐색으로 얻은 *가상 소프트웨어 재료*를 조합하여 최종 *아이템 / program / construct*를 제작. Pillar 4 (The Build)의 가장 직접적인 표현.

> **깁슨 어휘**: "ICE Shard", "ROM Echo", "Biosoft Agent" — 원작의 *software/material* 어휘 차용.

## 3-Tier 구조

```
Tier 0 — Raw Material (5종)
  ↓ (2-3개 조합)
Tier 1 — Component (4종)
  ↓ (+ tier upgrade)
Tier 2 — Final Product (Program / Item / Construct)
```

### Tier 0: 원료 (Raw Materials)

| ID | 이름 | 희귀도 | 드롭 소스 |
| --- | --- | --- | --- |
| `ice_shard` | ICE Shard | common | combat.ice.standard, combat.ice.watchdog |
| `data_fragment` | Data Fragment | common | combat, data nodes, story events |
| `rom_echo` | ROM Echo | uncommon | construct nodes, story events (Dixie, Loa) |
| `wetware_chip` | Wetware Chip | rare | story events, rare drops |
| `biosoft_agent` | Biosoft Agent | rare | construct encounters, high-tier events |

**드롭 확률** (전투 승리 시):
- ICE 격파: `ice_shard` 60%, `data_fragment` 30%, 기타 10%
- Data node 추출: `data_fragment` 70%, `data_crystal` 20%, 기타 10%
- Construct 조우: `rom_echo` 50%, `biosoft_agent` 30%, 기타 20%

### Tier 1: 부품 (Components)

2-3개 원료 조합. 4종.

| ID | 이름 | 레시피 |
| --- | --- | --- |
| `combat_module` | Combat Module | `ice_shard` × 2 + `data_fragment` × 1 |
| `construct_shard` | Construct Shard | `rom_echo` × 1 + `biosoft_agent` × 1 |
| `wetware_data` | Wetware Data | `data_fragment` × 2 + `wetware_chip` × 1 |
| `ice_construct` | ICE Construct | `ice_shard` × 3 + `rom_echo` × 1 |

### Tier 2: 완성품 (Final Products)

**Programs** (메뉴 스킬):
```
combat_module × 1 + upgrade(T1) → T1 Program (Wisp-tier)
combat_module × 2 + upgrade(T2) → T2 Program (Hammer-tier)
combat_module × 3 + upgrade(T3) → T3 Program (Goliath-tier)
combat_module × 4 + upgrade(T4) → T4 Program
combat_module × 5 + upgrade(T5) → T5 Program (Kraken-tier)
```

**Items** (장비):
```
wetware_data × 1 + upgrade(T1) → T1 Item (basic)
wetware_data × 2 + upgrade(T2) → T2 Item
... (T1~T5)
```

**Constructs** (메타 진행):
```
construct_shard × 3 → Construct Fragment (런 내)
construct_shard × 5 (across runs) → Construct unlock (메타)
```

**Special Programs** (Black ICE-class):
```
ice_construct + upgrade(T3) → Black ICE-tier program (T3~T4)
```

## 대체 경로: Info Market (CRED 구매)

ADR-0014의 CRED 사용처. 픽서 construct의 *Info Market* (Hub에 표시).

- **가격표** (티어에 비례):
  - T1: 100 CRED
  - T2: 300 CRED
  - T3: 800 CRED
  - T4: 2000 CRED
  - T5: 5000 CRED
- **CRED 드롭**: combat, data nodes, story events
- **조합 vs 구매**:
  - 조합 = 직접 제작, 보상은 더 좋음 (예: T5 program 자체는 Kraken)
  - 구매 = 즉시, T4까지만 가능 (T5는 *조합만*)
  - T5 program (Kraken)은 *crafting only* — Market에 없음

## 데이터 구조

### `data/crafting/materials.json`

```json
{
  "ice_shard": {
    "id": "ice_shard",
    "name": "ICE Shard",
    "tier": 0,
    "category": "raw",
    "rarity": "common",
    "description": "Residual data from a defeated ICE. Glitches when held.",
    "drop_sources": ["combat.ice.standard", "combat.ice.watchdog"]
  },
  "combat_module": {
    "id": "combat_module",
    "name": "Combat Module",
    "tier": 1,
    "category": "component",
    "description": "Stabilized combat data. Used to craft programs.",
    "recipe": {
      "ice_shard": 2,
      "data_fragment": 1
    }
  }
}
```

### `data/crafting/recipes.json`

```json
{
  "t1_program": {
    "id": "t1_program",
    "name": "T1 Program",
    "tier": 2,
    "category": "program",
    "recipe": {
      "combat_module": 1,
      "upgrade_t1": 1
    },
    "result_tier": 1,
    "examples": ["wisp", "shield"]
  },
  "kraken": {
    "id": "kraken",
    "name": "Kraken",
    "tier": 2,
    "category": "program",
    "tier_level": 5,
    "recipe": {
      "combat_module": 5,
      "upgrade_t5": 1
    },
    "crafting_only": true
  }
}
```

### `data/crafting/market.json`

```json
{
  "t1_program": {
    "price": 100,
    "tier_level": 1,
    "examples": ["wisp", "shield"]
  },
  "t4_program": {
    "price": 2000,
    "tier_level": 4,
    "examples": ["goliath", "wardrone"]
  },
  "t5_program": null
}
```

## Crafting 흐름

```
[Hub: Crafting 메뉴]
  ↓
[원료 보유 확인]
  ↓
[레시피 선택]
  ↓
[재료 충분?]
  | Yes ↓          No ↓
  ↓                 [부족 메시지]
[재료 차감]         [Info Market으로?]
  ↓
[부품 생성] ─────────┐
  ↓                 │
[부품 + upgrade]     │
  ↓                 │
[완성품 생성]        │
  ↓                 │
[Inventory 추가] ────┘
  ↓
[Hub 복귀]
```

## 사망 시 재료 손실 정책 (Pillar 3)

**선택안** (사용자 결정 필요):
- **Option A**: 자키 사망 = 보유 재료 *전부* 손실. Pillar 3 극대화.
- **Option B**: 자키 사망 = 재료의 *50%* 손실 (랜덤). Pillar 3 일부 완화.
- **Option C**: 자키 사망 = 재료 *유지*, *완성품*만 손실. Pillar 3 약화.

**기본값 (Phase 6 결정)**: Option A (전부 손실) — 깁슨 톤, Pillar 3 극대화.

## Pillar 정합

- **P1 (The Run)**: 한 런 = 재료 수집 + 조합 + 구매. 무게 유지.
- **P2 (The Matrix)**: 재료는 매트릭스 안의 데이터. Pillar 2 정합.
- **P3 (The Flatline)**: 자키 사망 = 수집한 재료 손실 (Pillar 3 유지).
- **P4 (The Build)**: *가장 직접적인* Pillar 4 표현. unlock + 조합 + 구매.
- **P5 (The Style)**: ICE Shard, ROM Echo, Biosoft — 깁슨 어휘.

## 구현 가이드 (Phase 6+)

### `crafting/materials.py`

```python
@dataclass(frozen=True, slots=True)
class Material:
    id: str
    name: str
    tier: int  # 0, 1, 2
    category: str  # "raw", "component", "final"
    rarity: str
    description: str
    recipe: dict[str, int] | None = None  # for components

class MaterialRegistry:
    def __init__(self, materials: dict[str, Material]): ...
    def get(self, material_id: str) -> Material | None: ...
    @classmethod
    def load(cls, path: Path) -> MaterialRegistry: ...
```

### `crafting/recipes.py`

```python
@dataclass(frozen=True, slots=True)
class Recipe:
    id: str
    name: str
    tier: int
    category: str  # "program", "item", "construct"
    inputs: dict[str, int]  # material_id -> count
    output_tier: int | None  # for programs/items
    crafting_only: bool = False

class RecipeBook:
    def __init__(self, recipes: dict[str, Recipe]): ...
    def can_craft(self, inventory: dict[str, int], recipe_id: str) -> bool: ...
    def craft(self, inventory: dict[str, int], recipe_id: str) -> dict[str, int]:
        """Return new inventory with materials consumed and item added."""
```

### `crafting/market.py`

```python
@dataclass(frozen=True, slots=True)
class MarketItem:
    item_id: str
    price: int
    tier: int
    available: bool  # T5 = False (crafting only)

class InfoMarket:
    def __init__(self, items: dict[str, MarketItem]): ...
    def can_purchase(self, credits: int, item_id: str) -> bool: ...
    def purchase(self, credits: int, item_id: str) -> int:
        """Return new credits after purchase."""
```

## Phase 범위

### Phase 5 (현재)

- **데이터만**: JSON 파일 + ADR
- **UI 없음**
- **구현 없음**

### Phase 6+

- Crafting UI (Hub)
- Info Market UI (Hub)
- 전투 승리 시 드롭 표시 (matrix_view)
- 사망 시 재료 손실 정책 구현
- 조합 자동화 (recipes.json 기반)
- 구매/인벤토리

## 향후 결정

- 사망 시 재료 손실 정책 (Option A/B/C)
- CRED 드롭 확률 / 양
- 조합 비용 (시간 / AP / 픽서 수수료?)
- 레시피 발견 (일부 숨김? 또는 전부 표시?)
- Info Market 가격 변동 (시간 / faction 호감도)
- Tier upgrade 토큰 드롭처 (보상? 구매? 이벤트?)
- Biosoft Agent 추가 시나리오 (Phase 6+)
- Construct unlock 정책 (5개 across runs? 또는 unlock 트리?)

## 관련 문서

- `decisions/0015-crafting-system.md` — ADR
- `decisions/0008-progression-system.md` — Item Tier
- `decisions/0014-data-salvage.md` — CRED / Data Salvage
- `decisions/0013-story-events.md` — 이벤트 보상
- `design/systems/combat.md` — 전투 (드롭처)
- `design/systems/hacking.md` — 매트릭스 (드롭처)
- `testcases/systems/crafting.md` — TC-CRAFT 시나리오
