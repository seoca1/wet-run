# System: Combat (전투 시스템)

> **상위 결정**: `../../decisions/0003-combat-system.md` (Accepted, Revised), `../../decisions/0014-data-salvage.md` (Accepted)
> **관련**: ADR-0008 (Item Tier), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR), ADR-0013 (Events)

## 목적

사이버스페이스 안에서 ICE / 적 decker와의 전투를 *실시간 + 메뉴 스킬* (RT-MS)로 표현. Pillar 1 (The Run), 3 (The Flatline), 5 (The Style)를 모두 만족.

> **Pillar 3 (강화, ADR-0014)**: 전투 승리 시 *Data Salvage*로 부분 회복 가능. 단, *이겨야만* + *20%만* + *선택해야만* — 무게 유지.

## RT-MS (Real-Time with Menu Skills)

ADR-0003의 핵심. 한 줄 요약: **실시간 자동 공격 + 메뉴로 강력한 스킬**.

### 자원 (Resources)

| 자원 | 설명 | 회복 |
| --- | --- | --- |
| **HP** (Health) | 데크의 무결성. 0 = flatline. | 전투 승리 시 Data Salvage (HEAL 15%, ADR-0152 rebalance) |
| **AP** (Action Points) | 스킬 비용. 시간 경과로 자동 회복. | 자연 회복 |
| **BW** (Bandwidth) | 동시 활성 program 수. | 자연 회복 |
| **PW** (Processing Power) | program 복잡도 한계. | 고정 (장비 의존) |

**HP 풀 (T1~T5)**:
- T1: 100 HP
- T2: 120 HP
- T3: 150 HP
- T4: 200 HP
- T5: 300 HP

(구체 수치는 `decisions/0008-progression-system.md` L213 "향후 결정" — Phase 5+ 밸런스 패치에서 확정)

### 자동 공격 (Auto-Attack)

- 양쪽 (플레이어 + 적)이 일정 간격으로 자동 공격
- 1 attack / 2초 (양쪽 동시)
- 기본 데미지: 자키 기본 5, ICE 기본 3 (T1 기준)
- 시각: ASCII 깜빡임, 사이드 이동, 데미지 숫자
- 한쪽 HP 0 또는 플레이어가 결정할 때까지 지속

### 메뉴 스킬 (Skill)

- `[SPACE]` → 메뉴 열림, **시간 정지**
- 사용 가능한 스킬 목록 (AP 비용, 효과)
- 방향키 선택, `[ENTER]`로 실행 → 시간 재개
- 명확한 피드백: 데미지, 효과, 자원 변화 표시

### Programs (메뉴 스킬)

| Program | Type | AP | 효과 |
| --- | --- | --- | --- |
| **Goliath** | Attack | 3 | heavy hit (3x base, 25 dmg) |
| **Kraken** | Attack | 4 | strongest attack (50 dmg) |
| **Hammer** | Attack | 2 | medium attack |
| **Virus** | Attack | 2 | DoT (3 ticks) |
| **Worm** | Attack | 2 | multi-hit (2-3 hits) |
| **Wisp** | Defense | 2 | shield +1 (active) |
| **Wardrone** | Defense | 2 | auto-counter (active) |
| **Shield** | Defense | 1 | one-time block |
| **Watchdog** | Detect | 1 | reveal enemy next attack |
| **Probe** | Detect | 1 | show enemy HP / skill |
| **Hellhound** | Track | 3 | forced engagement |

(데이터: `data/programs/programs.json`)

### Combat Flow

```
[Matrix: encounter ICE]
  ↓
[PPL vs ZDR 표시 — 진입 결정]
  ↓ (Continue)
[Combat begins: real-time, auto-attack starts]
  ↓ (continuous)
[Auto-attack ticks: 양쪽 자동 공격, 시각: 깜빡임/숫자]
  ↓ (player presses SPACE anytime)
[Menu: time pauses]
  ↓
[Player selects skill]
  ↓
[Time resumes, skill executes]
  ↓
[Combat continues until: ICE HP 0 OR player HP 0 OR player disengages]
  ↓ (ICE 격파 시)
[Data Salvage 메뉴 — 시간 정지 유지 (ADR-0014)]
  ↓
[매트릭스 복귀]
```

### Construct Companion (Dixie — Pillar 5 actual combat ally)

> **Cycle 4 polish (2026-08-03, ADR-0140 partial)**: Dixie Flatline은 기본적으로 dialog-only NPC이지만, `state.construct_companion_active = True`일 때 **실제 전투 동료**로 작동한다. 깁슨 코퍼스의 "digital ghost" 톤을 그대로 반영 — Dixie가 console cowboy와 함께 싸우는 모습.

**Activation**: `state.construct_companion_active` (default `False`). 토글은 옵션/설정 화면 또는 construct_whisper UI에서 노출 (v1.2.0+).

**Combat behavior** (구현: `combat/state.py::tick_dixie_ally`):

| 항목 | 값 | 비고 |
| --- | --- | --- |
| Tick interval | **2000 ms** (`ALLY_AUTO_ATTACK_INTERVAL_MS`) | 플레이어 자동 공격(1500 ms)보다 느림 — 보조 딜러 포지션 |
| Damage per tick | **5** (`DIXIE_ALLY_DAMAGE`) | 고정값 — Pillar 4 unlock-only meta-progression (stat boost 금지) |
| Target | `combat_state.target` | 플레이어와 동일 대상 — focus fire |
| Stunned check | None | Dixie는 status effect 면역 (구현 단순화) |

**Wire-up**: `engine/main_loop.py::_advance_combat`이 `step_combat` 직후, `maybe_boss_phase_transition` 직전에 `tick_dixie_ally(state.combat_state, state)` 호출.

**Ephemeral state**: `combat_state._dixie_last_attack_ms` (dynamic attribute, `CombatState` schema에 미포함 — ephemeral per-run).

**Pillar 정합**:
- **Pillar 4 (The Build)**: unlock-only meta-progression. Dixie ally는 stat boost 없이 *동일 stats + DPS 보조*. AppState() 생성 시 자동 reset (테스트로 검증: `test_does_not_modify_player_stats`).
- **Pillar 5 (The Style)**: Dixie는 깁슨 코퍼스의 *construct* — 죽은 decker의 ROM에 저장된 인격. 전투에서 싸우는 것은 톤과 정합 ("Dixie strikes ..." 로그).

**Combat log example**:
```
>>> Dixie strikes black-ice for 5
>>> Dixie strikes black-ice for 5
```

**Test coverage** (`tests/unit/test_construct_companion.py::TestTickDixieAlly`, 5 tests):
- `test_no_op_when_construct_companion_inactive` — default dialog-only
- `test_attacks_when_construct_companion_active` — deals DIXIE_ALLY_DAMAGE
- `test_no_op_when_combat_finished` — no attack after combat ends
- `test_no_op_when_target_is_dead` — no attack when target HP <= 0
- `test_respects_attack_interval` — consecutive calls don't double-attack

**의도적 제약** (구현 단순화):
- Dixie는 skill 사용 불가 (auto-attack만)
- Dixie는 damage 받지 않음 (no HP, no death state)
- Dixie는 target selection 로직 없음 (플레이어 target 그대로 따름)
- Dixie는 status effect 면역

향후 확장 (v1.2.0+ backlog):
- Dixie skill set (예: `[[decompile]]`, `[[icebreaker_overdrive]]`)
- Dixie HP / damage taken / player damage source 추적
- AI target selection (lowest HP enemy)

## Data Salvage (ADR-0014)

전투 승리 후 *데이터 회수* 흐름. Pillar 3의 무게를 일부 완화하되, *선택 + 승리 + 제한* 으로 무게 유지.

### Salvage 메뉴

```
=========================
   DATA SALVAGE
=========================
ICE 격파. 잔여 데이터 회수 가능.

> HEAL    +20% max HP (T1 = +20, T3 = +30)
  FRAG    +1 salvage fragment (in-run unlock; alarm ≥3 시 50% 감소)
  CRED    +30 credits, alarm -1 (alarm ≥3 시 50% 감소)
  SKIP    no reward

↑/↓ select, ENTER confirm
=========================
```

### Phase 5 범위

- **HEAL만 작동** (FRAG, CRED는 "Phase 6+: not yet implemented" 안내)
- 회복량: `round(max_hp * 0.20)`, 최소 1
- HP가 max인 상태에서 HEAL 선택 → "no damage to repair" 메시지 + 회복 0 (자원 낭비 알림)

### Phase 6+ 확장 (ADR-0147, v1.1.0+ Cycle 1)

- **HEAL**: **15% max HP** (ADR-0152 rebalance, was 20%), tier-scaled, max-cap alert
- **FRAG**: +1 `state.salvage_fragments` (in-run unlock, death 시 loss — Pillar 4 정합)
- **CRED**: +30 `state.credits` + `-1 state.alarm_level` (clamped ≥ 0, Pillar 1 weight)
- **SKIP**: 보상 없음 (전략적 선택)
- **Alarm trade-off** (Pillar 1 weight): `state.alarm_level >= 3` 이면 FRAG/CRED yield 50% 감소 (rounded down, min 0)
- **3-way decision trade-off**: HEAL 즉시 회복 vs FRAG in-run unlock vs CRED + alarm relief. Alarm level 이 trade-off 결정에 영향.

### Disengage / Death

- **Disengage (철수)**: ICE 격파 X → salvage 없음 (ADR-0003)
- **Death (자키 HP 0)**: salvage 없음 → flatline (Pillar 3)

### Pillar 정합

- **P1 (The Run)**: 한 런 = 한 무게. 회복은 *승리의 보상*. 매번 모든 전투 이길 수 없음 → 자키는 여전히 위험.
- **P2 (The Matrix)**: salvage는 매트릭스 안의 *데이터 추출*. Pillar 2 정합.
- **P3 (The Flatline)**: 회복이 *있지만* (a) 이겨야만, (b) HEAL만, (c) 20%만. 무조건 회복 X. 자키가 5번 싸워서 1번 회복할 수 있는 구조 — 무게 유지.
- **P4 (The Build)**: FRAG (런 내 unlock), CRED (메타 진행) — Pillar 4와 정합.
- **P5 (The Style)**: ICE 격파 → "data exposed" → salvage — 깁슨 어휘.

## 비주얼 디자인 (ADR-0011, ADR-0003)

### 전투 화면

```
[Player]              [Enemy]
◉P◉                   ▲ICE▲
[▓▓▓▓▓░░░] HP 50/100  [▓▓▓▓▓▓▓▓] HP 80/100
[█] AP 4/6            (ICE: AP N/A)

Action log:
> You hit ICE for 5 damage.
> ICE hits you for 3 damage.
> You hit ICE for 5 damage.

[SPACE] for skills   [ESC] to disengage
```

### 메뉴 (시간 정지)

```
=========================
        MENU
=========================
Skills available (AP 4/6):

> GOLIATH    (3 AP)  - heavy attack
  WISP       (2 AP)  - shield (active)
  WARDRONE   (2 AP)  - auto-counter (active)
  PROBE      (1 AP)  - reveal enemy
  VIRUS      (2 AP)  - DoT
  CANCEL

↑/↓ select, ENTER confirm
=========================
```

### 애니메이션

- **자동 공격**: 0.2초 깜빡임 + 데미지 숫자 표시
- **스킬 발동**: 0.5초 효과 (브래킷 변경, 색 변화, 큰 데미지)
- **메뉴 열림**: 화면 dim, 메뉴 박스 fade-in
- **HP 변화**: HP 바 색 변화 (녹→황→적)
- **상호작용**: 적 공격 시 화면 흔들림 효과 (ASCII)
- **ICE 격파**: portrait fade-out (선택)

## Combat Depth Expansion (ADR-0148, v1.1.0+ Cycle 2)

> Cycle 1 (ADR-0147) 의 alarm-aware salvage 가 본 ADR 의 Pillar 1 weight 보완. 4 sub-feature 가 1v1 의 단조로움 해소.

### Counter Window

적의 skill 사용 직후 **200ms** 동안 player 의 `SkillEffect.COUNTER` skill 사용 가능. counter-attack 성공 시 2x damage + 0.5s stun. 시간 정지 (RT-MS 의 "reactive gameplay").

```
>>> ICE Watchdog uses "trace"!
>>> COUNTER WINDOW (200ms)!
[Space] → Counter-Strike (2x damage + stun)
```

**Pillar 정합**:
- P3 (The Flatline): HEAL 변화 없음, *기술적* 깊이 추가.
- P5 (The Style): 깁슨 "counter-trace" 어휘.

### Defense Stackable + Duration

3가지 defense program 의 stackable + duration 로직:

| Program | Shield | Duration | Special |
|---|---|---|---|
| **Wisp** (T1) | +1 | 5s | Stackable, duration refresh |
| **Shield** (T1) | +3 | 1-hit | One-shot (consumed on attack) |
| **Wardrone** (T4) | +2 | 10s | + auto-counter (5s cool down) |

`state.shield` (전역 카운터) + per-status shield (`StatusEffect.is_shield=True`). Multiple Wisp stacks → cumulative shield + latest duration.

### Companion Skills (Dixie)

`construct_companion_active = True` 일 때 Dixie 가 skill 사용 가능:

| Skill | AP | 효과 |
|---|---|---|
| `[[decompile]]` | 1 | target 의 attack_bonus -1 (3s) |
| `[[icebreaker_overdrive]]` | 3 | target 에 50 데미지 + damage_up 5s |

Pillar 4 (The Build) in-run only (death = loss). construct_whisper UI 와 연동 (Pillar 5: construct = digital ghost).

### ICE Aggression Tiers

`ice_kind` 별 4-tier aggression (skill use probability):

| Tier | Probability | 예시 |
|---|---|---|
| PASSIVE | 5% | tutorial ICE, low-grade |
| STANDARD | 15% | watchdogs, standard, patrol |
| AGGRESSIVE | 35% | black, goliath, hunter |
| BOSS | 50% | wintermute, neuromancer, ta_prime |

`data/combat/ice_types.json` 의 `aggression` field. Cycle 3 (ADR-0149) 의 Boss Phase 4 의 scripted mechanic 기반.

## PPL & ZDR 통합 (ADR-0012)

### Combat 진입 전

```
> You approach: [ICE — Standard]
> ZDR: 7 (TOUGH for your PPL 6)
> Recommendation: Disengage or upgrade.

[Continue] [Disengage]
```

### Combat 중 HUD

```
[YOU: PPL 6]  [ZONE: ZDR 7]  Status: TOUGH (0.86x)
◉P◉ [▓▓▓▓▓░░░] HP 50/100     ▲ICE▲ [▓▓▓▓▓▓▓▓] HP 80/100
```

### Status (5 categories)

| Ratio | Status | 색상 | 의미 |
| --- | --- | --- | --- |
| > 1.5 | SAFE | green | 압도적 |
| 1.0 - 1.5 | MATCH | cyan | 균등 |
| 0.75 - 1.0 | TOUGH | yellow | 불리 |
| 0.5 - 0.75 | DEADLY | red | 매우 위험 |
| < 0.5 | FUTILE | dark_red | 자살행위 |

## Boss Phase 4 Finale (ADR-0149, v1.1.0+ Cycle 3 of A+B+C)

> Cycle 1 (ADR-0147) 의 alarm-aware salvage + Cycle 2 (ADR-0148) 의 aggression tier 기반. 5 주요 boss 의 *climactic finale*.

### Phase 4 Trigger

HP ≤ 15% 시 1회 scripted mechanic 발동. `phase4_triggered` flag 로 one-shot 보장.

### Phase 17 UI 노출 (F.4 Boss Phase Transitions)

Phase 17 에서 보스 phase 전환이 실제 combat 흐름에 통합되어 *시각적으로* 드러난다.

**전투 데미지 적용** (`engine/combat_tick.py::_calculate_damage`):
```python
multiplier = boss_phase_tracker.get_damage_multiplier(enemy_id, current_phase)
applied = round(base_damage * multiplier)
```

**CombatState phase change 기록** (`combat/state_models.py`):
- `phase_change_ms: int` — phase 전환 발생 timestamp (ms)
- `phase_change_color: tuple[int, int, int]` — phase 고유 RGB (5 phase 별)

**렌더링** (`engine/combat_view_render.py`):
- 전투 렌더링 시 `(now_ms - phase_change_ms) < 1500` 이면 HUD 색상이 **yellow → phase color** 로 1.5초간 블렌드
- 시각 효과: 보스가 phase 진입한 직후 짧은 색상 강조 — 깁슨 톤의 "the ICE shifts, changes color, knows it's hurt"

**테스트 커버리지** (`tests/unit/test_f4_boss_phase_combat.py`, 331 LOC):
- 8 test: phase 진입 → 데미지 multiplier 적용, state 기록, HUD 블렌드 윈도우 검증

### Per-Boss Mechanics

| Boss | Mechanic | 효과 |
|---|---|---|
| **Wintermute** | `personality_drift` | player 의 attack_bonus 50% 감소 (3s) |
| **T-A Prime** | `family_vote` | AoE damage 20 + construct companion 있으면 +10 |
| **Neuromancer** | `construct_merge` | boss HP 20% 회복 + attack +2 (3s) |
| **Goliath Prime** | `ground_slam` | player stun 1s + screen shake |
| **Black ICE Lord** | `glitch_burst` | 3 random status effects (3s each) |

### Death Taunts (Pillar 3)

Player 사망 시 boss 의 마지막 한마디 (5 boss × 2-3 lines):

| Boss | Taunt (EN sample) |
|---|---|
| Wintermute | "I see you, cowboy. Your pattern is mine." |
| T-A Prime | "Family consensus: you are not welcome." |
| Neuromancer | "We are the merger. You are the remainder." |
| Goliath Prime | "Ground... settles... all." |
| Black ICE Lord | "Glitch. Catch. Static. You." |

### Intro Enhancement

3-stage text overlay on boss encounter:
1. **Stage 1**: `[BOSS NAME]`
2. **Stage 2**: `role` (e.g. `WINTERMUTE // neural intruder`)
3. **Stage 3**: `warning` (e.g. `data vulnerable. personal trace detected.`)

Pillar 정합:
- P1: 15% trigger, 1회, mechanic 은 HP 추가 (*not* buff) — anti-pattern 회피.
- P3: death taunts 가 Pillar 3 weight 강화.
- P4: Phase 4 mechanic 보상 = ADR-0147 salvage 통합.
- P5: 5 unique 깁슨 어휘 (construct, family, merger, ground, glitch).

## Info Market Intel Items (ADR-0151, Cycle 6)

> ADR-0147 §Phase 6+ 의 "CRED: Info Market 에서 정보 구매" deferred item 구현. 3-way salvage trade-off 의 CRED branch 완성.

3 intel items purchasable with CRED at the Info Market (픽서 construct):

| Item | Price | 효과 | Pillar |
|---|---|---|---|
| **alarm_reducer** | 30 credits | `state.alarm_level -= 2` (clamped ≥ 0) | P1 (Run) |
| **mission_hint** | 40 credits | 현재 미션 objective data node 위치 status message 표시 | P1 (Run) |
| **faction_rumor** | 50 credits | 다음 faction event 확률 +25% (faction_tension) | P5 (Style) |

### Purchase Flow

```
>>> Alarm Reducer: 30 credits. Purchase? [Y/n]
>>> CRED spent: 30 (50 → 20)
>>> Alarm level: 4 → 2 (Pillar 1 weight 감소)
```

### Pillar 정합

- **P1 (The Run)**: alarm_reducer + mission_hint → run weight 감소 (information advantage)
- **P4 (The Build)**: in-run only (death = loss via `AppState` reset)
- **P5 (The Style)**: faction_rumor → 깁슨 "construct echo" 어휘 강화

### 기존 인프라 재사용

- `crafting/info_market.py` 의 `InfoMarket` 클래스 + `MarketItem` + `purchase()` + faction discount
- `AppState.credits: int` + `AppState.inventory: dict[str, int]`
- `engine/hub.py` 의 market display

### 신규 모듈

- `combat/intel_items.py` (~150 LOC): `apply_intel_item(state, item_id)` + 3 item definitions
- `AppState.purchased_intel_items: list[str]` 필드 (one-shot per item_id tracking)

## Multi-Enemy Encounters (ADR-0152, Cycle 8)

> Cycle 2 Option 1 의 deferred multi-enemy 구현. ADR-0147 (alarm-aware salvage) + ADR-0148 (intel alarm) + ADR-0151 (intel alarm_reducer) 가 1vN 의 Pillar 3 weight 보완.

### Encounter Count by Grade

| Grade | Enemies | Description |
|---|---|---|
| 1-2 | 1 | Novice, tutorial |
| 3-4 | 2 | Intermediate, pack |
| 5-6 | 3 | Veteran, swarm |

점진적 난이도 curve: Grade 1-2 에서 1v1 으로 시작, Grade 3 부터 1v2, Grade 5 부터 1v3.

### Player Auto-Attack (Multi-Enemy)

Player 의 auto-attack 은 **모든 alive enemy** 를 순차 공격 (ADR-0152 §Consequences.3). 매 auto-attack tick 마다:

```
for target in all_alive_enemies(state):
    dmg, is_crit = _calculate_damage(state, base_dmg, player, target)
    applied = _apply_damage(state, target, dmg)
    state.push(f"You strike {target.name} for {applied} damage.")
```

Player 가 Tab key 로 `cycle_target` 호출 → `target_index` 순환 (dead enemy skip).

### HEAL Rebalance 20% → 15% (ADR-0152 §Consequences.2)

1vN 에서 HEAL 20% 가 *trivial* (3명 damage → 1회 HEAL로 60 회복 = damage 1회당 HEAL 1회 보상) 되는 문제. HEAL_PCT 0.20 → **0.15** 로 rebalance:

| Tier | Old (20%) | New (15%) |
|---|---|---|
| T1 (100 max) | +20 | +15 |
| T3 (150 max) | +30 | +22 (banker's rounding 22.5 → 22) |
| T5 (300 max) | +60 | +45 |

Pillar 3 (The Flatline) weight 보존: 1vN 에서 HEAL 1회로 *3명 damage 보상 불가* → player 가 더 strategic 해야 함.

### Pillar 정합

- **P1 (The Run)**: 1vN alarm accumulate → alarm-aware salvage (ADR-0147) + intel alarm_reducer (ADR-0151) 가 보완.
- **P3 (The Flatline)**: HEAL 15% + 1-of-4 choice → Pillar 3 weight 보존 (1vN 에서 trivial 방지).
- **P5 (The Style)**: 깁슨 어휘 + multi-enemy 묘사 ("swarm", "pack", "encircle").

### 신규 모듈

- `combat/multi_enemy.py` (~115 LOC): `cycle_target` + `all_alive_enemies` + `encounter_count_for_grade` + `auto_attack_all_alive`
- 기존 `CombatState.enemies` + `target_index` 인프라 100% 재사용

## 구현 가이드

### Phase 5+ Combat 모듈 구조

```
src/wet_run/combat/
├── __init__.py
├── state.py        # CombatState (player, enemy, tick, menu)
├── state_models.py # CombatState phase_change_ms + phase_change_color (Phase 17)
├── programs.py     # Program 데이터 + 사용 가능 슬롯
├── engine.py       # 자동 공격 tick, menu pause/resume
├── damage.py       # damage 계산, HP 변화
├── salvage.py      # Data Salvage 메뉴 (ADR-0014)
├── boss_phase_tracker.py  # BossPhaseTracker.get_damage_multiplier (Phase 17 wiring)
├── telemetry_integration.py  # TelemetryIntegrator.record_boss_reached (Phase 16)
├── multi_enemy.py  # 1vN encounter (ADR-0152)
├── intel_items.py  # Info Market 3 intel items (ADR-0151)
└── render.py       # combat 화면 렌더링 (Phase 17 1.5s blend)
```

**Engine 통합 (Phase 15-17)**:
- `engine/combat_view_state.py::start_combat` → 보스 ICE 시작 시 `record_boss_reached` 발동 (opt-in 한정, ADR-0184)
- `engine/combat_tick.py::_calculate_damage` → `BossPhaseTracker.get_damage_multiplier()` 적용
- `engine/combat_view_render.py` → phase_change_ms 윈도우 내 yellow→phase color 블렌드

### Player state 확장

```python
@dataclass
class Player:
    loadout: Loadout
    hp: int           # current HP
    max_hp: int       # calculated from tier
    ap: int           # current AP
    bw: int           # bandwidth
    pw: int           # processing power
```

### Salvage flow

```python
def apply_salvage(choice: SalvageChoice, player: Player) -> int:
    """Return new HP after applying salvage choice."""
    if choice is SalvageChoice.HEAL:
        heal = max(1, round(player.max_hp * 0.20))
        return min(player.max_hp, player.hp + heal)
    if choice is SalvageChoice.SKIP:
        return player.hp
    # FRAG, CRED: Phase 6+
    return player.hp
```

## 향후 결정

- HP 풀 T1~T5 구체적 수치 (Phase 5+ 밸런스)
- 자동 공격 속도 (1-2초)
- AP 회복 속도
- 메뉴 키 (Space vs Tab)
- 다중 적 (1-3 동시)
- 시각 효과 디테일

## Status Effect Glyphs (ADR-0207 / wet_run-web Tier 4)

`wet_run-web` 전투 화면에 표시되는 5개 상태이상 글리프 (2026-08-26):

| Glyph | 상태 | 효과 |
|---|---|---|
| `[B]` | Burn | 지속 DOT |
| `[S]` | Stun | 행동 불가 (N턴) |
| `[L]` | Slow | 공격 속도 감소 |
| `[M]` | Silence | 스킬 사용 불가 |
| `[V]` | Vulnerable | 받는 damage 증가 |

**위치**: `wet_run-web/src/renderer/vfx.ts::STATUS_GLYPHS` + `formatStatusGlyph()`. ICE 이름 옆 표시. **현재 web mock 데이터** (`mockStatusEffectsForTurn`) 사용 — Python reducer 통합은 Tier 5+ 에서.

**ASCII Art 효과 (wet_run-web)**:
- `hitFlashColor(delta)` — HP 변동 시 색상 플래시
- `ICE_DEFEAT_ART` / `PLAYER_DEFEAT_ART` — 격파 시 ASCII 아트
- `centerArt(art, width)` — 중앙 정렬
- HEAL 비율 (20% 적절? 15%? 25%?)
- FRAG / CRED 시스템 상세 (Phase 6+)
- 알람 / trace와 salvage의 상호작용

---

## Deck Size Selection (Phase 15)

> 런 시작 시 자키는 데크 사이즈를 선택 — LIGHT / STANDARD / HEAVY. combat 자원 (program slots / AP regen / cooldown) 에 직접 영향.

**3 옵션** (`engine/menu.py::render_deck_select`, `_confirm_deck_choice`):

| 사이즈 | Program Slots | AP Regen Modifier | Cooldown Modifier | Pillar 영향 |
|---|---|---|---|---|
| **LIGHT** | 6 slots | +50% | -10% | P1 (The Run) — 빠른 회복, 제한된 슬롯 |
| **STANDARD** | 8 slots | balanced (baseline) | baseline | P4 (The Build) — 기본 |
| **HEAVY** | 10 slots | -30% | +15% | P1 (The Run) — 많은 슬롯, 느린 회복 |

**선택 시점**: character select 직후, NEW RUN 의 첫 화면. ENTER 키로 확정.
**Telemetry trigger** (Phase 16): `record_deck_chosen(deck_size)` 가 opt-in 상태에서 발동.
**메뉴 진입**: `state.deck_select_index` 가 0/1/2 (LIGHT/STANDARD/HEAVY), 위/아래 키로 변경.

**Pillar 정합**:
- P1 (The Run): 사이즈 선택은 한 번의 결정 — 런 진행 중 변경 불가. 무게 유지.
- P4 (The Build): unlock-only meta-progression 과 정합 (deck_size 는 런 시작 시점 메타 preference).
- P5 (The Style): menu 렌더링 시 깁슨 톤 라벨 — "Light decks for the cautious. Heavy for the bold. Standard for the practical."

## 관련 문서

- `decisions/0003-combat-system.md` — RT-MS
- `decisions/0014-data-salvage.md` — Data Salvage
- `decisions/0008-progression-system.md` — Item Tier, HP 풀
- `decisions/0011-ascii-portraits.md` — combat portrait
- `decisions/0012-difficulty-rating.md` — PPL/ZDR
- `decisions/0013-story-events.md` — combat event
- `design/core_loop.md` — combat micro-loop
- `design/glossary.md` — HP, AP, BW, PW, Salvage
- `testcases/combat/salvage.md` — TC-COMBAT-001~008
