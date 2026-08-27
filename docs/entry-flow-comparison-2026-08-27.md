# Entry Screen + Progression Flowchart — Per-Version Comparison (2026-08-27)

**날짜**: 2026-08-27
**Scope**: 게임 진입 시 첫 화면 ASCII 아트 + Python/wet_run-web 진행 플로우차트 + 버전별 비교표
**Method**: 직접 코드 + 문서 추출 (render_menu, ScreenKind, renderMissionSelect, render_graphic_novel_menu)

---

## 1. 진입 화면 — Python (v1.4.0, Main Menu)

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                       W E T   R U N                           ║
║              A cyberpunk roguelike based on                    ║
║                  Gibson's Sprawl trilogy                      ║
║                                                                ║
║  ─────────────────────────────────────────────────────────    ║
║                                                                ║
║    > [1]  N E W   R U N            ─ 자키 선택부터 시작       ║
║      [2]  G R A P H I C   N O V E L ─ 스토리 자동재생         ║
║      [3]  C O N T I N U E          ─ 마지막 세이브 로드       ║
║      [4]  S E T T I N G S                                      ║
║      [5]  C R E D I T S                                         ║
║      [6]  H A L L   O F   D E A D  ─ 사망 자키 아카이브        ║
║      [7]  H E L P                ─ 조작법/도움말              ║
║      [8]  E N D I N G S            ─ 엔딩 브라우저 (Phase 15) ║
║      [9]  S T A T S (옵트인 시)   ─ 텔레메트리 집계 (Phase 17) ║
║                                                                ║
║  v1.4.0 · Phase α-L + Tracks A/B/D                            ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Source**: `prototype/src/wet_run/engine/menu/main_menu.py:1-30` (docstring), `:OPTION_*` constants
- **Canonical**: 9 options (NEW_RUN, GRAPHIC_NOVEL, CONTINUE, SETTINGS, CREDITS, HALL_OF_DEAD, HELP, ENDINGS, STATS)
- **STATS** 는 telemetry_opt_in 시에만 표시 (조건부)

---

## 2. 진입 화면 — wet_run-web (Tier 4, Mission Select)

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                WET RUN — Select Mission                       ║
║                                                                ║
║   ENTER: launch | ESC: quit | Arrow keys: navigate             ║
║                                                                ║
║    ▸ 1. first_jack           [T1 | 50cr]                        ║
║      2. watchdog_patrol      [T1 | 75cr]                        ║
║      3. ono_sendai_repair    [T2 | 100cr]                       ║
║      4. construct_market     [T2 | 120cr]                       ║
║      5. ghost_signal_origin  [T3 | 200cr]                       ║
║      ... (30 missions, Tier 1-5, 6 zones)                      ║
║                                                                ║
║   [HUD right] MISSION SELECT                                   ║
║              Selected: 1/30                                    ║
║                                                                ║
║   Tier 4 · ADR-0209 IDB backend                               ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Source**: `wet_run-web/src/main.ts:renderMissionSelect()`
- **Canonical**: 1 screen (mission select), 30 missions (Tier 3), 1 ICE per mission
- **No main menu** (no NEW RUN / GRAPHIC NOVEL / SETTINGS options)

---

## 3. 진행 플로우차트 — Python (v1.4.0)

```
                            ┌──────────────┐
                            │   BOOT       │
                            │   (app.py)   │
                            └──────┬───────┘
                                   │
                            ┌──────▼───────┐
                            │    MENU      │ ◄─────────────┐
                            │  (9 options) │               │
                            └──────┬───────┘               │
                                   │                       │
        ┌──────────┬──────────┬────┴────┬─────────┬────────┐
        │          │          │         │         │        │
   [1] NEW RUN  [2] GN MODE [3] CONT [4] SET [5] CRE│...
        │          │         │         │         │
        ▼          ▼         ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────┐ ┌─────┐
│ CHARACTER│ │ GN_MENU  │ │ SAVED_   │ │SET- │ │CRED-│
│ _SELECT  │ │ (4 opts) │ │ PROGRESS │ │TINGS│ │ITS  │
│ (9자)    │ │          │ │          │ └─────┘ └─────┘
└────┬─────┘ └────┬─────┘ └──────────┘
     │            │
     ▼            ▼
┌──────────┐ ┌──────────┐
│ DECK_    │ │ GRAPHIC_ │
│ SELECT   │ │ NOVEL    │
│ (light/  │ │ (auto-   │
│ standard/│ │ play)    │
│ heavy)   │ │          │
└────┬─────┘ └────┬─────┘
     │            │
     ▼            ▼
┌──────────┐ ┌──────────┐
│ BRIEFING │ │ SAVED_   │
│ (mission)│ │ PROGRESS │
└────┬─────┘ │ (continue│
     │       │  reading)│
     ▼       └──────────┘
┌──────────┐
│ TRAVEL   │
│ (matrix  │
│ → nodes) │
└────┬─────┘
     │
     ▼ (procedural BSP, surface → mid → deep → core)
┌──────────┐
│ MATRIX   │ ← events (ADR-0165)
│ (nodes)  │ ← mission discovery
└────┬─────┘
     │
     ▼
┌──────────┐
│ COMBAT   │ ← ICE encounter
│ (RT-MS)  │ ← deck cards + alarm
└────┬─────┘
     │
  ┌──┴──┐
  │     │
  ▼     ▼
┌────┐ ┌────┐
│VIC-│ │DE- │
│TORY│ │FEAT│
└─┬──┘ └─┬──┘
  │     │
  ▼     ▼
┌────┐ ┌────────┐
│RE- │ │DEATH_  │──► HALL_OF_DEAD
│WAR-│ │SUMMARY │    (6번 옵션)
│D  │ │        │
└─┬──┘ └────────┘
  │
  ▼
┌──────────┐
│ JACK_OUT │──► HUB ──► 다음 미션
└──────────┘ (or 메인메뉴)

[Hub 후 옵션: 9자키 / 47 미션 / 제작 / 인벤토리 / 종료]
```

**Source**: `prototype/src/wet_run/engine/state.py:ScreenKind`, `engine/menu/*.py`, `engine/game_structure.md`

---

## 4. 진행 플로우차트 — wet_run-web (Tier 4)

```
                          ┌──────────────┐
                          │    BOOT      │
                          │   (boot())   │
                          └──────┬───────┘
                                 │
                          ┌──────▼───────┐
                          │ MISSION_     │ ◄──────────┐
                          │ SELECT (30)  │            │
                          └──────┬───────┘            │
                                 │ [Enter]            │
                                 ▼                    │
                          ┌──────────────┐            │
                          │  APPROACH    │            │
                          │ (jacking-in) │            │
                          │  ← M 토글     │            │
                          └──────┬───────┘            │
                                 │ [Enter / 1-9]      │
                                 ▼                    │
                          ┌──────────────┐            │
                          │   COMBAT     │            │
                          │ (1 ICE,      │            │
                          │  RT-MS sim)  │            │
                          │ + deck       │            │
                          │ + alarm      │            │
                          │ + SFX/VFX    │            │
                          │ + status     │            │
                          │   glyphs     │            │
                          └──────┬───────┘            │
                                 │                  │
                            ┌────┴────┐             │
                            │         │             │
                            ▼         ▼             │
                      ┌─────────┐ ┌─────────┐       │
                      │ VICTORY │ │ DEFEAT  │       │
                      │ + creds │ │ (없음) │       │
                      └────┬────┘ └────┬────┘       │
                           │           │             │
                           ▼           ▼             │
                      ┌─────────┐ ┌─────────┐       │
                      │CONTINUE │ │ JACK_OUT│ ──────┘
                      │(next    │ │ (Q →)  │
                      │ mission)│ └─────────┘
                      └────┬────┘
                           │
                           ▼ (반복)
                      ┌─────────┐
                      │ JACK_OUT│
                      │ (Q)    │
                      └────┬────┘
                           │
                           ▼
                    (back to menu)
```

**Source**: `wet_run-web/src/main.ts:Game.handleAction`, `state.ts:applyAction`, `touch.ts:mountVirtualGamepad`

---

## 5. 화면별 비교표 (Python vs wet_run-web)

| Screen | Python (v1.4.0) | wet_run-web (Tier 4) | Status |
|---|---|---|---|
| **Main Menu** | ✅ 9 options (NEW_RUN / GRAPHIC_NOVEL / CONTINUE / SETTINGS / CREDITS / HALL_OF_DEAD / HELP / ENDINGS / STATS) | ❌ 없음 (직접 mission select로) | **Web missing** |
| **Character Select** | ✅ 9자키 풀 구현 (Case / Sil / Kas / Suit / Wigan / Angie / Sally / 3Jane / Neuromancer) | ❌ 없음 (player = 단일 runner) | **Web missing** |
| **Deck Select** | ✅ LIGHT / STANDARD / HEAVY 3 옵션 (ADR-0060) | ❌ 없음 | **Web missing** |
| **Mission Select** | ✅ JobBoard 209 미션 전체 | ✅ 30 missions (Tier 3 curated) | **Both implemented, scale differs** |
| **Briefing** | ✅ mission info panel | ❌ 없음 (직접 APPROACH) | **Web missing** |
| **Hub** | ✅ inventory + materials + recipes + NPC + Info Market | ❌ 없음 | **Web missing** |
| **Travel (Matrix Navigation)** | ✅ procedural BSP dungeon (ADR-0060) | ❌ 없음 | **Web missing** |
| **Matrix (Encounters)** | ✅ node graph + events (ADR-0165) | ❌ 없음 | **Web missing** |
| **Combat** | ✅ RT-MS + 30 programs + 97 ICE + boss 4-phase | ✅ simplified 1-ICE + 30 programs + status glyphs | **Both implemented** |
| **Data Salvage / Reward** | ✅ HEAL 15% (ADR-0152) + materials | ✅ HEAL 15% (tier-scaled) | **Both implemented** |
| **Death Summary** | ✅ DEATH_SUMMARY + restart menu | ❌ 없음 (직접 JACK_OUT) | **Web missing** |
| **Hall of Dead** | ✅ 자키 아카이브 (ADR-0040) | ❌ 없음 | **Web missing** |
| **Jack Out** | ✅ JACK_OUT 화면 → HUB | ✅ JACK_OUT → mission select | **Both implemented** |
| **Graphic Novel Mode** | ✅ 9자키 × 4 씬 × 3 endings + prologue | ❌ 없음 (gn_prologue strings key만 존재) | **Web missing** |
| **Ending Screen** | ✅ ENDING / SALVATION_ENDING (29 endings) | ❌ 없음 | **Web missing** |
| **Save / Continue** | ✅ 10+1 slots (auto + manual) | ✅ 1 autosave slot (IDB, ADR-0209) | **Both implemented, scale differs** |
| **Settings** | ✅ audio / colorblind / keymap / resolution | ❌ 없음 | **Web missing** |
| **Credits** | ✅ static HTML rendering | ❌ 없음 | **Web missing** |
| **Help** | ✅ Phase 7 onboard | ❌ 없음 | **Web missing** |
| **Endings Browser** | ✅ Phase 15 29-endings browser | ❌ 없음 | **Web missing** |
| **Stats (Telemetry)** | ✅ Phase 17 옵트인 (9번 옵션) | ❌ 없음 | **Web missing** |

### 합계

- **Python**: 19/19 screens implemented (전부)
- **Web**: 3/19 screens implemented (MISSION_SELECT, COMBAT, JACK_OUT 만)

---

## 6. 단계별 비교 (Step-by-Step)

### Python (12 stages)

```
BOOT → MENU (9 opts)
        ├→ NEW RUN → CHARACTER_SELECT (9) → DECK_SELECT (3) → BRIEFING → TRAVEL → MATRIX → COMBAT
        ├→ GRAPHIC_NOVEL → GN_MENU (4 opts) → GRAPHIC_NOVEL (auto-play 36 scenes) → SAVED_PROGRESS
        ├→ CONTINUE → SAVED_PROGRESS
        ├→ SETTINGS (sub: 7 items)
        ├→ CREDITS
        ├→ HALL_OF_DEAD
        ├→ HELP
        ├→ ENDINGS (browser 29)
        └→ STATS (옵트인)

HUB (Hub: inventory, recipes, NPC, Info Market)
        ↓
JACK_OUT (animation) ← COMBAT victory/defeat
        ↓
[repeat run cycle]
        ↓
ENDING (9 chars × 3 endings + salvation × 29)
```

### wet_run-web (4 phases)

```
BOOT → MISSION_SELECT (30)
        ↓ [Enter]
APPROACH (jacking-in transition)
        ↓ [Enter / 1-9]
COMBAT (1-ICE, RT-MS, deck, alarm)
        ↓
VICTORY / DEFEAT (no death screen)
        ↓
JACK_OUT → back to MISSION_SELECT
[no cycle — 1 mission = 1 game]
```

### 단계 수

| Tracked | Python | web | Diff |
|---|--:|--:|---|
| BOOT → 시작 화면 | 1 | 1 | = |
| 메인 메뉴 옵션 수 | 9 | 0 (직접 시작) | -9 |
| 캐릭터 선택 단계 | 3 (CS, DS, Briefing) | 0 | -3 |
| 매트릭스 단계 | 2 (Travel, Matrix) | 0 | -2 |
| 전투 단계 | 1 | 1 | = |
| 사망/엔딩 단계 | 5 (Death, Hall, End, Salv, etc.) | 0 | -5 |
| 저장/세션 단계 | 1 (Continue) | 1 (autosave) | = |
| **Total states** | **19** | **3** | **-16** |

---

## 7. 사용자 진입 시나리오 비교

### Python (5+ paths)

1. **첫 플레이**: BOOT → MENU → [1] NEW RUN → CHARACTER_SELECT (9) → DECK_SELECT → BRIEFING → TRAVEL → MATRIX → COMBAT → ...
2. **세이브 로드**: BOOT → MENU → [3] CONTINUE → SAVED_PROGRESS → last save → HUB
3. **스토리 감상**: BOOT → MENU → [2] GRAPHIC_NOVEL → GN_MENU → PROLOGUE → 36 scenes → 다른 캐릭터 옵션
4. **엔딩 감상**: BOOT → MENU → [8] ENDINGS → 브라우저 → 29 endings
5. **죽은 자키 보기**: BOOT → MENU → [6] HALL_OF_DEAD
6. **도움말**: BOOT → MENU → [7] HELP
7. **통계 (옵트인)**: BOOT → MENU → [9] STATS (telemetry_opt_in 시만)

### wet_run-web (1 path only)

1. **단일 미션**: BOOT → MISSION_SELECT (30) → [Enter] → APPROACH → [Enter] → COMBAT → [1-9 cards] → VICTORY/JACK_OUT → 반복

---

## 8. References

- **Python 진입 화면**: `prototype/src/wet_run/engine/menu/main_menu.py:1-30` (docstring + OPTION_* constants)
- **Python 진행 상태**: `prototype/src/wet_run/engine/state.py:ScreenKind` (StrEnum)
- **wet_run-web 진입 화면**: `wet_run-web/src/main.ts:renderMissionSelect()`
- **wet_run-web 진행**: `wet_run-web/src/main.ts:Game.handleAction` + `state.ts:applyAction`
- **버전 비교**: `docs/version-status.md` (Python v1.4.0 vs Web Tier 4)
- **이전 검증**: `docs/prologue-verification-2026-08-27.md` (전체 design ↔ impl 비교표 8개)
- **최신 review**: `docs/prologue-verification-2026-08-27.md §2.1` (메뉴 7~8 옵션 claim — 실제 9 옵션)