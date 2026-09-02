# Engagement Layer (ADR-0140)

> **Status**: v1.0.0 polish complete (Top 3: Memory Fragments + Construct Whisper + Module split scaffolding)
> **Cycle**: v1.1.0 (P2 proposals)
> **Owner**: variable reward nodes implemented 2026-08-03

## Overview

ADR-0140은 8개 engagement proposal 중 Top 3 (Memory Fragments + Construct Whisper +
module split scaffolding) 만 v1.0.0 cycle에서 구현. v1.1.0 cycle에서 P2/P3 의 나머지
5개 proposal (Variable Reward Nodes, Faction Tension, Auto-Play Tempo, Near-Miss,
Death Replay) + ADR-0140 P3 (Grade 6 Master Whisper) 가 defer 됨.

이 문서는 v1.1.0 P2/P3 의 Variable Reward Nodes (제안 6) + Near-Miss Extraction (제안 3)
디자인 스펙 + 구현 노트.

## Variable Reward Nodes (ADR-0140 §Proposal 6)

### 골재

Matrix 안의 DATA node 일부가 **anomaly variant** 로 표시된다. Jack-in 시 시각적으로
구분되며 (◆ glyph, magenta color), first entry 시 one-shot bonus reward 부여.

### 게임 디자인

- **Probabilities**: 30% of DATA nodes are anomalies (per ADR-0140)
- **Visual distinction**:
  - Glyph: `◆` (대비: regular DATA = `$`)
  - Color: `(255, 100, 255)` magenta (대비: regular DATA = `(255, 215, 0)` gold)
  - Label: "Anomaly" (대비: "Data")
- **Trigger**: player enters the anomaly node (first entry only)
- **One-shot**: `state.anomaly_triggered` set 으로 중복 트리거 방지

### Reward 종류 (Pillar 4 safe — no cross-run inheritance)

| Reward | Amount | Description | Pillar 4 Check |
|---|---|---|---|
| **CREDITS** | +50 | in-run currency (flat) | ✅ No inheritance |
| **SALVAGE** | +1 | in-run crafting material | ✅ Consumed in-run |
| **INFO** | +1 | narrative data fragment | ✅ Ephemeral |

**Weighted uniform**: 모든 reward 33% 확률. Tier scaling (later grade = bigger reward)
은 v1.1.0+ deferred.

### Pillar 정합 검증

- **Pillar 1 (The Run)**: anomaly 는 run-scoped. 새 런 = 새 anomaly detection.
- **Pillar 2 (The Matrix)**: anomaly 는 cyberspace 안 phenomenon.
- **Pillar 3 (The Flatline)**: anomaly reward 는 flat bonus, death 시 잃음.
- **Pillar 4 (The Build)**: rewards 는 *unlock-only* 형태로 cross-run inheritance 없음.
  - credits: in-run currency (사망 시 손실)
  - salvage: in-run crafting (사망 시 손실)
  - info: narrative piece (일회성)
- **Pillar 5 (The Style)**: anomaly 는 깁슨 코퍼스 톤 ("이 코드는 뭔가 다르다") 정합.

### Flow

```
[Player navigates matrix with arrow keys]
    |
    v
[_handle_cyberspace_movement() called]
    |
    v
[best_neighbor determined]
    |
    v
[state.current_node_id = best_neighbor.id]
    |
    v
[check_memory_fragment_on_node_entry() — ADR-0140 §2]
    |
    v
[NEW: check_anomaly_reward_on_node_entry() — ADR-0140 §6]
    |
    +-- if best_neighbor.is_anomaly AND not in triggered set:
    |   +-- pick random reward from anomaly_reward table
    |   +-- apply reward to state (credits / salvage_fragments / info_pieces)
    |   +-- append status message: ">>> Anomaly recovered: ..."
    |   +-- add best_neighbor.id to state.anomaly_triggered
    |
    +-- else: no-op
```

### 구현 노트

**파일**:
- `matrix/node.py` — `is_anomaly: bool = False` field 추가 (with `__post_init__` validation: DATA only)
- `matrix/generator.py` — `ANOMALY_PROBABILITY = 0.30` constant + 30% check per DATA node
- `matrix/anomaly_reward.py` (NEW) — `AnomalyRewardKind`, `AnomalyReward`, `AnomalyResult`, `roll_anomaly_reward`, `apply_anomaly_reward`, `check_anomaly_reward_on_node_entry`
- `engine/cyberspace_view.py` — `_ANOMALY_GLYPH` + `_ANOMALY_COLOR` constants + `_draw_node()` override + on_node_enter hook
- `engine/state.py` — `AppState.anomaly_triggered: set[str]` field
- `tests/unit/test_variable_reward.py` (NEW) — 22 tests across 5 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (143 source files)
- pytest: ✅ 3300 passed (22 new), 664 skipped, 0 failed

**Test coverage**:
- `TestNodeAnomalyField`: 5 tests (default false, DATA allowed, non-DATA rejected)
- `TestAnomalyProbability`: 4 tests (constant=0.30, empirical 0.20-0.40, label)
- `TestAnomalyReward`: 7 tests (roll, distribution, apply each kind, missing fields, message)
- `TestAnomalyTriggerOneShot`: 4 tests (non-anomaly, first entry, re-entry, multiple)
- `TestAnomalyIsPillar4Safe`: 2 tests (no meta_state, flat rewards)

### 향후 작업 (v1.1.0 ADR-0140 P2/P3 Deferred)

- **Faction Tension Events** (제안 7): 15-25% mission 에서 faction conflict trigger
- **Auto-Play Tempo Layering** (제안 8): graphic novel pacing variations
- **Near-Miss Extraction** (제안 3): 80%+ HP jack-out bonus
- **Death Replay** (제안 5): Hall of Dead echo
- **Grade 6 Master Whisper** (제안 4): master tier voice differentiation
- **Tier scaling** for anomaly rewards (grade 5+ = bigger bonuses)

### Cross-Reference

- `decisions/0140-engagement-layer.md` — proposal status (Phase 1+2 done, Phase 3 deferred)
- `decisions/0060-project-improvement-plans.md` — workspace-level improvement tracker
- `IMPROVEMENTS.md` — historical 2026-07-01 cycle (Phase 5→6)
- `log.md` — 2026-08-03 entry for this commit cycle

---

## Near-Miss Extraction (ADR-0140 §Proposal 3)

### 골재

Player 가 exit node 도달 시 HP 가 threshold (default 80%) 이상으로 남아있으면, bonus reward.
**Death-avoidance payoff** — careful play 가 보상받음.

### 게임 디자인

- **Threshold**: 80% HP (default, configurable via `DEFAULT_NEAR_MISS_HP_THRESHOLD`)
- **Trigger**: player enters an EXIT node (`NodeKind.EXIT`)
- **One-shot per run**: `state.near_miss_triggered: bool` flag
- **Reward**:
  - +75 credits (in-run currency)
  - +1 salvage fragment (in-run crafting material)

### Pillar 정합 검증

- **Pillar 1 (The Run)**: one-shot per run, 새 런 = 새 기회.
- **Pillar 3 (The Flatline)**: HP > 80% 를 유지하는 것이 death avoidance 와 직접 연결.
- **Pillar 4 (The Build)**: rewards 는 in-run, no cross-run inheritance.
- **Pillar 5 (The Style)**: 깁슨 코퍼스 — "good contractor walks away with the prize" 톤.

### 흐름

```
[Player navigates matrix with arrow keys]
    |
    v
[Player enters EXIT node]
    |
    v
[best_neighbor.kind == NodeKind.EXIT]
    |
    v
[check_near_miss_extraction()]
    |
    +-- if state.player_hp / state.player_max_hp >= 0.80 AND not already_triggered:
    |   +-- apply +75 credits + +1 salvage fragment
    |   +-- append status message: ">>> Near-miss extraction (80% HP): ..."
    |   +-- set state.near_miss_triggered = True
    |
    +-- else: no-op
```

### 구현 노트

**파일**:
- `matrix/near_miss.py` (NEW) — `NearMissRewardKind`, `NearMissReward`, `NearMissResult`,
  `compute_hp_ratio`, `check_near_miss_extraction`
- `engine/cyberspace_view.py` — `check_near_miss_extraction` hook on EXIT node entry
- `engine/state.py` — `AppState.near_miss_triggered: bool = False` field
- `tests/unit/test_near_miss.py` (NEW) — 24 tests across 6 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (144 source files)
- pytest: ✅ 3324 passed (24 new), 664 skipped, 0 failed

**Test coverage**:
- `TestComputeHpRatio` (6): clamping, edge cases (zero max_hp, overheal, negative HP)
- `TestNearMissThreshold` (5): 80% boundary, custom threshold, full HP, zero HP
- `TestNearMissRewards` (5): credits, salvage, missing fields, status message
- `TestNearMissOneShot` (2): no double-reward, single status message
- `TestNearMissIsPillar4Safe` (2): no meta_state write, death-reset behavior
- `TestNearMissRewardIntegrity` (3): positive amounts, flat rewards

### 향후 작업 (v1.1.0 ADR-0140 P2/P3 Deferred)

- **Faction Tension Events** (제안 7): 15-25% mission 에서 faction conflict trigger
- **Auto-Play Tempo Layering** (제안 8): graphic novel pacing variations
- **Death Replay** (제안 5): Hall of Dead echo
- **Tier scaling** for anomaly + near-miss rewards (grade 5+ = bigger bonuses)

### Cross-Reference (Near-Miss)

- `decisions/0140-engagement-layer.md` — proposal status
- `prototype/src/wet_run/engine/state.py` — `AppState.near_miss_triggered`
- `prototype/src/wet_run/engine/cyberspace_view.py` — EXIT node hook
- `prototype/src/wet_run/matrix/near_miss.py` — implementation

---

## Faction Tension Events (ADR-0140 §Proposal 7)

### 골재

Per DATA node entry, 25% chance of triggering a faction-aware event. Uses
existing **FactionReputation** (ADR-0131) to resolve outcome:
- High rep (≥ 50, FRIENDLY+): positive event (credits + salvage fragment)
- Low rep (≤ -50, HOSTILE+): negative event (alarm +1)
- Mid rep: no event (NEUTRAL zone)

### 게임 디자인

- **Trigger probability**: 25% per faction node entry (Faction != NONE)
- **Faction scope**: Hosaka, T-A, Sense/Net, Maas (5 factions tracked)
- **Polarity**: positive (high rep) vs negative (low rep) — tracked independently
- **One-shot**: per (faction, polarity) pair per run
- **Pillar 4 safe**: all rewards in-run, alarm resets on death

### Reward / Penalty Constants

| Event Type | Effect | Constant |
|---|---|---|
| Positive (high rep) | +30 credits + +1 salvage fragment | `POSITIVE_CREDITS`, `POSITIVE_SALVAGE` |
| Negative (low rep) | alarm +1 | `NEGATIVE_ALARM_DELTA` |

### Reputation Thresholds

| Threshold | Value | Effect |
|---|---|---|
| Positive | `>= 50` (FRIENDLY+) | bonus reward |
| Negative | `<= -50` (HOSTILE+) | alarm penalty |
| Mid (NEUTRAL, TRUSTED) | -50..49 | no event |

### Pillar 정합 검증

- **Pillar 1 (The Run)**: one-shot per run per faction polarity.
- **Pillar 4 (The Build)**: rewards are in-run + ephemeral (no cross-run inheritance).
- **Pillar 5 (The Style)**: faction awareness — "your rep precedes you" 깁슨 톤.

### 흐름

```
[Player navigates matrix with arrow keys]
    |
    v
[Player enters DATA node with faction=X]
    |
    v
[check_faction_tension_on_node_entry()]
    |
    +-- if faction == NONE: skip
    +-- if rng.random() >= 0.25: skip (75% no event)
    +-- read reputation.get(X).score
    +-- if score >= 50: positive event
    |   +-- apply: +30 credits + +1 salvage fragment
    |   +-- status msg: ">>> Faction tension: hosaka assistance — +30 credits, +1 salvage fragment"
    |   +-- mark "{faction}:{True}" as triggered
    |
    +-- if score <= -50: negative event
    |   +-- apply: alarm +1
    |   +-- status msg: ">>> Faction tension: ta interference — alarm +1"
    |   +-- mark "{faction}:{False}" as triggered
    |
    +-- else: no event (NEUTRAL rep)
```

### 구현 노트

**파일**:
- `matrix/faction_tension.py` (NEW) — `FactionTensionEvent`, `FactionTensionResult`,
  `get_faction_rep`, `should_trigger`, `classify_rep`, `apply_faction_tension`,
  `check_faction_tension_on_node_entry`
- `engine/cyberspace_view.py` — `check_faction_tension_on_node_entry` hook on DATA node entry
- `engine/state.py` — `AppState.faction_tension_triggered: set[str]` field + `alarm_level: int`
- `tests/unit/test_faction_tension.py` (NEW) — 22 tests across 7 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (145 source files)
- pytest: ✅ 3346 passed (22 new), 664 skipped, 0 failed

**Test coverage**:
- `TestTriggerProbability` (2): 25% constant, empirical 200-300/1000
- `TestClassifyRep` (4): high-rep positive, low-rep negative, neutral no-event, boundary
- `TestGetFactionRep` (2): state access, direct score-set
- `TestApplyFactionTension` (4): positive reward, negative penalty, missing fields, status msg
- `TestCheckOnNodeEntry` (5): NONE faction, neutral rep, high rep, low rep, empirical probability
- `TestFactionTensionOneShot` (2): no double reward, polarity independence
- `TestFactionTensionIsPillar4Safe` (2): no meta_state write, alarm resets on death

### 향후 작업 (v1.1.0 ADR-0140 P2/P3 Deferred)

- **Auto-Play Tempo Layering** (제안 8): graphic novel pacing variations
- **Death Replay** (제안 5): Hall of Dead echo
- **Tier scaling** for anomaly + near-miss + tension rewards (grade 5+ = bigger effects)

### Cross-Reference (Faction Tension)

- `decisions/0140-engagement-layer.md` — proposal status
- `prototype/src/wet_run/run/reputation.py` — FactionReputation source
- `prototype/src/wet_run/engine/state.py` — `AppState.faction_tension_triggered`
- `prototype/src/wet_run/engine/cyberspace_view.py` — DATA node hook
- `prototype/src/wet_run/matrix/faction_tension.py` — implementation

---

## Auto-Play Tempo Layering (ADR-0140 §Proposal 8)

### 골재

Player가 graphic novel auto-play 중에 pacing 을 조정할 수 있다. 세 가지 mode
(SLOW / NORMAL / FAST) 가 dialogue advancement rate 에 multiplier 적용.

### 게임 디자인

- **Three modes**: SLOW (0.7x), NORMAL (1.0x), FAST (1.5x)
- **Multiplier 적용 위치**: `main_loop._advance_graphic_novel` 의 `delta_s * 1000 * multiplier`
- **Player-facing**: UI 에 mode 표시 + 키 바인딩 (e.g. T key) 으로 cycle
- **Persistence**: `AppState.tempo_mode` field (string, default "normal")
- **Per-session**: 새 런 = NORMAL 로 reset (state init)

### Tempo Mode Table

| Mode | Multiplier | Real-time 1s → Effective | Pacing |
|---|---|---|---|
| SLOW | 0.7 | 700ms | 1.43x slower (longer dialogue display) |
| NORMAL | 1.0 | 1000ms | 1.0x (default) |
| FAST | 1.5 | 1500ms | 0.67x (faster dialogue display) |

### Pillar 정합 검증

- **Pillar 1 (The Run)**: tempo 는 player preference, in-run toggle 가능.
- **Pillar 2 (The Matrix)**: pacing 은 UI/UX, 사이버스페이스 표현 무관.
- **Pillar 3 (The Flatline)**: death = reset to NORMAL (no advantage from preferred tempo).
- **Pillar 4 (The Build)**: tempo 는 ephemeral preference, no meta-progression.
- **Pillar 5 (The Style)**: 깁슨 톤 — "good contractor controls the pace" 정합.

### 흐름

```
[Player watches graphic novel auto-play]
    |
    v
[main_loop ticks _advance_graphic_novel(state, delta_s)]
    |
    v
[get_tempo_multiplier(state.tempo_mode)]
    |
    v
[state.gn_elapsed_ms += delta_s * 1000 * tempo_multiplier]
    |
    v
[If elapsed >= dialogue.duration_ms: advance to next dialogue]
```

### 구현 노트

**파일**:
- `engine/auto_play_tempo.py` (NEW) — `TempoMode` enum, `TEMPO_MULTIPLIERS`,
  `DEFAULT_TEMPO_MODE`, `get_tempo_multiplier`, `cycle_tempo_mode`
- `engine/main_loop.py` — `_advance_graphic_novel` uses `get_tempo_multiplier(state.tempo_mode)`
- `engine/state.py` — `AppState.tempo_mode: str = "normal"` field
- `tests/unit/test_auto_play_tempo.py` (NEW) — 19 tests across 4 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (146 source files)
- pytest: ✅ 3365 passed (19 new), 664 skipped, 0 failed

**Test coverage**:
- `TestTempoMode` (2): enum values, default is NORMAL
- `TestTempoMultipliers` (8): 0.7/1.0/1.5 multipliers, string input, unknown fallback
- `TestCycleTempoMode` (4): SLOW→NORMAL→FAST→SLOW
- `TestMainLoopIntegration` (5): NORMAL full delta, SLOW reduced, FAST increased, FAST triggers sooner, unknown fallback

### 향후 작업 (v1.1.0 ADR-0140 P2/P3 Deferred)

- **Death Replay** (제안 5): Hall of Dead echo
- **Tier scaling** for anomaly + near-miss + tension rewards (grade 5+ = bigger effects)
- **Cycle 2 (Module Health)**: 4 modules > 1000 LOC → 4-way split per ADR-0112/0113/0141

### Cross-Reference (Auto-Play Tempo)

- `decisions/0140-engagement-layer.md` — proposal status
- `prototype/src/wet_run/engine/auto_play_tempo.py` — implementation
- `prototype/src/wet_run/engine/main_loop.py` — integration point
- `prototype/src/wet_run/engine/state.py` — `AppState.tempo_mode`
- `tests/unit/test_auto_play_tempo.py` — test coverage

---

## Grade 6 Master Whisper (ADR-0140 §Proposal 4)

### 골재

Grade 6+ master tier equipment 의 player 는 faction construct 의 *more
authoritative voice* 를 받는다. Normal rep-tier hint 를 대체하는 master-tier
hint — 더 깊은 통찰, 깁슨 톤의 "좋은 contractor 가 master 가 되는" 정합.

### 게임 디자인

- **Trigger condition**: `player_grade >= 6` AND `rep >= TRUSTED`
- **Voice difference**: "construct whispers" → "master construct decrees"
- **Content**: 각 faction 별 master-tier hint (4 factions × 1 hint)
- **One-shot**: 기존 `ConstructWhisper` tracker 사용 (master voice 도 1회/run)
- **Pillar 4 safe**: ephemeral, no meta-progression, death = reset

### Master Hint Tone

| Faction | Normal Voice | Master Voice (Grade 6+) |
|---|---|---|
| Hosaka | tactical advice | "decrees: the daemon is single-threaded..." |
| Maas | biochip warning | "intones: biochip telemetry leaks through..." |
| Sense/Net | alarm threshold | "reveals: alarm threshold is a sigmoid..." |
| T-A | protocol hint | "speaks: the family kept many secrets..." |

### Pillar 정합 검증

- **Pillar 1 (The Run)**: master voice = same per-run semantics.
- **Pillar 3 (The Flatline)**: death = reset (master voice is ephemeral).
- **Pillar 4 (The Build)**: unlock-only — Grade 6 equipment is unlock, not strength boost.
- **Pillar 5 (The Style)**: 깁슨 톤 — "good contractor earns the deepest signal" 정합.

### 흐름

```
[Combat start → check_construct_whisper_on_combat_start(state)]
    |
    v
[find_eligible_factions(reputation)]  # rep >= TRUSTED
    |
    v
[is_player_master(state)?]  # player_grade >= 6
    |
    +-- YES: get_master_hint_for_faction(faction)  # master voice
    +-- NO:  get_hint_for_faction(faction, tier)    # normal voice
    |
    v
[record_whisper(faction)]  # one-shot per run
    |
    v
[Append to status_messages with faction label]
```

### 구현 노트

**파일**:
- `lore/construct_whisper.py` — `MASTER_GRADE_THRESHOLD = 6`,
  `MASTER_HINTS_BY_FACTION` dict (4 factions), `get_master_hint_for_faction`,
  `is_player_master` helpers
- `lore/construct_whisper_hook.py` — `check_construct_whisper_on_combat_start`
  uses master voice when `is_player_master(state)` is True
- `tests/unit/test_grade_6_master_whisper.py` (NEW) — 15 tests across 4 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (146 source files)
- pytest: ✅ 3380 passed (15 new), 664 skipped, 0 failed

**Test coverage**:
- `TestMasterHintsTable` (2): all factions have master hints, threshold = 6
- `TestGetMasterHintForFaction` (3): known faction, NONE → None, unique voice
- `TestIsPlayerMaster` (5): grade 6+, 7, 5, 1, missing field
- `TestCombatStartHookIntegration` (5): Grade 6 master voice, Grade 5 normal, one-shot, below TRUSTED, all factions

### 향후 작업 (v1.1.0 ADR-0140 P2/P3 Deferred)

- **Death Replay** (제안 5): Hall of Dead echo
- **Tier scaling** for anomaly + near-miss + tension rewards (grade 5+ = bigger effects)
- **Cycle 2 (Module Health)**: 4 modules > 1000 LOC → 4-way split per ADR-0112/0113/0141

### Cross-Reference (Grade 6 Master Whisper)

- `decisions/0140-engagement-layer.md` — proposal status
- `prototype/src/wet_run/lore/construct_whisper.py` — `MASTER_HINTS_BY_FACTION`
- `prototype/src/wet_run/lore/construct_whisper_hook.py` — `is_player_master` check
- `prototype/src/wet_run/engine/state.py` — `AppState.player_grade`
- `tests/unit/test_grade_6_master_whisper.py` — test coverage

---

## BGM Manager (Cycle 3 polish)

### 골재

Per-screen background music controller. Centralized BGM that maps screen
names to theme names, provides volume control, and simulates crossfade
between themes. Wraps the existing `ThemePlayer` from `audio/theme.py`.

### 게임 디자인

- **Per-screen mapping**: 10 default screens registered
  - `MENU`, `HUB` → `finn_office` (Finn's office ambient)
  - `MATRIX` → `matrix_rain` (default cyberspace)
  - `MATRIX_DEEP` → `cyberspace` (deeper zones)
  - `COMBAT` → `industrial` (combat tension)
  - `COMBAT_BOSS` → `hammer_alert` (boss encounter)
  - `NPC` → `chiba` (street-level jazz)
  - `SENSE_NET` → `sense_net` (corporate data fortress)
  - `LOA` → `loa_drum` (Vodou construct zones)
  - `CINEMATIC` → `loa_drum_fade` (slow-mo scenes)
  - `SALVATION` → `manarase_drone` (ending zones)
- **Volume control**: 0.0–1.0, clamped. Default 0.6.
- **Mute control**: toggle, remembers last theme.
- **Crossfade**: simulated (real crossfade requires async audio). `fade_out()` calls `stop_theme()`.

### Pillar 정합 검증

- **Pillar 1 (The Run)**: BGM state is per-session, reset on new run.
- **Pillar 3 (The Flatline)**: death does NOT preserve BGM preferences.
- **Pillar 4 (The Build)**: NO meta-progression. BGM is ephemeral session preference.

### 흐름

```
[Screen transition detected]
    |
    v
[bgm.play_for_screen("MATRIX")]
    |
    v
[bgm._screen_themes["MATRIX"] → "matrix_rain"]
    |
    v
[play_theme("matrix_rain", config)]  → [audio/theme.py]
    |
    v
[bgm._settings.current_theme = "matrix_rain"]
```

### 구현 노트

**파일**:
- `audio/bgm_manager.py` (NEW, 246 LOC) — `BgmManager` class, `BgmSettings` dataclass,
  `get_bgm_manager()` / `reset_bgm_manager()` singletons
- `tests/unit/test_bgm_manager.py` (NEW) — 24 tests across 6 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (150 source files)
- pytest: ✅ 3404 passed (24 new), 664 skipped, 0 failed

**Test coverage**:
- `TestScreenRegistration` (4): register/overwrite, unknown theme raises, defaults cover all
- `TestThemePlayback` (6): play_for_screen, play_theme (known/unknown), muted, stop, fade_out
- `TestVolumeControl` (5): default, set, clamp low, clamp high, restart-on-set
- `TestMuteControl` (4): default not muted, mute stops, idempotent, unmute no-resume, toggle
- `TestSingleton` (2): same instance, reset creates new
- `TestPillar4Compliance` (2): no meta_state, volume ephemeral on reset

### 향후 작업 (v1.1.0+ Cycle 3 잔존)

- **True crossfade** (async audio mixing)
- **Per-region BGM** (not just per-screen — e.g. different BGM for Surface vs Deep matrix)
- **Combat dynamic BGM** (intensity-based, Phase B-3 boss vs trash)

### Cross-Reference (BGM Manager)

- `decisions/0140-engagement-layer.md` — Cycle 1 (complete)
- `prototype/src/wet_run/audio/theme.py` — `ThemePlayer`, `play_theme`, `stop_theme`
- `prototype/src/wet_run/audio/config.py` — `SoundConfig`
- `tests/unit/test_bgm_manager.py` — test coverage

---

## Accessibility Settings (Cycle 3 polish)

### 골재

기존 `settings_view.py` (audio + colorblind + keymap + resolution) 에 font_size
와 high_contrast 두 가지 접근성 옵션 추가. Pillar 4 (The Build) 의 unlock-only
metaprogression 과 일치 — ephemeral session preference, no meta-progression.

### 게임 디자인

- **font_size**: `"small"` / `"normal"` / `"large"` (3 modes, cycles on ENTER)
  - 작게 (compact UI) / 보통 (default) / 크게 (접근성 — 노인/시력 약함)
  - 향후 렌더링 훅 연동 (per-mode char_scale)
- **high_contrast**: `bool` (toggles on ENTER)
  - True 시 고대비 팔레트 적용 (colorblind mode 와 직교)
  - 향후 렌더링 훅 연동 (per-mode palette override)

### SETTINGS_OPTIONS 확장 (5 → 7)

기존 5개 (audio / colorblind / keymap / resolution / back) 에 2개 추가:

| opt_id | Label | Type | Action |
|---|---|---|---|
| `font_size` | Font Size | str | cycles small→normal→large |
| `high_contrast` | High Contrast | bool | toggles |

### Pillar 정합 검증

- **Pillar 1 (The Run)**: font_size / high_contrast 모두 run 시작 시 default (normal / False)
- **Pillar 3 (The Flatline)**: death 시 새 run → default 복귀
- **Pillar 4 (The Build)**: ephemeral session preference, meta_state 미사용
  - test_font_size_does_not_write_meta_state 검증
  - test_high_contrast_does_not_write_meta_state 검증

### 구현 노트

**파일**:
- `engine/state.py` (NEW fields) — `font_size: str = "normal"`, `high_contrast: bool = False`
- `engine/settings_view.py` (MODIFIED) — SETTINGS_OPTIONS 확장, render handler 추가,
  cycle logic (font_size: small→normal→large)
- `tests/unit/test_accessibility_settings.py` (NEW) — 10 tests, 3 classes
- `tests/unit/test_settings.py` (MODIFIED) — test_five_options → test_seven_options
  (back option moved from index 4 → 6)

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (150 source files)
- pytest: ✅ 3414 passed (10 new), 664 skipped, 0 failed

**Test coverage** (TestPillar4Compliance class):
- font_size_does_not_write_meta_state ✅
- high_contrast_does_not_write_meta_state ✅
- new_fields_dont_persist_across_resets ✅

### 향후 작업 (Cycle 3 잔존)

- **Options menu keyboard remapping** (per-game keymap customization)
- **Accessibility layer** (rendering hooks for font_size + high_contrast)
- **colorblind mode subtypes** (protanopia / deuteranopia / tritanopia)

### Cross-Reference (Accessibility)

- `decisions/0140-engagement-layer.md` — Cycle 1 (complete)
- `prototype/src/wet_run/engine/state.py` — `AppState.font_size`, `AppState.high_contrast`
- `prototype/src/wet_run/engine/settings_view.py` — `SETTINGS_OPTIONS` (7 items)
- `tests/unit/test_accessibility_settings.py` — test coverage

---

## Hardcore Mode (Cycle 4: Pillar 3 reinforcement)

### 골재

기존 death flow (death.py) 에 1-life permadeath mode 추가. Pillar 3 (The
Flatline) 의 "death has real weight" 를 강화하는 옵션. Pillar 4 (The
Build) 의 unlock-only metaprogression 과 일치 — ephemeral session
preference, no meta-progression (no stat boosts, no unlocks carried
over).

### 게임 디자인

- **Field**: `AppState.hardcore_mode: bool = False` (default)
- **Effect**: True 일 때 death → restart_with_new_jockey 차단 (Pillar 3 강화)
  - 기존 normal mode: death → DEATH_SUMMARY → HALL_OF_DEAD → new jockey 선택
  - hardcore mode: death → permanent (no revival)
- **Pillar 정합**:
  - Pillar 1: 게임 시작 시 default (False) — 새 런 = 새 기회
  - Pillar 3 강화: death = 진짜 끝 (permadeath)
  - Pillar 4: ephemeral session preference, meta_state 미사용

### Pillar 정합 검증

- **Pillar 1 (The Run)**: death 발생 시 default는 new jockey로 복귀 (perma-death X)
- **Pillar 3 강화 (The Flatline)**: hardcore mode 에서만 permadeath
- **Pillar 4 (The Build)**: death 시 new run = default (unlock-only metaprogression)

### 흐름

```
[Player death in combat]
    |
    v
[trigger_death(state, reason)]
    |
    v
[death.py logic: set is_dead=True, screen=DEATH]
    |
    v
[if hardcore_mode is True:]
    - block restart_with_new_jockey()
    - show "PERMANENT DEATH" screen
[else:]
    - show DEATH_SUMMARY → HALL_OF_DEAD → new jockey 선택
```

### 구현 노트

**파일**:
- `engine/state.py` (NEW field) — `hardcore_mode: bool = False` (Pillar 4 ephemeral)
- `engine/death.py` (DEFERRED) — restart_with_new_jockey() 에 hardcore_mode 체크
  (Pillar 3 강화), 현재는 field + test + design doc 까지
- `tests/unit/test_hardcore_mode.py` (NEW) — 8 tests, 3 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (150 source files)
- pytest: ✅ 3422 passed (8 new), 664 skipped, 0 failed

**Test coverage** (TestHardcoreModeField, TestPillar4Compliance, TestHardcoreModeBehavior):
- default is False
- can be enabled
- can be disabled
- no meta_state write
- does not persist across resets
- is boolean type
- default allows revival
- hardcore blocks revival (behavioral stub)

### 향후 작업 (Cycle 4 잔존)

- **death.py integration**: restart_with_new_jockey() 에 hardcore_mode 체크
  (Pillar 3 강화)
- **death screen UI**: "PERMANENT DEATH" vs "NEW JOCKEY" 분기 표시
- **New Game+ mode**: Salvation Phase 완료 후 재시작 (carryover options)
- **Construct companion**: Dixie 실제 전투 동료 (현재 dialog-only)

### Cross-Reference (Hardcore Mode)

- `decisions/0140-engagement-layer.md` — Cycle 1 (complete)
- `prototype/src/wet_run/engine/death.py` — `trigger_death`, `restart_with_new_jockey`
- `prototype/src/wet_run/engine/state.py` — `AppState.hardcore_mode`
- `tests/unit/test_hardcore_mode.py` — test coverage

---

## New Game+ Mode (Cycle 4: Pillar 4 unlock-only meta-progression)

### 골재

Salvation Phase 종료 후 다시 시작할 수 있는 New Game+ 모드. Pillar 4
(The Build) 의 "meta progress is unlock-only" 와 일치 — carryover
은 **unlocks** 만 허용, stat/stat boost 없음. Pillar 1 (The Run) 의
"새 런 = 새 기회" 와 충돌하지 않도록 ng_plus_active 는 ephemeral
(session preference) 로 운영.

### 게임 디자인

- **`ng_plus_unlocked: bool = False`**: Salvation Phase 완료 시 자동 True
  (ending 도달 후 unlock, Pillar 4 unlock-only)
- **`ng_plus_active: bool = False`**: 현재 run 에서 NG+ 적용 여부
  (Pillar 4 ephemeral, death/new run 시 reset)
- **Carryover 범위**: unlocks only (장비 access, faction access 등)
  - **부정 예**: stat boost, HP boost, inventory 잔존, credit 잔존
  - **긍정 예**: unlocked faction rep, unlocked equipment access,
    unlocked mission types, unlocked area access

### Pillar 정합 검증

- **Pillar 1 (The Run)**: 새 런 = 새 기회 (stat/인벤토리 reset, NG+ unlock + active 만 carryover)
- **Pillar 4 (The Build)**: unlock-only meta-progression, no stat boosts
  - test_ng_plus_does_not_modify_player_stats 검증
  - test_does_not_persist_across_resets 검증
- **Pillar 5 (The Style)**: unlocked content 만 (새로운 unlock 이 아닌 기존 unlock 재진입)

### 흐름

```
[Player completes Salvation Phase → ending]
    |
    v
[ng_plus_unlocked = True]  (Pillar 4 unlock)
    |
    v
[Player starts new run]
    |
    v
[Player can opt into NG+ (ng_plus_active = True)]
    |
    +-- ng_plus_active True:  carryover unlocks apply
    +-- ng_plus_active False: standard new run (no carryover)
    |
    v
[Death or new game → reset ng_plus_active]
    (ng_plus_unlocked remains True, Pillar 4 unlock persists)
```

### 구현 노트

**파일**:
- `engine/state.py` (NEW fields) — `ng_plus_unlocked: bool`, `ng_plus_active: bool`
- `engine/death.py` (DEFERRED) — ending 도달 시 ng_plus_unlocked=True
  (death.py 또는 salvation.py integration)
- `engine/main_loop.py` (DEFERRED) — 새 game 시작 시 ng_plus_active 선택 UI
- `tests/unit/test_ng_plus.py` (NEW) — 10 tests, 3 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (150 source files)
- pytest: ✅ 3432 passed (10 new), 664 skipped, 0 failed

**Test coverage** (TestNGPlusFields, TestPillar4Compliance, TestNGPlusBehavior):
- Default False for both fields
- Can be enabled independently
- Locked and active are independent fields
- No meta_state write
- Does not persist across resets
- Does not modify player stats (Pillar 4: unlock-only)

### 향후 작업 (Cycle 4 잔존)

- **death.py integration**: ending 도달 시 ng_plus_unlocked=True 설정
- **main_loop integration**: 새 game 시작 시 NG+ 선택 UI
- **Construct companion**: Dixie 실제 전투 동료 (Cycle 4 3/3)
- **Carryover 해부**: 어떤 unlock 이 carryover 되는지 명세화 (faction rep, equipment access 등)
- **Death Replay** (Hall of Dead echo) — v1.2.0+
- **Tier scaling** — v1.2.0+

### Cross-Reference (New Game+)

- `decisions/0140-engagement-layer.md` — Cycle 1 (complete)
- `prototype/src/wet_run/engine/state.py` — `AppState.ng_plus_unlocked`, `AppState.ng_plus_active`
- `tests/unit/test_ng_plus.py` — test coverage

---

## Construct Companion (Cycle 4: Pillar 5 actual combat ally)

### 골재

기존 Dixie Flatline 은 dialog-only NPC (npc_event.py: "ghost in the
machine"). Cycle 4 의 마지막 deliverable 로 Dixie 를 **실제 전투 동료**로
만드는 flag. Pillar 5 (The Style) 의 깁슨 코퍼스 톤 — Dixie 가 combat
ally 로서 플레이어와 함께 싸우는 모습. Pillar 4 (The Build) 와 일치 —
ephemeral session preference, no stat boost.

### 게임 디자인

- **`construct_companion_active: bool = False`**: Dixie 가 actual combat
  ally 로 활동하는지 여부 (Pillar 4 ephemeral, death = reset)
- **Default**: dialog-only (기존 npc_event.py 동작)
- **Enabling 시**: combat 에서 Dixie 가 플레이어와 함께 싸움 (Pillar 5 톤)
- **Pillar 정합**:
  - Pillar 1 (The Run): 새 런 = 새 기회
  - Pillar 4 (The Build): unlock-only meta-progression, no stat boost
  - Pillar 5 (The Style): Dixie 가 combat ally 로서 깁슨 코퍼스 톤 반영

### Pillar 정합 검증

- **Pillar 1 (The Run)**: 새 런 = 새 기회 (Dixie 도 reset)
- **Pillar 4 (The Build)**: ephemeral session preference, no meta-progression
  - test_does_not_persist_across_resets 검증
  - test_does_not_modify_player_stats 검증
- **Pillar 5 (The Style)**: Dixie 가 combat ally 로서 깁슨 코퍼스 톤

### 흐름

```
[Player encounters Dixie in dialog (npc_event.py)]
    |
    v
[Player recruits Dixie: construct_companion_active = True]
    |
    v
[Combat phase: Dixie fights alongside player (Pillar 5)]
    |
    v
[Death or new game: construct_companion_active = False (reset)]
    (dialog-only mode resumes — Pillar 1)
```

### 구현 노트

**파일**:
- `engine/state.py` (NEW field) — `construct_companion_active: bool = False`
- `engine/npc_event.py` (DEFERRED) — Dixie combat ally 행동 추가
- `engine/combat.py` (DEFERRED) — Dixie가 ally로 combat 참여하는 로직
- `tests/unit/test_construct_companion.py` (NEW) — 9 tests, 3 classes

**Quality gates**:
- ruff: ✅ All checks passed
- mypy: ✅ 0 errors (150 source files)
- pytest: ✅ 3441 passed (9 new), 664 skipped, 0 failed

**Test coverage** (TestConstructCompanionField, TestPillar5Compliance, TestConstructCompanionBehavior):
- Default False (dialog-only)
- Can be enabled (combat ally mode)
- Can be disabled
- is_boolean_type
- No meta_state write
- Does not persist across resets
- Does not modify player stats
- Default is dialog-only
- Can be toggled to combat ally

### 향후 작업 (Cycle 4 완료 후)

- **graphic_novel_view.py 4-way split** (deferred per ADR-0133) — v1.1.0+ 후속
- **Death Replay** (Hall of Dead echo) — v1.2.0+
- **Tier scaling** — v1.2.0+
- **Dixie combat ally 구현** (np_event.py, combat.py integration)
- **Carryover 해부** (NG+ 에서 어떤 unlock carryover 되는지 명세화)
- **User action**: push (34+ commits), PyPI, Notion

### Cross-Reference (Construct Companion)

- `decisions/0140-engagement-layer.md` — Cycle 1 (complete)
- `prototype/src/wet_run/engine/state.py` — `AppState.construct_companion_active`
- `prototype/src/wet_run/engine/npc_event.py` — `Dixie Flatline` (dialog-only by default)
- `tests/unit/test_construct_companion.py` — test coverage
