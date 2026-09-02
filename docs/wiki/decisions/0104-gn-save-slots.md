# ADR-0104: GN Save Slot 확장 (3 슬롯)

**상태**: **Accepted** (2026-07-25, Sisyphus + 사용자)
**날짜**: 2026-06-21 (Draft) → 2026-07-25 (Accepted)
**결정자**: 사용자
**우선순위**: P2
**관련 ADR**: ADR-0044 (원래 단일 슬롯, 마이그레이션 대상), ADR-0051 (save system infrastructure — 본 ADR의 predecessor)
**Notion 발행**:
- v1.0 (2026-07-25, P0~P8): https://app.notion.com/p/Projects-Progress-2026-07-25-3a8f643d35308189b6f0ebe5ab250347 — 페이지 ID `3a8f643d-3530-8189-b6f0-ebe5ab250347`
- v1.1 (2026-07-25, P0~P9 + 5편 보강): https://app.notion.com/p/Projects-Progress-2026-07-25-3a8f643d353081f39bdef6b7a798e17b — 페이지 ID `3a8f643d-3530-81f3-9bde-f6b7a798e17b` (최신)

## 컨텍스트 (Context)

현재 GN save 시스템은 **단일 슬롯** (`data/saves/gn_progress.json`):
- 한 번 저장 = 이전 저장 덮어쓰기
- 여러 캐릭터/엔딩 시도 시 비교 불가
- "다른 결말 보기 위해 시도하다가 기존 진행도 잃음" 문제

GN은 자동 플레이 (자동 진행) 이므로 사용자가 여러 결말을 시도해볼 여지가 큼.
**3 슬롯 = (A/B/C) × (3 chars) = 9 결말 조합 시도** 의 자연스러운 인프라.

## 고려한 옵션

### Option 1: 3 슬롯 (고정) ✓ 선택

- **설명**: `slot_1.json`, `slot_2.json`, `slot_3.json` (3개 고정).
- **장점**:
  - 단순, 빠른 구현
  - 3 chars × 3 endings = 9 매칭 가능
- **단점**: 슬롯 추가 시 코드 변경.

### Option 2: 동적 슬롯 (N개)

- **설명**: 사용자가 슬롯 추가/삭제.
- **장점**: 무한 확장.
- **단점**:
  - UI 복잡 (생성/삭제 메뉴)
  - 인덱스 관리 어려움
  - 게임 끝까지 9개면 충분

### Option 3: 단일 슬롯 + 세이브 이름

- **설명**: 사용자가 슬롯에 이름 부여 (예: "case-ending-A-final").
- **장점**: 자유도.
- **단점**:
  - 입력 받는 UI 필요
  - 한글 입력 = 복잡

## 추천 (Recommendation)

**Option 1**. 3 슬롯 충분, 단순, 빠른 구현.

## 사용자 결정 (Decision)

[x] Option 1 (사용자 선택 "Save slot 확장")

## 결과 (Consequences)

### Save 파일 구조 ✅ 구현 완료

- `data/saves/gn_progress_slot_1.json` (기본, ADR-0044 마이그레이션)
- `data/saves/gn_progress_slot_2.json`
- `data/saves/gn_progress_slot_3.json`
- `data/saves/gn_progress.json` (옛 단일 슬롯, 보존)

### 신규 API (`engine/graphic_novel_save.py`) ✅ 구현 완료

- `GN_SAVE_SLOTS = 3` 상수 (line 40)
- `SAVE_SLOT_PATTERN = "gn_progress_slot_{slot_id}.json"` (line 41)
- `slot_path(slot_id: int) -> Path` (line 44) — 1-indexed
- `has_gn_save_slot(slot_id, save_dir) -> bool` (line 418)
- `save_gn_progress_slot(progress, slot_id, save_dir) -> Path` (line 432) — atomic write
- `load_gn_progress_slot(slot_id, save_dir) -> GNProgress` (line 469)
- `delete_gn_progress_slot(slot_id, save_dir) -> bool` (line 493)
- `list_save_slots(save_dir) -> list[dict]` (line 502) — `(slot_id, exists, has_save, progress, saved_at, mtime)`
- `migrate_legacy_single_slot() -> bool` (line 566) — `gn_progress.json` → `slot_1` rename (idempotent)

### Backward Compatibility ✅ 구현 완료

- 기존 `data/saves/gn_progress.json` (단일 슬롯, ADR-0044 era) — 보존
- `migrate_legacy_single_slot()` — 첫 실행 시 1회성 migration
  - `gn_progress.json` → `gn_progress_slot_1.json`로 rename
  - slot 1이 이미 존재하면 legacy는 보존 (no data loss)
  - 이후 모든 새 save는 슬롯 기반

### 신규 Screen + State ✅ 구현 완료

- `ScreenKind.SAVE_SLOT_SELECT` — `state.py:88` (3-slot picker)
- `AppState.gn_save_slot_selected: int = 0` — `state.py:265` (0=none, 1..3)
- 입력 핸들러: `engine/menu.py:389 handle_save_slot_select_input` (N1/N2/N3 → 슬롯 1/2/3, ESC → 이전 메뉴, DEL → delete)
- App dispatch: `engine/app.py:445` (render) + `engine/app.py:723` (input)

### Render (구현 완료)

- 3 슬롯 카드 형식 (`engine/app.py:445`):
  - 빈 슬롯: "EMPTY" + 메타데이터
  - 사용된 슬롯: character / ending / scene / saved_at + DEL 키
- BGM 매핑: `engine/original_story.py:382` — `finn_office` (theme)

### 영향 받는 항목

- `decisions/0044-graphic-novel-save.md` — 다중 슬롯 추가 (predecessor)
- `decisions/0051-graphic-novel-save-metadata.md` — ADR-0051은 본 ADR의 save system infrastructure (코드 주석이 ADR-0051 참조인 이유, ADR-0104 = 3-slot 확장)
- `design/scenario/graphic-novel.md` — 슬롯 UI 명세
- `tests/unit/test_graphic_novel_save.py` — 슬롯 API + 마이그레이션 (신규 ~30 tests)
- `tests/unit/test_save_slots_phase73.py` — 메인 save (10-slot + autosave, ADR-0090/Phase 7.3 — 본 ADR과 별개 시스템)

### Scripts ✅ 신규 작성

- `scripts/save_slot_demo.py` — 3 슬롯 시각 데모 (list / fill / load / delete / migrate / auto) — **2026-07-25 신규**

### 사용 예시 (Demo)

```bash
# 전체 데모 (auto)
uv run python scripts/save_slot_demo.py

# 단일 액션
uv run python scripts/save_slot_demo.py --action list
uv run python scripts/save_slot_demo.py --action fill --slot 2 --mode veteran --character-id sil
uv run python scripts/save_slot_demo.py --action load --slot 1
uv run python scripts/save_slot_demo.py --action delete --slot 3
uv run python scripts/save_slot_demo.py --action migrate
```

### Known Limitations / 향후 보강

- `test_graphic_novel_save.py`에 명시적 slot migration 테스트 추가 가능 (현 `migrate_legacy_single_slot()`는 API만 존재, 회귀 테스트 일부만 작성)
- `ScreenKind.SAVE_SLOT_SELECT`의 시각 데모는 현재 tcod headless 미지원 — `scripts/save_slot_demo.py`로 우회

## 신규 테스트

- `tests/unit/test_save_slots.py` (~30 tests):
  - `slot_path(1/2/3)` 정확한 경로
  - `save_gn_progress_slot` / `load_gn_progress_slot` round-trip
  - `has_gn_save_slot` (empty / filled)
  - `delete_gn_progress_slot`
  - `list_save_slots()` returns 3 entries (some empty, some filled)
  - Backward compat: `gn_progress.json` → `gn_progress_slot_1.json` migration
  - ScreenKind.SAVE_SLOT_SELECT exists
  - Slot rendering shows metadata

## 변경 이력

- 2026-06-21: Draft 작성
- 2026-07-25: **Accepted** — 구현 검증 완료, Consequences 실제 구현 반영 (8 files + 4 slot files + demo script). ADR-0104 (이 파일) = 3-slot 확장 / ADR-0051 (predecessor) = save infrastructure 코드 주석 참조. `scripts/save_slot_demo.py` 신규 작성.