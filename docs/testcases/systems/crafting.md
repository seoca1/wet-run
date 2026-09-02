# TC-CRAFT: Crafting (재료 & 조합)

> **관련**: `../../decisions/0015-crafting-system.md`, `../../design/systems/crafting.md`
> **관련 design**: `../../design/systems/combat.md` (드롭), `../../design/systems/hacking.md` (드롭)

Tier 0 → Tier 1 → Tier 2 조합 흐름에 대한 시나리오.

## TC-CRAFT-001: 원료 드롭 (P0, Active)

**Given**: 자키가 ICE 격파
**When**: Data Salvage 메뉴 (또는 전투 종료)
**Then**: `ice_shard` 드롭 (60% 확률), 또는 `data_fragment` (30%), 또는 미드롭 (10%)

## TC-CRAFT-002: Combat Module 조합 (P0, Active)

**Given**: 인벤토리에 `ice_shard` × 2, `data_fragment` × 1
**When**: Combat Module 레시피 선택
**Then**: `combat_module` × 1 생성
**Then**: 인벤토리에서 `ice_shard` × 2, `data_fragment` × 1 차감
**Then**: `combat_module` × 1 추가

## TC-CRAFT-003: 부족한 재료 (P0, Active)

**Given**: 인벤토리에 `ice_shard` × 1, `data_fragment` × 0
**When**: Combat Module 레시피 선택
**Then**: 조합 실패, "insufficient materials" 메시지
**Then**: 인벤토리 변화 없음

## TC-CRAFT-004: T1 Program 제작 (P0, Active)

**Given**: 인벤토리에 `combat_module` × 1, `upgrade_t1` × 1
**When**: T1 Program 레시피 선택
**Then**: T1 program 생성 (예: Wisp)
**Then**: 인벤토리에서 `combat_module` × 1, `upgrade_t1` × 1 차감
**Then**: program 슬롯에 `·W·` 표시 (T1)

## TC-CRAFT-005: T5 Program (Kraken) (P1, Active)

**Given**: 인벤토리에 `combat_module` × 5, `upgrade_t5` × 1
**When**: Kraken 레시피 선택
**Then**: Kraken (T5) 생성
**Then**: 인벤토리에서 `combat_module` × 5, `upgrade_t5` × 1 차감
**Then**: program 슬롯에 `★K★` 표시 (T5)

## TC-CRAFT-006: Construct Shard 조합 (P1, Active)

**Given**: 인벤토리에 `rom_echo` × 1, `biosoft_agent` × 1
**When**: Construct Shard 레시피 선택
**Then**: `construct_shard` × 1 생성
**Then**: 인벤토리에서 원료 차감

## TC-CRAFT-007: Construct Fragment (런 내) (P1, Active)

**Given**: 인벤토리에 `construct_shard` × 3
**When**: Construct Fragment 레시피 선택
**Then**: `construct_fragment` × 1 생성
**Then**: 인벤토리에서 `construct_shard` × 3 차감

## TC-CRAFT-008: Info Market — T1 Program 구매 (P1, Active)

**Given**: CRED 200 보유
**When**: Info Market에서 Wisp (T1, 가격 100) 구매
**Then**: CRED 100 차감
**Then**: Wisp program 획득

## TC-CRAFT-009: Info Market — 구매 불가 (P1, Active)

**Given**: CRED 50 보유
**When**: T1 program (가격 100) 구매 시도
**Then**: "insufficient credits" 메시지
**Then**: 구매 실패, CRED 변화 없음

## TC-CRAFT-010: Info Market — T5 Program (P1, Active)

**Given**: T5 program (Kraken) 구매 시도
**When**: Info Market 메뉴
**Then**: "T5 available by crafting only" 메시지
**Then**: 구매 불가 (조합으로만 획득)

## TC-CRAFT-011: 사망 시 재료 손실 (P0, Active) — *Option A 기본값*

**Given**: 자키가 인벤토리에 `ice_shard` × 5, `data_fragment` × 3, `combat_module` × 1 보유
**When**: 자키 사망 (HP 0)
**Then**: 인벤토리 *전부* 손실 (Option A)
**Then**: 메타 진행 = unlock만 유지 (Pillar 3 + 4)

## TC-CRAFT-012: 자키 등급 + 재료 (P2, Active)

**Given**: 5-up 자키 (T5 deck, 등급 unlock 모두)
**When**: T1 program Wisp 제작
**Then**: 조합 가능 (자키가 *낮은* 등급 program 제작 가능)
**Then**: T5 program (Kraken)은 *등급 무관* (Pillar 1: 동일 시작점에서 강해지지 않음)

## Phase 6+ 자동화 (예정)

- `tests/unit/test_crafting_materials.py` — Material 데이터 클래스
- `tests/unit/test_crafting_recipes.py` — Recipe / RecipeBook (조합 가능 여부, 차감)
- `tests/unit/test_crafting_market.py` — Info Market (구매 가능 여부, 차감)
- `tests/integration/test_crafting_flow.py` — 드롭 → 조합 → 완성 흐름
- 회귀 테스트: 매 crafting 시스템 변경 시
