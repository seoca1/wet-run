# ADR-0048: GN 메뉴 엔딩 선택 + Save 마이그레이션 (1.0.0 → 1.1.0)

**상태**: Accepted
**날짜**: 2026-06-21
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

ADR-0046에서 엔딩 B 6 씬 (Case/Sil/Kas × 2 씬)을 추가했지만:

- **메뉴 접근 불가** — `--ending {A,B}` CLI 플래그만 존재, 메뉴에서는 A만 선택 가능
- **이어서 읽기 손실** — `GNProgress`에 ending 필드 없음 → 재개 시 항상 ending A로 복원
- **UI 비대칭** — "12 씬이 있어요" 라고 표시되지만 실제로는 한 번에 4 씬만 볼 수 있음

엔딩 B를 정식 게임 흐름에 통합하여 **메뉴 parity + save parity** 확보.

## 고려한 옵션

### Option 1: 캐릭터별 8 옵션 (Novice-A, Novice-B, Veteran-A, ...) ✗

- **설명**: 메뉴에 8개 옵션을 펼쳐서 표시.
- **장점**: 단일 화면, 빠른 접근.
- **단점**:
  - 메뉴 화면 길어짐 (Pillar 5 위반)
  - 향후 Ending C 추가 시 12 옵션으로 확장
  - 키 매핑 복잡 (1-8)

### Option 2: 엔딩 서브메뉴 화면 ✓ 선택

- **설명**: 캐릭터 선택 후 새 화면 `GRAPHIC_NOVEL_ENDING_MENU` 표시: [엔딩 A] [엔딩 B] [BACK]. State 필드 `gn_ending_choice` 추가.
- **장점**:
  - 깨끗한 분리 (3-4 옵션 화면 유지)
  - 향후 Ending C/D 확장 용이 (3-4 옵션 그대로)
  - i18n 일관성
- **단점**:
  - 화면 1개 추가
  - 키 입력 1-2번 더 필요

### Option 3: 엔딩 무작위 자동 선택

- **설명**: 메뉴에서 캐릭터 선택 시 50/50으로 A/B 자동.
- **장점**: 입력 단순.
- **단점**:
  - **Pillar 1 (The Run) 위반** — 플레이어 선택권 박탈
  - "대안 결말"이라는 의도 무의미
  - 결정론적 테스트 어려움

## 추천 (Recommendation)

**Option 2**. 깨끗한 분리 + 확장성 + 플레이어 선택권.

## 사용자 결정 (Decision)

[x] Option 2 (User-selected "엔딩 B 메뉴 UI 동기화")

## 결과 (Consequences)

### 신규 Screen + State 필드

- **`ScreenKind.GRAPHIC_NOVEL_ENDING_MENU`** (`state.py`)
  - 캐릭터 선택 후 표시
  - 3 옵션: [엔딩 A (기본)] [엔딩 B (대안)] [BACK]
- **`AppState.gn_ending_choice: str = ""`** (`state.py`)
  - `""` (선택 안 함) | `"A"` | `"B"`
  - GRAPHIC_NOVEL 진입 시 사용

### 신규 입력 핸들러

- **`handle_graphic_novel_ending_menu_input()`** (`menu.py`)
  - N1 → "A", N2 → "B", N3 → "back" (혹은 ESC)

### 신규 렌더

- **`render_graphic_novel_ending_menu()`** (`graphic_novel_view.py`)
  - 화면 너비: 제목 + 캐릭터명 + 3 옵션 + 백

### 변경 함수

- **`_action_graphic_novel_menu(state, mode, ending="A")`** (`play.py`)
  - ending 파라미터 추가
  - state.gn_ending_choice 설정
  - chain 로드 시 ending 전달

### Save 마이그레이션

- **`GN_SAVE_VERSION = "1.0.0"` → `"1.1.0"`** (additive change)
- **`GNProgress.ending: str = "A"`** 필드 추가
- **`from_dict()`**: 기본값 `"A"` (구버전 save 호환)
- **`make_progress()`**: ending 파라미터 추가 (default `"A"`)
- **CONTINUE READING**:
  - 로드 시 ending 필드 확인
  - `state.gn_ending_choice`에 복원
  - 체인 로드 시 해당 ending 사용
  - SAVED_PROGRESS 화면에 "(엔딩 B)" 표시

### 메뉴 옵션 구조

```
MENU (5 옵션)
└── GRAPHIC NOVEL
    └── GRAPHIC_NOVEL_MENU (5 옵션)
        1. PROLOGUE (랜덤 — 항상 ending A)
        2. CASE (Novice)
           └── GRAPHIC_NOVEL_ENDING_MENU (3 옵션)
               1. ENDING A — 케이의 의뢰 수락 (4 씬)
               2. ENDING B — 신비로운 의뢰 거절 (4 씬, ADR-0046)
               3. BACK
        3. SIL (Veteran) → ending menu
        4. KAS (Heretic) → ending menu
        5. BACK
```

### 영향 받는 스크립트

- `play.py`, `demo.py`, `demo_all.py`, `graphic_novel.py`
  - 새 화면 핸들링 추가
- `scripts/text_visibility_demo.py` — 변경 없음 (엔딩 무관)

## 영향 받는 항목

- `decisions/0044-graphic-novel-save.md` (Save format 버전 정책)
- `decisions/0046-graphic-novel-ending-b.md` (CLI → 메뉴 통합)
- `design/scenario/graphic-novel.md` (§9 메뉴 구조 갱신)
- `tests/unit/test_graphic_novel_save.py` (Save 마이그레이션 테스트 추가)
- `tests/unit/test_menu_extended.py` (엔딩 메뉴 입력 테스트)
- `tests/unit/test_graphic_novel_endings.py` (체인 로드 + ending 연동)

## 신규 테스트

- `tests/unit/test_graphic_novel_ending_menu.py` (~25 tests):
  - 렌더: 3 옵션 + 캐릭터 헤더 + ending hint
  - 입력: N1→A, N2→B, N3/ESC→back
  - state transition: GRAPHIC_NOVEL_MENU → GRAPHIC_NOVEL_ENDING_MENU → GRAPHIC_NOVEL
  - ending 필드: GNProgress.from_dict v1.0.0 → 기본 "A" (마이그레이션)
  - CONTINUE READING: ending B 저장 → 재개 시 chain_length 검증 + ending B 로드
  - i18n: 한글 옵션 표시

## 변경 이력

- 2026-06-21: Draft 작성
- 2026-06-21: Accepted (구현 완료)

### 구현 결과

**Code**:
- `src/wet_run/engine/state.py`: `ScreenKind.GRAPHIC_NOVEL_ENDING_MENU` + `gn_ending_choice: str = "A"`
- `src/wet_run/engine/menu.py`: `handle_graphic_novel_ending_menu_input()` (N1=A, N2=B, N3/ESC/Q=back)
- `src/wet_run/engine/graphic_novel_view.py`: `get_gn_ending_menu_options()`, `render_graphic_novel_ending_menu()`, 상수 `GN_ENDING_A/B/BACK`, `_ENDING_DESCRIPTIONS` per character
- `src/wet_run/engine/graphic_novel_save.py`: `GN_SAVE_VERSION = "1.1.0"`, `GNProgress.ending: str = "A"`, `make_progress(ending="A")`, `from_dict` v1.0.0 migration
- `scripts/play.py`: `_action_graphic_novel_ending_menu()`, ending in cache key + chain load
- `scripts/demo.py`: ending menu hop, render call, cache key
- `scripts/demo_all.py`: cache key update
- `scripts/graphic_novel.py`: `--continue` reads `saved_progress.ending` (CLI `--ending` overridable)

**Tests** (35 신규):
- `tests/unit/test_graphic_novel_ending_menu.py`:
  - State field (default "A", settable)
  - GN_SAVE_VERSION = "1.1.0"
  - GNProgress ending field (default, make_progress, to_dict, from_dict v1.0.0→A, invalid→A, round-trip)
  - Save migration (file-level v1.0.0 load, v1.1.0 with ending B)
  - get_gn_ending_menu_options (3 options, EN+KO labels, all characters)
  - handle_graphic_novel_ending_menu_input (N1→A, N2→B, N3→back, ESC→back, Q→back, unmapped→"")
  - render_graphic_novel_ending_menu (no crash EN/KO, character label visible, 3 options visible)
  - GN_ENDING_A/B/BACK constants
  - ScreenKind.GRAPHIC_NOVEL_ENDING_MENU exists

**검증**:
- pytest: **2420 passed** (2385 + 35)
- ruff check: All checks passed
- ruff format: 195 files already formatted
- mypy strict: Success: no issues found in 94 source files

**시각 검증**:
- EN: `> [1] ENDING A — Case accepts the Finn's job — first run succeeds` ✓
- KO: `> [1] 엔딩 A — 케이의 의뢰 수락 — 1차 잭 성공` ✓
- 3 옵션 + character header + ESC 안내 모두 정상
