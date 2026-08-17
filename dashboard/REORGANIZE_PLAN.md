# Dashboard Reorganization — Taxonomy & Structure Plan

## Status (2026-07-08)

### Completed
- [x] `story.html` deleted — `missions.html` (new canonical, same content)
- [x] `stories.html` deleted — `library.html` (new canonical, same content)
- [x] `novel.html` deleted — redirect to `library.html#hook-dispatch` (stub removed)
- [x] `story_read.html` deleted — `stories/episode-reader.html` (already moved)
- [x] `stories/journey/*.html` nav links updated: `../../stories.html` → `../../library.html`
- [x] `test_pages_deploy.py` updated: removed `novel.html`, `story_read.html` from `DASHBOARD_HTML_FILES`
- [x] `library.html` comment cleaned: "stories.html's" → "library.html's"

### Pending (Decisions from §7 still open)
- [x] `stories/journey/` — Decision: keep as-is. `stories/journey.html` is the canonical tabbed viewer; `journey/` subdirectory is legacy orphaned content. `library.html` journey cards updated to link to `journey.html`. (Open question 1 — resolved)

### Completed (Decisions from §7 — auto-resolved)
- [x] Statistics JSON filenames — `story_stats.json` and `novel_stats.json` were stale; `mission_stats.json` and `library_stats.json` already existed with richer content (build_dashboard.py already used new names)
- [x] Deleted stale `story_stats.json`, `novel_stats.json` (replaced by `mission_stats.json`, `library_stats.json`)
- [x] `build_dashboard.py` comment updated: old filenames removed

---

## 1. 문제 인식: Concept Overloading

현재 dashboard 페이지 이름과 실제 콘텐츠가 일치하지 않는다. 핵심 혼란:

| 현재 파일 | 실제 내용 | 문제 |
|---|---|---|
| `story.html` | 게임 미션 스토리 (47 미션 카드, arc/챕터/이벤트) | "story"라는 이름이 모호함 |
| `stories.html` | Fiction 파생 단편소설 36개 | `story`와 `stories`가 별도 콘텐츠 |
| `story_read.html` | 챕터 JSON 기반 에피소드/비트 내비게이션 | 이름이 `story.html`과 구분 안 됨 |
| `novel.html` | Novel→게임 Hook 디스패치 파이프라인 | "novel"이 원작 소설이 아님 |
| `novel_stats.json` | 사실은 단편소설(catalog) 통계 | 파일 이름과 내용 불일치 |
| `graphic-novel.html` | 81 씬 그래픽 노블 | "novel" 재사용으로 혼동 |

---

## 2. 명확한 Concept 계층 정의

```
[ vault root ]
├── Fiction/
│   ├── raw/                        ← 원본 (읽기전용)
│   │   └── William Gibson/         ← Neuromancer.txt, Count Zero.txt...
│   ├── wiki/                       ← LLM 분석 위키 (인용가능)
│   │   ├── authors/               ← william-gibson.md (1)
│   │   ├── works/                  ← neuromancer, count-zero, mona-lisa-overdrive... (7)
│   │   ├── characters/            ← 48 캐릭터
│   │   ├── settings/              ← cyberspace, the-sprawl, freeside... (11)
│   │   ├── concepts/              ← ice, wintermute, simstim... (5)
│   │   ├── themes/                ← 43 주제
│   │   ├── factions/              ← tessier-ashpool, yanaka-family (2)
│   │   └── index.md, log.md
│   └── derivative/
│       └── sprawl-trilogy/
│           ├── short-stories/      ← ★ 이차 창작 단편소설 36 stems (EN+KO pairs)
│           │   ├── 2026-06-23_*.md (41 EN files)
│           │   ├── 2026-06-23_*.ko.md (41 KO files)
│           │   └── .archive/2026-06-22/ (10 superseded v1)
│           ├── novelettes/         ← ★ 원작 발췌/확장 3개 (aleph_fragment, mollys_razor, ta_heist)
│           │   └── 2026-06-30_*.md / *.ko.md
│           ├── novellas/           ← (empty — 미사용)
│           └── INDEX.md            ← 카탈로그 인덱스
│
└── Game/wet_run/
    ├── design/                     ← 게임 디자인 문서
    │   ├── GDD.md
    │   ├── CHARACTER_PATHS.md
    │   ├── glossary.md
    │   ├── pillars.md
    │   ├── core_loop.md
    │   ├── design/systems/        ← combat.md, missions.md, i18n.md... (20)
    │   ├── design/scenario/        ← chapter-*.md, graphic-novel.md... (28)
    │   └── design/story/           ← aftermath.json, reactions.json
    │                                ← arcs/, chapters/, prologues/ (JSON)
    │
    ├── prototype/data/
    │   ├── missions/
    │   │   └── missions.json      ← 47 미션 (게임 세계관 핵심)
    │   ├── story/
    │   │   ├── arcs/              ← 9 arc JSON (kas_arc, sil_arc...)
    │   │   ├── chapters/          ← 14 챕터 JSON (case, sil_expanded, kas_expanded...)
    │   │   ├── prologues/         ← 3 프롤로그 JSON
    │   │   ├── aftermath.json     ← 엔딩 후 이벤트
    │   │   └── reactions.json     ← NPC 반응
    │   ├── scenes/                ← 그래픽 노블 씬 (9 캐릭터 × 9 씬 = 81)
    │   ├── programs/
    │   ├── combat/
    │   ├── i18n/
    │   └── ...
    │
    └── dashboard/                  ← ★ 대시보드 (이 문서의 대상)
        ├── index.html             ← 허브
        ├── data/                  ← JSON 통계 (build_dashboard.py 생성)
        │   ├── index_stats.json
        │   ├── story_stats.json   ← (이름 혼동: 실제로는 미션/단편 통계)
        │   ├── novel_stats.json   ← (이름 혼동: 실제로는 단편 카탈로그)
        │   └── ...
        └── stories/               ← 정적 HTML 파일
            ├── journey/           ← 3 캐릭터 여정 (novice/veteran/heretic)
            └── short-stories/     ← 36 단편소설 HTML (EN+KO pairs)
```

---

## 3. Proposed Concept Taxonomy for Dashboard

### 3.1 네이밍 기준

| 용어 | 정의 | 예시 |
|---|---|---|
| **Source** | Gibson 원작 (raw) | Neuromancer, Count Zero, Mona Lisa Overdrive |
| **Derivative** | Fiction 프로젝트의 2차 창작 | short-stories/*, novelettes/* |
| **Mission** | 게임 임무 (missions.json) | armitage_infiltration, ice_run |
| **Arc** | 게임 내 스토리 아크 (arc JSON) | kas_arc, sil_arc |
| **Chapter** | 챕터 (chapter JSON) | case_expanded.json, 14 files |
| **Episode** | 챕터 내 에피소드 | "The First Jack" |
| **Beat** | 에피소드 내 비트 | dialogue, combat, interior_monologue |
| **Hook** | 단편→게임 연결 (ADR-0061) | NARRATIVE, EXCERPT, EVENT, COMBAT, ITEM, CINEMATIC |

### 3.2 새로운 대시보드 카테고리 (4개)

```
Wet Run Dashboard
├── Hub (index.html)
│
├── 📖 Story Project        ← [현재: story.html + story_read.html 통합]
│   ├── 미션 목록 (47 missions → Fiction source 매핑)
│   ├── 아크/챕터 구조
│   └── 에피소드/비트 리더 (story_read.html 기능 통합)
│
├── 📚 Derivative Library   ← [현재: stories.html + novel.html 통합]
│   ├── 단편소설 (short-stories/)  ← 36 stems, EN+KO
│   ├── 노블렛 (novelettes/)       ← 3 stems, EN+KO
│   ├── Hook 카탈로그 (novel_stats.json → 재명명)
│   └── 게임 연동 상태
│
├── 🎮 Game Systems         ← [현재: combat.html, play.html, stages.html...]
│   ├── Combat (ICE, skills, programs)
│   ├── Play (미션 진행, 3×5×47)
│   ├── Stages (状态 머신)
│   ├── Cyberspace (world/sector/server/node)
│   ├── Equipment (items, crafting)
│   └── Achievements
│
└── 📊 Project Stats        ← [현재: data/*.json 통계]
    ├── 테스트 (4231 passed)
    ├── 프로그래스 (Phase 7/7)
    └── 빌드 상태
```

---

## 4. 대시보드 파일 재명명/통폐합 계획

### 4.1story.html 계열 (현재 4개 파일)

| 현재 | 제안 | 이유 |
|---|---|---|
| `story.html` | `missions.html` | 미션 스토리 프로젝트의 정체 |
| `story_read.html` | `stories/episodes.html` | 에피소드 리더reader 통합 |
| `stories.html` | `library.html` | 파생 단편소설 라이브러리 |
| `novel.html` | `library.html#hooks` (섹션 통합) | novel은 파생 단편과 같은 것 |

**이유:**
- `story.html`의 실제 내용 = missions.json 기반 미션 스토리 카드
- `stories.html`의 실제 내용 = Fiction/derivative 단편소설
- `novel.html` = ADR-0061 hook 파이프라인 (단편과 같은 출처)
- `story_read.html` = 챕터 JSON 기반 에피소드 리더 (story.html의 서브뷰)

### 4.2 통폐합 매트릭스

| 현재 파일 | 새 이름 | 유형 | 비고 |
|---|---|---|---|
| `story.html` | `missions.html` | 수정 | 미션 스토리 프로젝트 |
| `story_read.html` | `stories/reader.html` | 이동 | 에피소드 리더 |
| `stories.html` | `library.html` | 수정+병합 | 단편소설 라이브러리 허브 |
| `novel.html` | `library.html#hooks` | 병합 | Hook 파이프라인 섹션 추가 |
| `stories/journey/` | `stories/journey.html` (렌더링) | 이동 | 3 캐릭터 여정 HTML들 |
| `stories/short-stories/` | `stories/short-stories/` | 그대로 | 72개 HTML 파일 |

### 4.3 네이밍 기준

```
story     → 혼용 (과거). 미션 스토리/게임 스토리 의미.
            dashboard에서는 사용 금지.
stories   → Derivative 단편소설 컬렉션.
            "Fiction/derivative/sprawl-trilogy/short-stories/" 의 줄임말.
mission   → 게임 임무 (missions.json 의 개별 항목).
arc       → 게임 아크 (story/arcs/*.json).
chapter   → 게임 챕터 (story/chapters/*.json).
episode   → 챕터 내 에피소드.
beat      → 에피소드 내 비트 (대화/전투/내면 독백).
library   → 파생 창작물 (단편소설 + 노블렛) 통합视图.
```

---

## 5. 상세 재구성 계획

### Phase A: 네이밍 변경 (통폐합)

```html
<!-- 파일명 변경 -->
story.html       → missions.html
story_read.html  → stories/episode-reader.html
stories.html     → library.html
novel.html       → library.html#hook-dispatch (섹션으로 통합)
```

### Phase B: library.html 구조

```html
<!-- library.html = stories.html + novel.html 통합 -->
<h1>📚 Derivative Library</h1>

<!-- Tab 1: 단편소설 -->
<section id="short-stories">
  <h2>Short Stories (단편소설)</h2>
  <!-- 36 stems 카드 그리드 -->
</section>

<!-- Tab 2: 노블렛 -->
<section id="novelettes">
  <h2>Novelettes (노블렛)</h2>
  <!-- 3 novelette 카드 -->
</section>

<!-- Tab 3: Hook Dispatch -->
<section id="hook-dispatch">
  <h2>Hook Dispatch (게임 연동)</h2>
  <!-- novel.html 콘텐츠 + 117 catalog entries -->
</section>
```

### Phase C: missions.html 구조

```html
<!-- missions.html = story.html + story_read.html 통합 -->
<h1>🎯 Mission Stories</h1>

<!-- 상단: 요약 통계 (story.html 현재 stats-box) -->
<div class="stats-grid">
  <div>47 Missions</div>
  <div>14 Stages</div>
  <div>9 Arcs</div>
  <div>36 Fiction Sources</div>
</div>

<!-- 중단: 미션 카드 그리드 (story.html 현재 26개 카드 유지) -->

<!-- 하단: 에피소드 리더 (story_read.html 기능) -->
<section id="episode-reader">
  <h2>Episode Reader</h2>
  <!-- 캐릭터 탭 → 챕터 → 에피소드 → 비트 -->
</section>
```

### Phase D: 통계 JSON 파일명 정리

```json
<!-- 현재 이름 → 제안 이름 -->
story_stats.json  → mission_stats.json
novel_stats.json → library_stats.json
```

- `build_dashboard.py`의 `load_story_stats()` → `load_mission_stats()` 리네임
- `build_dashboard.py`의 `load_novel_stats()` → `load_library_stats()` 리네임
- HTML 내 `data-stat` 키도 함께 업데이트

---

## 6. 검증 체크리스트

### 파일 존재성
- [ ] 모든 새 파일 경로가 유효한지
- [ ] 내부 링크 (`href=`) 전부 업데이트
- [ ] `index.html` 네비게이션 전부 업데이트

### 데이터 무결성
- [ ] missions.json 47개 미션 → missions.html 카드 전부 렌더링
- [ ] 36 Fiction stems → library.html 단편 카드 전부 렌더링
- [ ] 3 novelette stems → library.html 노블렛 카드 전부 렌더링
- [ ] 117 catalog entries (novel_stats) → library.html#hooks 전부 렌더링
- [ ] episode-reader → chapter JSON에서 데이터 로드 확인

### 테스트
- [ ] `test_dashboard_broken_hrefs` — 모든 href 유효
- [ ] `test_dashboard_title_h1_match` — 모든 H1 일치
- [ ] `test_dashboard_no_untitled_pages` — 제목 없는 페이지 없음
- [ ] `test_dashboard_mission_coverage` — missions.json 전부 커버

### 네비게이션 일관성
```
index.html
├── missions.html          (story.html → rename)
│   └── stories/episode-reader.html  (story_read.html → move)
├── library.html          (stories.html + novel.html → merge)
│   ├── #short-stories   (단편소설 탭)
│   ├── #novelettes      (노블렛 탭)
│   └── #hook-dispatch    (novel.html → 섹션 통합)
├── systems/
│   ├── combat.html
│   ├── play.html
│   ├── stages.html
│   ├── cyberspace.html
│   ├── equipment.html
│   ├── achievements.html
│   └── settings.html
├── graphic-novel.html
└── sound.html
```

---

## 7. 미해결 질문

1. **`stories/journey/` 의 처리** — 6개 HTML 파일 (novice.html/veteran.html/heretic.html + README). 별도 페이지로 유지할지, `stories/journey.html` 단일 파일로 합칠지?
2. **`graphic-novel.html`** — "novel"이라는 이름이 novelette와 혼동. `graphic-novel.html` 유지하지만 설명을 "Visual Novel"이 아닌 "Graphic Novel"으로 명확히.
3. **통계 JSON 파일명** — `story_stats.json` → `mission_stats.json` 변경 시, `build_dashboard.py`를 수정해야 함. 이 변경을 원하는가?
4. **`novel_stats.json` 카탈로그** — 현재 36 stems (단편) + novelettes 구분 없이 단일 카탈로그. novelette를 별도 카탈로그로 분리할지?
5. **link URL 변경** — 파일명 변경 시 모든 내부 링크 수정 필요. Git 히스토리 영향.
