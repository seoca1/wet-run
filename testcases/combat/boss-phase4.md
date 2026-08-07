# TC-PHASE4: Boss Phase 4 Finale (ADR-0149)

> **관련**: `../../decisions/0149-boss-phase4-finale.md`, `../../decisions/0050-boss-ice-system.md`, `../../decisions/0125-boss-aoe-minion-spawn.md`
> **관련 design**: `../../design/systems/combat.md` §Boss Phase 4 Finale
> **구현**: `../../prototype/src/roguelike_sprawl/combat/boss_phase4.py`

5 주요 boss 의 climactic finale — Phase 4 (HP ≤ 15%), Per-Boss Mechanics, Death Taunts, Intro Enhancement.

## TC-PHASE4-001: Phase 4 Trigger at HP 15% (P0, Active)

**Given**: combat 진행 중, boss ICE HP 100/100, max_hp 100
**When**: `step_combat` 으로 boss HP 14/100 (14% ≤ 15%) 됨
**Then**: `combat_state.boss_phase4_mechanic` 가 1회 set 됨
**Then**: `app_state.phase4_triggered = True`
**Then**: 상태 메시지: ">>> PHASE 4: {boss_name} activates {mechanic}!"

## TC-PHASE4-002: Wintermute Personality Drift (P0, Active)

**Given**: Wintermute Phase 4 trigger
**When**: `apply_wintermute_personality_drift(state)`
**Then**: player.statuses 에 `personality_drift` (3s, attack_bonus=-50% of base) 추가
**Then**: 상태 메시지: "Wintermute: personality drift applied — your patterns are mine."

## TC-PHASE4-003: T-A Prime Family Vote (P0, Active)

**Given**: T-A Prime Phase 4 trigger
**When**: `apply_ta_family_vote(state, has_companion=False)`
**Then**: player HP 20 damage
**When**: `has_companion=True`
**Then**: player HP 30 damage (companion penalty)

## TC-PHASE4-004: Neuromancer Construct Merge (P0, Active)

**Given**: Neuromancer Phase 4 trigger, boss HP 20/100
**When**: `apply_neuromancer_construct_merge(state)`
**Then**: boss HP 회복 (max_hp * 0.20) = 100 * 0.20 = 20 → HP 40
**Then**: boss.statuses 에 `merged` (3s, attack_bonus=+2) 추가
**Then**: 상태 메시지: "Neuromancer: construct merge complete. We are the merger."

## TC-PHASE4-005: Goliath Prime Ground Slam (P0, Active)

**Given**: Goliath Prime Phase 4 trigger
**When**: `apply_goliath_ground_slam(state)`
**Then**: player.statuses 에 `stun` (1000ms, is_stunned=True) 추가
**Then**: state.shake.trigger(intensity=3.0, duration_ms=400) 호출

## TC-PHASE4-006: Black ICE Lord Glitch Burst (P0, Active)

**Given**: Black ICE Lord Phase 4 trigger
**When**: `apply_black_ice_glitch_burst(state, rng)`
**Then**: 3 random status effects (3s each) — weakened / slowed / damaged_up
**Then**: 상태 메시지: "Black ICE Lord: glitch burst — 3 random status applied."

## TC-PHASE4-007: Phase 4 Triggers Only Once (P0, Active)

**Given**: Phase 4 이미 triggered
**When**: 추가 step_combat (boss HP 14/100 유지)
**Then**: mechanic 재발동 X (one-shot 보장)
**Then**: `phase4_triggered = True` (변화 없음)

## TC-PHASE4-008: Phase 4 Does Not Apply if HP > 15% (P0, Active)

**Given**: boss HP 50/100 (50% > 15%)
**When**: step_combat
**Then**: `boss_phase4_mechanic` 변화 없음
**Then**: `phase4_triggered` False 유지

## TC-PHASE4-009: Wintermute Death Taunt (P1, Active)

**Given**: player HP 0, Wintermute 가 마지막 공격
**When**: `_end_combat` defeat path
**Then**: `app_state.death_taunt` = "I see you, cowboy. Your pattern is mine." (random pick from 2-3 lines)
**Then**: 상태 메시지: ">>> Wintermute: I see you, cowboy. Your pattern is mine."

## TC-PHASE4-010: Neuromancer Death Taunt (P1, Active)

**Given**: player HP 0, Neuromancer 가 마지막 공격
**When**: `_end_combat` defeat path
**Then**: `app_state.death_taunt` = "We are the merger. You are the remainder."

## TC-PHASE4-011: T-A Prime Death Taunt (P1, Active)

**Given**: player HP 0, T-A Prime 가 마지막 공격
**When**: `_end_combat` defeat path
**Then**: `app_state.death_taunt` = "Family consensus: you are not welcome."

## TC-PHASE4-012: Goliath Prime Death Taunt (P1, Active)

**Given**: player HP 0, Goliath Prime 가 마지막 공격
**When**: `_end_combat` defeat path
**Then**: `app_state.death_taunt` = "Ground... settles... all."

## TC-PHASE4-013: Death Taunt None When Not Boss (P1, Active)

**Given**: player HP 0, regular ICE (not boss) 가 마지막 공격
**When**: `_end_combat` defeat path
**Then**: `app_state.death_taunt` = None

## TC-PHASE4-014: Intro Enhancement Stage 1 (P2, Active)

**Given**: combat encounter 시작, boss = Wintermute
**When**: `apply_boss_intro_enhancement(state, boss_id="wintermute")`
**Then**: `app_state.boss_intro_enhancement.stage_1` = "[WINTERMUTE]"

## TC-PHASE4-015: Intro Enhancement Stage 2 (P2, Active)

**Given**: Intro enhancement applied for Wintermute
**When**: `state.boss_intro_enhancement.stage_2`
**Then**: "WINTERMUTE // neural intruder"

## TC-PHASE4-016: Intro Enhancement Stage 3 (P2, Active)

**Given**: Intro enhancement applied for Wintermute
**When**: `state.boss_intro_enhancement.stage_3`
**Then**: "data vulnerable. personal trace detected."

## 자동화 (예정)

- `tests/unit/test_boss_phase4.py` — TC-PHASE4-001~016 단위 테스트
- `tests/integration/test_boss_phase4_e2e.py` — 전체 combat 시뮬레이션 (Phase 4 mechanic + death taunt + intro)
- 회귀: 매 boss 시스템 변경 시
