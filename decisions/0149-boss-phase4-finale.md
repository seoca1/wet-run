# ADR-0149: Boss ICE Phase 4 Finale — Per-Boss Mechanics, Death Taunts, Narrative Closure

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (전투 게임성 강화, v1.1.0+ Cycle 3 of A+B+C)
**관련**: [ADR-0050 — Boss ICE System (3-phase)](./0050-boss-ice-system.md), [ADR-0125 — Boss Phase AoE + Minion Spawn (B-3)](./0125-boss-aoe-minion-spawn.md), [ADR-0147 — Data Salvage Phase 6+ (Cycle 1)](./0147-data-salvage-phase6.md), [ADR-0148 — Combat Depth Expansion (Cycle 2)](./0148-combat-depth-expansion.md), [ADR-0090 — Salvation Phase Integration](./0090-salvation-phase-integration.md)

## 컨텍스트 (Context)

`combat/boss.py` (724 LOC, Phase B-3 1000+ LOC 한계 근접) 와 `combat/bosses.py` (627 LOC) 의 분석 결과:

**이미 존재** (ADR-0050 + ADR-0125 + Cycle 2 ADR-0148 의 aggression tier):
- `PhaseProfile` dataclass (phase, hp_threshold, damage_multiplier, color, glyph, intro_text, skills, aoe_damage, spawn_minions)
- `BossProfile` (ice_type, name, phases) + `max_phases` property
- 3 주요 boss: WINTERMUTE (3-phase, ADR-0050), TA_CONSTRUCT_PRIME (3-phase, ADR-0050), GOLIATH PRIME / BLACK ICE LORD / WATCHDOG ALPHA (3-phase, ADR-0125)
- `BossSpec` (id, name, base_ice_type, hp_multiplier, attack_multiplier, defense_multiplier, phases, intro_lines, death_lines, vfx_theme)
- `BossPhase` (index, name, hp_threshold_pct, intro_line, color, attack_bonus_pct, speed_bonus_pct, screen_shake_intensity, special_ability, aoe_damage, spawn_minions, vfx_theme)
- `boss_intro_sequence`, `boss_phase_transition`, `boss_death_sequence`, `boss_epilogue_lines` 모두 구현
- Cycle 2 ADR-0148: `aggression="boss"` (50% skill use) — Boss Phase 4 의 scripted mechanic 기반 제공

**부재** (Cycle 3 Option C 의 핵심):
- **Phase 4 Finale**: 5 주요 boss (wintermute, ta_prime, neuromancer, goliath_prime, black_ice_lord) 모두 3-phase. Phase 4 (finale, HP ≤ 15%) 부재.
- **Per-boss scripted mechanics**: Wintermute "personality drift" (status effect 강제), T-A "family vote" (multi-target AoE), Neuromancer "construct merge" (heal + buff), Goliath "ground slam" (knockback), Black ICE "glitch burst" (random status). 현재는 `special_ability: str | None` 필드만 정의, 실제 효과 미구현.
- **Death taunts**: 현재 `death_lines: tuple[str, ...]` 가 있으나, *player death* (자키 사망) 시 boss 가 마지막 한마디 — 부재.
- **Intro cinematic enhancement**: 현재 3-5s intro. Phase 4 unlock 시 추가 cinematic (3-stage text overlay) 미구현.

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: Phase 4 가 *점진적* (HP 15% 이하에서만 trigger) — 게임성 보존.
- **Pillar 3 (The Flatline)**: Phase 4 의 강력한 mechanic 이 *승리* 시에만 발동 (player HP 0 시는 Death cycle). death taunts 는 톤 유지.
- **Pillar 4 (The Build)**: Phase 4 mechanic 의 보상 (FRAG/CRED) 은 ADR-0147 salvage 와 통합.
- **Pillar 5 (The Style)**: 깁슨 어휘 ("construct personality", "family consensus", "merger complete").

**기술 제약**:
- `combat/boss.py` 724 LOC — ADR-0110 1000+ LOC 한계 근접. 신규 로직은 별도 모듈 권장.
- 신규 모듈 250 LOC ceiling (ADR-0110).
- `CinematicSequence` 이미 구현 (bosses.py:313) — Phase 4 cinematic 의 기반.

## 고려한 옵션

### Option 1: Phase 4 Finale 만 (HP 15% 이하에서 1회 scripted mechanic)

- **설명**: 5 boss 각각의 Phase 4 (finale) 정의. HP ≤ 15% 시 자동 trigger. mechanic 은 `special_ability` enum.
- **장점**:
  - 변경 범위 최소 — `combat/boss_phase4.py` ~120 LOC + `BossPhase` 확장.
  - 1 boss mechanic 추가가 게임성에 큰 영향.
  - Pillar 1 weight 보존 (15% HP trigger, 한 번만 발동).
- **단점**:
  - Death taunts / intro cinematic enhancement 미포함.
  - Per-boss 차별화 부족 (1 mechanic 만).
- **Pillar 정합**:
  - P1: 15% trigger, 1회.
  - P3: 보존.
  - P4: salvage 통합.
  - P5: 깁슨 어휘.

### Option 2: Phase 4 + Per-Boss Mechanics (Wintermute/T-A/Neuromancer/Goliath/Black ICE 각각 다른 mechanic)

- **설명**: 5 boss × 1 mechanic = 5 scripted effects. 각 mechanic 은 status effect (Wintermute personality drift, T-A family vote AoE, Neuromancer construct merge heal, Goliath ground slam knockback, Black ICE glitch burst random).
- **장점**:
  - Per-boss 차별화 (5 unique mechanics).
  - 1v1 의 다양성 즉시 향상.
  - Pillar 5 톤 강화 (각 boss 의 깁슨 어휘).
- **단점**:
  - 변경 범위 중간 — 5 mechanic + test surface 폭증.
  - death taunts 미포함.
- **Pillar 정합**:
  - P1: 15% trigger.
  - P3: *승리* 시 mechanic 발동 (player HP 0 시는 Death cycle).
  - P4: salvage 보상.
  - P5: 5 unique 깁슨 어휘.

### Option 3: Phase 4 + Per-Boss Mechanics + Death Taunts + Intro Enhancement (전체)

- **설명**: 본 ADR 의 4 sub-feature 모두 구현.
  - **Phase 4 Finale**: 5 boss × 1 mechanic (Option 2).
  - **Death Taunts**: 5 boss × 2-3 taunt lines (`state.death_taunt` field set on player death by boss).
  - **Intro Enhancement**: 3-stage text overlay (name + role + warning) on boss encounter.
  - **Anti-pattern check**: Phase 4 mechanic 은 HP 추가 (*not* HP-buff) — anti-pattern 회피.
- **장점**:
  - 4 sub-feature 모두 — *narrative climax* 완성.
  - Death cycle (ADR-0040) + death taunts 통합 — 톤 강화.
  - Intro enhancement 가 1v1 의 첫 인상 강화.
- **단점**:
  - 변경 범위 최대 — `combat/boss_phase4.py` ~200 LOC + 4 sub-feature.
  - CinematicSequence 확장 필요.
- **Pillar 정합**:
  - P1: 15% trigger, 1회 (anti-pattern 회피).
  - P3: death taunts = Pillar 3 weight 강화.
  - P4: salvage 보상 통합.
  - P5: 깁슨 어휘.

## 추천 (Recommendation)

**Option 3** (Phase 4 + Per-Boss Mechanics + Death Taunts + Intro Enhancement).

이유:
1. **Pillar 정합성**: 5 Pillar 모두 매핑. Pillar 1 weight 보존 (15% HP trigger + 1회). Pillar 3 weight 는 death taunts 로 강화. Pillar 5 톤은 5 unique 깁슨 어휘.
2. **사용자 가치**: Cycle 1 (salvage) + Cycle 2 (depth) 의 기반 위에 *climactic finale* 추가 — v1.1.0+ 의 "전투 강화" 의 마지막 가치 단위.
3. **테스트 커버리지**: 5 mechanic × 2 tests = 10 + death taunts × 3 = 13 + intro × 2 = 4 = 17 tests. combat/boss coverage 96% → 99%.
4. **확장 가능성**: 5 mechanic 은 status effect framework (Cycle 2) 기반 — 후속 cycle (v1.2.0+) 에서 mechanic 추가 용이.
5. **모듈 사이즈**: 신규 `combat/boss_phase4.py` ~200 LOC (250 ceiling 의 80%). 기존 1000+ LOC 모듈 0개 신규.
6. **기존 시스템 호환**: `BossProfile`, `PhaseProfile`, `CinematicSequence` 모두 존재. 신규 hook 없음.

**순서 (Cycle 3 sub-cycles)**:
- 3A: Phase 4 Finale mechanics (1 sub-session)
- 3B: Death taunts + intro enhancement (1 sub-session)

각 sub-session 1-2 시간. Cycle 3 전체 = 2-3 시간.

## 사용자 결정 (Decision)

[x] Option 3 (Phase 4 + Per-Boss Mechanics + Death Taunts + Intro Enhancement) — 2026-08-07 Cycle 3 채택
[ ] Option 1 (Phase 4 Finale 만)
[ ] Option 2 (Phase 4 + Per-Boss Mechanics 만)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. 신규 모듈

`prototype/src/roguelike_sprawl/combat/boss_phase4.py` (NEW, ~200 LOC):

```python
"""Boss Phase 4 Finale (ADR-0149).

5 main bosses with unique scripted mechanics at HP <= 15%:
- Wintermute: personality_drift (status effect - status resistance)
- TA_PRIME: family_vote (AoE damage to player + npc construct if present)
- Neuromancer: construct_merge (heal + buff - boss regains 20% HP + +2 attack)
- Goliath: ground_slam (knockback - player stunned 1s + screen shake)
- Black_ICE: glitch_burst (random status - 3 random status effects on player)

Death taunts (player death by boss):
- 2-3 lines per boss, player death triggers random pick.

Intro enhancement:
- 3-stage text overlay (name + role + warning) on boss encounter.
```

### 2. 신규 enum / dataclass

`Phase4Mechanic` (StrEnum): PERSONALITY_DRIFT / FAMILY_VOTE / CONSTRUCT_MERGE / GROUND_SLAM / GLITCH_BURST
`DeathTaunt` (frozen dataclass): boss_id, lines (tuple[str, ...])
`BossIntroEnhancement` (frozen dataclass): stage_1_name, stage_2_role, stage_3_warning

### 3. AppState / CombatState 확장

- `AppState.death_taunt: str | None = None` (set on player death by boss)
- `AppState.phase4_triggered: bool = False` (one-shot per boss fight)
- `AppState.boss_intro_enhancement: BossIntroEnhancement | None = None` (set on boss encounter)
- `CombatState.boss_phase4_mechanic: str | None = None` (current Phase 4 mechanic)

### 4. 기존 함수 patch

- `combat/boss.py` 의 `BOSS_PROFILES` 매핑에 Phase 4 mechanic 추가
- `engine/combat_view_state.py::_end_combat` 의 `defeat` path 에 death taunt set
- `engine/main_loop.py` 의 boss encounter path 에 intro enhancement set

### 5. i18n 갱신

`data/i18n/{en,ko}.json` 의 `boss_phase4` 섹션 신규:
- intro_stage_1: "[{boss_name}]" (boss 이름)
- intro_stage_2: "{role}" (예: "WINTERMUTE // neural intruder")
- intro_stage_3: "{warning}" (예: "data vulnerable. personal trace detected.")
- death_taunt_* per boss × 2-3 lines
- personality_drift_applied, family_vote_damage, construct_merge_heal, ground_slam_stun, glitch_burst_status

### 6. 테스트 추가 (17 tests)

`tests/unit/test_boss_phase4.py` (NEW):
- TC-PHASE4-001: Phase 4 trigger at HP 15% threshold
- TC-PHASE4-002: Wintermute personality drift reduces player attack
- TC-PHASE4-003: T-A family vote deals AoE damage
- TC-PHASE4-004: Neuromancer construct merge heals + buffs boss
- TC-PHASE4-005: Goliath ground slam applies stun + screen shake
- TC-PHASE4-006: Black ICE glitch burst applies 3 random statuses
- TC-PHASE4-007: Phase 4 triggers only once per fight (one-shot)
- TC-PHASE4-008: Phase 4 mechanic does not apply if HP > 15%
- TC-PHASE4-009: Phase 4 mechanic does not apply if phase 4 already triggered
- TC-PHASE4-010: Wintermute death taunt (player death by wintermute)
- TC-PHASE4-011: Neuromancer death taunt
- TC-PHASE4-012: T-A Prime death taunt
- TC-PHASE4-013: Goliath Prime death taunt
- TC-PHASE4-014: Death taunt is None when player dies to non-boss
- TC-PHASE4-015: Intro enhancement stage 1 sets boss name
- TC-PHASE4-016: Intro enhancement stage 2 sets role
- TC-PHASE4-017: Intro enhancement stage 3 sets warning

### 7. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | 15% trigger, 1회 | TC-PHASE4-001, 007, 008 |
| P2 (The Matrix) | 깁슨 어휘 | i18n strings |
| P3 (The Flatline) | death taunts (Pillar 3 weight) | TC-PHASE4-010~014 |
| P4 (The Build) | Phase 4 mechanic 보상 = salvage (ADR-0147) | integrated test |
| P5 (The Style) | 5 unique 깁슨 어휘 | i18n strings |

## 영향 받는 항목

- `prototype/src/roguelike_sprawl/combat/boss_phase4.py` (NEW)
- `prototype/src/roguelike_sprawl/combat/__init__.py` (re-exports)
- `prototype/src/roguelike_sprawl/combat/boss.py` (BOSS_PROFILES Phase 4 mechanic 추가)
- `prototype/src/roguelike_sprawl/engine/state.py` (AppState 확장)
- `prototype/src/roguelike_sprawl/engine/combat_view_state.py` (defeat path death taunt)
- `prototype/src/roguelike_sprawl/engine/main_loop.py` (intro enhancement trigger)
- `prototype/data/i18n/{en,ko}.json` (boss_phase4 섹션)
- `prototype/tests/unit/test_boss_phase4.py` (NEW)
- `design/systems/combat.md` (Boss Phase 4 Finale section)
- `testcases/combat/boss-phase4.md` (NEW: TC-PHASE4-001~017)
- `log.md` (Cycle 3 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0149 entry)

## 관련 결정

- ADR-0050 — Boss ICE 3-phase (Accepted)
- ADR-0125 — Boss AoE + Minion Spawn (Phase B-3, Accepted)
- ADR-0147 — Data Salvage Phase 6+ (Cycle 1, Accepted)
- ADR-0148 — Combat Depth Expansion (Cycle 2, Accepted, aggression="boss" 50% skill use 기반)
- ADR-0110 — 모듈 사이즈 정책 (boss_phase4.py ~200 LOC, 250 ceiling 의 80%)
- ADR-0090 — Salvation Phase Integration (per-boss mechanic 의 narrative 기반)
- ADR-0040 — Death & Restart Cycle (death taunt 통합)

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 3 of A+B+C)
- 2026-08-07: Accepted (Option 3, 사용자 Cycle 3 채택)
