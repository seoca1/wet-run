# System: Inventory & Equipment (인벤토리 · 장비)

> **상위 결정**: `../../decisions/0008-progression-system.md` (Accepted, Revised)
> **관련**: [crafting.md](./crafting.md) (제작), [progression.md](./progression.md) (메타 진행), [combat.md](./combat.md) (전투)
> **구현**: `../../prototype/src/wet_run/equipment/equipment.py`

## 목적

자키의 **8개 사이버펑크 신체 슬롯** 에 장비를 장착해 combat stats 를 변화시킴.
Pillar 4 ("The Build") 의 핵심 — 같은 자키가 다른 장비로 전혀 다른 전투 스타일.

## 8 슬롯 (EquipSlot)

| 슬롯 | 설명 | 대표 장비 |
|---|---|---|
| **DECK** | 사이버데크 (메인 컴퓨터) | Ono-Sendai 7 → Ghost Cartographer |
| **HEADWARE** | 신경 잭, 두개 임플란트 | Trodes → Kereznikov Boost |
| **EYEWARE** | 시각 증강, AR 오버레이 | Militech Eagle Eye |
| **BODYSUIT** | 피하 갑옷, 스마트 직물 | Subdermal Weave → M-31 Combat Armor |
| **GLOVES** | 손 증강, 인터페이스 플러그 | Chrome Surgical Gloves |
| **BOOTS** | 발/다리 증강 | Chameleon Boots |
| **IMPLANT** | 내부 장기 모드 | Nano-Hive |
| **TRODES** | 보조 연결, 바이오 모니터 | Stealth Trodes |

깁슨 톤 — "Trodes", "Kereznikov Boost", "Ono-Sendai", "Arasaka Onikiri" 등 고유명사 사용.

## 8 카테고리 (EquipCategory)

| 카테고리 | 의미 |
|---|---|
| CYBERNETIC | 기계-생체 하이브리드 |
| SOFTWARE | AI/에이전트 |
| BIOWARE | 유기체 기술 |
| NANOWARE | 나노 기술 |
| WETWARE | 뇌 인터페이스 |
| HARDWARE | 물리적 도구 |
| ICEBREAKER | 해킹 전용 |
| DAEMON | AI 프로그램 |

## 6 티어 (EquipTier)

| 티어 | 명칭 | 예시 |
|---|---|---|
| T0 | Baseline (시작) | Ono-Sendai 7 |
| T1 | Street | Ono-Sendai 11 Hot Rod |
| T2 | Commercial | Sakura Samurai, Subdermal Mk.II |
| T3 | Militech | Militech Centurion, M-31 |
| T4 | Corporate | Arasaka Onikiri, Kereznikov |
| T5 | Experimental | Ghost Cartographer |

## EquipStats (12 필드)

장비 한 개가 제공하는 stat 보너스:

| 필드 | 의미 |
|---|---|
| `attack_bonus` | 평타 추가 데미지 |
| `crit_bonus_pct` | 크리티컬 확률 % |
| `damage_bonus_pct` | 전체 데미지 % |
| `defense` | 평탄 데미지 감소 |
| `hp_bonus` | 최대 HP 증가 |
| `shield_bonus` | 매 턴 쉴드 회복량 |
| `ap_bonus` | AP 최대치 증가 |
| `ap_regen_bonus_pct` | AP 회복 속도 % |
| `program_power` | 스킬 데미지 증가 |
| `ice_resistance` | ICE 공격 데미지 감소 % |
| `grants_skill_id` | 새 스킬 부여 (예: `jackhammer`, `viral`, `bloodlust`) |
| `extra_effect` | 추가 효과 텍스트 |

## EquipmentLoadout (장착 중)

```python
@dataclass
class EquipmentLoadout:
    equipment: dict[EquipSlot, Equipment]
```

- `equip(item)` → 슬롯에 장착, 이전 장비 반환
- `unequip(slot)` → 슬롯에서 제거, 제거된 장비 반환
- `get(slot)` → 슬롯의 장비 조회
- `all_slots_filled()` / `empty_slots()` → 슬롯 상태 점검
- `is_complete()` → 8 슬롯 모두 채워졌는지
- `total_stats()` → 12 필드 합산 (모든 장비의 EquipStats 누적)

## PPL 통합 (combat_view.py)

전투 시작 시 `EquipmentLoadout.total_stats()` 가 호출되어 `Combatant` 의
equip_* 필드에 매핑됨 (`combat_view.py:851-902`):

```python
equip_attack_bonus → Combatant.equip_attack_bonus
equip_shield_bonus → Combatant.equip_shield_bonus
equip_program_power → Combatant.equip_program_power
... 등
```

## 업그레이드 시스템 (ADR-0015)

장비마다 `upgrade_slots: int` 와 `required_materials: dict[str, int]` 보유.

예: STREET_DECK (T1)
- upgrade_slots: 2
- required_materials: `{"ice_shard": 1, "data_fragment": 2}`

런 안에서 같은 티어의 장비를 더 좋은 등급으로 강화 (예: STREET_DECK → MILITECH_DECK).
`Equipment.is_upgradable()` 메서드로 판정.

## Set Bonus (Phase 6+)

장비에 `set_id: str | None` 필드 존재. 동일 set_id 의 장비 3개+ 장착 시 추가 보너스.
현재 15개 장비 중 set_id 있는 것 없음 — Phase 6 에서 추가.

## 기본 15장비 (Gibson 인스파이어드)

`equipment.load_default()` 가 다음 15개 등록:

| ID | 이름 | 슬롯 | 티어 |
|---|---|---|---|
| `deck_basic` | Ono-Sendai Cyberspace 7 | DECK | T0 |
| `head_basic` | Trodes (Stock) | HEADWARE | T0 |
| `deck_street` | Ono-Sendai 11 (Hot Rod) | DECK | T1 |
| `eyes_militech` | Militech Eagle Eye | EYEWARE | T1 |
| `gloves_chrome` | Chrome Surgical Gloves | GLOVES | T1 |
| `deck_corporate` | Sakura Cybermod "Samurai" | DECK | T2 |
| `bodysuit_subdermal` | Subdermal Weave Mk.II | BODYSUIT | T2 |
| `trodes_ninja` | Stealth Trodes | TRODES | T2 |
| `boots_ghost` | Chameleon Boots | BOOTS | T2 |
| `deck_militech` | Militech Centurion | DECK | T3 |
| `bodysuit_tactical` | M-31 Combat Armor | BODYSUIT | T3 |
| `implant_nanohive` | Nano-Hive | IMPLANT | T3 |
| `deck_arasaka` | Arasaka "Onikiri" | DECK | T4 |
| `head_kereznikov` | Kereznikov Boost | HEADWARE | T4 |
| `deck_ghost` | Ghost Cartographer | DECK | T5 |

깁슨 어휘: Ono-Sendai, Militech, Arasaka, Kereznikov 모두 원작 등장.

## 구현 위치

| 요소 | 파일 |
|---|---|
| Equipment / Stats / Slots | `equipment/equipment.py:1-118` |
| 15 기본 장비 | `equipment/equipment.py:124-332` |
| EquipmentRegistry | `equipment/equipment.py:340-381` |
| EquipmentLoadout | `equipment/equipment.py:389-429` |
| 전투 통합 | `engine/combat_view.py:820-903` |
| Hub 4-panel 표시 | `engine/hub.py:_draw_avatar_panel` |
| Wetware Stacking (Phase 15) | `equipment/wetware_stacking.py` + `engine/equipment_view.py:184-202` |

---

## Wetware Stacking (Phase 15)

자키가 동일 wetware ID 를 인벤토리에 다수 보유 시 누적 보너스가 적용된다. Pillar 4 (The Build) 의 *장착 도구* 표현.

### 메카닉

`equipment/wetware_stacking.py::stack_wetware(wetware_ids: list[str])` 가 보유 wetware ID 리스트를 받아 누적된 `EquipStats` 보너스를 계산한다. 같은 wetware ID 가 N 개 있으면 보너스 × N (또는 비선형 누적 곡선 — v1.1.0 follow-up).

### Equipment View 표시

`engine/equipment_view.py::_render_total_stats_panel` (line 184-202) 가 호출:

```python
# Phase 15: wetware stacking
wetware_ids = []
inventory = getattr(state, "inventory", {})
if inventory:
    from ..equipment.wetware_stacking import get_all_augments
    all_aug_ids = get_all_augments()
    wetware_ids = [k for k in inventory.keys() if k in all_aug_ids]
stacked = stack_wetware(wetware_ids)
```

장비 view 의 `Total Stats` 패널에 stacked 보너스가 12 필드 `EquipStats` 와 함께 표시된다 (예: stacked attack_bonus = +3, hp_bonus = +12).

### Pillar 정합

- **P4 (The Build)**: "장비와 도구"의 직접적 표현 — wetware N개 = 누적. 메타 진행과 *직교* (death 시 reset, in-run only).
- **P5 (The Style)**: HUD 에 `[wetware stack: +3 atk]` 짧은 한 줄로 깁슨 톤.

### 향후 확장 (v1.2.0+ backlog)

- 비선형 누적 곡선 (예: 3개 초과 시 0.5× decay)
- Wetware 별 stacking cap (예: 같은 wetware max 5개)
- Per-tier scaling (T1 wetware 1× vs T4 wetware 2.5×)

## 미래 작업 (Phase 6+)

- **Set bonus**: `set_id` 매칭으로 추가 보너스
- **Modular upgrades**: 슬롯별 개별 강화 (현재는 장비 단위)
- **Cyberpsychosis risk**: 인간성 슬라이더, T4+ 누적 시 위험
- **Hacking-specific 데크**: ICEBREAKER 카테고리 독립 메트릭