# ADR-0330: 소비 아이템 — 그리고 hoard 가 삼키던 지출

**상태**: Accepted (오너 결정: *"계속"* → 핸드오프 §4-4)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P1 (경제 · 전투)

## 컨텍스트 (Context)

핸드오프 §4 의 마지막 항목: *"`use_item` — 첫 소비 아이템 후보 `maas_neuropozyne_dose`"*.
제안서 §1 은 이 재료를 "consumable candidate; HP/ICE 저항의 대가"로, §6-5 는 *"효과 수치는 harness 전까지
placeholder"* 로 남겼다.

구현하려다 **선행 결함**을 찾았다. ADR-0323 의 hoard 병합은

```
earned = max(0, run − seed)          # seed = hoard + 미션 보상
hoard  = menu + earned
```

인데, 런이 **hoard 재료를 소비**하면 `run < seed` 가 되어 `max(0, …)` 가 **지출을 지운다** —
소비 아이템이 공짜가 된다. ADR-0323 시점엔 런 중 재료를 쓰는 경로가 없어 드러나지 않았다.

## 결정 (Decision)

**⑴ hoard 병합을 재료별 `menu + (run − seed)` 로 바꾼다** ([`wallet.ts`](../../../web/src/core/state/wallet.ts)):

- 즉시 잭아웃은 여전히 아무것도 주조하지 않는다(`run == seed`).
- 런이 번 것은 그대로 더해진다.
- **런이 쓴 것은 차감된다** — 소비 아이템의 지출이 처음으로 기록된다.

**⑵ 소비 아이템을 loot stop 슬롯 10 으로 배선한다** ([`consumables.ts`](../../../web/src/core/state/consumables.ts),
`takeLootItem`, `run_screen.ts`):

- 첫 소비 아이템 **`maas_neuropozyne_dose`** → **플레이어 shield pool**(최대 HP의 25%)을 다음 전투에 부여.
- **회복이 아니다** — repair 슬롯이 HP 를 소유하고, 회복을 복제하면 결정이 아니라 중복이 된다. 흡수 pool 은
  `applyPrep` 의 "ice" 옵션과 같은 기계를 쓴다.
- 수치는 placeholder(측정 대상).

## 결과 (Consequences)

- **지출이 실제로 지출된다**: 소비 아이템이 공짜가 되지 않는다(테스트가 hoard 차감을 고정).
- **기록 기준선 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0** — bare runner 는 슬롯 10 을
  누르지 않고, hoard 병합 변경은 런이 재료를 쓸 때만 갈린다(곡선은 전투 수치만 읽는다).
- **검증**: vitest **234 files / 4430 tests**(신규 `adr0330_consumables` 8) · typecheck/lint 0 error · build OK · 게이트 7종 CLEAN.
- **남은 것**: `buy`(시장 — 화면·데이터 전무, 가격은 오너 결정 5번) · AP·스킬·효과 서브시스템 ·
  소비 아이템 효과 수치 확정(오너) · 장비 파워↔난이도 동시 설계(오너).
