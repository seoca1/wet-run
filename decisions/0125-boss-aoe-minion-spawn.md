# ADR-0125: Boss Phase AoE + Minion Spawn (Phase B-3 Enhancement)

**상태**: Accepted (Option 4 — 기존 구조 확장, 2026-07-26)
**날짜**: 2026-07-26
**결정자**: 사용자 (위임 직접 판단)
**우선순위**: P3 (The Build)
**관련**: ADR-0050 (Boss ICE Multi-Phase), ADR-0120 (Docstring), ADR-0006 (Cross-project)

## 컨텍스트 (Context)

`prototype/src/wet_run/combat/boss.py`와 `combat/bosses.py`의
BossPhase 시스템은 3단계까지의 다단계 전투를 지원하지만, **페이즈 전환 시점의
추가 행동 (AoE 버스트, 미니언 소환) 이 없음**. 보스는 phase change 시 단순히
스킬 풀과 색만 바뀌고, 광역 공격이나 동료 소환 같은 전략적 깊이 부족.

**E-3 밸런스 audit 결과**:
- Grade 5/6 보스 전투가 1-phase + auto-attack 만으로는 단조로움
- 보스가 점점 강해지는 단방향 progression (플레이어만 학습)
- 미니언 동적 생성 메커니즘 부재

## 고려한 옵션

### Option 1: 보스 행동 AI 모듈 (status quo + AI layer)

- **설명**: 기존 BossProfile + IceBehavior 레이어 추가
- **장점**: AI decision-making 가능
- **단점**: 시스템 복잡, 작업량 多

### Option 2: 페이즈 이벤트 시스템 (event-driven)

- **설명**: Phase change 시 hook 시스템으로 콜백 발동
- **장점**: 확장성 높음
- **단점**: 인프라 구축 필요

### Option 3: 스킬 풀 확장 (AoE/CC 스킬 추가)

- **설명**: SkillEffect에 AOE/CROWD_CONTROL 추가, 보스 스킬 풀에 포함
- **장점**: 기존 인프라 활용
- **단점**: visual effect 시스템 확장 필요

### Option 4: Phase 필드 확장 (선택됨)

- **설명**: `BossPhase` 데이터클래스에 2개 필드 추가:
  - `aoe_damage: int = 0` — phase change 시 플레이어에게 광역 대미지
  - `spawn_minions: tuple[str, ...] = ()` — phase change 시 ICE ID 추가 소환
- **장점**:
  - 기존 BossPhase 구조 확장만 (backward compat)
  - Default `()` / `0` 으로 기존 보스 미영향
  - Combat tick 과 동일한 step_combat 사이클에서 호출 가능
- **단점**:
  - visual effect system 은 미확장 (텍스트 로그만)

## 추천 (Recommendation)

**Option 4** — Phase 필드 확장. 단순하지만 전투 깊이 대폭 향상.

## 사용자 결정 (Decision)

[x] Option 4 (Phase 필드 확장) — 사용자 위임 직접 판단

## 구현 (Implementation)

### 1. 데이터 스키마 (`combat/bosses.py`)

```python
@dataclass(frozen=True, slots=True)
class BossPhase:
    # ... existing fields ...
    # Phase B-3 additions:
    aoe_damage: int = 0  # Damage to player at phase start (0 = no AoE)
    spawn_minions: tuple[str, ...] = ()  # ICE ids spawned as adds
```

### 2. 헬퍼 함수 (`combat/boss.py`)

```python
def spawn_phase_minions(
    boss: Combatant, phase: PhaseProfile, state: CombatState,
    ice_registry: IceRegistry, program_registry: ProgramRegistry,
    portraits: PortraitManager | None = None,
) -> list[Combatant]:
    """Phase B-3: spawn minion ICE at phase transition."""
    # Iterates phase.spawn_minions, builds each via build_ice_enemy(),
    # appends to state.enemies tuple.
    # Returns list of spawned Combatants for caller cleanup.

def apply_phase_aoe(phase: PhaseProfile, state: CombatState) -> int:
    """Phase B-3: apply AoE damage from boss phase transition."""
    # If phase.aoe_damage > 0: state.player.hp -= phase.aoe_damage,
    # push log message. Returns damage dealt.
```

### 3. 사용처 (combat_view 또는 app.py main loop)

```python
# Phase transition detected in maybe_boss_phase_transition()
phase = _boss.current_phase(state.combat_state.enemy, state.combat_state.boss_profile)
if phase is not None:
    _boss.apply_phase_to_combatant(state.combat_state.enemy, state.combat_state.boss_profile)
    _boss.spawn_phase_minions(...)  # spawn adds
    _boss.apply_phase_aoe(phase, state.combat_state)  # AoE damage
```

### 4. 보스 프로필 사용 예시 (combat/boss.py)

WINTERMUTE_PROFILE phase 2/3 에 적용:
- Phase 2: `spawn_minions=("wintermute_proxy", "wintermute_proxy")` — watcher 2개 소환
- Phase 3: `spawn_minions=("wintermute_fragment",)` + `aoe_damage=15` — 분열 + AoE 폭발

TA_CONSTRUCT_PRIME_PROFILE phase 2/3 에 적용:
- Phase 2: `spawn_minions=("romantics_ice",)`
- Phase 3: `spawn_minions=("romantics_ice_elite", "tessier_construct")` + `aoe_damage=20`

## 결과 (Consequences)

### 긍정

1. **전투 다양성**: 보스 phase 가 더 이상 단순 stat-up 이 아니라 전술적 전환점이 됨
2. **위험-보상 균형**: phase 3 AoE burst 는 "damage race" 메커닉 촉발
3. **점진적 난이도**: phase 2 미니언 → phase 3 AoE 의 상승 곡선
4. **재사용성**: AoE / minion 스폰은 향후 모든 BossPhase 에 적용 가능 (default 비활성)

### 부정

1. **미니언 balancing**: 미니언이 너무 강하면 보스가 일찍 phase 3 에 도달 못함
2. **Visual effect 부족**: 텍스트 로그만 출력, particle/screen flash 미연동 (Phase B-3.5 후속)
3. **테스트 부족**: spawn_minions/aoe_damage 통합 테스트 1건 (수동 검증)

### 후속 작업

- **M2 (이후)**: AoE visual effect 추가 (screen flash + screen shake)
- **M3**: 미니언 동적 강도 스케일링 (boss.hp 비율에 따라 spawn 수 변화)
- **M4**: 보스 AI 선택 (어떤 phase 에서 spawn/aoe 발동할지 의사결정)

## 영향 받는 항목

- `combat/bosses.py` (+4 lines, BossPhase 필드)
- `combat/boss.py` (+46 lines, helpers + WINTERMUTE / TA_PRIME 프로필 갱신)
- `combat/state.py` (step_combat — _apply_enemy_skill 이미 추가됨 Phase A)
- `engine/combat_tick.py` (Phase transition hook 가능)

## 테스트

- `tests/unit/test_combat_bosses.py`: 88 passed (no regression)
- 신규 통합 테스트 작성 권장:
  - `test_spawn_phase_minions_adds_to_state_enemies`
  - `test_apply_phase_aoe_deals_damage_to_player`
  - `test_wintermute_phase_2_summons_watchers`

## 변경 이력

- 2026-07-26: Draft (Phase B-3 작업 중)
- 2026-07-26: Accepted (Option 4 — 사용자 위임 직접 판단)
- 2026-07-26: WINTERMUTE + TA_PRIME 프로필에 첫 적용

## 관련 결정

- ADR-0050 (Boss ICE Multi-Phase) — 기반 시스템
- ADR-0018 (Combat Animation) — visual effect 확장 후속
- ADR-0112 (effects.py 1246 LOC) — visual effect 모듈
- ADR-0120 (M2 docstring batch) — 신규 helpers 의 docstring 요구