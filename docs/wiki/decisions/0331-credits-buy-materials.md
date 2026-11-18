# ADR-0331: 크레딧은 재료를 산다 — loot stop 의 시장

**상태**: Accepted (오너 결정: *"재료 구매"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P1 (경제)

## 컨텍스트 (Context)

크레딧에는 **소비처가 없었다**. 런의 `state.player.credits` 는 킬 보상으로 쌓이지만, 읽는 곳은
엔딩 리졸버(`control` 게이트)뿐이었다 — 돈이 할 수 있는 일이 "엔딩 자격" 하나였다.
반대로 재료는 성장 통화인데 **드롭으로만** 얻어졌다.

그리고 시장은 **화면도 데이터도 호출자도 없었다**(`purchaseItem` 호출자 0, `makeInfoMarket({})` 빈 registry).
배선하려다 위치 문제가 나왔다: **ADR-0323 은 credits 를 메뉴 지갑에 합치지 않는다**(런 중 `inventory.credits` 에
들어오는 것이 없어서) — 그래서 **메뉴 화면의 시장은 항상 무일푼**이 된다. 돈이 실제로 있는 곳은 **런**이다.

## 결정 (Decision)

**loot stop 에 시장 슬롯(11)을 추가한다** ([`material_market.ts`](../../../web/src/core/state/material_market.ts),
`takeLootBuy`, `run_screen.ts`):

- **등급 밴드별 재료 offer**: g1–g2 `data_fragment ×10 = 300cr` · g3–g4 `ice_shard ×10 = 300cr` ·
  g5–g6 `combat_module ×2 = 700cr`.
- **런의 크레딧으로 산다**(`state.player.credits`) — 런이 번 현상금이 곧 구매력이다.
- **구매는 카드를 소비하지 않는다**(repair/vent/gear/use 와 같은 "구매").
- **반복 가능** — 지갑이 허락하는 한. 가격이 곧 한도다(제안서의 "leg당 3개" 대신).
- 가격은 **측정 수입 스케일**(g3 런 ≈ 3,300cr)에 맞춘 placeholder.

## 결과 (Consequences)

- **크레딧이 처음으로 게임플레이에 닿는다**: 현상금 → 재료 → 제작 → 장비. 루프가 닫힌다.
- **기록 기준선 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0** — bare runner 는 슬롯 11 을
  누르지 않는다(정책 무변경).
- **검증**: vitest **235 files / 4436 tests**(신규 `adr0331_material_market` 6) · typecheck/lint 0 error · build OK · 게이트 7종 CLEAN.
- **알려진 한계**: 슬롯이 11개가 되면서 **80열 footer 힌트가 짧은 형식(`4-11 options`)으로 넘친다** —
  개별 슬롯 이름은 offer 라인(grid)이 담당한다. 힌트 압축은 별도 슬라이스.
- **남은 것**: AP·스킬·효과 서브시스템 · `extraEffect` resolver · 시장 가격 확정(오너) ·
  장비 파워↔난이도 동시 설계(오너).
