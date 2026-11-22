# ADR-0348: mutation 을 카드·팩션까지 — 그리고 또 "누락된 테스트 파일"이었다

**상태**: Accepted (오너: *"응 후속 진행해줘"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

mutation 셋이 전투·엔딩·경제·매트릭스를 덮은 뒤(ADR-0333~0347), 다음으로 **게임플레이 표면을 넓힌다**:
카드 가치(`program_effects`)와 팩션 평판(`faction_reputation`).

## 결정 (Decision)

**변이 3건 추가.**

- `program_effects.ts` `programBaseDamage`: `program.tier * 5 → * 4` (카드가 "N 데미지"라 적는 값)
- `faction_reputation.ts` `TIER_THRESHOLDS[ALLIED].min`: `80 → 70`
- `faction_reputation.ts` `TIER_MULTIPLIERS.ALLIED`: `0.5 → 0.9`
- 기본 셋에 `program_effects` · `program_catalog_text` · `faction_reputation` 테스트 추가.

## 결과 (Consequences)

- **23/23 KILLED.**
- **또 하나의 교훈(ADR-0345 와 동일)**: 첫 실행에서 `base-damage-4` 가 **SURVIVED** 였는데, 상수는 살아
  있었고(설명 문자열을 만듦) 그 값을 고정하는 `program_catalog_text.test.ts` 가 **내 셋에 없었다**.
  추가하니 1개 테스트가 잡았다. **mutation 은 대상 모듈의 계약 테스트를 포함해야 하며, 안 그러면
  생존 변이가 구멍인지 누락인지 구분되지 않는다** — 이 세션에서 두 번째(매트릭스에 이어).
- **팩션 평판은 즉시 KILLED**(threshold 2, multiplier 3) — 평판 임계/배수가 이미 잘 고정돼 있다.
- 검증: mutation **23/23** · vitest **237 files / 4454 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — 변이 3 + 카드/팩션 테스트 3파일
- 실행: `npm run mutation` → **23/23 KILLED**(base-damage-4 1, allied-threshold 2, allied-multiplier 3)

**Notes**: 남은 모듈(세이브·오디오·i18n 등)은 후속. mutation 셋은 모듈별 계약 테스트를 함께 넣는 규칙.

## 영향 받는 항목

- `web/scripts/mutation_spike.ts`

## 관련 결정

- ADR-0333 (mutation 도입) · ADR-0344 (엔딩·경제) · ADR-0345 (매트릭스, 같은 교훈) · ADR-0347 (장비 병합)

## 변경 이력

- 2026-11-22: Accepted (카드·팩션 확대 → 23/23; 생존 변이는 또 누락 테스트 파일)
