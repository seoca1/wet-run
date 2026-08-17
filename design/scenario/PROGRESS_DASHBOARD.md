# Wet Run — Project Dashboard

**Last Updated**: 2026-07-08 (Phase 7 완료 상태)
**Project Phase**: Phase 7 완료 (2026-07-07)
**참고**: Phase 4 당시 작성. Phase 7 기준으로 부분 업데이트됨. 최신 전체 진도는 `chapter-progress.md` 참조.

---

## 1. 구현 현황 요약

| 항목 | 현재 | 목표 | 진도 |
|------|------|------|------|
| 플레이어블 챕터 | **31/45** | 45/45 | **69%** |
| phases 데이터 | 45/45 챕터 | 45/45 챕터 | **100%** ✅ |
| 컷씬 참조 | 41개 | 45개 | 91% |
| Stories (단편소설) | **39 stories** (EN/KO pairs) | — | ✅ |
| 미션 수 | **47 missions** | — | ✅ |
| GN 씬 (9자키) | **72 scenes** (9×8) | 72 | **100%** ✅ |
| 케이 전체 챕터 | ✅ 25 eps, 103 beats, 8 combats | — | — |
| 실 전체 챕터 | ✅ 25 eps, 99 beats, 12 combats | — | — |
| 카스 전체 챕터 | ✅ 25 eps, 100 beats, 11 combats | — | — |
| Chapter Flow 대시보드 | ✅ 동적 로딩 | — | — |
| Story HTML | ✅ 78 files (EN↔KO) | — | **NEW** |
| ICE 스케일링 시스템 | ✅ 완비 (41 types) | — | **UPDATED** |
| 9자키 완전 통합 | ✅ Phase 7~9 | — | **NEW** |
| 검증 파이프라인 스크립트 | ✅ scripts/verify_story_pipeline.py | — | — |
| Player Status HUD | ✅ HP bar + Grade + PPL | — | — |

---

## 2. 캐릭터 출처

| 캐릭터 | 게임명 | 원작 | 출처 |
|--------|--------|------|------|
| Case | 케이 (K) | Neuromancer (1984) | 깁슨 1부작 |
| Sil | 실 (Sil) | Count Zero (1986) | 깁슨 2부작 |
| Kas | 카스 (Kas) | Mona Lisa Overdrive (1988) | 깁슨 3부작 |

**단편소설**: 오리지널 확장 스토리 (원작 에피소드 기반 + 미션 디테일/전투/대화 오리지널)

---

## 3. 단편소설 → 스테이즈 → 이벤트 → 데모 파이프라인

### 콘텐츠 출처

| 구분 | 소스 파일 | 출력 | 용도 |
|------|-----------|------|------|
| 단편소설 (Short Stories) | `data/story/chapters/*_expanded.json` | `dashboard/stories/*_{en,ko}.html` | E-book Reader HTML |
| 스테이즈 (Stages) | `dashboard/data/story/arcs/chapter_flow.json` | 동적 로딩 | 챕터 흐름 뷰어 |
| 이벤트 (Events) | `data/story/arcs/*_arc.json` | play.py 게임 루프 | 플레이어블 챕터 |
| 그래픽 노블 씬 (GN Scenes) | `data/scenes/{case,sil,kas}/*.json` | 게임 내 컷신 | 컷신 재생 |

### 파이프라인 비교표

```
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
구분                   │        단편소설 (expanded.json)       │     스테이즈 (chapter_flow)      │     이벤트 (arc.json)       │   GN 씬
──────────────────────│ episodes    beats  combats  │ chapters   phases  story_beats │ chapters   phases    beats │  count
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
  CASE                │       25      103        8  │        5       25         103  │        5       25       103  │      8
  SIL                 │       25       99       12  │        5       25          99  │        5       25        99  │      8
  KAS                 │       25      100       11  │        5       25         100  │        5       25       100  │      8
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
  합계                  │       75      302       31  │       15       75         302  │       15       75       302  │     24
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
```

### 파이프라인 상태

| 단계 | 데이터 | 상태 | 비고 |
|------|--------|------|------|
| 단편소설 작성 | expanded.json | ✅ 완전 | 75 eps, 302 beats, 31 combats, Ch5 endings 포함 |
| 스테이즈 매핑 | chapter_flow.json | ✅ 완전 | 75 phases, story_beats 참조 존재 |
| 이벤트 구현 | arc.json | ✅ 완전 | 75 phases, 302 beats 매핑 완료 |
| HTML 출력 | dashboard/stories/ | ✅ 완전 | 6개 파일 (45-52KB each) |
|Combat 시스템 | ice_types.json | ✅ 완전 | 8 types, registry 완비 |
| 검증 파이프라인 | scripts/verify_story_pipeline.py | ✅ 완전 | 5단계 자동 검증 |

**✅ Gap 해결**: Story beats 302개 → Arc beats 302개 (0 beats 미매핑)

### HTML 출력 파일

```
dashboard/stories/
├── case_en.html  (45KB) — 케이 전체 (25 episodes, 103 beats) ✅
├── case_ko.html  (50KB) — 케이 전체 (KO)
├── sil_en.html   (49KB) — 실 전체 (25 episodes, 99 beats) ✅
├── sil_ko.html   (52KB) — 실 전체 (KO)
├── kas_en.html   (44KB) — 카스 전체 (25 episodes, 100 beats) ✅
└── kas_ko.html   (49KB) — 카스 전체 (KO)
```

**생성 명령**: `uv run python scripts/generate_story_html.py --lang both`

### 대시보드 HTML 파일

| 파일 | 용도 |
|------|------|
| `dashboard/index.html` | 메인 대시보드 허브 |
| `dashboard/combat.html` | RT-MS 전투 시스템 |
| `dashboard/equipment.html` | 장비 & 제작 시스템 |
| `dashboard/player.html` | **NEW** 플레이어 스테이터스 |
| `dashboard/story_read.html` | **NEW** 에피소드/비트 단위 독서 |
| `dashboard/cyberspace.html` | 매트릭스 탐색 시스템 |
| `dashboard/sound.html` | 사운드 & 음악 |
| `dashboard/graphic-novel.html` | 그래픽 노블 (ADR-0032) |
| `dashboard/story.html` | 스토리 프로젝트 대시보드 |
| `dashboard/stories.html` | 단편소설_reader |

### 대시보드 동적 로딩

| 파일 | 출처 | 용도 |
|------|------|------|
| `dashboard/data/story/arcs/chapter_flow.json` | arc JSON + phases 메타데이터 | 챕터 흐름 뷰어 동적 로딩 |
| `dashboard/story.html` | 챕터 흐름 섹션 | 케이/실/카스 chapter flow 표시 |
| `dashboard/stages.html` | 챕터 흐름 섹션 | stages.html 내 chapter flow 표시 |
| `dashboard/story_read.html` | `*_expanded.json` | 에피소드/비트 단위 독서 |

---

## 3. 챕터별 구현 상태

### 케이 (Novice / Case) — 원작: Neuromancer

| 챕터 | playable | phases | cutscenes | 상태 | 비고 |
|------|:--------:|:------:|:----------:|------|------|
| Prologue | — | — | 1 | ✅ Done | |
| Chapter 1 | ✅ | 5 phases | 3 | ✅ Done | **메타데이터 완비** (episodes/beats/combat) |
| Chapter 2 | ✅ | 5 phases | 3 | ✅ Done | generic phases |
| Chapter 3 | ❌ | 0 | 1 | ⚪ Data only | |
| Chapter 4 | ❌ | 0 | 1 | ⚪ Data only | |
| Chapter 5 | ❌ | 0 | 1 | ⚪ Data only | |

### 실 (Veteran / Sil)

| 챕터 | playable | phases | cutscenes | 상태 | 비고 |
|------|:--------:|:------:|:----------:|------|------|
| Prologue | — | — | 1 | ✅ Done | |
| Chapter 1 | ✅ | 5 phases | 3 | ✅ Done | **메타데이터 완비** (episodes/beats/combat) (**NEW**) |
| Chapter 2 | ✅ | 5 phases | 3 | ✅ Done | generic phases |
| Chapter 3 | ❌ | 0 | 3 | ⚪ Data only | |
| Chapter 4 | ❌ | 0 | 2 | ⚪ Data only | |
| Chapter 5 | ❌ | 0 | 2 | ⚪ Data only | |

### 카스 (Heretic / Kas)

| 챕터 | playable | phases | cutscenes | 상태 | 비고 |
|------|:--------:|:------:|:----------:|------|------|
| Prologue | — | — | 1 | ✅ Done | |
| Chapter 1 | ✅ | 5 phases | 3 | ✅ Done | **메타데이터 완비** (episodes/beats/combat) (**NEW**) |
| Chapter 2 | ✅ | 5 phases | 3 | ✅ Done | generic phases |
| Chapter 3 | ❌ | 0 | 3 | ⚪ Data only | |
| Chapter 4 | ❌ | 0 | 2 | ⚪ Data only | |
| Chapter 5 | ❌ | 0 | 2 | ⚪ Data only | |

---

## 4. 완료된 작업 (전체)

**스토리 파이프라인:**
- ✅ 단편소설 전체 (3캐릭 × 5챕터 = 75 episodes, 302 beats, 31 combats)
- ✅ chapter_flow.json phases 매핑 (75 phases, story_beats 참조)
- ✅ arc.json beats 매핑 (302 beats 완전 매핑)
- ✅ PhaseData.beats 필드 추가 (BeatData 로딩)
- ✅ phase_view.py 렌더러 (arc phases/beats tcod 출력)
- ✅ HTML 스토리 출력 (6개 파일, 45-52KB each)

**play.py 게임 루프:**
- ✅ ScreenKind.ARC_PHASE + AppState 필드 추가
- ✅ CHAPTER → ARC_PHASE 전환
- ✅ ARC_PHASE 렌더링 + auto-advance (3초/beat)
- ✅ combat beat → story-mode auto-resolve (ICE Shard + 50cr)
- ✅ ARC_PHASE → HUB 완료 흐름
- ✅ GN "continue" → CHAPTER 연동 (SAVED_PROGRESS)
- ✅ ENDING screen (ScreenKind.ENDING + 5초 후 auto-return to MENU)
- ✅ GN 씬 cutscene_ref 연결 (arc JSON에 GN scene ID 매핑) **NEW**

**전투 시스템:**
- ✅ ICE 스케일링 시스템 (8 types + 21 enemy aliases, registry 완비)
- ✅ ICE 스케일링 playground 검증 (combat_grades_demo.py)

**기타:**
- ✅ 검증 파이프라인 (scripts/verify_story_pipeline.py)
- ✅ Player Status HUD 개선 (status_panel.py + hub.py)
- ✅ play_arc_chapter.py (console 데모)
- ✅ play_arc_phase.py (tcod 데모)

---

## 5. ICE 난이도 시스템

### 스케일링 공식

```
Grade > Tier: HP = hp_base + (hp_per_grade × Grade 차이)
Grade < Tier: HP = hp_base × max(0.7, 1.0 + (grade_diff × 0.15))
```

### ICE 타입 데이터 (`data/combat/ice_types.json`)

| ICE | Tier | HP Base | HP/Grade | DMG Base | DMG/Grade | 내성 |
|-----|------|---------|----------|----------|-----------|------|
| Wisp | 1 | 35 | 5 | 2 | 0 | 0% |
| Standard | 1 | 80 | 15 | 3 | 1 | 0% |
| Watchdog | 1 | 50 | 10 | 2 | 1 | 0% |
| Spider | 1 | 40 | 8 | 4 | 1 | 0% |
| Raven | 2 | 60 | 12 | 5 | 2 | 0% |
| Black | 3 | 200 | 40 | 8 | 2 | 20% |
| Goliath | 3 | 150 | 30 | 5 | 2 | 10% |
| Dixie | 4 | 300 | 60 | 6 | 3 | 30% |

### 검증 스크립트 (`scripts/verify_story_pipeline.py`)

```bash
uv run python scripts/verify_story_pipeline.py
```

출력:
```
STEP 1: 단편소설 검증 (expanded.json) — ✅ PASS
STEP 2: 스테이즈 검증 (chapter_flow.json) — ✅ PASS
STEP 3: 이벤트 검증 (arc.json) — ✅ PASS (302 beats mapped)
STEP 4: HTML 출력 검증 — ✅ PASS
STEP 5: Combat 시스템 검증 — ✅ PASS

Overall: ✅ PASS — Gap: 0 beats unmapped
```

### ICE 데모 시나리오 (`scripts/combat_grades_demo.py`)

| 시나리오 | Grade | PPL | 적 | 결과 |
|---------|-------|-----|-----|------|
| A | 1 | 6 | Wisp x1 | victory (HP 92/100) |
| B | 3 | 22 | Watchdog+Spider | 시뮬레이션 필요 |
| C | 5 | 45 | Black+Goliath | 시뮬레이션 필요 |

---

## 6. 테스트 상태

```
4106 passed ✅ (prototype/.venv pytest)
ruff: All checks passed ✅
mypy: 0 errors ✅
```

### 검증 파이프라인 스크립트

```bash
# 전체 검증 파이프라인 실행
uv run python scripts/verify_story_pipeline.py

# 출력: Step 1-5 검증 + Gap Analysis + JSON 리포트
# 리포트 저장: scripts/verification_report.json
```

---

## 7. 주요 결정 사항

| ADR | 내용 | 상태 |
|-----|------|------|
| Phase = Stage alias | backward compat 유지 | ✅ Accepted |
| ChapterState enum | PROLOGUE → ENDING_A/B/C | ✅ Accepted |
| is_playable 분기 | false = cutscene만 재생 후 스킵 | ✅ Accepted |
| cutscene_end 매핑 | 다음 챕터 start scene 재사용 | ✅ Accepted |
