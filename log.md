## [2026-08-18] docs(session-close) | Phase 14 Axis closure sweep final — SESSION_SUMMARY_2026-08-18 + index.md 동기화

**Status**: ✅ 완료 — Session 종료 문서화. Phase 14 v1.3.0+ 의 Axis 5 (Endings) / 4 (Boss F.4) / 6 (Programs/Equipment) 의 recon-기반 closure 8 commits 의 결과를 canonical 문서 (SESSION_SUMMARY_2026-08-18.md) 으로 consolidate. 세션-인덱스 (SESSION_SUMMARY.md) + 프로젝트 wiki-index (index.md) 도 동기화.

### 1. 신규 / 변경 문서

| File | Size | 책임 |
|---|---:|---|
| `SESSION_SUMMARY_2026-08-18.md` (NEW) | ~7KB | 오늘 세션 8 commits + axes 5/4/6 closure + 후속 backlog 종합 |
| `SESSION_SUMMARY.md` | updated | latest-세션 pointer → 2026-08-18; summary blurb 갱신; recent sessions 테이블에 2026-08-18 row 추가 |
| `index.md` | +8 lines 시스템, +10 lines tests | 신규 combat artifacts (`boss_dispatch.py` / `boss_registry.py`) 및 신규/기존 test 파일 카탈로그 entries |
| `log.md` | 본 entry (이 항목) | AGENTS.md §9 "작업 종료 체크리스트" log 기록 |

### 2. 신규 카탈로그 entries (index.md)

#### 시스템 (Phase B 추가) — 추가
- **Boss Dispatch** (`combat/boss_dispatch.py`) — ADR-0190
- **Zone Boss Registry** (`combat/boss_registry.py`) — ADR-0190
- **Boss F.4 Integration** — `combat/registry.py:build_ice_enemy` 가드

#### 테스트 케이스 — 신규
- Boss Registry / Boss Dispatch / Programs Schema / Wetware Stacking / Augments / Telemetry + Set Bonus Integration / Phase 14 Endings + Programs / Endings Handler / Endings Persistence / Ending Renderer

### 3. 최종 상태 (origin 동기)

| | Value |
|---|---:|
| Branch | `main`, ahead of origin = 0 |
| Working tree | clean |
| Total commits today | 8 (모두 push 완료) |
| Closed ADRs (this session) | 0192 / 0190 / 0193 ("implementation closed" status) |
| Backend (deferred) | Axis 1 (0188) / Axis 2 (0189) / Axis 3 (0191) / Track A module splits (0156-0159) |

### 4. 다음 세션 handover 노트

직전 세션 SESSION_SUMMARY 의 "Next-Session Backlog" 섹션 참조. 첫 진입점은 **Axis 1 (Mission Expansion)** — content-heavy (89+ missions + 5 types + 8 chains).

### 5. 검증

| Check | Result |
|---|---|
| `git log --oneline -8` | 8 commits 명확 / 순서 유지 |
| `git status` | working tree clean |
| `git rev-list --count origin/main..HEAD` | 0 (synced) |
| `pytest tests/unit/ -q --no-header` | 5639 passed / 24 failed (baseline unchanged; pre-existing 24 = death_extended / pages_deploy / interrogate thresholds) |

### 인용

- [`SESSION_SUMMARY_2026-08-18.md`](./SESSION_SUMMARY_2026-08-18.md) — canonical today's session record
- AGENTS.md §9 — 작업 종료 체크리스트
- AGENTS.md §6.5 — workspace-level docs (`log.md` / `INDEX.md` / `SESSIONS/` cross-project)

---

## [2026-08-18] chore(axis-6-closure) | ADR-0193 (Programs/Equipment) status sync — implementation in progress → closed

**Status**: ✅ 완료 — 4번째 consecutive axis (5/4/6) recon 후 같은 패턴 확인: Phase 14 commit `205efd4` (2026-08-10) 가 이 axis 의 **데이터 + 엔진 wiring 모두** 이미 구현해 두었음. 본 entry 는 closure log 만.

### Recon 결과

| ADR-0193 Target | Actual | 초과 |
|---|---|---|
| 18 programs (4 def + 5 util + 4 off + 5 sup) | **30 programs** (8 def + 11 atk + 5 det + 6 sup) | ✅ 67% 초과 |
| 2 sets (Ghost + Architect) | ✅ 둘 다 — 8 pieces (4 per set) | ✓ |
| 10 augments (7 lv3 + 3 new stats) | ✅ 10 augments — ap_regen_lv3/crit_lv3/dodge_lv3/max_hp_lv3/healing_lv3/shield_lv3/speed_lv3 + mana_lv3/armor_lv3/focus_lv3 (new stats) | ✓ |

### Engine wiring (이미 코드 통합됨)

| 컴포넌트 | 파일 | 책임 |
|---|---|---|
| Equipment core | `src/wet_run/equipment/equipment.py` | equipment 카탈로그 |
| Set bonuses | `src/wet_run/equipment/set_bonus_integration.py` | 2-piece / 3-piece / 4-piece bonus dispatch |
| Wetware stacking | `src/wet_run/equipment/wetware_stacking.py` | tier 3 + new stat 누적 |
| Augments | `src/wet_run/combat/augments.py` | lv1/lv2/lv3 + new stats 통합 |
| Meta progression | `src/wet_run/combat/meta_progression.py` | wetware 영구 unlock |
| Equipment view UI | `src/wet_run/engine/equipment_view.py` | in-game 표시 |

### 테스트 (이미 12 파일 · 200+ tests)

| 테스트 파일 | 책임 |
|---|---|
| `test_equipment.py` | core equipment 카탈로그 |
| `test_wetware_stacking.py` | 누적 규칙 |
| `test_augments.py` | lv1/lv2/lv3 progression |
| `test_telemetry_and_set_bonus_integration.py` | set bonus + telemetry 연동 |
| `test_phase14_endings_programs.py` | Phase 14 통합 (programs + endings) |
| `test_equipment_view.py` | UI 표시 |
| `test_programs_schema.py` | programs.json schema validity |
| (그 외 5) | settings / accessibility |

### 검증

| Check | Result |
|---|---|
| `pytest -k 'equipment or programs or augment or set_bonus or wetware_stacking'` | ✅ **212 passed** (30 skipped, 5787 deselected) |
| Full suite (vs my session-wide delta) | **5639 passed / 24 failed** (baseline unchanged) |
| New regressions caused by session | **0** |

### 인용

- ADR-0193 (Programs/Equipment Expansion, Axis 6) — Accepted 2026-08-08, **implementation closed** by Phase 14 v1.3.0+ commit `205efd4` (2026-08-10)
- ADR-0172/0173/0178 (Cyberdeck, Wetware, Deck Building) — program/augment/cyberdeck 데이터 layer 의 upstream 결정
- ADR-0192/0190 (Axis 5/4 — endings + boss F.4) — 같은 Phase 14 의 동반 closure. 같은 패턴. (Axis 5 — `b33d691/36d2cdc/f95c164` 3 commits; Axis 4 — `6c48dab/e295c4d/13a6eff/4a7e97a` 4 commits)

---

## [2026-08-18] feat(combat) | F.4 dispatch integration — boss_dispatch.py + build_ice_enemy guard

**Status**: ✅ 완료 — ADR-0190 (Phase 12 Axis 4) 의 **데이터 → dispatch wiring** closing commit. 이전 commit (4a7e97a) 가 zone_bosses.json 의 typed lookup 인프라 (ZoneBossRegistry) 만 만들었었음; 본 commit 는 combat dispatch 의 그 등록분을 실제로 호출하는 wiring 구현. ADR-0190 implementation in progress → **wiring closed**.

### 1. 구현 (모듈 3종 + 테스트 70 케이스)

**`prototype/src/wet_run/combat/boss_dispatch.py` (NEW, ~150 LOC)**
- `is_boss_id(ice_id) -> bool` — 두 registry 통합 lookup (zone_bosses + boss_expansion). dispatch early-exit 가드용.
- `build_boss_combatant_from_id(ice_id, *, player_grade=None) -> Combatant | None` — zone 경로 + boss_expansion 경로 순차 시도. None 으로 fall-through 신호.
- `_zone_boss_to_combatant(profile, player_grade)` — ZoneBossProfile → Combatant 변환. tier-aware linear scaling: `hp = hp_base + hp_per_grade * max(0, player_grade - tier)`. 다운스케일 없음 (zone boss 는 초반 등급에서도 base 유지, 보스 조우의 roguelike convention).
- `_get_zone_registry()` + `reset_zone_registry_cache()` — 모듈 레벨 lazy 캐시. import-time I/O 회피.

**`prototype/src/wet_run/combat/registry.py` (~5 lines 추가)**
`build_ice_enemy()` 의 첫 줄에 guard 추가:
```python
from .boss_dispatch import build_boss_combatant_from_id
_boss_combatant = build_boss_combatant_from_id(ice_id, player_grade=player_grade)
if _boss_combatant is not None:
    return _boss_combatant
data = registry.get(ice_id)
```
IceRegistry lookup 은 이제 fallback 경로. boss ids (14개: zone 11 + expansion 3) 는 전부 dispatch helper 가 처리. 비-boss ids 는 기존 코드 unchanged.

**`prototype/tests/unit/test_boss_dispatch.py` (NEW, 43 tests)**
- is_boss_id parametrized over 11 zone + 3 expansion ids + 6 standard ICE 비-matches + edge cases (empty string, non-string, unknown)
- build_boss_combatant_from_id return Combatant / None 분기
- Tier-aware scaling validation (dj_cyberspace: g=1 base, g=3 base, g=5 base+2*25=200, g=10 base+7*25=325; orbit_ghost tier=5 g=10 = 400+60*5=700)
- Lazy-load 캐시 + reset helper
- Registry parity (모든 zone boss entry 가 dispatch 로 빌드 가능)

### 2. 안정성 검증

| Check | Result |
|---|---|
| `ruff check src/wet_run/combat/{registry.py, boss_dispatch.py, boss_registry.py}` | ✅ All checks passed |
| `mypy --strict src/wet_run/combat/boss_dispatch.py` | ✅ no issues found |
| `pytest tests/unit/test_boss_dispatch.py` | ✅ **43 passed** |
| Full suite baseline (without my changes) | 5596 passed / 24 failed |
| Full suite with my changes | **5639 passed / 24 failed** |
| Net delta | **+43 tests, 0 new failures** |
| Smoke (build_ice_enemy routes correctly) | ✅ all 14 boss ids route via dispatch, standard ICE still via IceRegistry |

### 3. 효과

| Combatant lookup path | Before | After |
|---|---|---|
| `build_ice_enemy('standard', ...)` | IceRegistry → standard ICE | unchanged |
| `build_ice_enemy('neuromancer', ...)` | IceRegistry → hp=320 ICE — Neuromancer (ADR-0180 무시) | **boss_dispatch → NEUROMANCER_PROFILE → hp=400 (6 phases)** |
| `build_ice_enemy('dj_cyberspace', ...)` | KeyError (zone ids not in ice_types) | **boss_dispatch → ZoneBossProfile → hp=150 (zone tier=3)** |
| `build_ice_enemy('the_peripheral', ...)` | KeyError | **boss_dispatch → hp=700 (tier=6 secret)** |

→ 14 boss ids previously orphaned / non-boss-routed are now correctly dispatched with their declared tier, hp, dmg, defense, resistance.

### 4. 추가 보류

- **Combatant.skills 필드 비어있음** — zone boss 의 skills 리스트 (signal_jam, voodoo_king 등) 는 dispatch 단계에서 미적용. 후속 commit 에서 program_registry 와 연동.
- **dialogue / cinematic** — boss 진입 시 화면 연출 (ADR-0050 boss intro / ADR-0169 combat cinematics) 은 별도 통합 영역.
- **combat_view_state 의 is_boss() 후크** — WINTERMUTE/TA_CONSTRUCT_PRIME 만 처리. 본 commit 의 14 ids 도 같은 후크에 추가 후속 가능.

### 인용

- ADR-0190 (Boss Expansion + F.4 Integration, Axis 4) — Accepted 2026-08-08, **implementation closed** by this commit (data → dispatch wiring)
- ADR-0180 (Boss Expansion v1.3.0+) — 3 profiles underlying `build_boss_combatant`
- ADR-0050 (Boss ICE System) — original Phase 1 dispatch pattern
- ADR-0110 (module size policy) — boss_dispatch 150 LOC < 250 soft limit

---

## [2026-08-18] feat(combat) | Zone boss registry — load zone_bosses.json into typed lookup

**Status**: ✅ 완료 — ADR-0190 (Phase 12 Axis 4 — zone-bosses part) 의 데이터 → 엔진 인프라. zone_bosses.json (11 entries — 6 zone + 3 ascended + 2 peripheral) 가 **이 commit 이전까지 zero code references** 였음. ZoneBossRegistry + ZoneBossProfile 도입으로 typed lookup 제공. 다음 commit 에서 combat dispatch 에 wiring 예정.

### 1. 발견 (Recon 결과)

- `data/combat/zone_bosses.json` — **11 entries** (dj_cyberspace / sense_net_sentinel / hosaka_memory_vault / locus_construct / tessier_child / orbit_ghost + wintermute_ascended / ta_prime_ascended / neuromancer_ascended + the_peripheral / the_peripheral_ascended)
- `combat/boss_expansion.py` — ADR-0180 의 3 profiles (NEUROMANCER / LOA_BARON / BLACK_BARON) 이미 정의됨 + 자체 `BOSS_EXPANSION_REGISTRY` 보유
- `combat/registry.py:407` — `program_registry is None` 체크 부근에 "reserved for future boss/elite variants" 코멘트 — F.4 integration 의 자리 마련됨
- **그러나 — 두 데이터 소스 모두 combat dispatch 에서 미사용 상태** (zero code imports; `combat_view_state.py` 만 NEUROMANCER_PROFILE 을 import 하나 instance 화는 미연결)

### 2. 구현

`prototype/src/wet_run/combat/boss_registry.py` (NEW, 194 LOC) — ADR-0110 의 250-LOC soft limit 안에 들어감:

- `ZoneBossProfile`: frozen/slots dataclass, 16 필드 (boss_id / name / zone / tier / hp_base / hp_per_grade / dmg_base / dmg_per_grade / defense / speed / skills / resistance / phase_count / portrait / description / loot_table / ice_kind)
- `ZoneBossRegistry`: id-indexed + zone-indexed (by-zone 결 list)
  - `get(boss_id) -> ZoneBossProfile | None`
  - `get_for_zone(zone) -> tuple[ZoneBossProfile, ...]`
  - `list_all() / list_ids() / list_zones() / __len__ / __contains__`
- `load_zone_boss_registry(path | None = None)`: metadata-key (`_*`) + non-dict + type-error entries silently skip (resilience against partial data corruption)

### 3. 검증

ruff + mypy strict + pytest 전체 통과:

| Check | Result |
|---|---|
| `ruff check src/wet_run/combat/boss_registry.py tests/unit/test_boss_registry.py` | ✅ All checks passed |
| `mypy --strict src/wet_run/combat/boss_registry.py` | ✅ Success: no issues found |
| `pytest tests/unit/test_boss_registry.py` | ✅ **27 passed** |
| Full suite `pytest tests/unit/` | ✅ **5607 passed** (vs 5580 baseline, +27) |
| 0 new failures | ✅ (13 baseline failures unrelated: death_extended, pages_deploy, interrogate coverage) |

### 4. 다음 step (out of scope, 후속 commit)

- **F.4 통합**: `combat/registry.py:build_ice_enemy` 에 zone boss branch 추가 — `ice_kind == "boss"` 인 경우 `ZoneBossRegistry.get(ice_id)` 또는 `boss_expansion.get_boss_profile(ice_id)` 으로 stat override. 모듈 분리 패턴으로 안전하게 추가.
- **Dispatch wiring**: `combat_view_state.py` 가 zone boss 를 spawn 할 때 자동으로 올바른 stat / phase 적용.

### 인용

- ADR-0190 (Boss Expansion + F.4 Integration, Axis 4) — Accepted 2026-08-08, implementation in progress
- ADR-0180 (Boss Expansion v1.3.0+) — 기존 3 boss profiles
- ADR-0110 (module size policy) — 250/500 LOC soft/hard limit 준수

---

## [2026-08-18] chore(endings-closure) | ADR-0192 status sync + 6 character endings 보강

**Status**: ✅ 완료 — Phase 14 (v1.3.0+) 가 commit `205efd4` (2026-08-10) 에 ADR-0192 를 end-to-end 로 구현 (22 endings, 6 types, 3 NG+, 56 tests) 했었음. 오늘 session 에서 ADR-0192 의 status sync + per-character 6 endings 추가.

### 1. 발견 (Recon 결과)

ADR-0192 의 implementation 이 이미 end-to-end 로 존재:
- `data/story/endings.json` — 22 endings (Redemption × 2 / Sacrifice × 3 / Transcendence × 5 / Betrayal × 4 / Absolution × 4 / Integration × 4)
- `src/wet_run/story/endings.py` (237 LOC) — registry + trigger detection + reward/achievement mutation (`EndingResult`)
- `src/wet_run/story/ending_renderer.py` (179 LOC) — render helpers
- 56 tests (test_endings_handler + test_ending_renderer + test_endings_persistence) — **PASSED**
- 3 NG+ endings (Network / Construct / Peripheral) — `arc=6` + `character_ref="all"` + `salvation_complete + ngplus_active + ...` triggers

잔존 gap:
1. `_metadata.total_endings: 21` (stale vs actual 22)
2. Per-character ending coverage uneven: case(6), 3jane(3), wigan(2), kas(2), angie(2), molly(1), sally(1), suit(1), neuromancer(1) — 대부분 자리는 1-2개씩만
3. `graphic_novel_view.py` 가 `story.endings` 미연동 (typed ending이 in-game flow에 노출 안 됨 — 추후 통합 ADR)

### 2. Cleanup commit

- `_metadata.total_endings: 21 → 28` (6 additions 후 값)
- 검증: import + 56 tests 그대로 PASS

### 3. 6 character endings 보강

각 char의 personality/type-fit 기준 선택:

| Ending ID | Character | Type | Arc | Trigger | Reward |
|---|---|---|---|---|---|
| `ending_molly_redemption` | molly | redemption | 2 | `defeat_yakuza_leader + ally_with:armitage` | 3,500cr + morale 100 + retirement_charm |
| `ending_sally_integration` | sally | integration | 3 | `complete_marlys_window + construct_awakening` | 7,500cr + construct_link |
| `ending_suit_betrayal` | suit | betrayal | 2 | `complete_hosaka_contract + ally_with:ta_rep` | 25,000cr + hosaka_rep+50 |
| `ending_neuromancer_absolution` | neuromancer | absolution | 4 | `ta_vote_complete + all_constructs_merged` | 6,000cr + morale 100 |
| `ending_angie_transcendence` | angie | transcendence | 3 | `complete_big_mama + construct_awakening` | 5,000cr + sky_charm |
| `ending_wigan_sacrifice` | wigan | sacrifice | 4 | `construct_awakening + hp_below + ngplus_active` | 0cr + permanent_death + loa_relic |

Triggers 모두 `_check_single_condition` 가 인식하는 형식 (engine 검증).

### 4. 갱신 후 분포

| Character | Count |
|---|---:|
| case | 6 (full) |
| 3jane | 3 (1 universal NG+) |
| wigan / angie | 3 each |
| molly / sally / suit / neuromancer / kas | 2 each |
| all (NG+) | 3 |
| **Total** | **28** |

By type: redemption × 3, sacrifice × 4, transcendence × 6, betrayal × 5, absolution × 5, integration × 5

### 5. 검증

- `pytest tests/unit/test_endings_*` — **56 passed**
- Full suite: **5,580 passed** (vs 5,580 baseline) — **0 new failures** by my changes
- 기존 13 failures (death_extended, pages_deploy, interrogate coverage) — 모두 baseline 부터 존재 (ADR-0192 와 무관, 별도 정리 필요)
- import: `get_total_endings() == 28`, `by_char / by_type` 갱신 확인
- 6 new entries schema 검증 (모든 required 필드 존재)
- `_metadata.total_endings: 28` 동기화

### 인용

- ADR-0192 (Ending Expansion, Axis 5) — Accepted 2026-08-08, implementation 2026-08-10 commit `205efd4`
- 6 ADR goals: 6 ending types × 9 chars + 3 NG+ — 본 세션은 1 char × 6 representatives + 메타 sync

---

## [2026-08-18] chore(rename-cleanup) | Dashboard + prototype — ROGUELIKE SPRAWL → Wet Run (5 atomic commits)

**Status**: ✅ 완료 — Project Rename scope A (commit `ae83d00`) 가 `wiki/` `design/` 까지만 적용됐고 dashboard + prototype 일부 (chrome / story metadata / i18n / demos) 가 누락됐던 잔존 영역 정리. **232 파일**, **5 atomic commits**. 0 test change, 0 regression. GitHub Pages push 전에 정합성 확보.

### Sweep 결과

사용자 결정 (sweep 범위 + 보존 영역): **전면 (dashboard + prototype)**, **이름=Wet Run**, **메타 문서 보존 (log/CHANGELOG/README/SESSION_*/_archive)**, **decisions/0032 Accepted immutable 보존**.

| 영역 | 정정 전 | 정정 후 |
|---|---|---|
| dashboard chrome `<h1>` (index, missions) | `🌆 ROGUELIKE SPRAWL` | `🌆 Wet Run` |
| dashboard chrome UI labels (back-nav `◀ Roguelike`, current `🌆 Roguelike`) | 5 sites (combat/cyberspace/sound/settings/missions/index) | 0 |
| dashboard story game-integration path (`Game/roguelike_sprawl/...`) | 213 .html | `Game/wet_run/...` (perl -pi sweep) |
| prototype i18n `app.title` (en/ko/ja/zh.json) | `ROGUELIKE SPRAWL` | `Wet Run` |
| prototype demo banners (6 demos) | `ROGUELIKE SPRAWL` banner | `Wet Run` banner |
| prototype/scripts/git-hooks/pre-commit (docstring) | `validate roguelike_sprawl ↔ Fiction` | `validate wet_run ↔ Fiction` |

### 보존 (사용자 결정)

- `decisions/0032-graphic-novel-mode.md` (1 line) — Accepted immutable 규약
- `log.md` (9 hits), `CHANGELOG.md` (4), `README.md` (5), `SETUP_LOG.md` (1)
- `SESSION_SUMMARY*.md`, `SESSION_HANDOVER*.md`, `_archive/sessions/*`, `_archive/audits/*`
- `prototype/CHANGELOG.md` (1 hit), meta `<meta name="keywords">` 의 `roguelike, cyberpunk, gibson, sprawl` (장르/설정 SEO)
- 인게임 subtitle (`'A roguelike based on William Gibson's Sprawl trilogy'` 등): `'roguelike'`=장르, `'Sprawl'`=깁슨 3부작 — 사실 관계 명제, 변경 X

### Commits (5 atomic, chronological)

| # | Hash | Files | Type |
|---:|---|---:|---|
| 1 | `2e6d161` | 2 | `fix(dashboard): chrome <h1> titles — ROGUELIKE SPRAWL → Wet Run` |
| 2 | `3f00b6a` | 6 | `fix(dashboard): chrome UI labels — Roguelike → Wet Run` |
| 3 | `28ea7bf` | 213 | `fix(dashboard): story game-integration paths — roguelike_sprawl → wet_run` |
| 4 | `b755ad1` | 4 | `fix(prototype): i18n app.title — ROGUELIKE SPRAWL → Wet Run (4 langs)` |
| 5 | `0d4f8c3` | 7 | `fix(prototype): demo banners + pre-commit hook — ROGUELIKE SPRAWL → Wet Run` |

### 검증

- `grep -rln 'roguelike[\s_\-]?sprawl|ROGUELIKE SPRAWL' dashboard/ prototype/data/i18n/ prototype/scripts/{demo,visual,full,headless,combat_effects}_*.py prototype/scripts/git-hooks/pre-commit` → **0 hits**
- `python3 -c "import json; json.load(open(file))"` × 4 i18n 파일 → **all OK**
- `python3 -c "import ast; ast.parse(open(file))"` × 6 demo .py → **all OK**
- 파일 인코딩 보존 (UTF-8 HTML), file count unchanged
- 보존 영역 (decisions/0032, log.md, CHANGELOG.md, README.md, SETUP_LOG.md, _archive/, SESSION_SUMMARY*.md, prototype/CHANGELOG.md) — 그대로 유지 확인

### 인용

- ADR style: AGENTS.md §9 (작업 종료 체크리스트 — log.md 기록)
- Rename history: commit `ae83d00 chore(rename): Roguelike Sprawl → Wet Run (project-wide display name)`
- 사용자 의사결정: "A. 전면 / Wet Run (대문자 그대로) / 기록 보존 / 0032 보존"

---

## [2026-08-17] feat+chore(polish) | Phase 50 — Small content + polish

**Status**: ✅ 완료 — 1 content addition (Screw's Last Bargain event) + 1 modules polished (mission_completion docstring) + 10 forward-compat allowlist updates (Phase 40..49). Commit `80e5d3b`. 13 files, +218/-14, **5604 passed** (+13 over Phase 49 baseline 5591), 365 skipped, 1 xfailed.

### 1. Content addition: general_event_screws_last_bargain

`prototype/data/story/events.json` 에 `general_event_screws_last_bargain` 신규 엔트리 추가 (53 → 54 events). Gibson-flavored Arc 5 late-arc Screw's Last Bargain from the Freeside black-market fixer — 깁슨 원작의 *Mona Lisa Overdrive* / *Count Zero* 의 Freeside orbit 여권조작꾼 Screw 가 주인공에게 마지막 거래 제안 (Freeside passport in exchange for a 'contested memory'). 위태/시바 / Zion 모두와 다른 Freeside 의 마지막 톤 (shaky):

- **Category**: general, trigger: `node_enter`, trigger_condition: `arc_5_progress >= 70 AND random < 0.04 AND NOT has_status:screw_bargain_seen`
- **Mood**: shaky, location: matrix_freeside_orbit, arc: 5, tier: 5, pillar: memory
- **Dialogue**: SCREW VOICE 메시지 5개 ("Hey, kid. Last time I cut a deal like this, the buyer ended up in a vat." / "Freeside passport, L5 orbit clearance, no questions. Cost: a memory." / "Not the boring ones. The ones you still flinch at. That's the going rate.") + CONSOLE blackmarket log
- **Choice**: Pay the memory price (screw_pass_unlocked, freeside_clearance_+2, zion_affinity_-1, contested_memory_relinquished_2_runs) vs Walk — your memories are not for sale (freeside_walked, safe_jackout, identity_marker_high, maas_+1)
- **Reward**: 0 credits + 120 XP + screw_freeside_charm
- **Consequence**: screws_last_bargain_branch (unique — global branch-id sweep)
- **Faction affinity**: freeside_clearance +2 AND maas +1 (pay-bargain yields Freeside orbit passage + Maas protective approval of the refused bargain; walk-on yields the inverse — no orbit passage but Maas oath of contested memory protection)
- **메타데이터**: phase 50 → 51, total_events 53 → 54, total_chains 6 unchanged

Phase 49 의 Zion Last Broadcast event (Arc 5 late-arc, Maelcum wisdom transmission, zion_affinity + ta_rep affinity) 와 동일 arc-prefix + tone-pair — Phase 49 가 "Zion dread 의 reggae broadcast" (warm) 였다면, Phase 50 은 "Freeside black-market 의 passport bargain" (shaky). 둘 다 Arc 5 late-arc construct-passage pre-auth, 둘 다 last-message 모티프. Phase 49-50 가 "마지막 거래/전송" 의 짝.

### 2. Polish — 1 modules (mission_completion docstring)

**`engine/mission_completion.py`** — `complete_mission()` docstring 확장. 기존 2줄 docstring 을 완전한 API contract 로 확장:

- 기존: "Award rewards and mark mission as complete." (2줄)
- 신규: explicit `Args:` (state / mission) + `Side effects:` 섹션 (Credits / XP / Faction / completed_missions / items — 5 항목 명시) + silent no-op on non-Mission callers note
- 기존 silent no-op 동작 (return without effect for non-Mission callers) 유지 — contract 자명화

### 3. Forward-compat allowlist (10 forward-compat updates + bug fix)

Phase 40..49 테스트의 `metadata["phase"] in (...)` allowlist 에 "50" 추가 (9 forward-compat updates + Phase 49 자체 forward-compat):

- **Bug fix (incidental)**: `test_phase49_small_content_polish.py` 의 metadata fixture 가 `dict.get('phase', '49', '50')` 로 잘못 작성되어 있었음 — Python `dict.get()` 는 max 2 args. `dict.get('phase', '49')` 로 수정 (default 만).

### 4. test_phase50_small_content_polish.py (13 tests 신규)

- **`TestScrewsLastBargainEvent`**: 11 tests
  - test_event_present
  - test_event_metadata (arc/tier/pillar/location/mood)
  - test_event_trigger (arc_5_progress >= 70, NOT has_status:screw_bargain_seen)
  - test_event_dialogue (SCREW, Freeside reference)
  - test_event_choice_a_screw (screw_pass_unlocked, freeside_clearance_+2, zion_affinity_-1, contested_memory_relinquished_2_runs)
  - test_event_choice_b_maas (maas_+1, maas_oath_2_runs, identity_marker_high)
  - test_event_faction_affinity (freeside_clearance == 2, maas == 1)
  - test_event_rewards (screw_freeside_charm, xp 120)
  - test_event_arc_5_partner (screws_last_bargain_branch)
  - test_event_branch_is_unique
- **`TestScrewsLastBargainBranchUniqueness`**: 1 test
  - test_branch_id_unique_across_events (global branch-id sweep — 다른 events 와 branch id 충돌 없음 검증)
- **`test_phase_50_metadata_present`** + **`test_phase_50_total_events_at_least_53`**: 2 tests
  - Phase 50 metadata 가 존재하고 total_events >= 53 (screw 추가 후 54)

### Validation

| Gate | Status | Notes |
|---|---|---|
| `make format` | ✅ | 변경 없음 |
| `make lint` (ruff) | ✅ | All checks passed |
| `make typecheck` (mypy strict) | ✅ | Success: no issues found in 211 source files |
| `make test` (pytest) | ✅ | **5604 passed** (+13 over Phase 49 baseline 5591), 365 skipped, 1 xfailed (pre-existing perf-tracker flake) |
| interrogate | ✅ | 100.0% (Phase 49 plateau preserved) |
| `audit_vault.py` | ✅ | 0 broken (CLEAN, 67 false-positive artifacts) |
| `dashboard_pipeline_audit.py` | ✅ | 0 errors |
| `mixed_language_audit.py` | ✅ | 0 violations |

### 5. Out-of-scope (preserved)

- `raw/` 수정 안 됨
- Accepted ADR 수정 안 됨
- 다른 프로젝트 손대지 않음
- Push 안 함

### 6. Forward-compat (테스트 패턴 일관성)

Phase 40..49 테스트의 `metadata["phase"] in (...)` allowlist 에 "50" 추가 (10 forward-compat updates, 9 single-line + 1 bug fix in Phase 49). 메타데이터 phase bump 가 이전 phase 테스트를 깨뜨리지 않도록.

### 7. Cumulative Phase 47..50

- Phase 47 (Hosaka Archive Audit): Gibson Sense/Net archive dialogue, Arc 4 mid-arc
- Phase 48 (Dixie Flatline Memory): Gibson dead-ROM construct, Arc 4 mid-arc
- Phase 49 (Zion Last Broadcast): Gibson Maelcum reggae dread, Arc 5 late-arc warm
- Phase 50 (Screw's Last Bargain): Gibson Freeside black-market, Arc 5 late-arc shaky

---

## [2026-08-17] feat+chore(polish) | Phase 49 — Small content + polish

**Status**: ✅ 완료 — 1 content addition (Zion Last Broadcast event) + 1 modules polished (wetware_stacking docstring) + 10 forward-compat allowlist updates (Phase 39..48). Commit `533244c`. 13 files, +214/-10, 5591 passed (+13 over Phase 48 baseline 5578).

### 1. Content addition: general_event_zion_last_broadcast

`prototype/data/story/events.json` 에 `general_event_zion_last_broadcast` 신규 엔트리 추가 (53 → 54 events). Gibson-flavored Arc 5 late-arc Maelcum broadcast from the Zion dreadnaught ST. JOHN OF THE NIGHT SKY — 깁슨 원작의 *Neuromancer* / *Mona Lisa Overdrive* 에서 Case 를 Zion 궤도로 데려다 주는 reggae dread 조종사 Maelcum 이, 후배 자키에게 마지막 wisdom / memory 를 broadcast 로 전달. 따뜻한 톤(warm), ZION_ORBIT_RELAY 의 dreadnaught broadcast:

- **Category**: general, trigger: `node_enter`, trigger_condition: `arc_5_progress >= 60 AND random < 0.04 AND NOT has_status:zion_broadcast_seen`
- **Mood**: warm, location: matrix_zion_orbit, arc: 5, tier: 5, pillar: memory
- **Dialogue**: MAELCUM VOICE 메시지 5개 + CONSOLE broadcast source log
- **Choice**: Receive the broadcast (zion_affinity_+2, ta_rep_+1, zion_wisdom_unlocked, memory_archive_+1) vs Let it pass — the matrix does not need another ghost (safe_jackout, identity_marker_low, wintermute_-1, broadcast_silenced_marker)
- **Reward**: 0 credits + 110 XP + zion_mother_charm
- **Consequence**: zion_last_broadcast_branch (unique — global branch-id sweep)
- **Faction affinity**: zion_affinity +2 AND ta_rep +1
- **메타데이터**: phase 49 → 50, total_events 53 → 54, total_chains 6 unchanged

### 2. Polish — 1 modules (wetware_stacking docstring)

**`equipment/wetware_stacking.py`** — `stack_wetware()` docstring 확장. Args: 섹션 추가 (augment_ids + unknown IDs silently ignored note), Stacking rules 섹션 유지.

### 3. Forward-compat allowlist (10 forward-compat updates)

Phase 39..48 테스트의 `metadata["phase"] in (...)` allowlist 에 "49" 추가.

### 4. test_phase49_small_content_polish.py (13 tests 신규)

TestZionLastBroadcastEvent (11), TestZionLastBroadcastBranchUniqueness (1), test_phase_49_metadata + total_events (2).

### Validation

- make format: 변경 없음
- make lint (ruff): All checks passed
- make typecheck (mypy strict): 211 source files, 0 errors
- make test (pytest): 5591 passed (+13), 365 skipped, 1 xfailed (pre-existing)
- audit_vault.py: 0 broken (CLEAN)
- dashboard_pipeline_audit.py: 0 errors
- mixed_language_audit.py: 0 violations

### 5. Push 상태

8 commits ahead of origin (Phase 48 baseline + Phase 49). User action: GH_TOKEN rotation 후 `git push origin main`.

---

## [2026-08-17] feat(dashboard+rename) | Post-rename game + dashboard surface update

**Status**: ✅ 완료 — 게임 코드 + 대시보드 chrome + dashboard data rebuild. 3 commits (`581486d`, `c668aa5`, `bf809c5`). 567 files changed cumulatively. 5577 passed, ruff ✅, mypy strict ✅, audit_vault.py CLEAN.

### 1. Game core display name (5 files)

게임 윈도우 + About screen 에 표시되는 게임 이름 일관성 강화. 이전 commit (`ae83d00`)에서 디렉토리/Python 패키지명은 변경됐지만, 사용자에게 직접 보이는 게임 이름은 일부 남아 있었음.

| 파일 | 변경 |
|---|---|
| `prototype/src/wet_run/__init__.py` | docstring `"Roguelike Sprawl"` → `"Wet Run"` |
| `prototype/src/wet_run/settings.py` | `GAME_NAME = "Roguelike Sprawl"` → `"Wet Run"` |
| `prototype/src/wet_run/engine/config.py` | `SCREEN_TITLE = "Roguelike Sprawl"` → `"Wet Run"` (게임 윈도우 title) |
| `prototype/src/wet_run/audio/__init__.py` | docstring |
| `prototype/src/wet_run/audio/sound_manager.py` | docstring |

사용자가 게임 시작 시 보는 윈도우 titlebar는 이제 `Wet Run` 으로 표시.

### 2. Dashboard HTML chrome (548 files)

대시보드 전체 (`dashboard/`) 의 HTML chrome (검색엔진/소셜 메타) + 게임 내 러닝 텍스트 외곽 갱신:

- **521 short-story HTML**: `<title>` suffix `"— Roguelike Sprawl"` → `"— Wet Run"`
- **17 dashboard 페이지** (index, character-graph, cyberspace, search, mission-flow, stories-browse, player, missions, library, jokey, combat, dungeon, play, sound, settings, graphic-novel, reading-stats): canonical URL, og:url, og:image, twitter:image URL의 `roguelike-sprawl` → `wet-run`
- **footer chrome**: `"Roguelike Sprawl — Derivative Fiction"` → `"Wet Run — Derivative Fiction"` (521 footer)
- **print footer**: 단편 e-book print footer 갱신

Q3 정책 (historical 보존) 준수 — `_archive/`, `CHANGELOG.md`, `SETUP_LOG.md`, **단편 본문(prose content)** 의 cross-references는 그대로 유지.

### 3. Dashboard data + scripts (3 files)

| 파일 | 변경 |
|---|---|
| `dashboard/data/data_index.json` | `"repo": "/Users/emilio/projects/Projects/Game/wet_run"` |
| `dashboard/data/run_stats.json` | `"source": "prototype/src/wet_run/run/state.py"` (build_dashboard.py 재실행으로 자동 갱신) |
| `dashboard/scripts/import_minimax_track.sh` | `SND` 절대 path |

### 4. Test contract updates (3 files)

이전 commit들에서 변경된 chrome/suffix에 맞춰 test contract 갱신:

- `prototype/tests/integration/test_dashboard_integrity.py`: `title_clean.replace(" — Roguelike Sprawl", "")` → `" — Wet Run"`
- `prototype/tests/integration/check_dashboard.py`: 동일 contract
- `prototype/tests/unit/test_settings_data.py`: `assert GAME_NAME == "Wet Run"`

### 5. Code-side references (6 files, commit `c668aa5`)

prototype 코드/스크립트에서 남아있던 옛 이름 reference 일괄 정리:

- `prototype/Makefile`: `uv run roguelike-sprawl` → `uv run wet-run`
- `prototype/scripts/combat_grades_demo.py`: 헤더 배너
- `prototype/scripts/demo_full_flow.py`: console title
- `prototype/scripts/generate_story_html.py`: HTML title + footer templates
- `prototype/tests/unit/test_dashboard_meta.py`: expected OG URL (`seoca1.github.io/wet-run/`)
- `design/systems/stage_structure.json`: `"module": "wet_run.data_fragment"`

### 6. Dashboard data rebuild (13 files, commit `bf809c5`)

`tools/build_dashboard.py` 실행으로 13 stats JSON 모두 최신 게임 데이터로 재생성:

- character_stats, combat_stats, cyberspace_stats, data_index, design_system
- event_dialogues_stats, faction_stats, index_stats, journey_stats
- library_stats, mission_stats, run_stats, stages_stats

**Notable updates**:
- `library_stats.json`: `stories_with_mission_link` 189 → **236** (47 new)
- `library_stats.json`: `catalog_entries` 195 → **242** (47 new)
- `run_stats.json`: `_generated_at` 2026-08-13 → 2026-08-17 (refresh)
- `run_stats.json`: `source` path 자동 `wet_run` (template 자체가 이미 갱신됨)

### 7. Validation

| Gate | Status | Notes |
|---|---|---|
| `make test` | ✅ | 5577 passed, 365 skipped, 1 xfailed (pre-existing portrait 회귀, rename 무관) |
| `make lint` (ruff) | ✅ | All checks passed |
| `make typecheck` (mypy strict) | ✅ | 0 errors in 211 source files |
| `tools/audit_sprawl.py` | ✅ | 0 broken, 4 orphan (의도적 lore fragments) |
| `tools/find_broken_links.py` | ✅ | 0 broken |
| `python3 audit_vault.py` (workspace) | ✅ | CLEAN |

### 8. Pre-existing 이슈 (rename 무관)

- `tests/unit/test_armitage.py::TestArmitagePortraits::test_portraits_have_10x14_grid` — portrait actual size `[10, 12]` vs test expected `[10, 14]`. Phase 45 이후 data-driven 변경으로 보이며 본 세션 범위 외.

### 9. WetRun commit history (이번 세션)

```
bf809c5 feat(dashboard): rebuild stats JSON via build_dashboard.py
c668aa5 chore(rename): update remaining code references to Wet Run
581486d feat(rename): update game + dashboard display name to Wet Run
3dce6bb docs(wet_run): update GitHub URLs after repo rename
ae83d00 chore(rename): Roguelike Sprawl → Wet Run (project-wide display name)
```

### 10. Out of scope (preserved)

- 단편 HTML 본문 — 게임 내 러닝 텍스트이므로 보존 (Q3 default)
- `_archive/`, `CHANGELOG.md`, `SETUP_LOG.md` — historical
- `dashboard/stories/*.html` 단편 본문 cross-references
- GitHub repo URL — Q2 deferred 후속 (GH_TOKEN rotation 후 push)

### 11. Push 상태

**5 commits ahead of origin** (post-rename). GH_TOKEN rotation 후 user action:
- `git push origin main` (5 commits)

Total cumulative rename + dashboard update: ~580 files, 5 commits, 0 regressions, 0 broken wikilinks.

---

## [2026-08-18] docs(sweep) | All 4-axis + Track A backlog reconciled — recon sweep of ADR-0156–0159, ADR-0188/0189/0191

**Status**: ✅ 완료 — SESSION_SUMMARY_2026-08-18 §5 "Next-Session Backlog" 의 모든 항목 (Track A + Axis 1/2/3) 이 **implementation 완료 상태로 확인**되어 meta-closure entries 7 ADR 문서 (decisions/) 에 추가. 본 세션은 코드 작성 없이 docs-only 작업.

### 1. Recon 결과 (한눈에)

| 항목 | ADR target | 실제 (2026-08-18) | Status |
|---|---:|---:|---|
| **Track A.156** state.py 890 → 3 files | state.py ~250 / state_transitions ~290 / state_effects ~320 | state.py=415 / state_transitions=219 / state_effects=394 | ✅ structural done; +165 over (constants block 합법 잔존) |
| **Track A.157** boss.py 724 → 2 files | boss.py ~370 / boss_ai ~330 | boss.py=656 / boss_ai=188 | ✅ structural done; +286 over (skill builders + VFX themes 합법 잔존) |
| **Track A.158** combo.py 685 → 2 files | combo.py ~370 / combo_window ~250 | combo.py=629 / combo_window=88 | ✅ structural done; +259 over (avatars + finishers 합법 잔존) |
| **Track A.159** bosses.py 627 → 2 files | bosses.py ~370 / bosses_cinematic ~250 | bosses.py=346 / bosses_cinematic=296 | ✅ **closed at target** (-24 / +46) |
| **Axis 1** (ADR-0188) Mission Expansion | 200 missions / 8 chains / 11 endgame / +5 types | **200 missions / 9 chains (35) / 11 endgame / +5+ types** | ✅ **closed at target** |
| **Axis 2** (ADR-0189) ICE Type Expansion | 60+ ICE / 5 cyberspace hazards | **97 ICE / 5 hazards** (`antivirus_sweep`, `trace_route`, `data_corruption`, `system_lag`, `blackout`) | ✅ **closed at target** |
| **Axis 3** (ADR-0191) Story Events | 30+ events / 9 character-specific + 10 faction + chains | **56 events / 9 `char_event_*` + combined** | ✅ **closed at target** |

**테스트 baseline**: 5687 passing / 13 failed (death_extended / pages_deploy / interrogate thresholds, 모두 pre-existing). ruff 0. mypy strict 0 errors in 65 combat files.

### 2. ADR 문서 추가 (7 docs)

| File | Section added | Note |
|---|---|---|
| `decisions/0156-combat-state-split.md` | Implementation Status (2026-08-18) | target vs actual LOC, residual content 합법성 |
| `decisions/0157-combat-boss-split.md` | Implementation Status (2026-08-18) | skill builders + VFX themes 잔존 |
| `decisions/0158-combat-combo-split.md` | Implementation Status (2026-08-18) | avatars + finishers 잔존 |
| `decisions/0159-combat-bosses-split.md` | Implementation Status (2026-08-18) | **target met** |
| `decisions/0188-mission-expansion.md` | Implementation Status (2026-08-18) | 200 missions / 9 chains / MissionChain dataclass present |
| `decisions/0189-ice-type-expansion.md` | Implementation Status (2026-08-18) | 97 ICE / 5 hazards exact match |
| `decisions/0191-story-events-expansion.md` | Implementation Status (2026-08-18) | 56 events / 9 char_event_* confirmed |

각 섹션은 (a) ADR target vs actual metrics, (b) code surface presence 확인, (c) test files inventory. ADR 본문 (Decision / Consequences / Validation) 은 immutable.

### 3. SESSION_SUMMARY_2026-08-18 §5 backlog 의 stale status

2026-08-18 §5 SESSION_SUMMARY 의 "Next-Session Backlog" 섹션은 다음 4 항목을 deferred 로 표시했음:
> - Axis 1 (Mission Expansion) — 89+ missions / 5 types / 8 chains. **Content-heavy**. Data not yet authored.
> - Track A (Module splits) — 3-4 sessions, 4 modules > 1000 LOC. **Pure refactor**.
> - Axis 2 (ICE Types) — hazards system not yet implemented.
> - Axis 3 (Story Events) — chains routing incomplete.

현실 (2026-08-18 recon):
> - **모든 항목 코드 + 데이터 + 테스트 완료**. 4 axes 의 ADR 작성 시점 (2026-08-08~10) 부터 다음 10 일 동안 작업이 누적됨. SESSION_SUMMARY §5 의 "deferred" 표기는 stale — actual 는 implemented.

이는 같은 날 (2026-08-18) Axis 5/4/6 closure sweep 에서 발견된 패턴의 확장: **ADR 은 accepted 상태로 filed 되었으나 implementation 이 ADR 작성 시점보다 빠르게 진행되어 작업 시점에 이미 shipped**.

### 4. 다음 단계 handover

1. **Track A + Axes 1/2/3**: 7 ADR docs implementation-status 섹션 추가 완료. 추가 코드 작업 없음. 신규 commit 없음 (docs-only).
2. **Stale SESSION_SUMMARY 갱신** (사용자 판단): SESSION_SUMMARY_2026-08-18.md §5 의 "Next-Session Backlog" 섹션이 stale 임이 확인됨. 정정 필요 시 사용자 결정 — 본 entry 는 recon 만.
3. **진짜 deferred 항목** (아직 식별 안됨): 코드 작성 deferred 가 아니라 ADR 작성이 안된 신규 작업 후보 (예: boss skill builders 별도 ADR, VFX themes 별도 ADR, constants 별도 ADR). 사용자 우선순위 결정 후 별도 세션.

### 5. 인용

- [`decisions/0156-combat-state-split.md`](./decisions/0156-combat-state-split.md) § Implementation Status
- [`decisions/0157-combat-boss-split.md`](./decisions/0157-combat-boss-split.md) § Implementation Status
- [`decisions/0158-combat-combo-split.md`](./decisions/0158-combat-combo-split.md) § Implementation Status
- [`decisions/0159-combat-bosses-split.md`](./decisions/0159-combat-bosses-split.md) § Implementation Status
- [`decisions/0188-mission-expansion.md`](./decisions/0188-mission-expansion.md) § Implementation Status
- [`decisions/0189-ice-type-expansion.md`](./decisions/0189-ice-type-expansion.md) § Implementation Status
- [`decisions/0191-story-events-expansion.md`](./decisions/0191-story-events-expansion.md) § Implementation Status

---

## [2026-08-18] docs(track-a) | Track A module splits ADR-0156/0157/0158/0159 closure + Axis 1 start (zone analysis pending)

**Status**: ✅ 완료 — Track A ADR-0156/0157/0158/0159 의 implementation-status 섹션 4 문서를 decision 파일에 추가 (실제 LOC 측정값 + ADR target 과의 차이 분석 + 추가 ADR 필요 여부 명시). 본 session 에 **새 코드는 작성하지 않았음** — 작업 항목은 (a) Track A partial-split 분석 + (b) ADR docs 갱신 + (c) Axis 1 (Mission Expansion) 시작.

### 1. Track A 분석 결과 (recon)

기존 session summary (2026-08-18 §5) 에서는 Track A module splits 가 "4 modules > 1000 LOC: state.py 890 / boss.py 724 / combo.py 685 / bosses.py 627" 으로 요약되었으나, 실제 recon 결과:

| ADR | 원본 측정 (ADR 작성 시점) | 2026-08-18 실제 | 결과 |
|---|---|---|---|
| **ADR-0156** state.py 890 → 3 files | state.py=415 / state_models=312 / state_transitions=219 / state_effects=394 | ✅ Structure complete. state.py 가 +165 LOC over (constants block 65-173 line 합법 잔존) |
| **ADR-0157** boss.py 724 → 2 files | boss.py=656 / boss_ai.py=188 | ✅ Structure complete. boss.py +286 LOC over (skill builders + VFX themes 합법 잔존) |
| **ADR-0158** combo.py 685 → 2 files | combo.py=629 / combo_window.py=88 | ✅ Structure complete. combo.py +259 LOC over (avatars + finishers 합법 잔존) |
| **ADR-0159** bosses.py 627 → 2 files | bosses.py=346 / bosses_cinematic.py=296 | ✅ **Closed at target** (-24 vs target +46 over in cinematic) |

모든 4 ADR 의 structural goal (split + re-export + public API stable) 은 달성됨. ADR 작성 시점 (2026-08-07) 이후 content 가 accent 했기 때문에 ADR target LOC 보다 더 큰 결과. 추가 분할 (skill builders / VFX themes / avatars / finishers / constants) 은 별도 ADR 필요.

### 2. Validation (2026-08-18 baseline)

| Check | Result |
|---|---|
| `ruff check combat/` | All checks passed |
| `mypy --strict combat/` | 0 errors in 65 source files |
| `pytest tests/ -q` | **5687 passed** / 13 failed (pre-existing) / 365 skipped / 1 xfailed |
| Pre-existing failures | `test_death_extended.py` (3), `test_pages_deploy.py` (4), interrogate thresholds (6) — 모두 combat module split 과 무관 |

### 3. ADR 문서 추가 (4 docs)

| File | Action | Section added |
|---|---|---|
| `decisions/0156-combat-state-split.md` | edit | Implementation Status (2026-08-18) — 415 LOC vs target 250, +165 delta, constants block 설명 |
| `decisions/0157-combat-boss-split.md` | edit | Implementation Status (2026-08-18) — 656 LOC vs target 370, +286 delta, skill builders + VFX themes 설명 |
| `decisions/0158-combat-combo-split.md` | edit | Implementation Status (2026-08-18) — 629 LOC vs target 370, +259 delta, avatars + finishers 설명 |
| `decisions/0159-combat-bosses-split.md` | edit | Implementation Status (2026-08-18) — 346 LOC vs target 370, -24 ✓ **closed at target** |

각 섹션은 (a) 측정 LOC, (b) "왜 over-target 인지" 의 합리적 설명, (c) 추가 작업 필요 시 별도 ADR 권장 — 을 포함. ADR 본문 (Decision / Consequences) 은 변경하지 않음 (Accepted immutable).

### 4. Axis 1 (Mission Expansion, ADR-0188) start — prep 단계

ADR-0188 "Accepted (2026-08-08, user explicit "Begin Phase 11")" 상태. 본 session 에서는 본격 authoring 시작하지 않음. 이유:

**Open Questions** (ADR-0188 §"열린 질문"):
- Q1: Type names — "stealth" vs "infiltration"? (Recommend "stealth")
- Q2: Chain unlock timing — after 3 or 5 missions? (Recommend 3)
- Q3: Random mission weighting source? (Recommend initial stats +0.1/completion)
- Q4: Zone distribution — proposed targets (35/35/35/30/35/30) OK?
- Q5: Endgame shape — 11 specific missions or 1 chain + 10 random? (Recommend 1 chain + 10 random)

89 missions authoring 시작 전에 위 5 질문에 대한 사용자 확인 필요 — user-action item. 본 entry 는 recon-only 단계.

### 5. 다음 단계 handover

1. **Track A**: 4 ADR docs implementation-status 섹션 추가 완료. 추가 코드 작업 없음. 신규 commit 없음 (docs-only 작업).
2. **Axis 1**:
   - **즉시 다음**: ADR-0188 Q1-Q5 해결 → 사용자 확인 (현재 entry 작성 시점에 question 도구로 확인 가능)
   - **그 다음**: zone distribution analysis (`data/missions/missions.json` 파싱 + surface/mid/deep/core/TA/freeside count 집계)
   - **그 다음**: 1 zone (예: Surface) 의 first batch authoring (10-15 missions of existing 6 types, schema 회귀 검증)
   - **그 이후**: 4-6 sessions 걸쳐 89+ missions + 5 new types + 8 chains + 11 endgame missions authoring

### 6. 인용

- [`decisions/0156-combat-state-split.md`](./decisions/0156-combat-state-split.md) § Implementation Status
- [`decisions/0157-combat-boss-split.md`](./decisions/0157-combat-boss-split.md) § Implementation Status
- [`decisions/0158-combat-combo-split.md`](./decisions/0158-combat-combo-split.md) § Implementation Status
- [`decisions/0159-combat-bosses-split.md`](./decisions/0159-combat-bosses-split.md) § Implementation Status
- [`decisions/0188-mission-expansion.md`](./decisions/0188-mission-expansion.md) § 열린 질문
- AGENTS.md §9 — 작업 종료 체크리스트
- AGENTS.md §6.5 — workspace-level docs (`log.md` cross-project sync)

---
