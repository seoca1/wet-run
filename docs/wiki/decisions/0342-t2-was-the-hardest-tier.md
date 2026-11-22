# ADR-0342: T2가 가장 어려웠다 — 도달률을 진짜 지갑으로 재고 비용표를 다시 잘랐다

**상태**: Accepted (오너: *"판단대로 진행해"* — 검증 후속 P3 재측정)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (경제 · 진행)

## 컨텍스트 (Context)

경제 축이 "T2+ 도달률 0%"로 보고됐지만, 그 수치는 두 가지 **측정 결함** 위에 있었다:

1. **probe 가 `final.inventory.materials`(= 미션 보상 + 드롭)를 합산**했다 — 실제 지갑(ADR-0323/0338:
   `earnedMaterials` = 획득분만, 보상 제외)보다 **관대**한 모델.
2. **probe 가 `--runs 3`** 으로 돌았다 — T2 의 의도된 지평(ADR-0324: ~8런)을 못 봤다. 3런에서는 어떤
   T2 레시피도 못 산다(당연).
3. **probe 가 `crafting-recipes-candidate.json`(복사본)을 검사**했다 — 실데이터(`src/data/recipes.json`)와
   값이 같았지만, **복사본임을 강제하는 장치가 없었다**(드리프트 위험).

## 측정 (Measurement)

probe 를 **실 지갑 함수(`earnedMaterials`)** + **실데이터(`src/data/recipes.json`)** 로 고치고 지평을 넓혔다.
등급별 8런 산출(중앙값): g1 `df 5·ish 12` · g2 `df 10·ish 4` · g3 `df 14·cm 1` · g4 `ish 74·cm 3` ·
g5 `df 85·cm 42·cs 28` · g6 `cm 24·cs 16·t6 1`.

옛 비용표의 도달률(8런, earned-only):

| tier | 옛 도달률 | 비용 산출 vs 그 등급 |
|---|---|---|
| T1 | 58% | ok |
| **T2** | **0~3.3%** | 비용 df 12-18 > g2 산출 df **10** ← **병목** |
| T3 | 38% | 비용 df 16-22 > g3 산출 df **14** |
| T4 | 55% | ok |
| T5 | 79% | ok |
| T6 | 64% | ok |

**역전**: 첫 업그레이드 등급(T2)이 가장 도달 불가, 상단(T5)이 가장 쉬움. g2 는 저등급이라 산출이 적은데
비용은 최고 수준이었다(ADR-0324 의 "자기 등급에서 판정" 규칙 아래).

## 결정 (Decision)

1. **probe 정정**: `earnedMaterials`(실 지갑) · `src/data/recipes.json`(실데이터) · 지평 `--runs 8` 기준.
   복사본 `crafting-recipes-candidate.json` **삭제**(드리프트 제거).
2. **T2/T3 비용 재조정** — 자기 등급의 8런 산출에 맞춘다:
   - T2: `deck_corporate df16→8·ish4→3` · `bodysuit_subdermal df12→6·ish4→3` · `trodes_ninja df18→8` ·
     `boots_ghost df15→7·ish4→3`
   - T3: `deck_militech df20→13` · `bodysuit_tactical df16→12` · `implant_nanohive df22→14`
   - `equipment_catalog.ts` 의 `requiredMaterials` 도 동기화(테스트가 drift 를 막는다).

## 결과 (Consequences)

- **도달률 곡선이 일관된다**: 8런에서 T1 58% · **T2 47~58%** · T3 48~50% · T4 55% · T5 79% · T6 64%.
  역전 해소(T2 3.3% → 47~58%). 12런에서 전 등급 57~100%.
- **측정이 신뢰 가능해졌다**: probe 가 실 지갑·실데이터를 읽으므로 결론이 실제 게임과 일치한다.
- **드리프트 제거**: 복사본 후보 파일 삭제. 비용은 `recipes.json` + `equipment_catalog.ts` 두 곳이며
  `recipes_data.test.ts` 가 둘의 일치를 강제한다(중복이지만 테스트가 지킨다).
- **밸런스 무영향**: 재료는 전투 수치에 닿지 않는다 — `balance`/`gear` 골든 byte-identical 예상(검증에서 확인).
- **남은 것**: 재료 산출이 등급에 대해 **비단조**(g4 df 9 < g3 df 14, g5 df 85) — 드롭 테이블 자체의
  문제로 별도 검토. 시장(ADR-0331)은 probe 에 미포함이라 실제 도달률은 이보다 약간 높다.
- 검증: vitest **236/4446** · typecheck 0 · lint 0 error · 러틴 9/9.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/crafting_probe.ts` — `earnedMaterials` · shipped `recipes.json` · NOTE 갱신
- `web/src/data/recipes.json` — T2/T3 비용 재조정 + `_comment`
- `web/src/core/state/equipment_catalog.ts` — `requiredMaterials` 7건 동기화
- 측정: T2 3.3% → 47~58% (8런)
- 삭제: `web/scripts/crafting-recipes-candidate.json`

**Notes**: 드롭 테이블 비단조성은 후속. probe 는 여전히 `--runs` 지평을 명시해야 의미가 있다(기본 3런은 T2 를 못 본다).

## 영향 받는 항목

- `web/scripts/crafting_probe.ts` · `web/src/data/recipes.json` · `web/src/core/state/equipment_catalog.ts`

## 관련 결정

- ADR-0323 (hoard 보존) · ADR-0324 (자기 등급 판정) · ADR-0325 (장비 데이터) ·
  ADR-0338 (계약 재료 carry) · ADR-0331 (재료 시장) · ADR-0341 (장비↔난이도)

## 변경 이력

- 2026-11-22: Accepted (probe 실지갑화 + T2/T3 비용 재조정)
