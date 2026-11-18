# ADR-0325: 장비는 소유된다 — 크래프팅이 배선된다

**상태**: Accepted (오너 결정: *"커밋 + 데이터 파일·화면 배선"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (경제 · 성장)

## 컨텍스트 (Context)

[`system-map-2026-11-18.md`](../../design/system-map-2026-11-18.md) 의 빈 출구: **장비 18종의 획득 경로가 0**이었다.
데이터는 다 있었지만 서로 연결이 없었다.

- **크래프팅 화면이 빈 registry를 읽었다** — `main.ts` 가 `makeRecipesFromData({})` / `makeMaterialsFromData({})`
  (Python 프로토타입의 스텁)를 호출해 **레시피 0종**을 그렸다.
- **크래프팅이 장비를 안 줬다** — `craftItem` 성공 시 `inventory.programs` 에 **임시 `Program`** 을 밀어 넣었다.
  레시피는 장비(deck/body/eyes/…)인데 결과물이 프로그램이었다.
- **장비 메뉴가 소유와 무관했다** — `handleEquipmentInput` 이 "그 슬롯의 첫 번째 카탈로그 항목"을 그냥 장착했다.
  소유 상태라는 축이 없었다.

ADR-0324 가 비용표를 확정했지만, 그 비용표는 **아무 화면도 읽지 않았다.** 이 ADR 이 그 배선이다.

## 결정 (Decision)

**⑴ 데이터 파일 2종을 만든다** (`web/src/data/`):

- `recipes.json` — **16종**(T1~T6; T0 starter 2종은 지급이므로 제외). 비용은 ADR-0324 의 v2 표.
- `materials.json` — **28종**. **`ice_types.json` 의 `loot_table.item` 집합과 정확히 일치**한다(드롭되는 것만 재료다).
- `main.ts` 는 실제 import 로 바꾸고, **빈 registry 면 boot 시 throw** 한다 — 빈 화면을 그리는 대신 누락된 데이터 파일을 즉시 드러낸다.

**⑵ 크래프팅 = 재료 차감 + 소유 획득 (한 transaction)** — `craftItem` 성공 시 재료를 빼고 그 장비를 **소유**한다
(`owned_equipment.ts`, `localStorage` `wetrun_owned_equipment`). 재료 지갑도 함께 영속한다.

**⑶ 소유만 장착된다** — `owned_equipment.ts`: T0 starter 는 **지급**(카탈로그 `tier === "T0"` 에서 파생),
나머지는 **제작으로만** 소유. EQUIPMENT 메뉴는 소유한 것만 장착한다.

**⑷ 카탈로그의 `requiredMaterials` 를 v2 비용으로 동기화** — 유령 재료(`wetware_chip`·`biosoft_agent`·`wetware_data`,
드롭되지 않는 id)를 제거하고 `recipes.json` 과 일치시킨다. 드리프트는 테스트가 막는다.

## 결과 (Consequences)

- **장비에 획득 경로가 생겼다**: 크래프팅이 **입을 수 있는 것**을 준다. T1 3종은 3런, T6 3종은 8런 안에 ≥50%.
- **소유는 지속된다**(`localStorage`) — 새로고침을 견딘다. 소유는 단조(제거 없음).
- **밸런스 byte-identical**: 레시피·소유는 전투 수치에 닿지 않는다. `npm run balance` **100/100/100/97.1/70.6/47.0**.
- **검증**: vitest **230 files / 4396 tests**(신규 `owned_equipment` 8 · `recipes_data` 8) · typecheck/lint 0 error · build OK.
- **남은 것** (핸드오프 §4 "그 다음"): ⑴ `buy` — 시장 offer 가격은 **오너 결정 5번** 대기 ⑵ 미사용 스탯 9종 배선
  (특히 없는 플레이어 방어 단계) ⑶ `use_item` ⑷ `drop` 을 획득 경로로 배선(현재 craft 만 구현).
- **알려진 한계**: EQUIPMENT 메뉴는 여전히 **슬롯당 첫 소유 항목**을 장착한다(교체/해제 UI 는 별도 슬라이스).
