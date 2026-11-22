# ADR-0345: mutation 을 매트릭스까지 — 18/18, 그리고 남은 하나는 테스트 파일이었다

**상태**: Accepted (오너: *"매트릭스 확대로 진행하자"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

ADR-0344 가 mutation 을 엔딩·경제로 넓히며 "남은 것: 매트릭스 모듈"로 끝냈다. 매트릭스는 런의
**보드 자체**(노드 수·존 순서·그리드 크기·fog 순서)라, 곡선 하네스가 못 보는 축이다.

## 결정 (Decision)

**매트릭스/던전 변이 3건을 추가한다.**

- `matrix.ts` `NUM_NODES = 5 → 4` (보드 노드 수)
- `matrix_navigation.ts` `NO_HOP = -1 → 0` (hop 없음 센티넬)
- `dungeon_layout.ts` `GRID_BY_GRADE[4] = [13, 8] → [9, 6]` (4등급 그리드)
- 기본 셋에 `matrix_structure` · `matrix` · `matrix_navigation` · `dungeon_layout` · `exploration` 추가.

## 결과 (Consequences)

- **18/18 KILLED**(전투 10 · 엔딩 2 · 경제 3 · 매트릭스 3).
- **가르친 것**: 첫 실행에서 `matrix-nodes-short` 가 **SURVIVED**(0/333) 였다. 상수는 살아 있었지만
  (`matrix.ts` 가 `bossNode = NUM_NODES - 1` 로 사용) 그 값을 고정하는 `matrix.test.ts` 가 **내 테스트 셋에
  없었다**. 추가하니 **17개 테스트**가 잡았다 — 즉 생존 변이가 항상 "구멍"은 아니고, **셋에서 빠진 테스트
  파일**일 수 있다(mutation 측정의 고전적 함정: 테스트가 없으면 모든 변이가 생존한다).
- **교훈**: mutation 셋은 대상 모듈의 **계약 테스트를 포함**해야 한다. 셋이 좁으면 SURVIVED 가 구멍인지
  누락인지 구분되지 않는다(도구 자체가 오도 — 이 세션의 반복 주제).
- **남은 것**: `main.ts`(런 시작 seed)는 단위 테스트가 없어 변이 시 SURVIVED 로 나올 것이며, 이건 **진짜
  구멍**이다(호출부 미검증). 다음 후보: seed 계산을 순수 함수로 추출해 테스트.
- 검증: mutation **18/18** · vitest 236/4447(변경 없음) · typecheck 0.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — `MATRIX`/`MATRIX_NAV`/`LAYOUT` 변이 3 + 매트릭스 테스트 5파일
- 실행: `npm run mutation` → **18/18 KILLED**(matrix-nodes-short 17, nohop-zero 1, grid-g4-shrunk 1)

**Notes**: `main.ts` 호출부 테스트화는 후속(순수 함수 추출 필요).

## 영향 받는 항목

- `web/scripts/mutation_spike.ts`

## 관련 결정

- ADR-0333 (mutation 도입) · ADR-0344 (엔딩·경제 확대) · ADR-0343 (측정 도구 정직성)

## 변경 이력

- 2026-11-22: Accepted (매트릭스 확대 → 18/18; 생존 변이는 누락 테스트 파일이었음)
