# Changelog - Roguelike Sprawl

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-12

**Status**: Production/Stable (5)
**HEAD**: `633e38e` (origin/main)
**PyPI**: https://pypi.org/project/wet-run/

### Highlights

릴리즈 후보 (v1.0.0b1, 2026-07-08) 이후 누적 변경:
- 헬스 체크 5-area audit (73 파일 uncommitted 정리)
- ADR-0103 Dungeon-only mode + 6 신규 ADR (0110-0113, 0120)
- ADR-0120 docstring 자동화 도구 도입 (interrogate 1.7.0)
- 7 모듈 docstring 100% 달성 (ADR-0120 Phase 2)
- 빌드 시스템 수정 (symlink → 실파일 + hatch exclude)
- CI 자동화 강화 (docstring coverage job)
- dashboard stale link / 카피 일괄 갱신

### Added

- **ADR-0103 Dungeon-only mode** (Accepted): D 토글 제거, `dungeon_mode` 필드 제거, `matrix_view` backward-compat 보존
- **ADR-0110 Module size policy** (250/500/1000 LOC 가이드)
- **ADR-0111-0113 graphic_novel_view / combat/effects / combat_view** (Accepted Option 4): Keep + docstring 보강
- **ADR-0120 M2 docstring batch** (Accepted Option 1): 자동화 도구 (interrogate)
- **interrogate 1.7.0** 자동화 도구 (Makefile `docstring-check` + `all` 타겟)
- **CI docstring coverage job** (`.github/workflows/ci.yml`): 80% 미만 PR 자동 차단
- **Notion 발행**: `PROGRESS_REPORT_2026-07-12_NOTION_READY.md` (페이지 `39bf643d...`)
- **빌드 수정**: `prototype/data/sounds_test/*.wav` 12개 (symlink → 실파일) + hatch exclude
- **dashboard 수정**: stale `#hook-dispatch` anchor 제거, jokey.html 카운트 오타 (47 → 15)

### Changed

- **docstring coverage**: 86.8% → **88.7%** (+1.9pp)
- **docstring 100% 모듈**: 0 → 7 (`graphic_novel_view`, `matrix_view`, `graphic_novel_save`, `event_story`, `layout`, `novel/catalog`, `novel/manifest`)
- **누적 테스트**: 4231 → **2983 passed / 679 skipped** (chapter view obsolete 후속 skip 마커)
- **ROADMAP 갱신**: 2026-07-12 entry 추가 (헬스 체크 + Docstring Phase 2)
- **SESSION_SUMMARY**: Part 6 추가 (Phase 2 결과)
- **AGENTS.md §6**: 모듈 사이즈 정책 추가 (250/500/1000)
- **wiki/style_guide.md**: CJK 혼용 방지 정책 명시

### Fixed

- **dungeon movement**: graph neighbor 기반 + backtrack (PgUp 키)
- **TRAP / RANDOM_COMBAT 이벤트**: zone 기반 확률
- **Combat tick/stack freeze**: `step_combat()` 메인 루프 호출 추가
- **Combat VFX afterimage**: `_draw_vfx_overlay` 명시적 clear
- **HACK mini-game**: System Probe (20칸 probe bar)
- **Settings crash**: `handle_settings_input` KeyUp `return state`
- **CHAPTER → ARC_PHASE 전환**: `chapter_view.py` ENTER/Space/S = HUB → ARC_PHASE

---

## [1.0.0b1] - 2026-07-08

**Status**: Beta (4)
**PyPI**: https://pypi.org/project/wet-run/1.0.0b1/

### Highlights

- 9 characters × 8 scenes = **72 graphic novel scenes** (3 endings A/B/C + Ending C 추가 후 81)
- 47 missions across 5 zones (Surface/Mid/Core/TA)
- 41 ICE types
- 10 manual + 1 auto save slots
- Salvation Phase (ADR-0090) — 9 epilogues
- v1.0.0b1 PyPI Release 성공 (GitHub Actions workflow_dispatch)

### Verified (b1 시점)

- pytest: 4146 passed / 39 skipped
- ruff + mypy strict: 0 errors
- mkdocs --strict: 0 warnings

---

## [1.0.0a1] - 2026-07-04

**Status**: Alpha (3)

초기 alpha release (PyPI 사전 발행).

---

### Added - Phase 1-5 Gameplay Expansion (ADR-0060, ADR-0061)

#### **Phase 1 — Dungeon Mode**
- `engine/state.py: AppState.dungeon_mode: bool = False` flag.
- `engine/app.py` — `D` key toggles dungeon mode in the matrix screen.
- `engine/dungeon_view.py: render_dungeon_matrix()` — 2-D grid renderer
  using `_get_room_position()` for layout.
- 8 unit tests (`tests/unit/test_dungeon_view.py`).

#### **Phase 1.5 — Combat VFX Overlay**
- 4 cinematic spawners in `combat/effects.py`:
  - `spawn_jackin_glitch()` — JAC-IN glitch burst + slow-mo.
  - `spawn_room_flash()` — short color flash on ICE clear.
  - `spawn_data_acquired()` — DATA fragment pickup VFX + cinematic.
  - `spawn_jackout_whiteout()` — JAC-OUT whiteout burst.
- Each takes a `CombatEffects` container (first positional arg).
- 12 unit tests (`tests/unit/test_combat_vfx.py`).

#### **Phase 2 — Procedural BSP Dungeon**
- `matrix/dungeon_generator.py: ProceduralDungeonGenerator` —
  BSP partition + Kruskal MST + character dead-end branching.
- Configurable `min_leaf_size` / `room_padding`.
- 23 unit tests (`tests/unit/test_procedural_dungeon.py`).

#### **Phase 3 — Mission → Room Mapping**
- `matrix/mission_mapper.py: missions_to_rooms()` — list[RoomType].
- `matrix/mission_mapper.py: mission_to_graph()` — MatrixGraph + BSP.
- Bridges `data/missions/missions.json` (16 missions) to dungeon shape.
- 31 unit tests (`tests/unit/test_mission_mapper.py`).

#### **Phase 4 — ECS Dungeon Integration**
- `ecs/room_entity.py: node_to_entity()` / `room_to_entity()`.
- `ecs/dungeon_system.py: DungeonSystem` —
  populate / on_enter / on_exit / defeat / cleared / visited.
- 22 unit tests (`tests/unit/test_dungeon_ecs.py`).

#### **Phase 5 — Novel Integration (ADR-0061)**
- New `novel/` subpackage: `NovelCatalog` / `NovelManifest` /
  `NovelDispatcher` / `NovelRuntime` / `load_novel_runtime()`.
- 6 `HookKind`s: `narrative`, `excerpt`, `event`, `combat`,
  `item`, `cinematic`. Extensible via `register_hook_action()`.
- 39 unit tests (`tests/unit/test_novel.py`).

### Added - Operator Demos

- 5 headless demos in `prototype/scripts/` to exercise Phase 1-5
  without opening a window:
  - `play_dungeon_mode.py`  (Phase 1)
  - `play_vfx_overlay.py`   (Phase 1.5)
  - `play_mission_mapping.py` (Phase 3)
  - `play_ecs_dungeon.py`   (Phase 4)
  - `play_novel_runtime.py` (Phase 5)

### Docs - Phase 1-5

- ADR-0060 (`Dungeon Exploration Redesign`) — Accepted.
- ADR-0061 (`Novel Integration Architecture`) — Accepted.
- `docs/DUNGEON_*.md` (3 files) — design + verification checklist.
- `dashboard/dungeon.html` + `dashboard/novel.html` — ADR landing pages.
- `dashboard/play.html` + `data/play_game.json` — interactive demo.
- `dashboard/README.md` — page ↔ data-source map.

## [Phase 5.1] - 2026-06-18

### Added - UX Improvements

#### **Enhanced Current Node Visibility** (5 Indicators!)
- **Bright cyan border**: `#═══║` instead of gray `+---\|`
- **Yellow text**: Node name and stats in bright yellow
- **Dark cyan background**: Interior tinted for visibility
- **Arrow markers**: `> < v ^` pointing from all 4 sides
- **"[ YOU ]" label**: Displayed above current node
- **Title bar update**: Shows "MATRIX — [Current Node Name] [Type]"
- **Impossible to miss**: Multiple redundant visual cues

#### **Comprehensive Status System**
- **Real-time action feedback**: Every player action now shows a status message
- **Status message log**: Messages appear in footer (last 20 stored)
- **Context-aware indicators**: Clear indication of what each action does

#### **Matrix Screen Enhancements**
- **Current node status panel** (Side):
  - Node name and type
  - ZDR and combat status
  - Context-specific instructions ("→ SPACE: Extract data")
  - Visited node counter
- **Movement feedback**: Shows direction and destination
  - ">>> Moved ↑ UP to DATA-7F (Data)"
  - ">>> No node in direction ← LEFT"
- **Action feedback**: Confirms every action
  - ">>> SCAN: DATA-7F (data)"
  - ">>> EXTRACT: Data retrieved from DATA-7F"
  - ">>> ENGAGE: Initiating combat with ICE-Guardian"
- **Dynamic controls**: Bottom bar shows context-specific hints
  - At DATA node: "SPACE: Extract data (mission objective)"
  - At ICE node: "SPACE: Engage ICE (combat)"
  - At EXIT node: "SPACE: Jack out (exit matrix)"

#### **Combat Screen Enhancements**
- **Skill selection feedback**:
  - ">>> Selected: ICE BREAKER"
  - ">>> Used skill: ATTACK"
- **Error feedback** when skill unavailable:
  - ">>> ICE BREAKER on cooldown (1.5s)"
  - ">>> Not enough AP (2/3)"

#### **Visual Improvements**
- Clearer "WHAT TO DO" section in side panels
- Arrow symbols in movement messages (↑ ↓ ← →)
- Action-specific control hints
- Real-time cooldown display in skills menu

### Changed
- Matrix action menu now opens with **SPACE** instead of ENTER (more intuitive)
- Footer now displays most recent status message alongside step counter
- Side panels prioritize current context over generic info

### Technical
- Added `engine/logger.py` - Centralized logging system (not yet integrated)
- Added `AppState.status_messages` - In-game message queue
- Added `AppState.context_hint` - Dynamic help text
- Updated `layout.py:draw_footer()` - Supports status messages
- Enhanced all input handlers with status logging

---

## [Phase 5.0] - 2026-06-18

### Added - Arrow Key Navigation

#### **Complete Menu Navigation**
- **Matrix Action Menu**:
  - ↑↓ to select action
  - ENTER to confirm
  - Visual cursor (`>`) shows selection
  - Color coding: Cyan (selected), White (available), Gray (locked)
  - `[LOCKED]` indicator for Phase 6+ features

- **Combat Skill Menu**:
  - ↑↓ to select skill
  - ENTER to use skill
  - Real-time cooldown display
  - Visual feedback for disabled skills
  - Cooldown shown as `[1.5s]`
  - AP cost shown as `[2 AP]`

#### **Visual Distinction System**
- **Colors**:
  - Cyan `(0, 255, 255)` - Selected item
  - White `(200, 200, 200)` - Available
  - Dark Gray `(80, 80, 80)` - Disabled/Locked/Cooldown
- **Cursor**: `>` marks current selection
- **Status indicators**:
  - `[X AP]` - Action Point cost
  - `[X.Xs]` - Cooldown remaining
  - `[LOCKED]` - Feature not yet implemented

#### **Cooldown System**
- Skills now have proper cooldowns
- Cooldowns tracked in `CombatState.skill_cooldowns`
- Real-time countdown displayed
- Auto-decremented each combat tick

#### **State Management**
- `AppState.action_menu_index` - Action menu selection
- `AppState.combat_skill_index` - Skill menu selection
- `CombatState.skill_cooldowns` - Per-skill cooldown tracking

### Changed
- Number/letter shortcuts (1-9, S, E, J) still work (legacy support)
- Controls footer updated to show arrow key hints
- Menu rendering now shows selection state

### Documentation
- Added `CONTROLS.md` - Complete controls reference
- Updated `DEMO_GUIDE.md` - Arrow key navigation examples
- Updated `README.md` - Quick controls summary

---

## [Phase 5.0 Beta] - 2026-06-18 (Earlier)

### Fixed
- **Font charmap issue**: Changed `CHARMAP_CP437` → `CHARMAP_TCOD`
  - Fixed garbled text in all screens
  - Affects: `app.py`, `test_tcod.py`, `full_demo.py`, `prologue.py`
- **Tileset indentation error**: Fixed `tileset` loading in demo scripts

### Added
- `scripts/text_demo.py` - Text-only story viewer (no graphics)
- `scripts/test_tcod.py` - Font rendering diagnostic tool
- `DEMO_GUIDE.md` - Complete playthrough guide (391 lines)

---

## [Phase 5.0 Alpha] - 2026-06-17

### Added - Full Game Flow Demo

#### **Cinematic Story System**
- Typing effects (3 speeds: INSTANT, FAST, NORMAL, SLOW)
- Glitch effects (random cyberpunk visual corruption)
- NPC portraits (ASCII, e.g., `♠F♠` for Finn)
- Bilingual support (English + Korean placeholders)

#### **Story Scenes**
- **Prologue**: Gibson's iconic opening (6 story lines)
- **Briefing - The Finn**: First mission briefing (5 story lines)

#### **Game Flow Integration**
- Seamless transitions: Prologue → Briefing → Matrix → Combat
- Auto-progression between scenes
- `scripts/full_demo.py` - Complete demo experience

#### **Demo Variants**
- `make demo` - Standard speed
- `make demo-fast` - 3x faster typing
- `make demo-skip` - Skip prologue

---

## [Phase 4] - Earlier

### Implemented
- Matrix exploration (5x5 grid, fog of war)
- RT-MS combat system
- Hub screen (4-panel layout)
- Action menu system
- ECS architecture
- 124 unit tests

---

## Version History

- **Phase 5.1** - UX Improvements (Status system, Context-aware UI)
- **Phase 5.0** - Arrow Key Navigation + Full Game Flow Demo
- **Phase 4** - Core Systems (Matrix, Combat, Hub)
- **Phase 3** - ECS Architecture
- **Phase 2** - Basic Combat
- **Phase 1** - Project Setup

## [Phase 5.2] - 2026-06-18 - Sound System

### Added - Audio Integration (Phases 1-6 Complete)

#### **SoundManager Core** (`src/wet_run/audio/sound_manager.py`)
- 267 lines, zero external Python dependencies
- Cross-platform: macOS (afplay), Linux (aplay), Windows (winsound)
- Auto-generates 27 placeholder WAVs on first use (synthesized via `wave` module)
- Thread-safe, non-blocking playback with subprocess management
- Volume (0.0-1.0, clamped), mute toggle, master controls

#### **Sound Categories** (27 sounds across 5 categories)
- **UI** (5): menu_select, menu_confirm, menu_cancel, error, notification
- **Story** (3): text_typing, dialogue_advance, event_trigger
- **Combat** (12): hit_normal, hit_crit, hit_miss, skill_physical, skill_magic,
  skill_heal, skill_buff, skill_debuff, block, stun, victory, defeat
- **Movement** (4): nav_step, jack_in, jack_out, nav_block
- **Items** (3): equip, pickup, cant

#### **Settings UI** (`src/wet_run/engine/settings_ui.py`)
- `get_volume()`, `set_volume()`, `adjust_volume(±delta)` helpers
- `is_muted()`, `toggle_mute()` helpers
- `render_settings_overlay()` for HUD display
- Global hotkeys wired in `app.py`:
  - **M** = Toggle mute
  - **+** / **=** = Volume up
  - **-** = Volume down

#### **Engine Integration** (7 modules)
- `story_cinematic.py` - typing + event trigger sounds
- `combat_view.py` - 14 SkillEffect types mapped to sounds
- `cyberspace_browser.py` - jack-in on server select
- `cyberspace_view.py` - nav_step + nav_block feedback
- `action_menu.py` - menu select/cancel
- `npc_view.py` - dialogue navigation
- `hub.py` - mission select (helper)
- `status_panel.py` - AUDIO section at bottom of right panel

#### **safe_play() Helper**
- Single entry point for engine modules
- Swallows all exceptions (sound must never break gameplay)
- Replaces 7 duplicate `_play_*_sound` helpers

#### **Testing**
- `tests/unit/test_sound_manager.py` - 12 tests (manager, volume, mute, play)
- `tests/unit/test_settings_ui.py` - 8 tests (volume adjust, mute toggle, clamp)
- All 144 tests passing (was 124, +20 new)

#### **Makefile Targets**
- `make sound-test` - Check audio backends
- `make sound-manager` - Run sound tests
- `make sound-demo` - Play all 27 sounds
- `make sound-demo-full` - Full game demo with sound
- `make sound-clean` - Remove generated WAVs

### Documentation
- `SOUND_PLAN.md` - All 6 phases checked, status section added

### Verified
- **mypy strict**: 0 errors (61 source files)
- **ruff**: 0 issues
- **pytest**: 144/144 passing
- **sound assets**: 27/27 auto-generated

## [Phase 5.3] - 2026-06-18 - Jockey Avatar (ADR-0016)

### Added - Avatar System

#### **`src/wet_run/avatar/`** module
- `state.py` - Data models: AvatarState, ProgramSlot, Status, ConstructKind, AvatarLines
- `renderer.py` - Pure ASCII stick-figure renderer with color palette
- `__init__.py` - Public API exports

#### **Head (HP) Visualization**
- 100% HP: `◉P◉` (green, full integrity)
- 75% HP: `◉P·` (yellow-green)
- 50% HP: `◉P/` (yellow, tilted/glitching)
- 25% HP: `◉Px` (red, critical)
- 0% HP: `X` (dark red, flatline)

#### **Body Pose (Status)**
- SAFE / MATCH / TOUGH: upright ` /|\ ` / ` \|/ `
- DEADLY: crouched ` /\ ` / ` \/ `
- FUTILE: glitching ` .\ ` / ` /, `

#### **Program Arms (Tier + State)**
- T5: `★X★` (starred, gold)
- T4: `▓X▓` (filled, purple)
- T3: `|X|` (double border, cyan)
- T2: `:X:` (single border, gray)
- T1: `·X·` (faded, dim)
- Depleted: `~X~` (one-shot used)
- Empty/locked: `═══` (meta-progression)

#### **Deck & Wetware**
- Deck: `║DK{N}║` (torso, tier shown)
- Wetware: `▓▓▓▓` (legs, count = tier)

#### **Construct Companion** (echo)
- Dixie: `◆D◆`
- Loa: `◯L◯`
- 3Jane: `▲▲J▲▲`

#### **Public API**
- `render_avatar_lines(state)` -> AvatarLines (text + color)
- `render_avatar(console, x, y, state, border=True)` - direct console rendering
- `build_avatar_state(hp, max_hp, ppl, zdr, ...)` - from raw game values

### Testing
- `tests/unit/test_avatar.py` - 28 tests covering:
  - 4 HP state visualizations
  - 5 status pose mappings
  - 5 program tiers
  - Depleted state
  - Empty/locked slot
  - Deck tier (T0-T5)
  - Wetware tier (T0-T5)
  - 3 construct kinds
  - 4 integration scenarios (full, damaged, critical, dead)
  - 6 state property tests

### Demo
- `scripts/demo_avatar.py` - 6 scenarios + reference tables

### Verified
- **mypy strict**: 0 errors (64 source files)
- **ruff**: 0 issues
- **pytest**: 172/172 passing (was 144, +28 new)

---

## [Phase 6] - 2026-06-20 to 2026-06-30

### Added - Content Pipeline (ADR-0031, ADR-0032, ADR-0040-0052)

#### **Graphic Novel Mode** (ADR-0032)
- 12 scenes (4 characters × 4 scenes) auto-play with typed dialogue
- Main menu expanded to 5 options: NEW RUN, GRAPHIC NOVEL, CONTINUE, SETTINGS, CREDITS
- Save progress after graphic novel completion
- 40 new tests (`test_graphic_novel_view.py`)

#### **Death & Restart Cycle** (ADR-0040)
- DEATH / DEATH_SUMMARY / HALL_OF_DEAD screens
- `jockey_history.py` — Hall of Dead Jockeys archive
- Restart options: New jockey, Same character, Quit
- 7 regression tests

#### **Scene Transitions** (ADR-0041, ADR-0042)
- Chapter title cards (Roman numerals I-XII)
- Fade transitions between scenes
- 15 sound cue → file mappings (ADR-0043)

#### **Ending B** (ADR-0046) + **Ending C** (ADR-0049)
- 6 new scenes for alternative endings (Disappear/Erase/Burn)
- 9 ending combinations per character
- Save format v1.1.0 → v1.2.0 migration

#### **Sound System** (ADR-0043)
- `graphic_novel_audio.py` — scene-level sound cue resolver
- 46 WAV files in `sounds_test/` (combat/UI/movement/story/themes)
- Per-category volume control (T/E/K/B/V/I keys)

#### **Core Content**
- 5 factions × 7 reputation tiers
- NPC greeting system (`npc_greeting.py`)
- Mission reputation locks + Info Market faction discounts
- Equipment set bonuses (3 sets × 2pc/3pc thresholds)

### Verified - Phase 6 End
- **mypy strict**: 0 errors (114 source files)
- **ruff**: 0 issues
- **pytest**: 2257/2257 passing (was 172, +2085 new)

---

## [Phase 7] - 2026-07-01 to 2026-07-07

### Added - Alpha Build (Phase 7.1-7.3)

#### **Save/Load Policy Expansion** (Phase 7.3)
- `MAX_SLOTS = 10` (was 5)
- `AUTO_SAVE_SLOT = 0` — separate auto-save slot
- `autosave()`, `has_autosave()`, `list_all()` methods
- 8 new tests (`test_save_slots_phase73.py`)

#### **Zone Content Expansion** (Phase 7.2)
- 9 new missions in MID/CORE/TA zones
- 3 new ICE types: `corporate_guard`, `archive_sentinel`, `wintermute_proxy`
- 47 total missions (surface 12 / mid 9 / deep 10 / core 7 / freeside 5 / ta 4)

#### **Tutorial / Help System** (Phase 7)
- `engine/help_view.py` — 5-page help (Universal/Matrix/Combat/Concepts/Mission Flow)
- `engine/state.py` — `ScreenKind.HELP`, `help_page` attribute
- N7 key → Help from menu

#### **Settings Screen** (Phase 7)
- `engine/settings_view.py` — 5 options (Audio/Colorblind/Keymap/Resolution/Back)
- Audio volume slider (20 steps, ± keys)
- Colorblind mode toggle
- `engine/state.py` — `ScreenKind.SETTINGS`, `settings_selected`, `colorblind_mode`

### Added - Alpha Build (Phase 7.4)

#### **Sound Upgrade** (Phase 7.3)
- `scripts/upgrade_sounds.py` — ffmpeg-based cyberpunk sound generator
- 46 improved WAV files with distortion/tremolo/bandpass/afade filters
- Categories: combat (12), UI (5), movement (10), story (3), items (3), themes (12)

#### **Crash Reporter** (Phase 7.3)
- `engine/crash_reporter.py` — `report_crash(exc, state, message)`
- Writes to `data/saves/crash.log` with timestamp + stack trace + state snapshot
- Integrated into `main()` and game loop

#### **Build / Release Pipeline** (Phase 7.4)
- `.github/workflows/release.yml` — GitHub Actions release workflow
- Builds wheel + tarball on tag push
- TestPyPI + PyPI publishing via OIDC (no passwords)
- Wheel verification step

### Fixed - Phase 7
- `help_view.py`: `event.keysym` → `event.sym`, `main_r.height` → `main_r.h`
- `settings_view.py`: `main_r.height` → `main_r.h`, `draw_controls` API correct usage
- `play.py`: duplicate function definition, f-string quote conflict

### Verified - Phase 7 End
- **mypy strict**: 0 errors (118 source files)
- **ruff**: 0 issues
- **pytest**: 4231/4231 passing (was 2257, +1974 new)

---

## [Phase 8] - 2026-07-04

### Added - Sally Shears (7th Jockey)
- `data/scenes/sally/` — 8 scenes (4 base + 4 ending)
- Character label: "Sally — Market Operator" / "샐리 — 시장 운영자"
- 1st-person cold operator perspective
- 14 new tests (`test_sally_character.py`)

### Verified
- **pytest**: 4169/4169 passing (+14 new)

---

## [Phase 9] - 2026-07-04

### Added - 3Jane Tessier-Ashpool + Neuromancer (8th + 9th Jockeys)

#### **3Jane** (8th Jockey)
- `data/scenes/3jane/` — 8 scenes (4 base + 4 ending)
- Character label: "3Jane — Family Heir" / "3Jane — 가족의 후계자"
- 1st-person aristocratic perspective (royal "we")
- 14 new tests (`test_3jane_character.py`)

#### **Neuromancer** (9th Jockey)
- `data/scenes/neuromancer/` — 8 scenes (4 base + 4 ending)
- Character label: "Neuromancer — Merged AI" / "뉴로맨서 — 합체된 AI"
- 1st-person AI perspective (vast, clinical, omniscient)
- 12 new tests (`test_neuromancer_character.py`)

### Added - Salvation Phase Integration (ADR-0090)
- `ChapterState.SALVATION_INTRO / EPILOGUE / DONE / FINAL`
- `Stage.SALVATION_EPILOGUE`
- `engine/salvation.py` — SalvationRunner (9-character epilogue selection/playback/ending)
- 9 × `09_epilogue.json` scene files
- 40 tests (`test_salvation.py`)

### Verified - Phase 9 End
- **pytest**: 4196/4196 passing (+27 new since Phase 8)
- **9 characters × 8 scenes = 72 GN scenes total**

---

## [Phase 10] - 2026-07-07

### Added - Phase 7 Completion

#### **All Phase 7 Items Done** (7/7)
- Save/Load policy (10 slots + auto) ✅
- Content expansion (9 chars / 72 scenes / 47 missions / 41 ICE) ✅
- Tutorial / Help system ✅
- Settings screen ✅
- Sound/Visual policy (ffmpeg cyberpunk sounds) ✅
- Crash reporting (crash.log) ✅
- Build/Deploy pipeline (GitHub Actions release workflow) ✅

### Final Metrics (Phase 7 완료 시점, 2026-07-07)
- **9 characters** (Case/Sil/Kas/Suit/Wigan/Angie/Sally/3Jane/Neuromancer)
- **72 graphic novel scenes** (9 chars × 8 scenes, Phase 9 후 81)
- **47 missions** (5 zones balanced)
- **41 ICE types**
- **10 manual + 1 auto save slots**
- **4231 tests passing** (Phase 7 시점 — 후속 작업 후 2983으로 변경)
- **mypy strict**: 0 errors | **ruff**: 0 issues | **mkdocs --strict**: 0 warnings
- **60+ ADRs** all Accepted

> **Note**: 본 Phase 10 항목의 4231 tests는 Phase 7 시점 누적입니다.
> 후속 헬스 체크 + Docstring Phase 2 + 회귀 제거 작업으로 [1.0.0] 시점에 2983 passed / 679 skipped 으로 변경됨.
