# ADR-0044: 그래픽 노블 진도 저장/복원

**상태**: Accepted
**날짜**: 2026-06-20
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

그래픽 노블 모드에서 중간에 ESC로 종료하면 **처음부터 다시 봐야 함**.
사용자가 "이어서 읽기" 옵션을 메뉴에서 선택할 수 없음.

`SaveManager`는 메인 게임 Run용 (5 slots, Player/grade/mission/credits 등).
그래픽 노블은 **read-only progress** (어느 씬/대사까지 봤는지) → 별도 처리 필요.

## 고려한 옵션

### Option 1: 전용 GN save module + 단일 슬롯 ✓ 선택

- **설명**:
  - `graphic_novel_save.py` 신규 모듈 (190 lines)
  - `GNProgress` dataclass: mode, scene_index, dialogue_index, elapsed_in_dialogue_ms, character_id, chain_length, saved_at, session_id
  - `save_gn_progress(progress)` — atomic write (temp + rename, POSIX 보장)
  - `load_gn_progress()` — version check (`GN_SAVE_VERSION = "1.0.0"`)
  - `has_gn_save()` / `delete_gn_progress()` — 빠른 존재 확인/정리
  - **저장 위치**: `data/saves/gn_progress.json` (단일 슬롯, JSON 형식)
  - **에러 클래스**: GNSaveError, GNSaveEmptyError, GNSaveVersionMismatchError, GNSaveCorruptedError
  - **버전 관리**: 마이그레이션 대비

- **장점**:
  - SaveManager와 책임 분리 (전투 vs 소설)
  - Atomic write로 interruption 안전
  - Version check로 미래 schema 변경 대응
  - 단일 슬롯 (가벼움) — 게임 save처럼 5 slots 불필요
  - 다국어 메뉴 라벨 ("CONTINUE READING" / "이어서 읽기")
- **단점**:
  - SaveManager 통합 안 됨 (별도 모듈)

### Option 2: SaveManager 통합 (5 slots, 게임 save와 함께)

- **장점**: 통합 관리
- **단점**:
  - SaveManager는 player/grade/mission 등 게임 필드를 위한 것 — GN progress와 의미 다름
  - 5 slots 불필요 (단일 슬롯이면 충분)
  - 같은 파일에 두 종류 save → 혼란

### Option 3: 메모리만 (no persistence)

- **장점**: 구현 매우 간단
- **단점**: 
  - 프로세스 종료 시 사라짐
  - 사용자가 "이어서 읽기" 못 함

## 추천 (Recommendation)

**Option 1** — 책임 분리 + 안전한 atomic write + 버전 관리.

## 사용자 결정 (Decision)

[x] Option 1 — 전용 GN save module + 단일 슬롯

## 결과 (Consequences)

### 긍정적
- **이어서 읽기** 가능 — 메인 메뉴에서 CONTINUE READING / 이어서 읽기 선택
- 게임 종료 후 재실행해도 진행 상황 유지
- Atomic write로 interruption 안전 (전원 차단, Ctrl+C 등)
- Version check로 미래 migration 지원
- 테스트로 모든 경로 검증 (24 tests)

### 부정적 / 위험
- Save 디렉토리 권한 필요 — `data/saves/` 자동 생성
- 한글 파일 경로 이슈 — Python 3.x는 UTF-8 기본 지원, 문제 없음
- 체인 길이 변경 시 (씬 추가/삭제) sanity check로 fallback — warn 메시지 출력하고 처음부터

## 영향 받는 항목
- `prototype/src/wet_run/engine/graphic_novel_save.py` — 신규 모듈
- `prototype/src/wet_run/engine/graphic_novel_view.py` — `get_gn_menu_options()`, `get_gn_menu_key()`, GN_MENU_* 상수
- `prototype/scripts/graphic_novel.py` — `--continue`, `--no-save` flag, save on exit
- `prototype/tests/unit/test_graphic_novel_save.py` — 신규 테스트 24개

## Save 포맷 (JSON)
```json
{
  "version": "1.0.0",
  "saved_at": "2026-06-20T19:39:28Z",
  "progress": {
    "mode": "novice",
    "scene_index": 0,
    "dialogue_index": 1,
    "elapsed_in_dialogue_ms": 6000.0,
    "character_id": "novice",
    "chain_length": 4,
    "saved_at": "2026-06-20T19:39:28Z",
    "session_id": "358aa8661773"
  }
}
```

## 메뉴 옵션 변화

**Before** (5 옵션):
```
[1] PROLOGUE — 3 random
[2] NOVICE
[3] VETERAN
[4] HERETIC
[5] BACK TO MAIN MENU
```

**After** (has_save=True → 6 옵션):
```
[1] CONTINUE READING    ← NEW
[2] PROLOGUE — 3 random
[3] NOVICE
[4] VETERAN
[5] HERETIC
    BACK TO MAIN MENU
```

## 실행 흐름
```bash
# 1. 처음부터 재생 → 종료 시 자동 저장
$ uv run python scripts/graphic_novel.py --mode novice --duration 2
[gn-save] Saved progress to data/saves/gn_progress.json

# 2. --continue로 이어보기
$ uv run python scripts/graphic_novel.py --continue
[gn-save] Resuming: mode=novice, scene 1, dialogue 2
 [1/4]  CHATTO'S 24/7  ·  NOVICE  ...
```

## 관련 결정
- ADR-0032 (그래픽 노블 모드) — 기반
- ADR-0041 (콘텐츠 확장) — 긴 텍스트 → 이어보기 동기 부여
- ADR-0042 (챕터 카드) — 씬 진입 시 자연스러운 재개

## 변경 이력

- 2026-06-20: Draft 작성 (Option 1 채택)
- 2026-06-20: Accepted — graphic_novel_save.py + 메뉴 통합 완료
  - `GNProgress` dataclass (frozen, slots, 8 fields)
  - `save_gn_progress()` atomic write (temp + rename)
  - `load_gn_progress()` version check
  - `has_gn_save()` / `delete_gn_progress()`
  - 4개 에러 클래스
  - 메뉴에 `CONTINUE READING` 동적 표시
  - `--continue` / `--no-save` CLI flag
  - 테스트 24개 추가 (`test_graphic_novel_save.py`)
  - **Total tests**: 2256 → **2257** (+1)