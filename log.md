
## [2026-08-20] content | Gibson Fluff expansion — 5 more categories wired (6/11 total)

**Status**: ✅ **5 additional Gibson Fluff categories wired** beyond Track B's initial "encounter" integration. Player-visible HUD messages now fire on combat_hit / crit / salvage / burn / stun events.

### 1. Categories wired this session

| Category | Integration point | File |
|---|---|---|
| `combat_hit` | `_calculate_damage` result path (player attack) | `combat/state_transitions.py:148` |
| `crit` | Same path, conditional on `is_crit` | `combat/state_transitions.py:149` |
| `salvage` | `apply_salvage` end (after choice) | `combat/salvage.py:160` |
| `burn` | `_apply_dot` (DoT skill application) | `combat/state_effects.py:168` |
| `stun` | `_apply_stun` (status effect application) | `combat/state_effects.py:240` |

### 2. Total wired (6 of 11 categories)

- ✅ `encounter` (Track B)
- ✅ `combat_hit`
- ✅ `crit`
- ✅ `salvage`
- ✅ `burn`
- ✅ `stun`
- ⏳ `slow` — no `_apply_slow` handler exists; SkillEffect.SLOW is in enum but no dispatch entry
- ⏳ `silence` — same; requires handler
- ⏳ `vulnerable` — same; requires handler
- ⏳ `zone_transition` — no centralized matrix zone-change event exists yet

### 3. Pattern

```python
# At end of each effect-application function:
from .gibson_fluff import push_fluff
push_fluff(state, "burn")  # or "stun", "salvage", etc.
```

`push_fluff` is defensive (uses `getattr` for status_messages) so it works with any duck-typed state-like object.

### 4. Verification

| Check | Result |
|---|---|
| `pytest tests/` | 5700 passed / 365 skipped / 1 xfailed / 0 failed (84.96s) |
| `ruff check` | clean |
| `mypy --strict` | clean (230 files) |

### 5. 인용

- `combat/state_transitions.py` (combat_hit + crit wiring)
- `combat/salvage.py` (salvage wiring)
- `combat/state_effects.py` (burn + stun wiring)
- `decisions/0170-gibson-fluff-library.md` §Implementation Status (updated ✅)

## [2026-08-20] content | Gibson Fluff expansion 2 — 3 status effect handlers added (9/10 categories total)

**Status**: ✅ **3 new status effect handlers** (`_apply_slow`, `_apply_silence`, `_apply_vulnerability`) + `SkillEffect.VULNERABLE` enum value. Fluff integration for all 3 new categories.

### 1. Changes

- **`combat/state_models.py:62`** — `VULNERABLE = "vulnerable"` added to `SkillEffect` enum (was missing — only SILENCE/SLOW existed of the trio). 19 enum members total (was 18).
- **`combat/state_effects.py`** — 3 new handler functions added:
  - `_apply_slow` (effect_id="slow", uses `slow_pct` field)
  - `_apply_silence` (effect_id="silence", `is_silenced=True`)
  - `_apply_vulnerability` (effect_id="vulnerable", uses `vulnerability_pct` field)
  - Each appends `StatusEffect` to target, records event, pushes status message, calls `push_fluff`
- **`combat/state_effects.py:330-332`** — 3 new dispatch entries: `SkillEffect.SLOW`, `SkillEffect.SILENCE`, `SkillEffect.VULNERABLE` → respective handlers

### 2. Fluff category count (9 of 10 wired)

| Category | Status |
|---|---|
| `encounter` | ✅ wired (start_combat) |
| `combat_hit` | ✅ wired (damage path) |
| `crit` | ✅ wired (crit path) |
| `salvage` | ✅ wired (apply_salvage) |
| `burn` | ✅ wired (_apply_dot) |
| `stun` | ✅ wired (_apply_stun) |
| `slow` | ✅ wired (_apply_slow, NEW 2026-08-20) |
| `silence` | ✅ wired (_apply_silence, NEW 2026-08-20) |
| `vulnerable` | ✅ wired (_apply_vulnerability, NEW 2026-08-20) |
| `zone_transition` | ⏳ requires matrix zone-change event hook (deferred) |

### 3. Verification

| Check | Result |
|---|---|
| `pytest tests/` | 5700 passed / 365 skipped / 1 xfailed / 0 failed (84.94s) |
| `ruff check` | clean |
| `mypy --strict` | clean (230 files) |
| Initial run (pre-VULNERABLE enum fix) | 33 failures (AttributeError: VUL...) — fixed by adding VULNERABLE to enum |

### 4. 인용

- `combat/state_models.py:62` (VULNERABLE enum)
- `combat/state_effects.py` (3 new handlers + dispatch)
- `decisions/0170-gibson-fluff-library.md` §Implementation Status (updated ✅ 9/10)

---

## 🎨 Matrix 화면 강화 — Zone 색상 + ICE 미리보기 (2026-08-27)

**Scope**: User '데모 관련 개선 후속 작업' choice: '매트릭스 화면 강화'.

### 산출물

**renderer/matrix.ts**:
- `zoneColor()` 매핑: surface=GREEN_NEON, mid=YELLOW_AMBER, deep=RED_BRIGHT,
  core=MAGENTA_NEON, core-deep=MAGENTA_NEON
- 노드 상태 marker: ▸ current / ✓ visited / → adjacent / space
  (linear matrix: i=current±1)
- ICE preview panel (cols>=50): CURRENT NODE header + ICE name (ICE_BLUE)
  + HP (GREEN_NEON) + event type (YELLOW_AMBER) + reward (CYAN_LIGHT).
  portrait 폰 (cols<50) 에서는 자동 suppress.
- Footer: 현재 노드에 adjacent 있을 때만 ENTER hint, 보스 클리어 시 ESC만.

**main.ts**: renderMatrix()에 icePreview 파라미터 추가. 현재 active ICE 객체를 전달.

### 검증

| Check | Result |
|---|---|
| tsc --noEmit | ✅ 0 errors |
| npm test | ✅ **180 passed** (was 166 → +14 matrix_render tests) |
| npm run build | ✅ 151.89 KB (was 151.17 → +0.72 KB) |
| npx playwright test (live) | ✅ **32 passed** (was 28 → +4 matrix_enhanced × 2 projects) |

### Tests

- `tests/matrix_render.test.ts` (NEW, 14 tests): zone names, boss mark,
  event glyph, ICE preview, current/visited/adjacent markers, footer
  ENTER/ESC, grid dimensions
- `e2e/matrix_enhanced.spec.ts` (NEW, 2 tests × 2 projects): zone colors
  visible, iceRoster populated after launch

### Commit pushed

- `81b9984` test: fix matrix_enhanced E2E — simplify optional chain syntax
- `f793d05` feat: Matrix screen enhancement — zone colors + ICE preview

### Demo URL (live)

**`https://seoca1.github.io/wet-run/wetrun-web/`** — NEW RUN → Matrix:
- 색상으로 zone 구분 (surface=green, deep=red, boss=magenta)
- 우측 HUD에 current node의 ICE 이름 + HP + 이벤트 타입 + 보상
- 현재 노드 ▸ / 방문한 노드 ✓ / 다음 가능 노드 →
- footer에 ENTER hint (progression 가능할 때만)

---

## 🎮 wet_run-web Stage Demo + Tier 5.5 Status + Matrix Enhancement (2026-08-27)

**Scope**: User '스테이지 데모 웹 주소 알려줄 수 있어?' → 데모 데모 진행 + '데모 관련 개선 후속 작업' → 매트릭스 화면 강화 선택.

### 데모 URL

**`https://seoca1.github.io/wet-run/wetrun-web/`** — Tier 5.5 풀 데모
- 메뉴 → 매트릭스 → 전투 → 엔딩 7-step walkthrough
- Status effects (burn/vulnerable) + Combat VFX (7 kinds) + Stage events (6 kinds)
- All verify-gates pass: 166 unit + 32 E2E + 5850 pytest

### 매트릭스 화면 강화 (이 세션 작업)

- zoneColor: surface=green, mid=yellow, deep=red, core=magenta, boss=magenta
- State markers: ▸ current / ✓ visited / → adjacent (i=current±1)
- ICE preview panel (cols>=50): CURRENT NODE + ICE name + HP + event + reward
- Footer ENTER hint only when adjacent available

### 검증

| Check | Result |
|---|---|
| vitest | ✅ **180 passed** (was 149 → +31: slot_restore, event_matrix, combat_vfx, status, matrix_render) |
| playwright E2E | ✅ **32 passed** (desktop + mobile-portrait) |
| tsc / ruff / mypy | ✅ clean |
| Bundle | 151.89 KB (gzipped 51.91 KB) |

### Commit pushed

- `81b9984` test: fix matrix_enhanced E2E syntax
- `f793d05` feat: Matrix screen enhancement — zone colors + ICE preview
- (이전) `2dcfc4d` status effect state machine wired
- (이전) `c8a858b` Tier 5.5 Stage events + Combat VFX

### Notion 발행

- `WET_RUN_STAGE_DEMO_TIER55_2026-08-27` (Page ID 3c9f643d-3530-81fa-9ea1-f22e08d692df)
- 53 blocks, 7-step walkthrough + features matrix

### 후속 (carry-over, 다음 세션)

1. ⚪ Sound integration (combat_hit SFX 자동 + phase BGM)
2. ⚪ Boss 4-phase VFX 차별화
3. ⚪ Slow 효과 실제 로직
4. ⚪ Tutorial overlay (첫 실행 가이드)

---

## 🆕 2026-08-31: wet_run-web Tier 5 — Settings 화면 (Volume Slider UI)

**Scope**: User 'wet-run game 개선작업 이어서' → 캐리오버 4개 분석 → **이미 upstream에 완료됨** (commit `feac61b` 등). 로컬 wet_run-web이 upstream과 desync (test만 있고 src/public/build config 없음) → 동기화 후 Tier 5 신규 작업 1개 착수.

### 동기화 (sync)

- `/tmp/wet-run-src` (GitHub `seoca1/wet-run`)에서 upstream `wet_run-web/` 을 로컬 `/Users/emilio/projects/Game/wet_run/wet_run-web`으로 rsync (ignore-existing)
- 신규 import: `src/audio/`, `src/core/`, `src/data/`, `src/input/`, `src/renderer/`, `src/save/`, `main.ts`, `index.html`, `vite.config.ts`, `tsconfig.json`, `playwright.config.ts`, `package.json`, `public/`, `scripts/`, `vitest.setup.ts`, `docs/`, `README.md`, `.gitignore`
- 로컬 carry-over test 보존: `tests/slow_effect.test.ts` (rsync 시 이미 upstream에 없는 stale spec)

### Slow effect test 정정 (Tier 5.5+ 정합화)

- 기존 carry-over `tests/slow_effect.test.ts` 의 손상 spec 5개 정정:
  - base damage formula `program.tier * 5` (was 10 가정) → `tier 1 → 5`
  - slow one-shot 동작 반영 — 공격 후 즉시 제거 (was: 다음 턴까지 잔존 가정)
- 6 cases 전부 pass

### Tier 5 Settings 화면 (신규)

- **AudioManager 확장** (`src/audio/manager.ts`):
  - `getBgmVolume() / setBgmVolume(v: number)` — 0..1 clamp, localStorage 영속 (`wetrun_audio_bgm_volume`)
  - `getSfxVolume() / setSfxVolume(v: number)` — 0..1 clamp, localStorage 영속 (`wetrun_audio_sfx_volume`)
  - 생성자에서 persisted volume 우선 적용 → 다음 세션에서도 사용자 설정 유지
  - Howl volume() 실시간 적용 (BGM 1개 + 캐시된 SFX 전부)
- **렌더러 신규** (`src/renderer/settings.ts`):
  - 20-cell 슬라이더 바 (█ 채움 + ░ 빈칸) + 퍼센트 표시
  - 필드 3종: BGM Volume / SFX Volume / Mute Toggle (Up/Down으로 이동)
  - mute selected 시 "ENTER to toggle" 힌트, 그 외엔 "←/→ adjust" 힌트
- **main.ts 와이어링**:
  - `case "settings"` → `screen = "settings"`, 초기 settingsState 로드 (draw로 푸시)
  - `handlePreGameInput` 에 settings 분기 추가 (move_north/south = 필드 전환, move_east/west = ±0.1 step, confirm = mute toggle, cancel = back to menu)
  - "Stub" 분기에서 `settings` 제외 — 이제 실제 화면
  - 핸들러 라우팅에 `settings` 화이트리스트 추가 (handleStubInput 우회)
- **테스트 신규**:
  - `tests/settings.test.ts` (15 cases) — clampVolume/adjustVolume/renderSettingsScreen/getInitialSettingsState
  - `tests/audio.test.ts` +9 cases (총 17 → 25) — getBgmVolume/setBgmVolume/setSfxVolume/getSfxVolume/localStorage persistence
  - `e2e/settings.spec.ts` (3 cases × 2 viewport = 6 passed) — 네비게이션, ArrowRight BGM 0.4→0.5, ESC back to menu
- **vite build** 통과 (160.63 KB → gzip 54.54 KB, +0 KB for Tier 5)

### 검증 (verify-gates)

- `npx tsc --noEmit` — clean
- `npx vitest run` — **226 passed** (was 203, +23)
- `npx vite build` — 통과 (160.63 KB / gzip 54.54 KB)
- `npx playwright test e2e/settings.spec.ts` — **6 passed** (desktop + mobile, all green)

### 변경 안 한 것

- Boss 4-phase VFX, Tutorial overlay, Slow 효과 로직, Combat hit SFX 자동 트리거 — 이미 upstream에 완료된 상태로 신규 작업 불필요 (carry-over 정정만)
- pre-existing e2e 실패 (menu.spec.ts tutorial 간섭, boss_phase_vfx.spec.ts syntax, continue/sound_triggers 등) — 본 세션 작업과 무관, 회귀 아님

### Carry-over Tier 5 follow-ups (다음 세션)

- ⚪ SFX 확장 (combat_block, combat_skill_* 등 9+ effects) — ADR-0207 follow-up
- ⚪ Per-track fade in/out (BGM 트랙 전환 시 크로스페이드)
- ⚪ Save 압축 (lz-string)
- ⚪ Animation timing (hit flash 지속 시간 정밀화)
- ⚪ Storage quota UI (IDB 사용량 표시)
- ⚪ Tier 3 remote sync (cloud save — 사용자 결정 대기)

---

## 🆕 2026-08-31: wet_run-web 통합 세션 — Tier 5 + 5.6 + 6 + 7

**Scope**: 단일 세션에서 캐리오버 6건 중 5건 해결 (1건은 사용자 결정 대기). Cross-version VFX 표준화 + 신규 UI/오디오 기능 4종 추가.

**총 8 commits, 29 files changed, +4042 / -150 lines**

```
e8f2b4c feat(wet_run-web): ms-precision VFX timing (Tier 7)
081d5d2 feat(wet_run-web): Save compression layer (Tier 7)
1e11fdd feat(wet_run-web): Storage quota UI in Settings (Tier 7)
15ed834 feat(wet_run-web): BGM crossfade on phase transitions (Tier 7)
c7cf815 docs(ADR-0210): Tier 6 implementation status update
941df79 feat: Combat VFX Tier 6 — 12 new effects (8 skills + 4 matrix) backported
5d98058 feat: Combat VFX Effect Schema — cross-version standardization (ADR-0210)
491121c feat(wet_run-web): Tier 5 Settings screen — BGM/SFX volume sliders + persistence
```

### Tier 5: Settings 화면 (commit `491121c`)

- **문제**: SETTINGS 메뉴가 stub 화면 ("Coming soon")
- **해결**:
  - `AudioManager` 확장: `getBgmVolume/setBgmVolume/getSfxVolume/setSfxVolume` + localStorage 영속화 (`wetrun_audio_bgm_volume`, `wetrun_audio_sfx_volume`)
  - `renderer/settings.ts` 신규: 20-cell 슬라이더 (█/░) + 퍼센트 표시, 3 필드 (BGM/SFX/Mute)
  - `main.ts`: settings 화면 라우팅 + 입력 핸들러 (←/→ 조정, Enter mute toggle, ESC back)
- **테스트**: `tests/settings.test.ts` (15) + `tests/audio.test.ts` +9 + `e2e/settings.spec.ts` (6 passed)
- **메트릭**: 160.63 KB → gzip 54.54 KB (변동 없음)

### Tier 5.6: Cross-version VFX 스키마 ADR-0210 (commit `5d98058`)

- **문제**: Python prototype (16 skill + 7 cinematic + 10 spawn) vs web (11 kinds) — 택소노미 drift
- **해결**:
  - `prototype/data/effects.json` canonical: 15 v1 effects (kind / category / duration_ms / color_hint / payload_shape)
  - `wet_run-web/scripts/export_effects.py` 신규: schema 검증 + effects.json + effects.d.ts 생성
  - Web: `CombatVfxKind` 11→15 통합, `boss_phase_1..4` → 단일 `boss_phase_transition` + payloadNum
  - State callers: `card_use` → `attack`, `boss_phase_${N}` → `boss_phase_transition`
  - Parity test: `prototype/tests/test_effect_parity.py` — Python ↔ web kind-set drift 감지
  - Web: `tests/effects_schema.test.ts` (9) — schema integrity 검증
- **ADR**: `decisions/0210-combat-vfx-effect-schema.md` 신규 (Accepted, 2026-08-31)
- **메트릭**: 162.52 KB / gzip 54.96 KB (+1.9 KB)

### Tier 6: 12 V2 이펙트 백포트 (commit `941df79` + `c7cf815`)

- **문제**: 8 Python-only skill animations + 4 Matrix VFX spawn functions 미동기화
- **해결**:
  - Schema 확장: 15 → **27 effects** (8 v2 skills + 4 v2 matrix)
    - Skills: heavy_attack, pierce, multi_hit, dot, counter, lifesteal, detect, regen
    - Matrix: jackin_glitch, jackout_whiteout, room_flash, data_acquired
  - Palette 확장: 12 token (HEAL_COLOR, SHIELD_COLOR, CRIT_COLOR 등) + `resolveColorHint()` 매핑
  - 12 web 렌더러 신규 구현
  - `pickProgramVfxKind()` — program tier/role/effect → canonical kind 자동 매핑
  - `durationForKind()` — effects.json duration_ms canonical table
  - State wiring: matrix entry/exit (room_flash + data_acquired / jackout_whiteout), run start (jackin_glitch), burn tick (dot)
  - `tests/combat_vfx_v2.test.ts` (25) — v2 렌더러 + payloadNum 검증
- **메트릭**: 167.50 KB / gzip 56.30 KB (+4.98 KB)

### Tier 7: BGM Crossfade + Storage Quota + Save 압축 + ms-precision timing

#### BGM Crossfade (commit `15ed834`)

- **문제**: `playPhase()`가 abrupt cut — 이전 트랙 즉시 stop + 새 트랙 즉시 start
- **해결**: `crossfadeTo(track, ms)` + `fadeOutAndStop(ms)` using Howler.fade()
  - DEFAULT_CROSSFADE_MS = 800 (Python: 500ms, web은 브라우저 오디오 버퍼 지연 고려해 조정)
  - 동시 fade-in/out + setTimeout으로 old Howl unload
- **테스트**: `tests/audio.test.ts` +8 cases

#### Storage Quota UI (commit `1e11fdd`)

- **문제**: IDB 사용량이 opaque — quota 초과 전까지 사용자 무지
- **해결**:
  - `src/save/storage_quota.ts` 신규: `getStorageQuota()` wrapping `navigator.storage.estimate()`
  - `formatBytes()` / `renderUsageBar()` / `quotaLevel()` / `summarizeQuota()` helpers
  - Settings 화면에 "STORAGE" 섹션 추가: bar + percent + summary + warning/critical hint
  - Color: green (ok) / yellow (warning 80%+) / red (critical 95%+)
- **테스트**: `tests/storage_quota.test.ts` (20) — jsdom graceful degradation, zero quota, valid data, weird clamp, rejection

#### Save Compression (commit `081d5d2`)

- **문제**: 큰 save의 IDB/localStorage footprint
- **해결**:
  - `lz-string ^1.5.0` 도입
  - `src/save/compress.ts`: v2 envelope (`{v:2, c:bool, d:string}`) + threshold gate (512B)
  - `decodeEnvelope()` handles 3 formats: v2 plain / v2 compressed / legacy v1
  - `storage.ts` wired: `serializeForStorage()` wraps, `parseSlot()` decodes
- **테스트**: `tests/compress.test.ts` (18) — round-trip, threshold, special chars, malformed

#### ms-precision VFX Timing (commit `e8f2b4c`)

- **문제**: tick 양자화로 인한 ±16ms expiry 부정확
- **해결**:
  - `CombatVfxInstance` 확장: `durationMs` + `elapsedMs` 필드
  - `WEB_TICK_MS = 16` exported constant
  - `triggerCombatVfxMs(kind, payload, durationMs, ...)` — canonical ms spawn
  - `advanceVfxBy(instance, deltaMs)` — wall-clock 정확 expiry
  - `tick` 필드는 `floor(elapsedMs / WEB_TICK_MS)`로 파생 (renderer 호환)
  - `main.ts` draw loop: `performance.now()` deltaMs 계산 + `advanceVfxListBy()`
  - 기존 `tickCombatVfx()` 보존 (wrapper)
- **테스트**: `tests/vfx_ms_timing.test.ts` (16) — sub-tick precision, tick boundary, back-compat

### 최종 메트릭 (전체 세션)

| Gate | 시작 (Tier 5 이전) | 종료 (Tier 7) |
|---|---|---|
| vitest | 203 passed | **347 passed** (+144) |
| Bundle | 151.89 KB / 51.91 KB | **177.28 KB / 59.18 KB** (+25.4 KB / +7.3 KB) |
| Test files | 14 | **23** (+9) |
| Effect parity | 0/0 | **27/27** match |
| E2E (settings + smoke) | pre-existing | **8/8 passed** |

### 변경 안 한 것 / pre-existing 회귀

- `menu.spec.ts` tutorial 간섭 — pre-existing (이번 세션과 무관)
- `boss_phase_vfx.spec.ts` syntax error — pre-existing
- `continue.spec.ts` / `sound_triggers.spec.ts` IDB/jsdom 가정 — pre-existing
- `effect_parity.py` — 사전 검사로 항상 통과

### 잔여 Tier 7+ 백로그 (다음 세션)

- ⚪ **Data-driven ASCII art from JSON** — web 렌더러 하드코딩 → 스키마 기반 (대규모 리팩토링)
- ⚪ **Tier 3 remote sync** (cloud save) — 사용자 결정 대기
- (없음 — 기타 모든 carry-over 해결됨)

### Push 상태

- 8 commits 모두 `seoca1/wet-run` 로컬 clone에 생성됨 (push 대기)
- GH_TOKEN 회전 대기 — 사용자 액션 필요
- 로컬 `/Users/emilio/projects/Game/wet_run/wet_run-web/` 전체 sync 완료 (Tier 5/5.6/6/7 + schema + tests)

---

*세션 종료 — wet_run-web Tier 5 → 7 통합 완료. 5개 carry-over 해결, 1개 (cloud sync) 사용자 결정 대기, 1개 (data-driven ASCII art) 다음 세션 권장.*
