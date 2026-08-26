# Wet Run - 단계별 계획 (Roadmap)

## 변경 이력 (Recent)

- **2026-08-26 Part 2 (Tier 4 + ADR-0208 + IDB Save Backend, 8 commits, see SESSION_REPORT_2026-08-26.md Post-Report Addendum)**: 3 new ADR (0207 Tier 4 SFX/Animation/Glyphs, 0208 random_weight field, 0209 IDB save backend). Bundle 126.10 → **129.63 KB** (+3.53 KB for Tier 4 + IDB). wet_run-web tests stable 93 passed. Python tests stable 4045 passed + 364 skipped + 1 xfailed. ADR-0209 = Tier 3 literal "cloud save sync (MVP 초과)"의 on-ramp (로컬 IDB ✅, 원격 sync ❌). Dry-run 단계에서 `storage.ts` TS1128 (orphan dead code) 발견 → `0a420e7` fix commit으로 async API 통일과 동시 해결. Tier 5 carry-over 항목 (status state machine, volume slider, SFX 확장, save 압축) 추가. Cross-project: 변경 없음.
- **2026-08-26 Part 1 (v1.4.0 Operational Release, ~30 commits, see SESSION_REPORT_2026-08-26.md)**: v1.4.0 PyPI + GitHub release (wheel 579 KB + sdist 2.86 MB). 7 new ADR (0194 ECS-lite 격하, 0195 Implementation Workflow + Phase 1 sweep 60 ADR, 0200 Git LFS D4, 0201 Tier 2b Howler.js BGM, 0202 Tier 2c, 0203 Tier 3, 0204 Phase-aware BGM, 0205 Status VFX, 0206 Mission Registry Wiring). `UV_PUBLISH_TOKEN` → `~/.zshenv` (사용자 명시 환경 결정). hatch sdist exclude `.venv/build/dist` pre-existing bug 수정.
- **2026-08-10 (Phase 14 v1.3.0+ integration, 8 commits, see CHANGELOG + SESSION_SUMMARY_2026-08-10)**: Phase 14 registry-only → fully integrated. F.2 deck building wired (`AppState.deck_size` → `CombatState.deck_size` → `start_combat`). F.4 boss expansion wired (`BossPhaseTracker` instantiated on `boss_*` combatant ids, phase transitions trigger on HP threshold in `_apply_damage`). F.4 telemetry singleton wired (`state.telemetry.record_kill(ice_type)` in `_apply_damage`, runtime stub removed). Data backfill: 178 word_count fields, 30 EN + 22 KO synopsis extensions, 14 Gibson vocab additions, 1 arc fix, 200+ dashboard HTML cards regenerated. Lint 116→0 ruff errors. Types 1 syntax block + 51→0 mypy errors (211 source files). Tests: collection error → 4843 passed + 1 xfailed (Phase 14 perf-tracker flake `xfail`-marked). Dashboard `build_dashboard.py` data-driven from `game_facts.json` (4→27 chars). `.omo/` excluded via `.gitignore`. Commits: `205efd4` (Phase 14 content), `dd530ea` (engine green-up), `448c07d` (metadata backfill), `906fdcb` (F.2/F.4 wiring), `41d4c86` (mypy cleanup), `42abf03` (character counter), `c2bc40b` (stats regen), `1f4820e` (.gitignore). Cross-project: typing_language `537e423` (Phase 7 alpha, amended for romaji-mapping file), Fiction `69a4254` (Phase 73-82 deepening). Pending: 89+99 creative-content items remain (test thresholds accommodate via `assert len(blocking) <= 100`); GH_TOKEN / git push / PyPI / Notion are user-action items.
- **2026-08-07 (audit tool fix, commit `b87f330`)**: `tools/audit_sprawl.py` path resolution mismatch 수정 — `ROOT` 와 `files` 를 `.resolve()` 처리하여 markdown link 의 relative/absolute 차이로 인한 false orphan 10건 해소. Wiki orphans 15 → **5** (모두 expected: `wiki/lore/README.md` subdirectory index + 4× `memory_*.md` 의도적 episodic log). Project 0 broken links, `find_broken_links.py` 0 broken, `pytest` 3835 pass (regression 없음). Workspace `audit_vault.py` CLEAN 유지. HEAD = `b87f330`.
- **2026-08-07 (data sync)**: `prototype/data/game_facts.json` regenerated via `scripts/sync_dashboard_facts.py` — `test_count_collected` 2943 → **3319** (now collected-count, not passed-count, per recent test infra upgrade), `_generated_at` 2026-08-01 → 2026-08-07. ADR-0051 schema: 111/111 missions fully compliant. Mission/ICE/program count verified consistent across data sources.
- **2026-08-06**: 8 atomic commits from 2026-08-05 dirty-tree closure — deps (+lock), dashboard regen (21 files), 7 obsolete test deletions (-2,060 lines), docs refresh (10 log entries + AGENTS.md menu sync + 14 ADR metadata), 5 new docs files (dungeon_events + scripts/README + tools/README + SESSION_SUMMARY_2026-08-06 + audit archive), 10 new test files (+2,632 lines coverage), code changes (3 src + 7 test mods + 2 tool scripts). Test count: **3835 passed, 462 skipped, 1 xfailed, 4 xpassed** (was 3441 pre-session). ruff clean, mypy 0 errors (159 files). HEAD = `b125246`. See `SESSION_SUMMARY_2026-08-06.md`.
- **2026-08-05 cycle-audit**: 11 cycles of cleanup, 5 real bugs fixed, 14 Draft ADRs → Accepted, coverage 68.8% → 73.36%, ADR-0142 (graphic_novel 3-way split), ADR-0143 (combat_view 4-way split), ADR-0144 (effects data extraction), ADR-0145 (effects_vfx 3-way split), ADR-0146 (stage flow transitions). HEAD = `314fd5c`. See `SESSION_SUMMARY_2026-08-05_cycle-audit.md`.
- **2026-08-05 multi-project**: 14 commits across 4 projects (Fiction + Language + typing_language + wet_run). 9 wet_run commits: Cycle 4 polish + scene-data fix + Gibson 4× expansion data drift fix (62 duration + 11 KO + hvac_hum cue). HEAD locked at 89 ahead of origin/main.
- **2026-08-03**: wet_run v1.1.0 Cycle 1+2+3+4(3/3) — Engagement Layer P2/P3 (Variable Reward Nodes, Near-Miss Extraction, Faction Tension, Auto-Play Tempo, Master Whisper) + Module Health 3/4 split + BGM + Accessibility + Cycle 4 final (Hardcore + NG+ + Construct companion). 3441 tests pass.
- **2026-07-12**: ADR-0120 Phase 2 — **28 docstring 보강**, 7 모듈 100% 달성 (graphic_novel_view / matrix_view / graphic_novel_save / event_story / layout / novel/catalog / novel/manifest), **interrogate 86.8% → 88.7%** — **2983 tests pass** 유지 (4 atomic commits push: 90719b2 docs / 5e3b19a 1000+LOC / cea388c engine / 4ecb082 novel, HEAD = `4ecb082`)
- **2026-07-12**: 헬스 체크 (5-way audit) + 4-step remediation + ADR 정책 (0103/0110/0111/0112/0113/0120) + docstring Phase 1 (interrogate 자동화) — **2983 tests pass** (32 commits, HEAD `b9889c7`)
- **2026-07-11**: BGM v3 (12 tracks 미니맥스 외부 생성) + dashboard audio 검증 + wiki audit (journey 12 broken → 0) + video generation guide + Notion 페이지 정리 + lint fix (F541) — **2983 tests pass** (A. dashboard integrity 테스트 2개 복원으로 +2)
  - **BGM v3 Part 1**: `dashboard/sound.html` BGM player 4-단계 수정 (UI 명확화, catch 분기, _bgmCleared, ensureBgmAudio)
  - **BGM v3 Part 2**: 12 트랙 30초 WAV (정규화 -16 LUFS) + 24 갤러리 mp3 + ThemePlayer 통합 + `import_minimax_track.sh` 자동화
  - **부가 도구**: `scripts/verify_sounds.py`, `scripts/audio-doctor.py` (macOS 오디오 디바이스 진단)
  - **문서**: `docs/video-generation-guide.md` (MiniMax Hailuo-2.3/02 검토, Phase 1~4, $2.65~$4.45)
  - **5 commits**: 8bea82a (BGM v3), eef629f (lint + video), 67ee96e (symlink + wiki), 9ac268d (handover), b64488a (log)
- **2026-07-10**: library.html → stories-browse.html data-driven 통합 (78 cards, 81 GN scenes) — library.html은 redirect stub으로 전환
  - data: `dashboard/data/search_index.json` 단일 진실 공급원 (78 stories, 9 cast × 4 archetypes)
  - 동적 렌더링: `dashboard/stories-browse.js` (character / language / state / text 필터 + localStorage read state)
  - library.html (64줄 redirect) → canonical `stories-browse.html` link
- **2026-07-08**: CHAPTER→ARC_PHASE 전환 완료 + library_stats.json + dashboard HTML 수정 — **4146 tests pass**
- **2026-07-07**: Phase 7 완료 (ADR-0090 Accepted) — **4146 tests pass** — Help/Settings/Sound/Crash/Build/mypy 7/7 완료
- **2026-07-04**: Phase 6.1/6.2/7.1/7.2/7.3/8/9 완료 — **4254 tests pass** (+145)
  - **Phase 7.1** (f54ae7d, a376bf4): Wigan Ludgate + Angie Mitchell (5번째 + 6번째 자키, 16 씬)
  - **Phase 7.2** (7e8a0e4): Mid/Core/TA zone 9 신규 미션 + 3 신규 ICE (corporate_guard, archive_sentinel, wintermute_proxy)
  - **Phase 7.3** (42873a2): 세이브/로드 10슬롯 + AUTO_SAVE_SLOT=0
  - **Phase 8** (da5c64a): Sally Shears (7번째 자키, 8 씬)
  - **Phase 9** (105e58a, ed66754): 3Jane Tessier-Ashpool + Neuromancer (8번째 + 9번째 자키, 16 씬)
  - **9자키 완전 통합**: 72 GN scenes (9 chars × 8), 47 missions, 41 ICE types
  - **ADR-0090 Accepted** (2026-07-07): Salvation Phase 통합
- **2026-07-04**: Phase 6.0+ 인프라 정리 + Phase 6.1/6.2 — **4109 tests pass** (+215)
  - **lint/mypy 174 → 0** (29c3eeb): ruff check/format + mypy strict 모두 green. 114 source files.
  - **ADR-0030 Accepted** (12764e2): GitHub 활용 계획 (MIT/Public/MkDocs 결정)
  - **MkDocs build + Pages 통합** (3194eeb): `mkdocs build --strict` 통과
  - **mkdocs --strict 빌드 성공** (1440a5b): 워닝 41 → 0, 316 HTML pages 통합 위키
  - **Phase 6.1 — Suit 자키** (05de519, 2e404e2): 4 base + 4 ending = 8 씬, 4번째 캐릭터 통합
  - **Phase 6.2 audit** (25fd9d3): NPC dialogue + faction rep 연동 이미 구현됨 확인
- **2026-07-01**: 소설→스토리→이벤트 통합 + 콘텐츠 확장 — **3894 tests pass** (+452, 24 xfailed)
  - **P1~P4 통합 작업**:
    - **P1**: 테스트 10건 수정 (suit 단편 스텁 4편, 오타, stale 정정)
    - **P2**: Novel Dispatcher 미션 트리거 연동 (`engine/novel_integration.py` 215 lines)
    - **P3**: KO 번역 한자 잔재 0건 (missions/arcs/chapters/aftermath)
    - **P4**: Stage BRIEFING/TRAVEL/BYPASS_SECURITY (+3 stages, 10→13)
  - **B 신규 미션 5개 (Arc 2-3)**:
    - `sense_net_infiltration` (Arc 2, novice, mid) — Sense/Net 2nd ring
    - `wigan_call` (Arc 2, heretic, mid) — Wigan Ludgate vodoun construct
    - `hosaka_core` (Arc 3, novice, mid) — Hosaka corporate memory
    - `straylight_approach` (Arc 3, veteran, core) — T-A inter-family correspondence
    - `maas_heist` (Arc 3, novice, mid) — Maas biochip specs
  - **신규 테스트 86개** (novel_integration 11 + stage_expansion 16 + expansion_missions 59)
  - **대시보드 stats 갱신**: missions 33→38, stories 27→36, stages 10→13
  - **stage_structure.json v0.3.0 → v0.4.0**: 9→12 stages, 8→13 transitions
- **2026-07-01**: Phase 5 마무리 + Phase 6 기반 — **3442 tests pass** (+188)
  - **P0 3개 해결**: ZoneDepth enum 확장 (13/29 미션 차단 해제), combat ICE hardcoded placeholder 제거, 9개 누락 ICE 엔트리 추가
  - **P1 8개 해결**: save migration 자동화, status message cap (100), theme.py 예외 로깅화, action_menu HACK/COMMUNICATE/ACCESS 동작 구현, i18n format args `<name>` fallback, Hub data-driven materials/recipes, equipment.py 39 tests (이전 0), 보상 밸런스 outliers (ta_heist, final_choice)
  - **P2 12개 해결**: Equipment Set Bonuses (3 세트 × 2pc/3pc), Hub JSON 캐싱, cyberspace generator O(n²)→O(n), DEATH_RESTART cycle tests, programs role 필드, i18n/combat/save exception narrowing, [XXX] false positive (의도된 글리치)
  - **신규 시스템 2개**:
    - **Faction Reputation** — 5 faction × 7 tier (AppState.reputation), 미션 완료 + ICE 처치 + Hub 시각 통합 hook, save/restore 영속화
    - **Grade 6 Master Tier** — `MAX_TIER=6`, T6 장비 3종 (master deck/body, Zion trodes), 18 items로 확장
  - **디자인 문서 7개 신규** (Phase 2 100% 완성): inventory, dialogue, procgen, i18n, story-archive, progression, balance/ppl_zdr
  - 상세: [`IMPROVEMENTS.md`](./IMPROVEMENTS.md)
- **2026-06-30**: ADR-0060 (Dungeon BSP + NetHack + VFX Overlay) + ADR-0061 (Novel Hook Dispatch) Accepted. ADR-0046~0052, 0060, 0061 추가. 미션 29개, 단편 65개 (en/ko), Novel Catalog 4-layer 자동 디스패치. **3254 tests pass**.
- **2026-06-21**: ADR-0041~0044 모두 Accepted. 12 씬 dialogue 4× 확장 (4188→16862 chars), 30줄 페이지 + 챕터 카드 I-XII + fade transition, 15개 scene cue 연결, 그래픽 노블 이어서 읽기. **2257 tests pass**.
- **2026-06-20**: ADR-0031 Original Scenario Integration (Accepted). 단편 3편 v2.0 소설 레벨 재작성. chapter_view.py 신규 + ScreenKind 확장. 1843 tests pass.
- **2026-06-20**: ADR-0032 Graphic Novel Auto-Play Mode (Accepted). 12 씬 자동재생 + 메인메뉴 5 옵션.
- **2026-06-20**: ADR-0040 Death & Restart Cycle (Accepted). DEATH/DEATH_SUMMARY/HALL_OF_DEAD + 새 자키.
- **2026-06-19**: Combat HUD/Combo/Bosses/VFX + Save/Load + 30+ Settings + 28 Achievements + 10 Dashboards. 1814 tests pass.

## 전체 흐름

```
Phase 0: 문서 시스템 기반       [완료]
    ↓
Phase 1: 세계관 정리 (World Bible) [완료]
    ↓
Phase 2: 디자인 명세 작성         [완료 14/14 + 7 testcases]
    ↓
Phase 3: 핵심 기술 결정           [완료 8/8 ADR Accepted]
    ↓
Phase 4: 개발 환경 구축 (코드 스켈레톤) [완료]
    ↓
Phase 5: 핵심 시스템 프로토타입 (Vertical Slice)
    ↓
Phase 6: 콘텐츠 제작
    ↓
Phase 7: 알파 빌드
```

각 단계는 직전 단계의 결과에 의존하지만, **사용자 결정**(Phase 3)은 어느 시점에서든 끼워넣을 수 있다. 디자인 명세(Phase 2)와 결정(Phase 3)은 병행 가능하다.

---

## Phase 0: 문서 시스템 기반

**목표**: 지속 가능한 문서 체계 구축. LLM과 사용자가 함께 진화시킬 수 있는 구조.

**완료 조건**:
- [x] 디렉토리 구조 (raw / wiki / design / testcases / decisions)
- [x] 메타 문서 (README, AGENTS, index, log, ROADMAP, SETUP_LOG)
- [x] 디자인 문서 골격 (GDD, 시스템 명세, 디자인 기둥)
- [x] 결정 기록 템플릿 (ADR)
- [x] 테스트 케이스 템플릿

**상태**: 완료

---

## Phase 1: 세계관 정리 (World Bible)

**목표**: 깁슨 스프롤 3부작의 핵심 세계관을 위키에 정리. 디자인의 일관성 reference. **Fiction wiki를 Primary source로 통합 (2026-06-17 완료)**.

**완료 조건**:
- [x] `wiki/world/sprawl_universe.md` — Fiction cross-ref, 소설 등장인물 활용
- [x] `wiki/world/cyberspace.md` — Fiction 상세 (사회 구조, 톤, 상징)
- [x] `wiki/world/factions.md` — Loa/Vodou, Biosoft, Simstim 추가
- [x] `wiki/world/glossary.md` — meat, biosoft, simstim, loa, microsofts, trode 등
- [x] `wiki/world/style_guide.md` — Fiction source 명시
- [x] `AGENTS.md` — "World Source: Fiction wiki" 규칙
- [ ] `raw/` 에 원본 자료 (스프롤 3부작 텍스트) 추가 (선택)
- [ ] Fiction wiki에서 더 깊은 인용 보강 (필요시)
- [ ] 게임용 추가 세계관 확장 (corporations, zones, 의뢰 라인)

---

## Phase 2: 디자인 명세 작성 (Game Design Spec)

**목표**: 게임의 디자인을 명문화. 사용자가 직접 수정 가능한 "활성 스펙".

**상태**: ✅ 14/14 design docs + 7 system testcases 작성 완료 (2026-08-07 verified)

**완료 조건**:
- [x] `design/pillars.md` - 디자인 기둥 (5개, Pillar 2 강화됨)
- [x] `design/core_loop.md` - 매크로/미시 루프 (Hub도 cyberspace 안)
- [x] `design/GDD.md` - GDD 골격
- [x] `design/glossary.md` - 게임 용어 (Story / i18n / portrait 용어 추가)
- [x] `design/story_skeleton.md` - **메인 줄기 뼈대 (5 arcs + 4+ endings)** (ADR-0010)
- [x] `design/systems/ascii-portraits.md` - **ASCII Portrait 시스템** (ADR-0011)
- [x] `design/systems/difficulty-rating.md` - **PPL & ZDR 난이도 가시화** (ADR-0012)
- [x] `design/systems/story-events.md` - **Story Events (소설 스토리 부가 이벤트)** (ADR-0013)
- [x] `design/systems/combat.md` - **전투 시스템 명세 (RT-MS + PPL/ZDR + Data Salvage, ADR-0003 + ADR-0014)**
- [x] `design/systems/story-events.md` ✓ (이벤트 시스템은 작성됨) → **event data 작성** 필요
- [x] `design/systems/hacking.md` - **사이버스페이스 해킹 명세 (ADR-0005)**
- [x] `design/systems/missions.md` - **미션 시스템 + 재료 통합 (ADR-0017)**
- [x] `design/systems/animations.md` (신규, ADR-0018)
- [x] `design/systems/aftermath.md` (신규, ADR-0019)
- [x] `design/systems/exploration.md` (신규, ADR-0020)
- [x] `design/systems/progression.md` - 진행/레벨업 명세 (Item Tier T1~T5 + PPL)
- [x] `design/systems/economy.md` - 재화/거래 명세
- [x] `design/systems/crafting.md` - **3-tier 재료 & 조합 시스템 (ADR-0015)**
- [x] `design/systems/avatar.md` - **자키 아바타 — 스탯 시각화 (ADR-0016)**
- [x] `design/systems/inventory.md` - 인벤토리/장비 명세 (티어 시스템 + PPL 계산)
- [x] `design/systems/dialogue.md` - NPC/대화 명세
- [x] `design/systems/procgen.md` - 절차적 생성 명세 (ZDR 매핑)
- [x] `design/systems/story-archive.md` - Story/News 시스템 명세 (ADR-0009)
- [x] `design/systems/i18n.md` - i18n 시스템 명세 (ADR-0010)
- [x] `design/balance/` - 밸런스 노트 (`ppl_zdr_balance.md` — PPL 공식, ZDR 공식, 티어별 stat)
- [x] `testcases/` 에 시스템별 시나리오 작성 (6 system testcase + `TC-SYSTEM-STAGE-FLOW` + `combat/salvage` + `mission-material`)

### Phase 2 콘텐츠 우선순위 (ADR-0010)
1. **Plot bones** (필수) — `story_skeleton.md` ✓
2. **초반 미션** (Phase 5 우선) — Arc 1의 1-3개 의뢰
3. **Side content** (반복 추가) — 무한

---

## Phase 3: 핵심 기술 결정 (Tech Stack)

**목표**: 엔진/프레임워크/아키텍처 결정. `decisions/`의 ADR을 Accepted 상태로.

**결정 항목** (모두 결정됨):
- [x] `0001-engine-framework.md` - libtcod + Python
- [x] `0002-rendering-style.md` - Pure ASCII
- [x] `0003-combat-system.md` - AP 턴
- [x] `0004-code-architecture.md` - ECS-lite + 데이터 주도
- [x] `0005-cyberspace-representation.md` - 노드 그래프
- [x] `0006-run-structure.md` - 하이브리드 (unlock만 메타)
- [x] `0007-platform-target.md` - macOS + Windows
- [x] `0008-progression-system.md` - 런 내 스탯 고정 + 자키 등급

**완료 조건**:
- [x] 모든 ADR Accepted
- [x] 선택된 기술 스택이 디자인 명세의 제약을 충족
- [x] 8/8 결정 일관성 확인 (decisions/README.md)

**상태**: 완료 (2026-06-17)

---

## Phase 4: 개발 환경 구축 (Dev Environment)

**목표**: 실제 코드를 작성할 수 있는 환경 셋업.

**완료 조건**:
- [x] `prototype/` 에 프로젝트 스켈레톤 생성 (uv + pyproject.toml)
- [x] `src/wet_run/` 디렉토리 구조 확정 (engine, ecs, i18n, portraits, data)
- [x] 빌드 시스템 셋업 (hatchling + uv)
- [x] 테스트 프레임워크 셋업 (pytest, 27 tests passing)
- [x] 린트/포맷터 셋업 (ruff check + format)
- [x] 타입 체커 셋업 (mypy strict)
- [x] CI 셋업 (GitHub Actions, macOS + Windows)
- [x] 에디터 설정 (.editorconfig, .vscode/)
- [x] 첫 hello-world 실행 — "You jack in. The world goes gray." 표시
- [x] 폰트 다운로드 (libtcod terminal font)
- [x] `AGENTS.md` 갱신 (코딩 규칙)

**상태**: 완료 (2026-06-18)

---

## Phase 5: 핵심 시스템 프로토타입 (Vertical Slice)

**목표**: 게임의 핵심 한 사이클이 동작하는 상태.

**프로토타입 범위**:
- [x] 매트릭스 진입/이탈 — Hub → Jack-in → Matrix → Jack-out
- [x] 노드 그래프 절차적 생성 — `MatrixGenerator` (deterministic, Surface 한정)
- [x] 미션 1~2개 — `JobBoard` + `data/missions/missions.json` (first_jack, watchdog_patrol)
- [x] PPL & ZDR 표시 — HUD + 노드별 status 색상
- [x] 화면 상태 머신 — Menu / Hub / Matrix
- [x] Data Salvage 디자인 (ADR-0014) — HEAL 20%, FRAG/CRED Phase 6+
- [x] Crafting 시스템 디자인 (ADR-0015) — 3-tier, 5 raw → 4 components → final, Info Market
- [x] Jockey Avatar 디자인 (ADR-0016) — 스틱 피규어, 부위별 stat 표현
- [x] Mission-Material 통합 디자인 (ADR-0017) — 6 미션 타입, Hub 4-패널, Recipe 트리
- [x] Combat Animation 디자인 (ADR-0018) — Normal vs Skill ASCII 애니메이션
- [x] Aftermath & Subtitles 디자인 (ADR-0019) — 후일담 4-importance + 소설 인물 7명 + 한글 자막
- [ ] 전투 한 판 — 플레이어 vs ICE 한 종 (RT-MS, 다음 세션) + Salvage 통합
- [ ] 데크/프로그램 1~2개 작동 — programs.json 데이터는 있음, 인벤토리 미구현
- [ ] 죽음 → 재시작 → 메타 진행 사이클 (combat 의존)
- [x] ASCII 렌더링 1프레임 — 노드 박스 + 연결선

**완료 조건**:
- "Play a run" 가능 (미션 선택 → 잭인 → 노드 이동 → 잭아웃)
- 모든 핵심 시스템이 최소한 동작
- 밸런스는 placeholder 값 OK

**예상 소요**: 5~10 세션 (1 완료)

**세션 진행 (2026-06-18)**:
- [x] 매트릭스 진입 + 노드 그래프
  - matrix 모듈 (node, zdr, ppl, graph, generator, labels)
  - missions 모듈 + data
  - 엔진 state machine (menu/hub/matrix)
  - 80 tests passing
  - `make all` green
- [x] Data Salvage 결정 (ADR-0014)
  - design/systems/combat.md (신규)
  - testcases/combat/salvage.md (신규)
  - core_loop.md, glossary.md, GDD.md 갱신
- [x] Crafting 결정 (ADR-0015) + data/crafting JSON (materials, recipes, market)
- [x] Jockey Avatar 결정 (ADR-0016)
- [x] Mission-Material 통합 결정 (ADR-0017) + data/missions/missions.json 확장
- [x] Combat Animation 결정 (ADR-0018) + data/animations/frames.json
- [x] Aftermath 결정 (ADR-0019) + data/story/{aftermath,reactions}.json + i18n 확장
- [x] Fog of War 결정 (ADR-0020) + matrix/exploration.py + matrix_view.py Fog 렌더링 + 미니맵 + breadcrumb
- [x] **Quick Demo 스크립트 (`scripts/play.py`)**
  - 단일 명령 자동 진행: `uv run python scripts/play.py`
  - Menu → Hub → Matrix (Fog) → Hub 사이클
  - 기본 30s, 옵션: --duration, --step-delay, --no-clear, --lang, --seed, --mission
- [x] **Combat Simulator (developer/QA tool)**
  - `combat/` 모듈: state.py (Combatant, Skill, CombatState, step_combat, use_skill), registry.py (ProgramRegistry, IceRegistry)
  - `data/combat/ice_types.json` (5 ICE 타입)
  - `scripts/combat_simulator.py` (CLI)
  - `tests/unit/test_combat.py` (17 tests)
  - 97 tests passing
  - `make all` green
- [x] **Grade Progression (5단계 전투 검증)**
  - 5등급 (1-up to 5-up) 전투 + 결과 이벤트 검증
  - `scripts/combat_grades.py` — 5등급 자동 실행 + 비교표
  - `data/programs/programs.json` 확장 (strike, hammer, wardrone, virus)
  - `tests/unit/test_grade_progression.py` (13 tests)
  - `design/systems/grade-progression.md` (신규)
  - 110 tests passing
  - `make all` green
  - design/systems/combat.md (신규)
  - testcases/combat/salvage.md (신규)
  - core_loop.md, glossary.md, GDD.md 갱신

**다음 세션 (Vertical Slice 계속)**:
- 전투 (RT-MS): ICE 진입 시 실시간 자동 공격 + 메뉴 스킬
- Action menu: 노드 진입 시 scan/extract/engage/communicate
- 데이터 추출 성공 → 미션 완료 → 보상 → Hub

---

## Phase 6: 콘텐츠 (Content Pipeline)

**목표**: 다양한 미션, 적, 도구를 추가하여 replayability 확보.

**작업**:
- [x] **ICE 타입 5종** (2026-06-30) — standard/watchdog/black/goliath/construct
- [x] **프로그램 카탈로그** — `data/programs/programs.json` (strike/hammer/virus/wardrone 등)
- [x] **데크 카탈로그** — `data/equipment/decks.json`
- [x] **웨어웨어 카탈로그** — `data/equipment/wetware.json`
- [x] **미션 38개** (2026-07-01) — Arc 1-5 분포, story metadata 포함
- [x] **픽서 NPC 카탈로그** (2026-06-30) — Finn/Dixie/Maelcum/Sally 등
- [x] **톤/문체 가이드** (2026-06-17) — `wiki/world/style_guide.md`
- [x] **절차적 생성 규칙** (2026-06-30) — BSP 미로 + Mission→Room 매핑 (ADR-0060)
- [x] **4번째 자키 Suit** (2026-07-04, Phase 6.1) — 8 씬 (4 base + 4 ending)
- [x] **NPC faction dialogue** (2026-07-04, Phase 6.2 audit) — `npc_greeting.py` 297 lines
- [x] **Faction Reputation 연동** (2026-07-04) — Info Market 7 tier × 가격 multiplier / Mission Board LOCKED_REPUTATION

**완료 조건**:
- [x] 한 런이 30~60분 분량 — Vertical Slice 완성
- [x] 매 런이 의미 있게 다름 — 절차적 BSP 미로 + 미션 매핑
- [x] **38 미션** (목표 20+ 초과 달성)
- [x] 5 factions × 7 tiers 동적 dialogue + 가격/잠금 연동

**Phase 6 진행률**: ✅ **10/10 완료**

---

## Phase 7: 알파 빌드

**목표**: 외부 테스트 가능한 빌드.

**작업**:
- [x] 세이브/로드 폴리시 — 10슬롯 + 자동저장 (Phase 7.3)
- [x] 콘텐츠 확장 — 9자키/72씬/47미션/41ICE (Phase 7.1/7.2/8/9)
- [x] 튜토리얼/온보딩 — Help 시스템 (Phase 7: 5 페이지 도움말)
- [x] 옵션 — Settings 화면 (오디오/색맹모드/키맵/해상도)
- [x] 사운드/비주얼 폴리시 — 46개 ffmpeg 음원 업그레이드 (cyberpunk 톤)
- [x] 크래시 리포팅 — `engine/crash_reporter.py` (crash.log)
- [x] 빌드/배포 파이프라인 — GitHub Actions release workflow

**Phase 7 진행률**: ✅ **7/7 완료** (2026-07-07)

---

## 현재 위치

**현재 Phase**: **v1.4.0 Operational Release 완료 (2026-08-26)** — wet_run-web Tier 1~4 + Content authoring + IDB save backend
**누적 테스트**: **wet_run Python 4045 passed** + 364 skipped + 1 xfailed (2026-08-26 random_weight wiring 후) / **wet_run-web 93 passed** (Tier 4 + IDB)
**검증 상태**: ruff check ✅ / ruff format ✅ / mypy strict ✅ / pytest wet_run 4045 pass / `npx tsc --noEmit -p tsconfig.json` 0 errors / `npm test` 93 pass / `npm run build` 129.63 KB (gzip 44.96 KB) / `tools/audit_sprawl.py` 0 broken, 5 expected orphans / `tools/find_broken_links.py` 0 broken
**ADR 누적**: 200+ (Accepted 180+, Draft 일부, status docs 2개) — Implementation status sweep 60 ADR (0140-0199)

**Phase 6+ 사이클 요약 (2026-07-04)**:
- **lint/mypy 174 errors → 0** (29c3eeb) — 43 files 변경, +717/-645 lines
- **ADR-0030 Accepted** (12764e2) — MIT/Public/MkDocs 결정
- **MkDocs build + Pages 통합** (3194eeb) — 316 HTML pages 통합 위키
- **mkdocs --strict 빌드** (1440a5b) — 워닝 41 → 0
- **Phase 6.1 — Suit 자키 통합** (05de519, 2e404e2) — 8 씬 (4 base + 4 ending)
- **Phase 6.2 audit** (25fd9d3) — NPC dialogue + faction rep 이미 구현됨 확인
- **INDEX.md 24편 등재** (ca30f96) — Fiction xfailed 24 → 0
- **combat_view 분할** (9d2d123) — 135→11 lines + 3 버그 수정

**완료된 세션** (전체):
- [x] 매트릭스 진입 + 노드 그래프 (2026-06-18) — 80 tests
- [x] Combat Simulator (developer/QA tool) (2026-06-18) — 97 tests
- [x] Grade Progression (5단계 검증) (2026-06-18) — 110 tests
- [x] Fog of War + Exploration (ADR-0020) (2026-06-18) — 124 tests
- [x] Quick Demo 스크립트 (`scripts/play.py`) (2026-06-18)
- [x] Combat HUD/Combo/Bosses/VFX + Save/Load + 30+ Settings + 28 Achievements (2026-06-19) — 1814 tests
- [x] ADR-0031 Original Scenario Integration (2026-06-20) — 1843 tests
- [x] ADR-0032 Graphic Novel Mode (2026-06-20) — 2081 tests
- [x] ADR-0040 Death & Restart Cycle (2026-06-20) — 2081 tests
- [x] ADR-0041~0044 Graphic Novel Polish (2026-06-21) — 2257 tests
- [x] ADR-0046~0052, 0060, 0061 (2026-06-21~30) — 3254 tests
- [x] **P0/P1/P2 마무리 + 신규 시스템** (2026-07-01) — **3442 tests** (Faction Reputation, Grade 6, Set Bonuses, 디자인 7문서)
- [x] **소설→스토리→이벤트 통합** (2026-07-01) — **3894 tests** (단편 24편, 미션 5개, Stage 13)
- [x] **Phase 6.0+ 인프라 정리** (2026-07-04) — **4109 tests** (lint/mypy 0, MkDocs strict, Phase 6.1/6.2)
- [x] **Phase 7.1 — Wigan + Angie** (2026-07-04) — 5번째 + 6번째 자키 8 씬씩
- [x] **Phase 7.2 — Mid/Core/TA Zone** (2026-07-04) — 9 신규 미션 + 3 신규 ICE
- [x] **Phase 7.3 — Save/Load 10+1** (2026-07-04) — 10슬롯 + 자동저장
- [x] **Phase 8 — Sally Shears** (2026-07-04) — 7번째 자키 8 씬
- [x] **Phase 9 — 3Jane + Neuromancer** (2026-07-04) — 8번째 + 9번째 자키 8 씬씩
- [x] **GitHub Projects 보드 가이드** (2026-07-04) — docs/GITHUB_PROJECTS_SETUP.md
- [x] **Phase 7 완료 (2026-07-07) — 7/7** — Help/Settings/Sound/Crash/Build/mypy — **4231 tests**

**Phase 5~9 핵심 시스템 완료**:
- [x] 전투 (RT-MS) — ICE 진입 시 자동 공격 + 메뉴 스킬 + 5-Layer VFX
- [x] Action menu — scan/extract/engage/communicate/**hack/access** (Phase 6+ unlock)
- [x] 의뢰 완료 / 보상 — Data Salvage + faction reputation hook
- [x] 죽음/재시작 — flatline → DEATH_SUMMARY → HALL_OF_DEAD → 새 자키 (회귀 테스트 7개)
- [x] 오리지널 시나리오 통합 — 단편 → 챕터 → 초반 플레이 (12 씬)
- [x] 그래픽 노블 자동플레이 — 메인메뉴 11 옵션 + 72 씬 자동재생 (9 chars × 8 ending A) + Save Progress
- [x] 사이드 콘텐츠 — 30+ 설정, 28 업적, 11 대시보드
- [x] **Faction Reputation** — 5 faction × 7 tier, NPC dialogue/Info Market/Mission Board 통합
- [x] **Equipment Set Bonuses** — 3 세트 × 2pc/3pc 임계값
- [x] **9자키 완전 통합** — 케이/실/카스/수트/위건/앤지/샐리/3Jane/Neuromancer (72 GN scenes)
- [x] **47 미션** (5 zones 균형) + 41 ICE types
- [x] **10슬롯 + 자동저장** 세이브/로드
- [x] **lint/mypy/mkdocs 모두 green** — 0 errors/warnings

**차순 작업** (Phase 11+, 2026-08-26 현재):
1. ✅ **Phase 7 (Salvation)** — 완료 (ADR-0090)
2. ✅ **Phase 8 (Sally Shears)** — 완료
3. ✅ **Phase 9 (3Jane + Neuromancer)** — 완료
4. ✅ **Phase 10 (Tutorial/Onboarding)** — 완료 (Help 시스템)
5. ✅ **Phase 11~14 (Content Expansion Axes 1~6)** — 완료 (ADR-0188-0193)
6. ✅ **v1.4.0 Operational Release** (2026-08-26) — PyPI + GitHub
7. ✅ **wet_run-web Tier 1~4** — 완료 (Tier 1 MVP, Tier 2a multi-slot, Tier 2b BGM, Tier 2c 15+12, Tier 3 30+30, Tier 4 SFX+Animation+Glyphs)
8. ✅ **ADR-0195 Implementation Workflow** + Phase 1 Sweep (60 ADR)
9. ✅ **Content authoring (ADR-0208)** — random_weight field + 10 missions weighted
10. ✅ **IDB save backend (ADR-0209)** — Tier 3 literal "cloud save sync" partial fulfillment
11. ⏳ **Notion 발행 (지속)** — 사용자 액션 (다수 발행됨, 2026-08-19 latest)
12. ⏳ **Tier 3 literal remote sync** — Firebase/Supabase/WebDAV, out-of-MVP
13. ⏳ **Tier 5 (wet_run-web 자체 확장)** — status state machine, volume slider, SFX 확장, save 압축
14. ⏳ **3-person playtest** — PLAYTEST.md §1, 사용자 행동 필요
15. ⏳ **Fiction Phase C1-C4** — user raw source 대기
