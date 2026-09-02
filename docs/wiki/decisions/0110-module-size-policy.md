# ADR-0110: 모듈 사이즈 정책 (현행 250 LOC)

**상태**: Accepted (Option 4, 사용자 결정 2026-07-12)
**날짜**: 2026-07-12
**결정자**: 사용자
**우선순위**: P3 (The Build)
**관련**: 프로젝트 코딩 규칙 (AGENTS.md §6)

## 컨텍스트 (Context)

2026-07-04 commit (29c3eeb) 기준으로 lint/mypy 0건 / 114 source files 그린. 그러나
2026-07-12 헬스 체크 결과 14 개 파일이 250 LOC 한도 초과:

| 파일 | LOC |
|---|---:|
| `engine/graphic_novel_view.py` | 1,510 |
| `combat/effects.py` | 1,246 |
| `engine/matrix_view.py` | 1,057 |
| `engine/combat_view.py` | 1,053 |
| `achievements.py` | 938 |
| `matrix/dungeon_generator.py` | 850 |
| `engine/app.py` | 845 |
| `run/state.py` | 759 |
| `engine/story_cinematic.py` | 754 |
| `engine/save_manager.py` | 739 |
| `combat/combo.py` | 685 |
| `engine/dungeon_view.py` | 678 |
| `engine/hub.py` | 672 |
| `engine/event_story.py` | 666 |

**문제**:
- AGENTS.md §6 의 "250 LOC" 규약이 사실상 미적용
- 코드 리뷰 / 변경 영향 분석 시 큰 모듈은 부담
- 4 모듈 (graphic_novel_view / combat/effects / matrix_view / combat_view) 은 docstring 90%+ 누락 — 사이즈와 결합
- matrix_view.py 는 ADR-0103 (Dungeon-only mode) 부로 runtime 미사용 — backward compat 보존 중

## 고려한 옵션

### Option 1: Strict 250 LOC 한도 강제

- **설명**: 모든 신규/수정 모듈은 250 LOC 이하. 초과 시 PR 리뷰에서 거부.
- **장점**:
  - 규약 일관성, 가독성, 신규 합류자 진입 장벽 낮춤
  - 단위 테스트 / mock / 리팩토링 부담 감소
- **단점**:
  - 14 기존 파일 모두 리팩토링 필요 (큰 작업)
  - 일부 모듈은 본질적으로 거대 (combat/effects 는 VFX 5-Layer 시스템)
  - 외부 의존성 있는 모듈은 분리 어려움 (e.g., python-tcod rendering wrapper)
  - 리팩토링 중 회귀 위험 (테스트 커버리지 부족 시)
- **Pillar 정합**:
  - P4 (The Build): 가독성 ↑↑
  - P3 (The Flatline): 회귀 위험 ↑

### Option 2: Soft 300 LOC 경고 + 500 LOC 차단

- **설명**: 300 LOC 미만 권장, 500 LOC 초과는 PR 리뷰 거부. CI 에서 자동 검사.
- **장점**:
  - 14 파일 중 일부는 300 미만 (engine/app.py 845, matrix_view.py 1,057 은 500 초과만 적용)
  - 실용적: 무조건 분할 부담 ↓
  - 점진적 개선 가능
- **단점**:
  - 일관성 ↓ (어떤 파일은 지키고 어떤 파일은 안 지킴)
  - 향후 추가된 모듈도 결국 기준을 어길 가능성
- **Pillar 정합**:
  - P4 (The Build): 실용성 ↑

### Option 3: Status quo (정책 없음, 휴먼 리뷰)

- **설명**: ADR-0110 없음. PR 시 작성자 재량.
- **장점**:
  - 즉시 작업 가능, 부담 없음
- **단점**:
  - AGENTS.md §6 의 250 LOC 규약이 텍스트로만 존재, 무의미
  - 헬스 체크가 다시 14+ 파일 지적
  - 신규 합류자 혼란

### Option 4: 신규 사이즈 가이드 (현실적)

- **설명**:
  - **250 LOC**: 신규 모듈 권장 한도 (PR 리뷰 체크리스트)
  - **500 LOC**: PR 거부 기준 (1회성으로 인정되는 단발성 시 700~800 허용)
  - **1000+ LOC**: 신규 ADR 필수 (정당화 + 분할 계획)
- **장점**:
  - 현실적 임계치, 점진적 개선 가능
  - 1000+ LOC 인 4 모듈 (graphic_novel_view, combat/effects, matrix_view, combat_view) 의 ADR 요구가 분명
- **단점**:
  - "한 번에 다 해결" 어려움 — phase 별 진행

## 추천 (Recommendation)

**Option 4 — 신규 사이즈 가이드**를 권장. 이유:
- AGENTS.md §6 텍스트를 실제 정책으로 격상
- 14 파일의 우선순위 자동 분류 (1000+ LOC 4 모듈은 별도 ADR 필요)
- 점진적 리팩토링 가능 (한 세션 부담 ↓)
- 신규 모듈 작성 시 명확한 가이드

## 사용자 결정 (Decision)

[x] Option 4 (신규 가이드 250/500/1000) — 사용자 결정 2026-07-12

## 결과 (Consequences)

### 정책 (Accepted)

- **250 LOC**: 신규 모듈 권장 한도 (PR 리뷰 체크리스트)
- **500 LOC**: PR 거부 기준 (1회성 / 단발성 모듈은 700~800 LOC 까지 예외 허용)
- **1000+ LOC**: 신규 ADR 필수 (정당화 + 분할 계획 OR 보유 사유 명시)

### 영향 받는 항목 (현행 14 파일)

| 파일 | LOC | 등급 | 처리 |
|---|---:|---|---|
| `engine/graphic_novel_view.py` | 1,510 | 1000+ | 별도 ADR (제안: 0111) |
| `combat/effects.py` | 1,246 | 1000+ | 별도 ADR (제안: 0112) |
| `engine/matrix_view.py` | 1,057 | 1000+ | ADR-0103 — backward compat 보존 결정 |
| `engine/combat_view.py` | 1,053 | 1000+ | 별도 ADR (제안: 0113) |
| `achievements.py` | 938 | 500 | 리팩토링 권장 (PR 거부 X) |
| `matrix/dungeon_generator.py` | 850 | 500 | 리팩토링 권장 |
| `engine/app.py` | 845 | 500 | 리팩토링 권장 |
| `run/state.py` | 759 | 500 | 리팩토링 권장 |
| `engine/story_cinematic.py` | 754 | 250 | soft 경고 |
| `engine/save_manager.py` | 739 | 250 | soft 경고 |
| `combat/combo.py` | 685 | 250 | soft 경고 |
| `engine/dungeon_view.py` | 678 | 250 | soft 경고 |
| `engine/hub.py` | 672 | 250 | soft 경고 |
| `engine/event_story.py` | 666 | 250 | soft 경고 |

### CI 적용 (option 4)

- 신규 PR 시 500 LOC 초과 시 lint 룰 또는 CI step 추가 검토
- 1000+ LOC 신규 모듈 PR 시 ADR 링크 필수

### AGENTS.md §6 갱신

(다음 commit): "한 줄 100자 (ruff)" 옆에 모듈 사이즈 가이드 추가:
- 250: 신규 권장
- 500: PR 거부
- 1000: ADR 필수

### ADR-0103 호환

- `matrix_view.py` (1,057 LOC) 는 ADR-0103 의 backward compat 보존 결정 우선
- 본 ADR-0110 채택 후에도 ADR-0103 의 matrix_view 모듈 처리 결정 유지
- 향후 matrix_view 가 정말 사용처 없으면 archive 결정 가능

### 후속 ADR (제안)

- ADR-0111: graphic_novel_view.py 분할 (1,510 → ~700 + 서브모듈 3-4개)
- ADR-0112: combat/effects.py 분할 (1,246 → VFX 5-Layer 시스템 모듈별 분리)
- ADR-0113: combat_view.py 분할 (1,053 → 렌더링 / 입력 / 상태 분리)
- 각 1000+ 파일별 별도 ADR 작성 후 리팩토링

## 영향 받는 항목

- AGENTS.md §6 — "한 줄 100자 (ruff)" 옆에 모듈 사이즈 섹션 추가
- 신규 14 파일:
  - 1000+ LOC (4): matrix_view 외 3 — 별도 ADR 필요
  - 500-999 (4): achievements, dungeon_generator, app, run/state
  - 250-499 (6): story_cinematic, save_manager, combat/combo, dungeon_view, hub, event_story
- 영향 ADR: ADR-0103 의 matrix_view 모듈 처리 결정

## 관련 결정

- ADR-0103 (Dungeon-only mode): matrix_view 폐기 결정 — 본 ADR 의 1000+ LOC 정책 표본

## 변경 이력

- 2026-07-12: Draft 작성 (헬스 체크 audit 결과)
- 2026-07-12: Accepted (Option 4 — 사용자 결정)
