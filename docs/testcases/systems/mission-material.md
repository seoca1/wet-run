# TC-MISMAT: Mission-Material Integration (미션-재료 통합)

> **관련**: `../../decisions/0017-mission-material-integration.md`, `../../design/systems/missions.md`
> **관련 design**: `../../design/systems/crafting.md`, `../../design/systems/avatar.md`

미션과 재료의 연계, Hub 메뉴, Recipe 트리 뷰 시나리오.

## TC-MISMAT-001: collect_material 미션 (P0, Active)

**Given**: 미션 "Ice Run" — `collect_material: ice_shard × 5`
**When**: 자키가 ICE 격파 → ice_shard +1 드롭 (× 5회)
**Then**: 미션 진행 [▓▓▓▓▓] 5/5
**Then**: 미션 완료, Hub 복귀, 보상 credits 500 + data_fragment × 2

## TC-MISMAT-002: deliver_material 미션 (P0, Active)

**Given**: 미션 "Delivery to Finn" — `deliver_material: data_fragment × 3`
**When**: 자키가 data_fragment × 3 보유
**Then**: Hub의 "Deliver" 버튼 활성
**When**: 픽서에게 전달
**Then**: data_fragment × 3 차감
**Then**: 보상 credits 800 + upgrade_t1 × 1

## TC-MISMAT-003: craft_item 미션 (P0, Active)

**Given**: 미션 "Craft Job" — `craft_item: T1 Program 1개`
**When**: 자키가 Hub에서 Crafting → T1 Program 레시피
**Then**: combat_module × 1 + upgrade_t1 × 1 차감
**Then**: Wisp (T1) 생성
**Then**: 미션 완료, 보상 credits 1000 + upgrade_t2 × 1

## TC-MISMAT-004: Secondary objective (P1, Active)

**Given**: 미션 "First Jack" — primary extract_data + secondary defeat ICE × 1
**When**: ICE 격파
**Then**: primary 진행 없음, secondary 진행 1/1 ✓
**Then**: secondary 완료는 *보상 없이* primary만 완료 시 미션 종료

## TC-MISMAT-005: 미션 진행도 HUD (P0, Active)

**Given**: 미션 "Ice Run" 진행 중, ice_shard 3/5
**When**: Matrix 화면 HUD 표시
**Then**: `[▓▓▓░░] 3/5` 게이지 표시
**Then**: 충족 시 `[▓▓▓▓▓] 5/5 ✓`

## TC-MISMAT-006: Visual Hub — 4 Panels (P0, Active)

**Given**: 자키가 Hub 입장
**When**: Hub 화면 렌더링
**Then**: Panel 1 (Avatar) 표시
**Then**: Panel 2 (Materials) — 도형적 게이지
**Then**: Panel 3 (Recipes) — T1~T5 트리, READY ✓ 표시
**Then**: Panel 4 (Job Board + Market)

## TC-MISMAT-007: Recipe Tree View — Kraken (P0, Active)

**Given**: 자키가 Crafting → "Kraken" 선택
**When**: 트리 뷰 렌더링
**Then**: Kraken ★K★ at top
**Then**: 5× combat_module + 1× upgrade_t5 표시
**Then**: combat_module의 레시피 표시 (2× ice_shard + 1× data_fragment)
**Then**: 각 노드에 *have/need* 게이지 + READY ✓

## TC-MISMAT-008: READY ✓ 표시 (P0, Active)

**Given**: 자키가 combat_module × 5, upgrade_t5 × 1 보유
**When**: Kraken 트리 뷰
**Then**: 모든 노드 "READY ✓"
**Then**: Craft 버튼 활성

## TC-MISMAT-009: 부족한 재료 — not READY (P0, Active)

**Given**: 자키가 combat_module × 2, upgrade_t5 × 1 (combat_module 부족)
**When**: Kraken 트리 뷰
**Then**: "need 3× combat_module" 표시
**Then**: Craft 버튼 비활성

## TC-MISMAT-010: Material drop 시각화 (P0, Active)

**Given**: 자키가 ICE 격파, ice_shard × 1 + data_fragment × 1 드롭
**When**: Data Salvage 메뉴 표시
**Then**: Drop 섹션에 `ICE Shard +1 [▓▓▓░░] 3/5` 표시
**Then**: `Data Fragment +1 [▓░░░░] 1/4` 표시
**Then**: HEAL / SKIP 메뉴

## TC-MISMAT-011: Mission Complete 보상 (P0, Active)

**Given**: 미션 "Ice Run" 완료
**When**: Hub 복귀
**Then**: "MISSION COMPLETE" 화면 표시
**Then**: 보상 표시: credits +500, data_fragment +2
**Then**: 업데이트된 재료 게이지
**Then**: Grade progress: 1-up (1/3 missions)

## TC-MISMAT-012: 미션 unlock (Phase 6+) (P2, Active)

**Given**: 자키가 Arc 1 미션 1개 완료
**When**: Hub Job Board 표시
**Then**: 다음 미션 (Arc 1 미션 2) unlock
**Then**: locked 미션은 "🔒 complete previous" 표시

## Phase 6+ 자동화 (예정)

- `tests/unit/test_mission_objective.py` — Objective / 진행 추적
- `tests/unit/test_hub_layout.py` — 4-패널 Hub 레이아웃
- `tests/unit/test_recipe_tree.py` — Recipe 트리 렌더링
- `tests/integration/test_mission_material_flow.py` — 미션 ↔ 재료 흐름
- 회귀 테스트: 매 미션/재료 시스템 변경 시
