# ADR-0047: 텍스트 가시성 개선 (Typed Status Messages)

**상태**: Accepted
**날짜**: 2026-06-21
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

현재 footer/status 텍스트는 모두 동일한 회색 `>>> text` 형식으로 출력되어:

- **카테고리 구분 불가** — 이동 / 전투 / 시스템 / 경고 / 에러가 같은 회색
- **시각적 위계 없음** — 중요한 경고도 일반 정보와 동일한 톤
- **tcod 색상 미활용** — `tcod.console`는 fg/bg를 지원하지만 현재 시스템은 미사용
- **그래픽 노블 prose 가독성** — 흰색 본문은 장시간 독서에 눈이 피로

깁슨 톤은 "정보 과부하 속 핵심만 강조"이므로, **카테고리별 시각 구분이 필수**.

## 고려한 옵션

### Option 1: 회색 텍스트 유지 (현상 유지)

- **설명**: 기존 `>>> text` 그대로.
- **장점**:
  - 코드 변경 0
  - 호환성 100%
- **단점**:
  - Pillar 5 (The Style) 위반 — 깁슨 톤은 "정보 과부하 속 시각 위계"
  - 게임 피드백 약함 — 무엇이 중요한지 알 수 없음

### Option 2: 전면 색상화 (모든 텍스트 무지개) ✗

- **설명**: 모든 메시지에 무작위 색상.
- **장점**: 시각적으로 다양.
- **단점**:
  - Pillar 1 (The Run) 위반 — 가독성 저하, 깜빡임
  - 깁슨 톤 아님 — 원작은 절제된 monochrome + 핵심 강조
  - 색맹 사용자에게 불리

### Option 3: 8종 카테고리 + 아이콘 + 절제된 색상 ✓ 선택

- **설명**: `MessageKind` enum (DEBUG/INFO/MOVEMENT/DIALOG/COMBAT/SUCCESS/WARNING/ERROR), 각 카테고리별 단일 색상 + 선택적 bg 하이라이트.
- **장점**:
  - 카테고리 8종으로 의미 명확
  - WARNING/ERROR만 bg 하이라이트 (시각 노이즈 최소화)
  - 기존 `>>> text` 자동 분류 (`from_legacy()` 휴리스틱)
  - cream `(232, 230, 220)` 본문색으로 GN 가독성↑
- **단점**:
  - 신규 모듈 `status_message.py` (~230 lines)
  - `layout.py`, `graphic_novel_view.py`, `matrix_view.py` 수정 필요

### Option 4: GUI 토스트 알림 (모달 popup)

- **설명**: 메시지를 별도 토스트 윈도우로 분리.
- **장점**: 화면 점유 명확.
- **단점**:
  - **Pillar 위반** — "in-line at the bottom" 명시적 (디지털 노트북 화면 비유)
  - tcod ASCII 미학 파괴
  - 정보 흐름 끊김

## 추천 (Recommendation)

**Option 3**. 깁슨 미학 (절제 + monochrome + 핵심 강조) + Pillar 5 (The Style) 정합.

## 사용자 결정 (Decision)

[x] Option 3 (Implemented)

## 결과 (Consequences)

### 신규 모듈

- **`src/wet_run/engine/status_message.py`** (230 lines):
  - `MessageKind(IntEnum)`: DEBUG=0 / INFO=10 / MOVEMENT=20 / DIALOG=30 / COMBAT=40 / SUCCESS=42 / WARNING=44 / ERROR=50
  - `MESSAGE_STYLE`: 8종 (icon + fg + optional bg)
  - `StatusMessage` dataclass (`frozen=True, slots=True`): kind/icon/text/fg/bg/timestamp_ms
  - `prefix` property: `"⚠ WARNING: "` 형식 (icon + name)
  - `from_legacy(text)` 정적 메서드: `"MOVE:"` / `"WARNING:"` / `"ERROR:"` / `"EXTRACT:"` 키워드 휴리스틱
  - `parse_legacy_messages(legacy, max_keep=10)`: 리스트 변환 + 최신 N개 유지

### 변경 모듈

- **`src/wet_run/engine/layout.py`** (~100 lines):
  - `draw_footer(..., use_styled: bool = True, status_messages: list[str] | None)`: 스타일드 모드 기본값
  - `draw_message_log(...)`: 사이드 패널용 다중 로그
  - WARNING/ERROR는 bg 하이라이트 (dark yellow / dark red)
- **`src/wet_run/engine/graphic_novel_view.py`**:
  - `render_scene()` prose body `fg = (232, 230, 220)` cream-white
- **`src/wet_run/engine/matrix_view.py`**:
  - `render_matrix()` 사이드 패널에 메시지 로그 추가

### 신규 스크립트

- **`scripts/text_visibility_demo.py`** (425 lines): 4-씬 시각 데모
  1. Footer BEFORE vs AFTER
  2. 8종 MessageKind 카테고리 전체
  3. GN prose body 새 cream color
  4. 풀 매트릭스 + 사이드 패널 로그

### 신규 테스트

- **`tests/unit/test_status_message.py`** (43 tests):
  - MessageKind enum (8종, IntEnum 순서)
  - MESSAGE_STYLE (모든 kind에 fg/bg 매핑)
  - StatusMessage 생성 (frozen, slots, prefix)
  - from_legacy() 휴리스틱 (MOVE/WARNING/ERROR/EXTRACT/HIT/GAINED 등)
  - parse_legacy_messages() (max_keep cap, str + StatusMessage 혼합)
  - 시각화 검증 (icon, fg, bg)

### 검증 결과

- pytest: **2385 passed** (43 신규)
- ruff check: **All checks passed**
- ruff format: **194 files already formatted**
- mypy strict: **Success: no issues found in 94 source files**

## 영향 받는 항목

- `design/scenario/graphic-novel.md` (§10 톤 가이드라인에 status message 스타일 명시)
- `design/systems/ui.md` (footer / message log 명세)
- `decisions/0032-graphic-novel-mode.md` (style layer 확장)
- `decisions/README.md` (인덱스 추가)

## 관련 결정

- ADR-0032 (Graphic Novel Mode) — 본문 렌더링
- ADR-0041 (Content Expansion) — 본문 길이 확장, 가독성 더 중요
- ADR-0046 (Ending B) — 새 씬 6개, 가독성 검증 필수

## 변경 이력

- 2026-06-21: Draft 작성 + Accepted (구현 완료 후 retrospective ADR)