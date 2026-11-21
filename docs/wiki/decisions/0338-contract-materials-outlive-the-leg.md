# ADR-0338: 계약의 재료는 leg 사이에서 살아남는다 — 그리고 미션 보상은 주조되지 않는다

**상태**: Accepted (오너: *"위임할게. 후속 진행해줘"* — 검증 보고 P3 경제, 재료 리셋)
**날짜**: 2026-11-19
**결정자**: 사용자
**우선순위**: P1 (경제 · 진행)

## 컨텍스트 (Context)

전수 검증(2026-11-19)의 P3: 크래프팅 도달률이 **T1 58~71% · T2 이상 0.0%**, 재료는
`data_fragment 16/129 · ice_shard 18/122 · combat_module 2/69 · construct_shard 1/42` 로 SHORT.
크래프팅 probe 의 NOTE 가 원인을 지목했다 — *"materials reset every mission today
(`startNextLeg` rebuilds the inventory from the leg's reward)"*.

코드를 확인하니 **결함 2건**이었다:

1. **`startNextLeg`(state.ts) 가 `inventory.materials` 를 넘기지 않는다.** credits·deck·
   `droppedEquipment`·`reviveUsed` 는 다 carry 하는데 재료만 빠졌다. 그래서 leg2 는
   `makeInitialState(leg2)` 의 **leg2 보상만** 들고 시작한다 — leg1 이 주운 것이 통째로 사라진다.
2. **`main.ts` 의 seed 가 hoard 뿐이었다.** ADR-0323 의 계약은 "seed = hoard + 보상"이고 그 seed 를
   빼서 주조를 막는다. 그런데 `runWalletSeed = this.inventory`(hoard)라, `merge = hoard + (run − hoard)`
   = **미션 보상까지 hoard 로 주조**됐다(잭아웃 1프레임에도). ADR-0323 의 테스트가 정의한 seed 의미와
   실제 호출부가 어긋나 있었다.

## 결정 (Decision)

**재료를 계약의 다리 사이에서 보존하고, seed 를 계약 전체 보상으로 넓힌다.**

1. `startNextLeg`: 다음 leg 의 인벤토리를 **이전 leg 의 재료 + 다음 leg 보상**으로 만든다
   (`addStacks(previous.inventory.materials, fresh.inventory.materials)`). 계약 중 주운 것이 쌓인다.
2. `main.ts`: `runWalletSeed = seedRunWallet(hoard, Σ contract legs rewards)` (계약이 없으면 그 미션 보상).
   런의 지갑은 모든 leg 보상을 누적하므로, seed 도 그것을 포함해야 한다. 그러면
   `merge = hoard + (run − seed)` 가 **런이 실제로 번 것**만 hoard 에 넣는다.
3. 우연이지만 중요: **(2)가 사전 잠복 버그(미션 보상 주조)도 함께 고친다.**

## 결과 (Consequences)

- **다리 사이 재료가 산다**: leg1 의 `data_fragment 7` 이 leg2 에서 `7 + leg2 보상` 으로 남는다
  (`adr0315_campaign_chain.test.ts` ADR-0338 테스트).
- **주조 차단이 실제로 성립**: 잭아웃 1프레임 런은 `run == seed` → `merge == hoard` (ADR-0323 의 약속,
  이제 코드가 지킴).
- **밸런스 무영향**: 재료는 전투 수치에 닿지 않는다. `balance:check` **3덱 일치** · `gear:check` **일치**
  (byte-identical) — 골든이 이 변경이 전투를 건드리지 않았음을 증명한다.
- **알려진 한계**: 크래프팅 probe 는 여전히 **자체 보존-지갑 모델**로 도달률을 재므로, 이 코드 수정이
  probe 수치를 바꾸지 않는다. 실제 도달률은 **지갑 인지(wallet-aware) probe** 가 필요하다(후속).
- 검증: vitest **236/4446**(신규 ADR-0338 테스트 1) · typecheck 0 · 러틴 9/9 · 골든 byte-identical.

## Implementation Status (2026-11-19)

**Status**: ✅ Implemented (carry + seed)

**Evidence**:
- `web/src/core/state/state.ts` — `startNextLeg` 재료 carry (`addStacks`)
- `web/src/main.ts` — `runWalletSeed = seedRunWallet(hoard, Σ 계약 보상)`
- `web/tests/adr0315_campaign_chain.test.ts` — ADR-0338 경계 테스트

**Notes**: 실제 크래프팅 도달률 재측정(지갑 인지 probe)은 후속. `CONTROL_WEALTH` 처럼 수치 튜닝 대상.

## 영향 받는 항목

- `web/src/core/state/state.ts`, `web/src/main.ts`, `web/tests/adr0315_campaign_chain.test.ts`

## 관련 결정

- ADR-0323 (hoard 는 런보다 오래 산다) · ADR-0330 (hoard 지출 회계) · ADR-0331 (재료 시장) ·
  ADR-0324 (비용표) · ADR-0315 (런은 계약이다) · ADR-0337 (검증 P1)

## 변경 이력

- 2026-11-19: Accepted (P3 재료 carry + seed 주조 차단)
