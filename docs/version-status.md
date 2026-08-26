# Wet Run — 버전 명칭 표준 + 트랙별 상태 비교

**날짜**: 2026-08-27
**Scope**: 두 트랙의 버전 명칭 표준화 + 상태 비교표 + 메뉴/플로우 비교
**대상 독자**: 신규 contributor, version-history 후속 작업자, Notion 동기화 자동화

---

## 1. 버전 명칭 표준 (Canonical Nomenclature)

Wet Run은 **두 개의 동시 진행 트랙**으로 구성된다. 두 트랙의 명명 규칙은 의도적으로 다르다.

### 1.1 wet_run (Python 데스크탑 게임)

> **표준**: [SemVer](https://semver.org/) 기반 — `MAJOR.MINOR.PATCH` + 선택적 pre-release suffix.

| 토큰 | 의미 | 예시 |
|---|---|---|
| **MAJOR** | 호환성 깨는 변경 (save format, 핵심 시스템 재설계) | `1.x.x → 2.x.x` |
| **MINOR** | 새 기능, ADR- 여러 개 묶음 | `0.7.11 → 1.0.0 → 1.1.0 → 1.4.0` |
| **PATCH** | 버그 수정, polish | (현재 미사용) |
| **pre-release suffix** | `-a1` (alpha), `-b1` (beta) | `1.1.0a1` |
| **+Phase suffix** | 작업 묶음 (Phase α-L, 14 등) | `v1.3.0+` |

**현재 최신**: `v1.4.0` (PyPI released 2026-08-26)

**Phase 표기** (작업 단위, 버전과 무관):
- **Phase α-L** (2026-07-26): 첫 cross-project 통합
- **Phase 14** (2026-08-10): Endings/Programs/Equipment/Story events/Boss expansion wiring
- **Tracks A/B/C/D** (2026-08-20): Quality Upgrade (A.4 module splits, B.9 ADR integrations, C content verified, D.5 meta, E.4 release prep)

### 1.2 wet_run-web (브라우저 MVP)

> **표준**: ADR-0199 기반 **Tier 시스템** — `Tier X.Y` (major.minor feature tier). SemVer 미사용.

| 토큰 | 의미 | ADR |
|---|---|---|
| **Tier 1** | MVP — 미션 선택 → 1 전투 → 승리 | ADR-0199 |
| **Tier 2a** | Multi-slot save (4 slots) | ADR-0200 범위 외 |
| **Tier 2b** | Howler.js BGM (단일 BGM, M 토글) | ADR-0201 |
| **Tier 2c** | Mission + ICE 다양성 (15+12) | ADR-0202 |
| **Tier 3** | 30+30 mission/ICE expansion | ADR-0203 |
| **Tier 4** | SFX + Animation VFX + Status glyphs | ADR-0207 |
| **Tier 5+** | (deferred) state machine 통합, fade, save 압축 | ADR-0207 §"향후 결정" |

**Tier 외 표기**:
- **ADR-0209** (2026-08-26): IndexedDB save backend — Tier 3 literal "cloud save sync"의 on-ramp
- **ADR-0208** (2026-08-26): Mission `random_weight` field

**현재 최신**: `Tier 4 + ADR-0209 IDB` (2026-08-26 deployed at `seoca1.github.io/wet-run/wetrun-web/`)

### 1.3 두 트랙의 매핑 (Cross-Reference)

| wet_run (Python) | wet_run-web (browser) | 동시 작업 |
|---|---|---|
| v0.7.11 (2026-07-10) | (pre-Tier 1, 미존재) | Phase α 시작 |
| v1.0.0 FINAL (2026-07-27) | Tier 1 시작 (ADR-0199 Draft) | Phase 14 시작 |
| v1.1.0a1 (2026-07-28) | Tier 1 MVP | alpha |
| v1.1.0 (2026-08-17) | Tier 1 → Tier 2a (multi-slot) | Project rename |
| v1.3.0+ (2026-08-10) | Tier 2b BGM (ADR-0201) | Phase 14 wiring |
| **v1.4.0 (2026-08-20)** | **Tier 2c/3/4 + ADR-0209** | Operational Release |

**핵심**: 두 트랙은 **독립적인 릴리스 사이클**을 가진다. Python 메이저 릴리스 (v1.4.0)와 web tier 진척 (Tier 1→4)은 같은 날 발생할 수 있다.

---

## 2. wet_run (Python) 버전별 상태 비교

### 2.1 마일스톤 요약

| 버전 | 날짜 | Phase/Track | 핵심 변경 | Tests | Status |
|---|---|---|---|--:|---|
| **v0.7.11** | 2026-07-10 | Pre-α | Cross-project 초기, orphan 19, app.py 825 LOC | 3,123 | Archived |
| **v1.0.0 FINAL** | 2026-07-27 | Phase 1-5 | Balance audit + meta_state + module split | 3,500+ | Archived |
| **v1.1.0a1** | 2026-07-28 | Engagement Top 3 | Variable Reward / Near-Miss / Faction Tension | 3,500+ | Archived |
| **v1.1.0** | 2026-08-17 | Rename + α-L | Roguelike Sprawl → Wet Run + 21 phases | 3,894 | Archived |
| **v1.3.0+** | 2026-08-10 | Phase 14 | F.2 deck + F.4 boss + F.4 telemetry wiring | 5,043 | Archived |
| **v1.4.0** | 2026-08-20 | Tracks A/B/D | Module splits + ADR integrations + release prep | 5,700 | **Current** |

### 2.2 콘텐츠 카운트 진화

| 항목 | v0.7.11 | v1.0.0 | v1.1.0 | v1.4.0 | 비고 |
|---|--:|--:|--:|--:|---|
| 미션 | 19 (orphan) | 38 | 47 | **209** | Arc6 + Expansion wiring (ADR-0206) |
| ICE 타입 | 25 | 41 | 41 | **97** |  |
| 자키 | 3 | 9 | 9 | **9** |  |
| GN 씬 | 7 | 56 | 72 | **81** |  |
| 프로그램 | 4 | 12 | 20 | **30** |  |
| 엔딩 | 1 | 1 | 3 | **29** |  |
| 미션 1회의 평균 분량 | 5-10 min | 30-60 min | 30-60 min | 30-60 min | (안정) |
| ADR | 54 | 90+ | 130+ | **209** |  |

### 2.3 모듈 사이즈 진화 (ADR-0110 정책)

| 버전 | app.py LOC | 가장 큰 모듈 | 비고 |
|---|--:|---|---|
| v0.7.11 | 825 | achievements.py 943 | 단일 파일 dispatcher |
| v1.0.0 | 500 | effects.py 1246 | ADR-0110 정책 (250/500/1000 LOC) |
| v1.4.0 | 230 (모듈) | 모든 모듈 ≤500 | 21/21 sub-modules ≤500 LOC (Track A.4) |

### 2.4 Phase별 진척 (2026-07-26 ~ 2026-08-26)

| Phase | 범위 | 산출물 |
|---|---|---|
| α | Cross-project 초기 | Fiction↔mission 양방향 |
| β-1/2 | UI + GN scene | Mission select link, 7→56 GN scenes |
| γ | Orphan cleanup | 19 → 0 |
| A | Combat quick wins | ICE kind, tier badge, dead code |
| B-1/2/3 | Boss enhancements | spawn_minions + aoe_damage (5 bosses) |
| C-1/2/3 | Stage flow | Data-driven stage_flow, chapter 통합 |
| D-2 | Game loop refactor | app.py -66% (6 modules) |
| E-1/2 | Onboarding | AAR, first-combat tutorial |
| F | Wiki + orphan | (consolidated in Phase L) |
| G | GN 81/81 | reward backfill, B-3 usage |
| H-L | B-3 wiring + wiki + log | 최종 통합 |
| **14** | F.2/F.4 wiring | 178 metadata + 200+ dashboard cards |
| **A.4** | Module splits | 4272 LOC → 21 sub-modules |
| **B.9** | ADR integrations | Death taunts, Gibson fluff, Matrix events |
| **D.5** | Meta & aftermath | Faction rep, replay, meta-progression |

---

## 3. wet_run-web 버전별 상태 비교

### 3.1 Tier 진척 매트릭스

| Tier | 날짜 | 미션 | ICE | 기능 | Bundle | Tests |
|---|---|--:|--:|---|--:|--:|
| **Tier 1** | 2026-08-25 | 5 | 5 | MVP: 미션 선택 → 1 전투 | 11 KB | 38 |
| **Tier 2a** | 2026-08-25 | 5 | 5 | Multi-slot save (4 slots) | 30 KB | 38 |
| **Tier 2b** | 2026-08-26 | 5 | 5 | Howler.js BGM + M 토글 | 67 KB | 47 |
| **Tier 2c** | 2026-08-26 | 15 | 12 | 미션 + ICE 다양성 (Gibson flavor) | 86 KB | 52 |
| **Tier 3** | 2026-08-26 | 30 | 30 | Full deck-building roster | 125 KB | 54 |
| **Tier 4** | 2026-08-26 | 30 | 30 | SFX + Animation VFX + Glyphs | 129 KB | 72 |
| **+ ADR-0209** | 2026-08-26 | 30 | 30 | IDB save backend | 130 KB | 93 |
| **+ Responsive** | 2026-08-27 | 30 | 30 | Portrait/landscape 전환 | 134 KB | 106 |
| **+ Progression fix** | 2026-08-27 | 30 | 30 | select_program 입력 + Playwright E2E | 134 KB | 106 + 6 E2E |

### 3.2 ADR 진척 (Web 트랙)

| ADR | Status | Subject |
|---|---|---|
| 0199 | **Accepted** | Wet Run Web MVP (Tier 1) |
| 0200 | **Accepted** | Git LFS D4 (오디오 현상 유지) |
| 0201 | **Accepted** | Tier 2b — Howler.js BGM |
| 0202 | **Accepted** | Tier 2c — 미션 + ICE 다양성 |
| 0203 | **Accepted** | Tier 3 — 30+30 expansion |
| 0204 | **Accepted** | Phase-aware BGM (5 tracks) |
| 0205 | **Accepted** | Status VFX + HUD Bars |
| 0206 | **Accepted** | Mission Registry Wiring (Arc6 + Expansion) |
| 0207 | **Accepted** | Tier 4 — SFX + Animation VFX + Glyphs |
| 0208 | **Accepted** | Mission random_weight (Python 미션 가중치) |
| **0209** | **Accepted** | **IDB save backend (Tier 3 literal partial)** |

### 3.3 Carry-over (다음 세션 후보)

| 항목 | 이유 | 우선순위 |
|---|---|---|
| Tier 5: status state machine 통합 | 현재 mock data | P1 |
| Tier 5: Animation timing (hit flash 지속) | 현재 instant | P2 |
| Volume slider UI | M 토글만 있음 | P2 |
| SFX 확장 (combat_block, combat_skill_*) | 3 effects만 | P2 |
| Per-track fade in/out | hard cut | P3 |
| Cloud save (Firebase/Supabase) | ADR-0209는 on-ramp만 | out-of-MVP |
| Multiplayer | out-of-MVP | out-of-MVP |
| Narrative integration (graphic novel mode) | out-of-MVP | out-of-MVP |

---

## 4. 메뉴 + 게임 진행 플로우 비교

### 4.1 wet_run (Python) — 메인메뉴 (Phase 7+, 7-8 옵션)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                       W E T   R U N                              │
│             A cyberpunk roguelike based on                       │
│              Gibson's Sprawl trilogy                             │
│                                                                  │
│   > [1]  N E W   R U N          ─ 자키 선택부터 시작             │
│     [2]  G R A P H I C   N O V E L ─ 스토리 자동재생            │
│     [3]  C O N T I N U E        ─ 마지막 세이브 로드             │
│     [4]  S E T T I N G S                                        │
│     [5]  C R E D I T S                                           │
│     [6]  H A L L   O F   D E A D ─ 사망 자키 아카이브            │
│     [7]  H E L P                ─ 조작법/도움말                  │
│     [8]  S T A T S (옵트인 시) ─ 텔레메트리 집계                  │
│                                                                  │
│   v1.4.0 · Phase A+B+D Complete                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 wet_run-web (Browser MVP) — 미션 선택 화면

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│               WET RUN — Select Mission                           │
│                                                                  │
│   ENTER: launch | ESC: quit | Arrow keys: navigate               │
│                                                                  │
│   ▸ 1. first_jack          [T1 | 50cr]                            │
│     2. watchdog_patrol     [T1 | 75cr]                            │
│     3. ono_sendai_repair   [T2 | 100cr]                           │
│     4. construct_market    [T2 | 120cr]                           │
│     5. ghost_signal_origin [T3 | 200cr]                           │
│     ... (30 missions, Tier 1-5, 6 zones)                         │
│                                                                  │
│   [HUD right] MISSION SELECT                                     │
│              Selected: 1/30                                      │
│                                                                  │
│   Tier 4 · ADR-0209 IDB backend                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**차이점**:
| 측면 | wet_run (Python) | wet_run-web |
|---|---|---|
| 메뉴 depth | 1-level (직접 진입) | 1-level (미션 직접 선택) |
| 옵션 수 | 7-8 (full game features) | 1 (mission select only) |
| 진입 후 깊이 | CHARACTER_SELECT → HUB → MATRIX → COMBAT | MISSION_SELECT → APPROACH → COMBAT |
| 게임 모드 | 매트릭스 노드 그래프 (다중 노드) | 단일 미션 (1 ICE = 1 전투) |
| 메타 진행 | Hall of Dead, Faction Rep, Replay | (미구현) |

### 4.3 wet_run (Python) — 게임 진행 플로우차트

```
                    ┌─────────────┐
                    │   BOOT      │
                    │   (app.py)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    MENU     │ ◄────────────┐
                    │  (7-8 opts) │              │
                    └──────┬──────┘              │
                           │                     │
        ┌──────────────────┼──────────────────┐  │
        │                  │                  │  │
   [1] NEW RUN      [2] GN MODE      [3] CONTINUE
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ CHARACTER_    │  │ GN_MENU       │  │ SAVED_        │
│ SELECT (9)    │  │ (4 opts)      │  │ PROGRESS      │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ BRIEFING      │  │ GRAPHIC_      │  │ HUB (re-entry)│
│ (mission)     │  │ NOVEL_AUTO    │  └───────────────┘
└───────┬───────┘  └───────┬───────┘
        │                  │
        ▼                  ▼
┌───────────────┐  ┌───────────────┐
│ TRAVEL        │  │ SAVED_        │
│ (matrix →     │  │ PROGRESS      │
│  nodes)       │  │ (GN continue) │
└───────┬───────┘  └───────────────┘
        │
        ▼ (multi-node: surface → mid → deep)
┌───────────────┐
│ MATRIX        │ ── 이벤트 (matrix_events.json)
│ (procedural)  │ ── 미션 발견
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ COMBAT (RT-MS)│ ◄─── ICE encounter
│ + VFX 5-layer │
│ + Boss phases│
└───────┬───────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
┌─────┐  ┌─────┐
│VICTORY│ │DEFEAT│
└──┬──┘  └──┬──┘
   │        │
   ▼        ▼
┌───────────────┐  ┌───────────────┐
│ REWARD +      │  │ DEATH_SUMMARY │ ──► HALL_OF_DEAD
│ LOOT (Salvage)│  │ + restart     │     (자키 아카이브)
└───────┬───────┘  └───────┬───────┘
        │                  │
        ▼                  ▼
   JACK_OUT ◄─────── JACK_OUT
        │
        ▼
┌───────────────┐
│ HUB           │ ── 다음 미션 / 인벤토리 / 제작
│ (ASCII panel) │
└───────┬───────┘
        │
        ▼ (반복 or 종료)
┌───────────────┐
│ ENDING (29)   │ ── Arc 1-6 + Salvation Phase
└───────────────┘
```

### 4.4 wet_run-web (Browser MVP) — 게임 진행 플로우차트

```
                    ┌─────────────┐
                    │    BOOT     │
                    │  (boot())   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ MISSION_    │ ◄──────────────┐
                    │ SELECT (30) │                │
                    └──────┬──────┘                │
                           │ [Enter]               │
                           ▼                       │
                    ┌─────────────┐                │
                    │  APPROACH   │                │
                    │ (jacking-in) │                │
                    └──────┬──────┘                │
                           │ [Enter / 1-9]         │
                           ▼                       │
                    ┌─────────────┐                │
                    │   COMBAT    │                │
                    │ (1 ICE,     │                │
                    │  RT-MS sim) │                │
                    │ + deck      │                │
                    │ + alarm     │                │
                    └──────┬──────┘                │
                           │                       │
                      ┌────┴────┐                  │
                      │         │                  │
                      ▼         ▼                  │
                ┌─────────┐  ┌─────────┐            │
                │ VICTORY │  │ DEFEAT  │            │
                │ + creds │  │ + death │            │
                └────┬────┘  └────┬────┘            │
                     │           │                │
                     ▼           ▼                │
                ┌─────────┐  ┌─────────┐            │
                │ CONTINUE│  │ JACK_OUT│ ───────────┘
                │ (next   │  │ → menu  │
                │ mission)│  └─────────┘
                └────┬────┘
                     │
                     ▼ (반복)
                ┌─────────┐
                │ JACK_OUT│
                │ (Q key) │
                └────┬────┘
                     │
                     ▼
              (back to menu)
```

**차이점**:
| 측면 | wet_run (Python) | wet_run-web |
|---|---|---|
| 단계 수 | 7 stages (BRIEFING/TRAVEL/MATRIX/COMBAT/REWARD/...) | 4 phases (menu/approach/combat/end) |
| 매트릭스 깊이 | 다중 노드 그래프 (procedural) | 단일 미션 (1 ICE) |
| 인벤토리/제작 | HUB panel (ASCII) | (없음) |
| 미션 반복 | JACK_OUT → 새 미션 선택 | CONTINUE 다음 미션 / JACK_OUT 메뉴로 |
| 사망 처리 | DEATH_SUMMARY → HALL_OF_DEAD → 새 자키 | (없음, 단순 JACK_OUT) |

### 4.5 입력 매핑 비교

| 입력 | wet_run (Python, 키보드) | wet_run-web (키보드) | wet_run-web (터치 게임패드) |
|---|---|---|---|
| 미션 선택 | Arrow keys / WASD | Arrow keys | D-pad ↑↓ |
| 확인 (launch/use) | Enter / Space | Enter / Space | A 버튼 |
| 취소 / 뒤로 | Escape | Escape | B 버튼 |
| 이동 (matrix) | Arrow keys | (없음, 매트릭스 없음) | (N/A) |
| 프로그램 사용 | Deck menu (1-9 keys) | **1-9 keys** (regression fix 2026-08-27) | **program row buttons** (combat only) |
| 음소거 | M (BgmPlayer 통합) | M | (없음, M 키보드만) |
| Jack out | Q | Q | (없음, 키보드만) |

**핵심 차이**: wet_run-web은 **단일 ICE = 1 전투**로 단순화되어 매트릭스 이동/인벤토리/제작 단계가 없음. `select_program` 입력은 2026-08-27 regression fix로 추가됨.

---

## 5. 검증 인프라 (Per-version 비교 가능성)

### 5.1 wet_run (Python)

| 도구 | 명령 | 검증 대상 |
|---|---|---|
| pytest | `make test` (or `prototype/.venv/bin/pytest`) | 4045+ unit tests |
| ruff | `make lint` | 코드 스타일 |
| mypy strict | `make typecheck` | 타입 안전성 |
| mkdocs strict | `mkdocs build --strict` | wiki 링크 무결성 |
| audit_vault.py | (workspace root) | cross-project broken links |

**현재**: 4045 passed / 364 skipped / 1 xfailed (2026-08-26 random_weight wiring 후)

### 5.2 wet_run-web (Browser MVP)

| 도구 | 명령 | 검증 대상 |
|---|---|---|
| vitest | `npm test` | 106 unit tests (state/layout/vfx/storage/audio/touch/missions) |
| playwright | `npm run e2e` | 6 E2E tests (desktop + mobile-portrait, smoke + progression regression) |
| smoke | `npm run smoke` | 배포 도달성 + asset 200 OK + JS 에러 0 |
| tsc --noEmit | `npm run build`의 사전 단계 | 타입 안전성 |
| vite build | `npm run build` | 번들 (134 KB) + GitHub Pages 자동 배포 |

**현재**: vitest 106 passed + playwright 6 passed (2026-08-27 progression fix 후)

### 5.3 Cross-track 회귀 감지

| 시나리오 | 감지 도구 |
|---|---|
| wet_run Python save 호환성 깨짐 | pytest save_manager tests + 사용자 매뉴얼 테스트 |
| wet_run-web IDB save 손실 | playwright + 수동 테스트 |
| wet_run-web combat 정체 (2026-08-27 버그) | **progression e2e test (신규)** |
| wet_run Python 미션 데이터 손실 | audit_vault.py + cross_project_integrity CI |
| wet_run-web BGM 누락 | audio.test.ts + playwright (수동 확인) |

---

## 6. 다음 세션 권장 (Per-version 표준화 후속)

| 우선순위 | 작업 | 이유 |
|---|---|---|
| P1 | wet_run-web main_menu 7-8 옵션 구현 | Python과 UX 일치 (현재 mission_select만) |
| P1 | wet_run-web 사망/리셋 사이클 | 단일 미션 → 다중 미션 run |
| P2 | wet_run-web 인벤토리/제작 UI | HUB 동등물 |
| P2 | wet_run-web 미션 진행 자동 save | 현재는 매 draw()마다 autosave |
| P2 | Notion 통합 자동화 | 현재 수동 (이 문서도 수동) |
| P3 | 두 트랙의 릴리스 노트 자동 생성 | CHANGELOG.md + web tier-history |

---

## 7. 부록: 작업 이력 추적

| 날짜 | wet_run (Python) | wet_run-web |
|---|---|---|
| 2026-07-10 | v0.7.11 | (pre) |
| 2026-07-26 | Unreleased Phase α-L | (pre) |
| 2026-07-27 | v1.0.0 FINAL | (pre) |
| 2026-07-28 | v1.1.0a1 | (pre) |
| 2026-08-10 | v1.3.0+ (Phase 14) | (pre) |
| 2026-08-17 | v1.1.0 (rename + α-L) | Tier 1 + 2a |
| 2026-08-20 | v1.4.0 (Quality Upgrade) | Tier 2b |
| 2026-08-25 | (patch prep) | Tier 2c / 3 |
| 2026-08-26 | v1.4.0 (PyPI release) | Tier 4 + ADR-0209 |
| 2026-08-27 | (maintenance) | Responsive + progression fix + E2E |

**결론**: wet_run (Python)은 **메이저 릴리스 단위** (v1.4.0 단일 날짜에 다수 기능 통합) 로 릴리스. wet_run-web은 **Tier 진척 단위** (Tier 4가 한 날에 SFX+Animation+Glyphs 통합) 로 릴리스. 두 트랙은 2026-08-26에 동시에 진척.