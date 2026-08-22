# 챕터 구현 진도 추적표

## 문서 상태: 부분 陈旧 (2026-07-08)

> **참고**: Phase 7에서 6자키(Suit/Wigan/Angie/Sally/3Jane/Neuromancer) 추가됨.
> 현재 9자키 × 5챕터 = 45 챕터. 아래 표는 原래 3자키 (Case/Sil/Kas) 전용 — 6자키 표는 추가 필요.

---

## 개요

- **목표 (원래)**: 5챕터 × 3캐릭터 = 15 챕터 전체 구현
- **현재 (확장됨)**: 9자키 × 5챕터 = 45 챕터
- **플레이어블 챕터**: 31/45 (69%) — Suit/Wigan/Sally/3Jane/Neuromancer는 5/5, Case/Sil/Kas는 2/5
- **완료 현황**: Phase A~E + 엔진 연동 기본 (chapter_state 전환)

### 콘텐츠 출처

| 구분 | 소스 | 출력 | 용도 |
|------|------|------|------|
| 단편소설 (Short Stories) | `data/story/chapters/*.json` | `output/stories/*_{en,ko}.html` | E-book Reader 스타일 HTML |
| 그래픽 노블 씬 (GN Scenes) | `data/scenes/{case,sil,kas}/*.json` | 게임 내 컷신 | 게임 내 컷신 재생 |
| 게임 챕터 (Game Chapters) | `data/story/arcs/*_arc.json` | play.py 게임 루프 | 플레이어블 챕터 |

### 텍스트 분량

| 구분 | EN chars | KO chars | 비고 |
|------|----------|----------|------|
| 단편소설 (3개) | 4,080 | 19,637 | case=1,406 / sil=1,359 / kas=1,315 |
| GN 씬 (24개) | 44,254 | 21,220 | 3캐릭 × 8 씬 |
| **총합** | **48,334** | **40,857** | |

### HTML 출력 파일

```
output/stories/
├── case_en.html  (6.7KB) — The First Jack (EN)
├── case_ko.html  (16KB)  — 첫 잭인 (KO)
├── sil_en.html   (6.7KB) — The Old Score (EN)
├── sil_ko.html   (17KB)  — 오래된 의문 (KO)
├── kas_en.html   (6.7KB) — The Declaration (EN)
└── kas_ko.html   (21KB)  — 선언 (KO)
```

### 게임 구현 진도

| 항목 | 현재 (3자키) | 목표 (3자키) | 전체 (9자키) |
|------|------|------|------|
| 플레이어블 챕터 | 6/15 (40%) | 15/15 | 31/45 (69%) |
| phases 데이터 | 6/15 (40%) | 15/15 | 45/45 (100%) |
| 컷씬 참조 | 41개 | 45개 | 91% |

---

## 구현 진도 표

### 케이 (Novice / Case)

| 챕터 | Cutscenes | Phases | 상태 | 비고 |
|------|-----------|--------|------|------|
| Prologue | 1 | 0 | 🟢 Done | CHARACTER_SELECT → CHAPTER (play.py) |
| Chapter 1 | 2 | 5 | 🟢 Done | cutscene_start/mid 연동 완료 |
| Chapter 2 | 3 | 5 | 🟡 Partial | start+mid+end phases 완료, is_playable=true — 미션 데이터는 generic 사용 |
| Chapter 3 | 2 | 4+2 | ⚪ Future | Straylight |
| Chapter 4 | 2 | 3+2 | ⚪ Future | Flatline |
| Chapter 5 | 2 | 3+2 | ⚪ Future | Neuromancer |

### 실 (Veteran / Sil)

| 챕터 | Cutscenes | Phases | 상태 | 비고 |
|------|-----------|--------|------|------|
| Prologue | 1 | 0 | 🟢 Done | JSON 생성됨, play.py 연동 동일 |
| Chapter 1 | 3 | 5 | 🟢 Done | start+mid+end (PAYROLL) |
| Chapter 2 | 3 | 5 | 🟢 Done | start+mid+end (CONTRACT) — playable ✅ |
| Chapter 3 | 3 | 0 | ⚪ Data | start+mid+end (ERASE) — non-playable |
| Chapter 4 | 2 | 0 | ⚪ Data | start+end (BLANK) — non-playable |
| Chapter 5 | 2 | 0 | ⚪ Data | start+end (BLANK) — non-playable |

### 카스 (Heretic / Kas)

| 챕터 | Cutscenes | Phases | 상태 | 비고 |
|------|-----------|--------|------|------|
| Prologue | 1 | 0 | 🟢 Done | JSON 생성됨, play.py 연동 동일 |
| Chapter 1 | 3 | 5 | 🟢 Done | start+mid+end (DECLARATION) |
| Chapter 2 | 3 | 5 | 🟢 Done | start+mid+end (SILENCE) — playable ✅ |
| Chapter 3 | 3 | 0 | ⚪ Data | start+mid+end (WEAPON) — non-playable |
| Chapter 4 | 2 | 0 | ⚪ Data | start+end (BURN) — non-playable |
| Chapter 5 | 2 | 0 | ⚪ Data | start+end (BURN) — non-playable |

---

## 완료된 작업

### Phase A: Prologue JSON ✅

| 항목 | 상태 | 파일 |
|------|------|------|
| Prologue JSON (케이) | ✅ Done | `data/story/prologues/case.json` |
| Prologue JSON (실) | ✅ Done | `data/story/prologues/sil.json` |
| Prologue JSON (카스) | ✅ Done | `data/story/prologues/kas.json` |

### Phase B: Chapter 구조 (코드 + 데이터) ✅

| 항목 | 상태 | 파일 |
|------|------|------|
| `Phase = Stage` alias | ✅ Done | `state.py` |
| `ChapterState` enum | ✅ Done | `state.py` (PROLOGUE → IN_CHAPTER_1 → … → ENDING_C) |
| `ChapterState`, `Phase` export | ✅ Done | `run/__init__.py` |
| `ArcData`, `ChapterData`, `PhaseData`, `CutsceneRef` | ✅ Done | `chapter_cutscene.py` |
| `load_arc`, `get_arc_for_character`, `get_chapter` | ✅ Done | `chapter_cutscene.py` |
| Arc JSON (케이) | ✅ Done | `data/story/arcs/case_arc.json` |
| Arc JSON (실) | ✅ Done | `data/story/arcs/sil_arc.json` |
| Arc JSON (카스) | ✅ Done | `data/story/arcs/kas_arc.json` |
| `chapter_state` 필드 (RunState) | ✅ Done | `state.py` |
| `start_chapter_1`, `complete_chapter_1` helpers | ✅ Done | `state.py` |
| `complete_chapter_2-5`, `is_in_chapter_2-5` | ✅ Done | `state.py` |
| `start_chapter_2-5` | ✅ Done | `state.py` |

### Phase C: Cutscene 인프라 ✅

| 항목 | 상태 | 파일 |
|------|------|------|
| `load_scene` id fallback | ✅ Done | `graphic_novel_view.py` |
| `ChapterCutsceneState` (tick, advance, skip) | ✅ Done | `chapter_cutscene.py` |
| `render_cutscene_frame` | ✅ Done | `chapter_cutscene.py` |
| `get_cutscene` (scene_id → SceneData) | ✅ Done | `chapter_cutscene.py` |
| Cutscene → GN scene 매핑 | ✅ Done | `case_arc.json` |

### Phase D: 엔진 연동 (play.py) ✅

| 항목 | 상태 | 파일 |
|------|------|------|
| CHARACTER_SELECT → CHAPTER | ✅ Done | `play.py:_action_character_select` |
| CHAPTER → HUB (chapter_state=IN_CHAPTER_1) | ✅ Done | `play.py:_action_chapter` |
| `ensure_run_state` → `chapter_state=PROLOGUE` | ✅ Done | `play.py:_action_character_select` |
| `chapter_state` transitions (PROLOGUE→IN_CHAPTER_1) | ✅ Done | `play.py` |
| cutscene_start (CHATTO'S 24/7) → HUB 후 표시 | ✅ Done | `play.py:_action_hub` + `_render_current` |
| cutscene_mid (JACK-IN) → MATRIX 첫 노드 방문 후 | ✅ Done | `play.py:_action_matrix` |
| CHAPTER_END → `complete_chapter_N()` 동적 호출 | ✅ Done | `play.py:_action_matrix` (jack-out 시) |
| `chapter_cutscene_state` rendering | ✅ Done | `play.py:_render_current` |

---

## 남은 작업

### 엔진 연동 (계속)

| 항목 | 비고 |
|------|------|
| 챕터 2-5 playable 전환 | ✅ Done — is_playable=false면 cutscene만 재생 후 자동 스킵 |
| cutscene_end 재생 시점 (CHAPTER_N_COMPLETE 진입 시) | ✅ Done — _action_hub에서 COMPLETED chapter의 cutscene_end 재생 후 자동 진행 |
| CHAPTER_5_COMPLETE → ENDING_A/B/C 전환 | ✅ Done — ending_type 기반 ENDING state 전환 |
| cutscene_end 데이터 추가 | ✅ Done — 15개 챕터 모두 cutscene_end 정의됨 (arc JSON 갱신) |

### Phase E: 테스트

| 항목 | 명령 |
|------|------|
| 유닛 테스트 | `make test` |
| 린트 | `make lint` |
| 타입체크 | `make typecheck` |
| 수동 검증 | `uv run python scripts/play.py --character novice --duration 60` |

---

## 색상 키

| 색상 | 의미 |
|------|------|
| 🟢 Done | 구현 + 테스트 완료 |
| 🟡 Partial | 구현 중 (일부 완료) |
| 🔴 Not Started | 미구현 |
| ⚪ Future | 향후 작업 |

---

## 새로 작성/수정된 파일

```
data/story/prologues/          # NEW: Prologue JSON (3캐릭터)
├── case.json (EN=1,406 / KO=2,147)
├── sil.json  (EN=1,359 / KO=5,387)
└── kas.json  (EN=1,315 / KO=6,868)

data/story/arcs/               # NEW: Arc JSON (5챕터 메타데이터, 3캐릭터)
├── case_arc.json
├── sil_arc.json
└── kas_arc.json

src/engine/chapter_cutscene.py  # NEW: Chapter cutscene 인프라
src/run/__init__.py             # MOD: ChapterState, Phase export 추가
src/run/state.py               # MOD: ChapterState enum, chapter_state 필드
src/engine/graphic_novel_view.py # MOD: load_scene id fallback
scripts/play.py                # MOD: chapter_state 전환 + cutscene 연동
```
