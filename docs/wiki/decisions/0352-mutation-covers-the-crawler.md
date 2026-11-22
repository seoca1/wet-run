# ADR-0352: mutation 을 던전 크롤러까지 — 글리프 계약

**상태**: Accepted (오너: *"응 진행해"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

mutation 셋이 주요 표면을 덮은 뒤(ADR-0333~0351), 남은 세부 모듈로 넓힌다 — 던전 크롤러
(`dungeon_crawler_*`). 문자열 enum(`TileType`/`EntityType`/`MonsterType`)이 **맵에 무엇을 그리는지**를
정한다: `"#"` 벽, `"."` 바닥, `"@"` 플레이어, `"M"` 몬스터, `"g"` 골리앗.

## 결정 (Decision)

**변이 3건 + 값 계약 테스트.**

- `TileType.FLOOR = "." → ","`
- `EntityType.MONSTER = "M" → "m"`
- `MonsterType.ICE_GOLIATH = "g" → "G"`
- 신규 `tests/dungeon_crawler_types.test.ts` 가 글리프 값을 고정.

## 결과 (Consequences)

- **36/36 KILLED.**
- **값 미고정 상수(또)**: 글리프 enum 의 **값을 고정하는 테스트가 없었다**(`dungeon_crawler_wiring.test.ts`
  는 존재/이동만 검사, 글리프 비교는 안 함). 계약 테스트가 셋에 들어가 변이 3건을 각 1개 테스트로 잡았다.
- **렌더링 계약 명문화**: 이제 `"#"`/`"."`/`"@"`/`"M"`/`"g"`/`"B"` 를 바꾸면 테스트가 먼저 깨진다(맵 외형
  변경이 의도된 결정임을 강제).
- 검증: mutation **36/36** · vitest **238 files / 4459 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — `CRAWLER_TYPES` 변이 3 + `dungeon_crawler_types` 테스트
- `web/tests/dungeon_crawler_types.test.ts` — 글리프 값 계약 테스트(2)
- 실행: `npm run mutation` → **36/36 KILLED**

**Notes**: 남은 세부 모듈(achievements 등, 함수형)은 anchor 설계가 필요.

## 영향 받는 항목

- `web/scripts/mutation_spike.ts` · `web/tests/dungeon_crawler_types.test.ts`

## 관련 결정

- ADR-0333 / 0349 / 0350 / 0351 (값 계약 테스트) · ADR-0345 / 0348 (누락 테스트 파일)

## 변경 이력

- 2026-11-22: Accepted (던전 크롤러 확대 → 36/36; 글리프 값 고정)
