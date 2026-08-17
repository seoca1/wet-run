# TC-DEPTH: Combat Depth Expansion (ADR-0148)

> **관련**: `../../decisions/0148-combat-depth-expansion.md`, `../../decisions/0147-data-salvage-phase6.md`
> **관련 design**: `../../design/systems/combat.md` §Combat Depth Expansion
> **구현**: `../../prototype/src/wet_run/combat/depth.py`

전투 깊이 확장 — Counter Window, Defense Stackable, Companion Skills, ICE Aggression Tiers.

## TC-DEPTH-001: Counter Window Opens on Enemy Skill (P0, Active)

**Given**: combat 진행 중 (player vs ICE)
**When**: ICE 가 `SkillEffect.STUN` 등 skill 사용
**Then**: `CombatState.counter_window_open_ms = state.tick_ms + 200`
**Then**: status message: ">>> COUNTER WINDOW (200ms)!"

## TC-DEPTH-002: Counter-Attack 2x Damage + Stun (P0, Active)

**Given**: counter window 열림 (200ms 이내)
**When**: player 가 `SkillEffect.COUNTER` skill 사용
**Then**: damage = base_dmg * 2
**Then**: target 에 0.5s (500ms) stun
**Then**: status message: "Counter-attack lands for {dmg} damage!"

## TC-DEPTH-003: Counter Window Closes After 200ms (P0, Active)

**Given**: counter window 열림
**When**: 200ms 경과 (step_combat 1-2 ticks)
**Then**: `counter_window_open_ms` 가 *expired* (즉시 다음 player action 에서 무시)
**Then**: counter skill 사용 시 normal damage (1x)

## TC-DEPTH-004: Wisp Stackable (P1, Active)

**Given**: player HP 50, no shield, no wisp status
**When**: Wisp skill 1 사용 (1 AP, +1 shield, 5s)
**Then**: state.shield = 1, player.statuses 에 wisp 5s 추가
**When**: Wisp skill 2 (5s 이내)
**Then**: state.shield = 2, wisp duration refresh (5s from now)

## TC-DEPTH-005: Shield One-Hit (P1, Active)

**Given**: player, state.shield = 3
**When**: enemy 가 10 damage 공격
**Then**: shield 가 3 모두 흡수, 7 damage 가 player HP 에 적용
**Then**: Shield status 가 consumed (제거)

## TC-DEPTH-006: Wardrone + Auto-Counter (P1, Active)

**Given**: player, Wardrone 10s active (state.shield = 2)
**When**: enemy 가 공격 (5s 이내)
**Then**: Wardrone 자동 counter (적에게 +5 damage, 적 0.5s stun)
**Then**: Wardrone duration 5s 감소 (10s → 5s)

## TC-DEPTH-007: Dixie Decompile Reduces Attack (P1, Active)

**Given**: `app_state.construct_companion_active = True`, target ICE hp 100
**When**: Dixie `[[decompile]]` 사용 (1 AP)
**Then**: target.statuses 에 decompiled (3s, attack_bonus=-1) 추가
**Then**: target 의 attack power 1 감소

## TC-DEPTH-008: Dixie Icebreaker Overdrive (P1, Active)

**Given**: `app_state.construct_companion_active = True`, target ICE hp 100
**When**: Dixie `[[icebreaker_overdrive]]` 사용 (3 AP)
**Then**: target 에 50 damage 적용
**Then**: target.statuses 에 damage_up (5s) 추가 — 받는 데미지 +25%

## TC-DEPTH-009: Companion Skill Requires Active (P0, Active)

**Given**: `app_state.construct_companion_active = False` (default)
**When**: Dixie skill trigger 시도
**Then**: skill 사용 안 됨 (no-op)
**Then**: AP 차감 없음
**Then**: status message: "Dixie is silent (companion mode off)"

## TC-DEPTH-010: Passive ICE Skill Use 5% (P2, Active)

**Given**: ICE aggression = PASSIVE
**When**: 100 step_combat ticks
**Then**: ICE skill use count ≤ 10 (mean ~5, given 15% per-tick)

## TC-DEPTH-011: Standard ICE Skill Use 15% (P1, Active)

**Given**: ICE aggression = STANDARD
**When**: 100 step_combat ticks
**Then**: ICE skill use count ~15 (15% per-tick)

## TC-DEPTH-012: Aggressive ICE Skill Use 35% (P1, Active)

**Given**: ICE aggression = AGGRESSIVE
**When**: 100 step_combat ticks
**Then**: ICE skill use count ~35 (35% per-tick)

## TC-DEPTH-013: Boss ICE Skill Use 50% (P1, Active)

**Given**: ICE aggression = BOSS
**When**: 100 step_combat ticks
**Then**: ICE skill use count ~50 (50% per-tick)

## TC-DEPTH-014: Defense Duration Refresh on Stack (P1, Active)

**Given**: Wisp 3s remaining (state.shield = 1)
**When**: Wisp skill 2 (5s, +1 shield)
**Then**: state.shield = 2, wisp duration 5s (refresh, not 3+5=8s)

## TC-DEPTH-015: Counter Window Only Opens on Enemy Skill (P0, Active)

**Given**: combat 진행 중
**When**: player 가 skill 사용
**Then**: counter window 열리지 않음 (적의 skill 만 trigger)
**Then**: counter_window_open_ms 변화 없음

## 자동화 (예정)

- `tests/unit/test_combat_depth.py` — TC-DEPTH-001~015 단위 테스트
- `tests/integration/test_combat_depth_e2e.py` — 전체 combat 시뮬레이션 (counter + defense + companion + aggression)
- 회귀: 매 combat 시스템 변경 시
