# ADR-0140: Engagement Layer for v1.1.0

**상태**: Accepted (Option 1, partial — Top 3 only)
**날짜**: 2026-07-28
**결정자**: 사용자
**우선순위**: P2 (v1.1.0 후보)
**연관**: ADR-0008 (Progression), ADR-0009 (Story/News), ADR-0012 (PPL/ZDR), ADR-0013 (Story Events), ADR-0017 (Mission-Material), ADR-0040 (Death & Restart), ADR-0131 (Meta State), Pillars 1/3/4/5

---

## 컨텍스트 (Context)

v1.0.0 release 후 사용자 consultation (2026-07-28) 에서 게임 중독성/쾌감 강화 방향 논의. 8개 design proposal 제시:

1. **Construct Whisper** — Faction rep 활용 (인-런 hint)
2. **Memory Fragment** — Ambient lore collection
3. **Near-Miss Extraction** — 80%+ jack-out 보상
4. **Grade 6 Master Whisper** — Master tier 차별화
5. **Death Replay** — Hall of Dead echo
6. **Variable Reward Nodes** — Matrix anomaly 30%
7. **Faction Tension Events** — 미션 중 faction 충돌
8. **Auto-Play Tempo Layering** — 그래픽 노블 pacing

**현재 부족한 영역** (audit 결과):
- 한 런 내 *즉각적 보상* 빈도 낮음 (Data Salvage 외 인-런 보상 부족)
- *능숙함*과 *운*의 구분 약함
- Faction rep cross-run 영속화 (ADR-0131) 의 활용처 부족
- Grade 5→6 성장 정체 (1.20x — ADR-0130 잔존 이슈)

---

## 고려한 옵션

### Option 1: 전체 통합 (권고 — 단계적)

8개 proposal 전체를 v1.1.0 cycle에 분산 배치:

| Priority | Proposal | Phase | 구현 비용 |
|---|---|---|---|
| P1 | Construct Whisper (제안 1) | v1.1.0 Phase 1 | 중간 |
| P1 | Memory Fragment (제안 2) | v1.1.0 Phase 1 | 낮음 |
| P1 | Grade 6 Master Whisper (제안 4) | v1.1.0 Phase 1 | 중간 |
| P2 | Variable Reward Nodes (제안 6) | v1.1.0 Phase 2 | 중간 |
| P2 | Faction Tension Events (제안 7) | v1.1.0 Phase 2 | 중간 |
| P2 | Auto-Play Tempo (제안 8) | v1.1.0 Phase 3 | 낮음 |
| P3 | Near-Miss Extraction (제안 3) | v1.1.0 Phase 3 | 중간 |
| P3 | Death Replay (제안 5) | v1.1.0 Phase 3 | 중간 |

- **장점**: 각 Pillar 준수 + 점진적 도입 + 구현 부담 분산
- **단점**: 8개 모두 v1.1.0 안에 들어가야 — 1.5~2 cycle 필요

### Option 2: Top 3 만 (Construct + Memory + Grade 6)

- **장점**: v1.1.0 release 에 3개로 한정. 빠른 검증.
- **단점**: 5개 proposal 미실행

### Option 3: Defer (현 v1.0.0 유지)

- **장점**: 출시 직후 변경 회피. v1.0.0 안정성 우선.
- **단점**: 사용자 consultation 결과 미실행. 다음 major release 까지 보류.

### Option 4: 통합 패키지 — Tier 1/2/3 동시 적용

8개 proposal 동시 구현. 단일 major release (v2.0) 로.

- **장점**: 일관된 engagement overhaul.
- **단점**: 회귀 위험 ↑, 테스트 부담 ↑, 출시까지 시간 ↑↑

---

## 추천 (Recommendation)

**Option 1 (단계적 통합)** 권고.

**근거**:
- Top 3 (제안 1, 2, 4) 은 **ADR-0131 cross-run rep의 활용처** + **v1.0.0 audit 잔존 이슈 (master 정체성)** 해결 — 즉시 가치
- P2 제안들 (제안 6, 7, 8) 은 *런 variety* 강화 — Phase 2~3 적절
- P3 제안들 (제안 3, 5) 은 *사후 만족* (loss aversion, death replay) — v1.1.0 후반 또는 v1.2.0 후보
- 한 사이클에 8개 모두는 회귀 위험

**잔존 결정 사항**:
- Construct Whisper 빈도 (런 당 max 5회? 무제한?)
- Memory Fragment 런 당 한도 (5~8개?)
- Grade 6 whisper phase 당 1회? 다른 construct voice?
- Near-Miss 임계값 (80% / 85% / 90%?)
- Faction Tension 미션 비율 (15%? 25%?)

---

## 사용자 결정 (Decision)

- [x] **Option 1 (전체 통합 단계적)** — 사용자 선택 (Top 3 우선)
- [ ] Option 2 (Top 3 만) *(de facto — Option 1의 Top 3가 먼저 완료됨)*
- [ ] Option 3 (Defer)
- [ ] Option 4 (통합 패키지)
- [ ] 기타: ___

**세부 결정** (Option 1, 2026-07-28 채택):
- [x] Construct Whisper 빈도: **런 당 faction 등급당 1회** (max 5회/런)
- [x] Memory Fragment 런 당 한도: **6개** (encounter_table base_chance 0.25, per_zone 조정)
- [x] Grade 6 whisper: v1.1.0+ 후속 (현재 ADR-0140 Option 1 Top 3만 우선)
- [ ] Near-Miss 임계값: v1.2.0+ 검토
- [ ] Faction Tension 비율: v1.2.0+ 검토

---

## 영향 받는 항목 (예정)

수락 시:
- `src/wet_run/matrix/construct_whisper.py` (신규)
- `src/wet_run/engine/memory_fragment.py` (신규)
- `src/wet_run/engine/death_replay.py` (신규)
- `combat/effects.py` 확장 (VFX hooks)
- `matrix/generator.py` 확장 (anomaly nodes)
- `design/systems/engagement.md` (신규 명세)
- `tests/unit/test_engagement.py` (신규)
- `log.md` 기록

---

## 결과 (Consequences)

(Accepted 후 작성)

---

## 관련 결정

- ADR-0131 — Faction Reputation Cross-Run Persistence (이 ADR의 기반)
- ADR-0130 — Balance Audit (Grade 6 정체성 해결)
- ADR-0040 — Death & Restart (Death Replay의 기반)
- ADR-0032 — Graphic Novel Mode (Auto-Play Tempo의 기반)
- ADR-0017 — Mission-Material Integration (Faction Tension의 기반)

---

## 결과 (Consequences)

**Option 1 Accepted (partial — Top 3 only)** (2026-07-28). 적용된 변경:

### Phase 1 — Memory Fragments ✅
- `wiki/lore/README.md` + 4 fragments (signal_echo, construct_cache, anomaly_log, dead_channel)
- `data/lore/encounter_table.json` (4 fragments × zone/grade/faction 매트릭스)
- `src/wet_run/lore/memory_fragment.py` (roll_memory_fragment, load_encounter_table)
- `src/wet_run/lore/fragment_tracker.py` (per-run cap enforcement)
- `src/wet_run/lore/fragment_hook.py` (matrix integration helper)
- `src/wet_run/lore/__init__.py` (re-exports)
- AppState.memory_fragment_tracker 필드
- cyberspace_view.py:519 hook 통합
- **Tests**: 12 (memory_fragment) + 9 (fragment_tracker) + 6 (fragment_hook) = 27

### Phase 2 — Construct Whisper ✅
- `src/wet_run/lore/construct_whisper.py` (faction-tier-gated hints)
- `src/wet_run/lore/construct_whisper_hook.py` (combat integration)
- AppState.construct_whisper_tracker 필드
- HINTS_BY_FACTION: 4 factions × 3 tiers = 12 hints
- **Tests**: 14 (core) + 8 (hook) = 22

### Phase 3 — Grade 6 Master Whisper ⏳
- v1.1.0+ 후속 (현재 scope 외)

### Phase P2 — Variable Reward Nodes (제안 6) ✅ (2026-08-03)
- `matrix/node.py` — `is_anomaly: bool = False` field + DATA-only validation
- `matrix/generator.py` — `ANOMALY_PROBABILITY = 0.30` constant + 30% per DATA node
- `matrix/anomaly_reward.py` (NEW) — `AnomalyRewardKind` (CREDITS/SALVAGE/INFO),
  `roll_anomaly_reward`, `apply_anomaly_reward`, `check_anomaly_reward_on_node_entry`
- `engine/cyberspace_view.py` — `_ANOMALY_GLYPH`/`_ANOMALY_COLOR` constants +
  `_draw_node` override + on_node_enter hook (applies reward on first entry)
- `engine/state.py` — `AppState.anomaly_triggered: set[str]` field (one-shot)
- `tests/unit/test_variable_reward.py` (NEW) — 22 tests across 5 classes
- `design/systems/engagement.md` (NEW) — design spec
- Reward weights: uniform (CREDITS 50 / SALVAGE 1 / INFO 1, 33% each)
- Pillar 4 safe: no cross-run inheritance (all in-run, ephemeral)
- Visual: anomaly = `◆` magenta `(255, 100, 255)` vs regular DATA = `$` gold

### Phase P3 — Near-Miss Extraction (제안 3) ✅ (2026-08-03)
- `matrix/near_miss.py` (NEW) — `NearMissRewardKind`, `NearMissReward`, `NearMissResult`,
  `compute_hp_ratio`, `check_near_miss_extraction`
- `engine/cyberspace_view.py` — `check_near_miss_extraction` hook on EXIT node entry
- `engine/state.py` — `AppState.near_miss_triggered: bool = False` field (one-shot)
- `tests/unit/test_near_miss.py` (NEW) — 24 tests across 6 classes
- Reward: +75 credits + +1 salvage fragment when HP > 80% at exit
- Threshold: 80% (configurable via `DEFAULT_NEAR_MISS_HP_THRESHOLD`)
- Pillar 4 safe: no cross-run inheritance (death loses rewards)

### Phase P2 — Faction Tension Events (제안 7) ✅ (2026-08-03)
- `matrix/faction_tension.py` (NEW) — `FactionTensionEvent`, `FactionTensionResult`,
  `get_faction_rep`, `should_trigger`, `classify_rep`, `apply_faction_tension`,
  `check_faction_tension_on_node_entry`
- `engine/cyberspace_view.py` — `check_faction_tension_on_node_entry` hook on DATA node entry
- `engine/state.py` — `AppState.faction_tension_triggered: set[str]` field + `alarm_level: int`
- `tests/unit/test_faction_tension.py` (NEW) — 22 tests across 7 classes
- Trigger probability: 25% per faction DATA node entry (`FACTION_TENSION_PROBABILITY`)
- Positive threshold: rep ≥ 50 (FRIENDLY+) → +30 credits + +1 salvage fragment
- Negative threshold: rep ≤ -50 (HOSTILE+) → alarm +1
- Polarity independence: positive and negative events tracked separately per faction
- Pillar 4 safe: no cross-run inheritance (all in-run, alarm resets on death)
- Leverages existing FactionReputation system (ADR-0131, run/reputation.py)

### Phase P2 — Auto-Play Tempo Layering (제안 8) ✅ (2026-08-03)
- `engine/auto_play_tempo.py` (NEW) — `TempoMode` enum, `TEMPO_MULTIPLIERS`,
  `DEFAULT_TEMPO_MODE`, `get_tempo_multiplier`, `cycle_tempo_mode`
- `engine/main_loop.py` — `_advance_graphic_novel` uses
  `get_tempo_multiplier(state.tempo_mode)` to scale elapsed_ms
- `engine/state.py` — `AppState.tempo_mode: str = "normal"` field
- `tests/unit/test_auto_play_tempo.py` (NEW) — 19 tests across 4 classes
- Three modes: SLOW (0.7x), NORMAL (1.0x), FAST (1.5x) applied to elapsed_ms delta
- Per-session preference (default NORMAL on new run)
- Pillar 4 safe: ephemeral preference, no meta-progression

### Phase 3 — Grade 6 Master Whisper ✅ (2026-08-03)
- `lore/construct_whisper.py` — `MASTER_GRADE_THRESHOLD = 6`, `MASTER_HINTS_BY_FACTION`
  dict (4 factions, more authoritative voice), `get_master_hint_for_faction`,
  `is_player_master` helpers
- `lore/construct_whisper_hook.py` — `check_construct_whisper_on_combat_start`
  uses master voice when `is_player_master(state)` is True
- `tests/unit/test_grade_6_master_whisper.py` (NEW) — 15 tests across 4 classes
- Trigger: `player_grade >= 6` AND `rep >= TRUSTED` (replaces normal tier voice)
- Voice difference: "construct whispers" → "master construct decrees"
- One-shot per run (uses existing `ConstructWhisper` tracker)
- Pillar 4 safe: ephemeral, no meta-progression (Grade 6 equipment is unlock)
- Pillar 3 reinforcement: death-avoidance payoff

### 잔존 (v1.2.0+)
- Phase P3: Death Replay (제안 5) *(Near-Miss Extraction ✅ done)*
- Tier scaling for anomaly + near-miss + tension rewards (deferred v1.1.0+)
- *(Variable Reward Nodes ✅, Faction Tension ✅, Auto-Play Tempo ✅, Grade 6 Master Whisper ✅ done)*

### 메트릭
- 신규 파일: 10 (lore 모듈 6 + anomaly_reward.py 1 + near_miss.py 1 + faction_tension.py 1 + auto_play_tempo.py 1)
- 신규 테스트: 151 (Phase 1 27 + Phase 2 22 + Phase P2 22 + Phase P3 24 + Phase P2.7 22 + Phase P2.8 19 + Phase 3 15)
- 회귀 위험: 낮음 (combat_view.py 변경 없음, cyberspace_view.py + main_loop.py + construct_whisper_hook.py 만 hook 추가)
- Pillar 정합: Pillar 3 (death-avoidance) + Pillar 4 (unlock-only) + Pillar 5 (Style)

---

## 변경 이력

- 2026-07-28: Draft 작성 (사용자 consultation 후속)
- 2026-07-28: **Accepted (Option 1 partial — Top 3)** — Phase 1 (Memory Fragments) + Phase 2 (Construct Whisper) 구현 완료
- 2026-08-03: Cycle 4 polish 1~4 (v1.1.0 final) — Engagement Layer 본 phase 완료 (Variable Reward + Near-Miss + Faction Tension + Auto-Play Tempo + Grade 6 Master Whisper)
- 2026-08-04: Hardcore / NG+ / Construct companion polish 추가 — 본 ADR의 8 proposal과 *별도* 디자인 (Pillar 3/4/5 각각). 자세한 문서는 design/ 하위에서 관리 (아래 "연관 결정" 참조)

---

## 연관 결정 (Cycle 4 polish — Engagement Layer와 직교)

본 ADR (Engagement Layer 8 proposals) 와 별도로, Cycle 4 polish (2026-08-03~04) 에서 추가된 3개 mechanic은 *다른 Pillar*를 다룬다. 본 ADR의 narrative alignment를 위해 cross-reference:

| Polish | Pillar | 관련 문서 | 핵심 구현 |
| --- | --- | --- | --- |
| **Hardcore mode** (1-life permadeath) | Pillar 3 (death has weight) | [`design/scenario/death-restart.md §6.5 Hardcore Mode Override`](../design/scenario/death-restart.md) + [`design/GDD.md §3 난이도 모드`](../design/GDD.md) | `state.hardcore_mode` flag, `restart_with_new_jockey` raises ValueError, MENU routing in `handle_death_summary_choice` / `handle_death_input`, "PERMANENT DEATH" UI |
| **NG+ mode** (Post-Salvation meta unlock) | Pillar 4 (unlock-only meta-progression) | [`design/systems/progression.md ## NG+ 라이프사이클`](../design/systems/progression.md) + [`design/scenario/SALVATION_PHASE_INTEGRATION.md §5.4`](../design/scenario/SALVATION_PHASE_INTEGRATION.md) | `state.ng_plus_unlocked` set in `salvation_view.handle_salvation_epilogue_input`, `state.ng_plus_active` toggle via N-key in `menu.handle_character_select_input`, lock gate enforcement |
| **Construct companion (Dixie)** | Pillar 5 (Style — digital ghost) | [`design/systems/combat.md ### Construct Companion (Dixie)`](../design/systems/combat.md) | `state.construct_companion_active` flag, `combat/state.py::tick_dixie_ally` (2000ms tick, 5 dmg), wired in `engine/main_loop._advance_combat` |

**의미**: 본 ADR의 8 proposal (Engagement — 즉각적 보상 + variety 강화) 과 polish 3 mechanic (Pillar 3/4/5 강화) 은 *직교 관계* — engagement는 "재미/중독성" 축, polish는 "의미/영속성" 축. 두 축이 함께 v1.1.0 의 *완성된* player experience 를 구성.