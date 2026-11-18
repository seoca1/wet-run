# ADR-0329: 장비는 발견된다 — loot stop 의 salvage 슬롯

**상태**: Accepted (오너 결정: *"장비 drop 경로"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (경제 · 성장)

## 컨텍스트 (Context)

제안서는 18종 장비 각각에 `craft / drop / buy` 중 **명시된 획득 경로**를 요구했지만,
ADR-0325 는 그중 **craft 하나만** 배선했다. `recipes.json` 의 `path` 는 이미 어느 것이 드롭되는지
적어 두었다(`eyes_militech` = "craft 또는 g1/g2 drop", `deck_master` = "craft, g6 boss drop, …").

드롭은 로그라이크의 **발견** 축이다 — 제작이 보장된 경로라면, 드롭은 런이 우연히 주워 오는 것이다.

## 결정 (Decision)

**loot stop 에 salvage 슬롯(9)을 추가한다** ([`equipment_drops.ts`](../../../web/src/core/state/equipment_drops.ts),
[`state_actions_phases.ts`](../../../web/src/core/state/state_actions_phases.ts) `takeLootGear`,
[`run_screen.ts`](../../../web/src/renderer/run_screen.ts)):

- **등급 → 조각**: `EQUIPMENT_DROP_BY_GRADE` = g1 `eyes_militech` · g2 `bodysuit_subdermal` ·
  g3 `deck_militech` · g5 `deck_ghost` · g6 `deck_master`. (g4 는 없음.)
- **미션당 1회 롤**, `missionSeedOf(mission) ^ hash(id)` 로 시드 — `Math.random` 을 **소비하지 않는다**.
  그래서 전투 RNG 스트림, 즉 **기록된 모든 밸런스 곡선이 불변**이다(`offeredCardIds` 와 같은 패턴).
- **`EQUIPMENT_DROP_CHANCE = 0.4`** (placeholder, 오너 튜닝 대상).
- 슬롯을 누르면 `state.droppedEquipment` 에 쌓이고, **런이 끝날 때** `main.ts` 가 `ownedEquipment` 로
  병합한다(재료가 hoard 로 병합되는 방식과 동일). 카드 슬롯은 소비하지 않는다(repair/vent 와 같은 "구매").

## 결과 (Consequences)

- **측정 (현행 53 미션 카탈로그)**: `g1 3/4 · g2 8/16 · g3 3/11 · g4 0/10 · g5 4/9 · g6 1/3` = **19/53 (36%)**.
  p=0.4 에서 **모든 등급 경로가 살아난다**(p≤0.3 에서는 g6 0/3 로 `deck_master` 경로가 죽었다).
- **기록 기준선 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0** (bare runner 는 슬롯을 누르지 않고, 롤은 별도 시드).
- **검증**: vitest **233 files / 4422 tests**(신규 `adr0329_equipment_drops` 6) · typecheck/lint 0 error · build OK · 게이트 7종 CLEAN.
- **알려진 한계**: 드롭은 미션 시드에 묶여 등급별 표본이 작다(미션 수가 적은 등급은 편차가 크다).
  `EQUIPMENT_DROP_CHANCE` 는 오너 튜닝 값이며, `g6` 는 3 미션뿐이라 p 를 낮추면 다시 죽는다.
- **남은 것**: `buy`(시장 — 오너 결정 5번) · AP·스킬·효과 서브시스템 · `use_item`(hoard 병합 수정 필요) ·
  장비 파워↔난이도 동시 설계(오너).
