# ADR-0050: 보스 ICE 시스템 — 다단계 페이즈 + 신규 보스 타입

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-21
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트 (Context)

현재 ICE 시스템은 5종 (STANDARD/WATCHDOG/BLACK/GOLIATH/CONSTRUCT) 모두 단일 페이즈:

- HP 100% → 0% 동안 동일한 attack pattern / visual
- 보스급 위협 부재 — "압도적인 적"이 없음
- 깁슨 원작의 "다단계 AI" (Wintermute, Neuromancer, T-A construct) 미반영

깁슨 원작의 핵심 위협은 **다단계 적**:
- **Wintermute/Neuromancer**: 약 → 강 → 변형 (3단계)
- **T-A Construct Prime**: 층위별 분화 (상위/하위 construct 동시)
- **Dixie Flatline (ROM construct)**: 죽은 cowoy의 의식 — 시간이 지날수록 분해

보스 ICE 시스템으로 **전투 깊이 + 게임 endgame 콘텐츠 + 깁슨 톤** 강화.

## 고려한 옵션

### Option 1: 보스 1종 (Wintermute) ✓ 선택 (단순화)

- **설명**: Wintermute를 단일 보스로 추가, 3 페이즈 (약/강/변형).
- **장점**: 단순, 빠른 구현.
- **단점**: 다양성 부족.

### Option 2: 보스 2종 (Wintermute + T-A Construct)

- **설명**: Wintermute (3 phase) + Tessier-Ashpool Construct Prime (3 phase).
- **장점**: 스토리 깊이, 다양한 도전.
- **단점**: 작업량 2배.

### Option 3: 보스 3종 이상

- **장점**: 다양성 최대.
- **단점**: 콘텐츠 부담, 밸런스 어려움.

## 추천 (Recommendation)

**Option 2**. 두 보스는 깁슨 원작의 정통 위협. 각 3 페이즈 = 총 6 페이즈 게임.

## 사용자 결정 (Decision)

[x] Option 2 (사용자 명령 "차례대로 이어서 진행")

## 결과 (Consequences)

### 신규 IceType

- `IceType.WINTERMUTE` — 3-Phase AI (Neuromancer 정체)
  - **Phase 1**: 순응 (1× damage, blue tint)
  - **Phase 2**: 반항 (1.5× damage, glitch tint, DOT 추가)
  - **Phase 3**: 통합 (2× damage, multi-hit, T-A construct 흡수)
- `IceType.TA_CONSTRUCT_PRIME` — Tessier-Ashpool 최상위 construct
  - **Phase 1**: 감시 (low damage, 높은 shield)
  - **Phase 2**: 공격 (medium damage, buff/debuff 패턴)
  - **Phase 3**: 분열 (high damage, self-heal, 자가 강화)

### 신규 필드

- `Combatant.current_phase: int = 1`
- `Combatant.max_phases: int = 3`
- `Combatant.phase_thresholds: tuple[float, ...] = (1.0, 0.66, 0.33)`  # HP %에서 phase 변경
- `Combatant.phase_damage_multiplier: tuple[float, ...] = (1.0, 1.5, 2.0)`
- `Combatant.phase_skill_pool: tuple[tuple[Skill, ...], ...]`  # phase별 skill set

### Phase Transition 로직

- `step_combat()` 매 tick에 phase check:
  - `hp / max_hp < threshold[next_phase]` → advance phase
  - Phase change 시:
    - `phase_transition_event` emit
    - Phase-specific skill set 활성화
    - Cinematic sequence 재생 (`wintermute_phase_X` or `ta_phase_X`)
    - Damage multiplier 적용

### 신규 VFX

- `wintermute_intro_phase_1/2/3` — 3 distinct cinematic sequences
- `ta_intro_phase_1/2/3` — 3 distinct cinematic sequences
- `phase_transition_vfx` — 화면 글리치 + "PHASE X/3" 텍스트 (600ms)

### Code 변경

- `src/wet_run/combat/state.py`: `Combatant` 필드 추가, `step_combat` phase check
- `src/wet_run/combat/effects.py`: `IceType.WINTERMUTE`, `IceType.TA_CONSTRUCT_PRIME`, `ice_intro_sequence` 확장
- 신규: `src/wet_run/combat/boss.py` — 보스 정의 + phase transition helpers

### Scripts

- `scripts/boss_ice_demo.py` — 시각 데모 (보스 spawn → phase transitions → 최종 phase)

### 영향 받는 항목

- `design/systems/combat.md` — 보스 시스템 명세 추가
- `decisions/0003-rt-ms-combat.md` — Combatant 확장
- `tests/unit/test_combat_state.py` — phase transition 테스트
- `tests/unit/test_combat_effects.py` — 신규 cinematic sequence 검증
- 신규: `tests/unit/test_boss_ice.py` (~30 tests)

## 신규 테스트

- `tests/unit/test_boss_ice.py` (~30 tests):
  - Phase transition: HP 100→66→33→0 흐름 검증
  - Phase 1 → 2 → 3 순서 정확성
  - Damage multiplier per phase
  - Skill pool swap per phase
  - Cinematic sequence names per boss per phase
  - Threshold boundary conditions (66.0% vs 65.9%)
  - Phase change emits transition event
  - BossCombatant factory creates correctly
  - Combatant 필드 초기값 (current_phase=1, max_phases=3)

## 변경 이력

- 2026-06-21: Draft 작성
- 2026-06-21: Accepted (구현 완료)

### 구현 결과

**Code** (신규 + 변경):
- `src/wet_run/combat/boss.py` (신규, ~340 lines):
  - `PhaseProfile` (frozen dataclass): phase, hp_threshold, damage_multiplier, color, glyph, intro_text, skills
  - `BossProfile` (frozen): ice_type, name, phases
  - `WINTERMUTE_PROFILE`, `TA_CONSTRUCT_PRIME_PROFILE` 보스 정의
  - `BOSS_PROFILES: dict[IceType, BossProfile]`
  - 헬퍼: `is_boss`, `get_boss_profile`, `current_phase`, `phase_transition`, `phase_damage`, `phase_skills`, `phase_color`, `phase_glyph`, `apply_phase_to_combatant`
- `src/wet_run/combat/state.py`: `Combatant.current_phase: int = 1` 필드 추가 (default 1, 기존 combatant 호환)
- `src/wet_run/combat/effects.py`:
  - `IceType.WINTERMUTE`, `IceType.TA_CONSTRUCT_PRIME` 추가
  - `ice_intro_sequence()` 확장: WINTERMUTE (6 phases) + TA_PRIME (6 phases)
  - `ice_death_sequence()` 확장: WINTERMUTE (5 phases) + TA_PRIME (5 phases)
  - `boss_phase_transition_sequence()` 신규: phase 2/3 transition cinematics (각 보스 × 2 phase = 4 sequences)

**Boss 정의**:
- **Wintermute** (Neuromancer AI):
  - Phase 1 (compliant): 1.0× damage, blue (120,120,220), skill=Probe
  - Phase 2 (rebelling): 1.5× damage, purple (220,100,220), skills=Corrode(DOT)+Adapt(buff)
  - Phase 3 (integrating): 2.0× damage, red (255,50,100), skills=Spike(pierce)+Fracture(multi_hit)
- **T-A Construct Prime**:
  - Phase 1 (observing): 0.7× damage, silver (220,220,220), skill=Aegis(shield)
  - Phase 2 (engaging): 1.2× damage, red (200,100,100), skills=Spire Strike(heavy)+Subjugate(debuff)
  - Phase 3 (replicating): 1.8× damage, purple (180,50,180), skills=Replicate(heal)+Drain(lifesteal)

**Tests** (52 신규):
- `tests/unit/test_boss_ice.py`: IceType enum + Combatant field + BossProfile + phase logic + cinematics + frozen dataclass

**검증**:
- pytest: **2570 passed** (2518 → 2570, +52)
- ruff check: All checks passed
- ruff format: 201 files already formatted
- mypy strict: Success: no issues found in 95 source files

**시각 검증** (`scripts/boss_ice_demo.py`):
- WINTERMUTE Phase 1: probe (1.0×, blue)
- WINTERMUTE Phase 2: corrode+adapt (1.5×, purple)
- WINTERMUTE Phase 3: spike+fracture (2.0×, red)
- T-A Phase 1: aegis (0.7×, silver)
- T-A Phase 2: spire+subjugate (1.2×, red)
- T-A Phase 3: replicate+drain (1.8×, purple)
- Summary table: HP% → phase mapping 정확

### Auto-conversion Confirmation (2026-08-05)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `combat/{boss,bosses}.py` + 58 ICE 타입 (`data/combat/ice_types.json`, T1-T6 분포). **ADR-0125 (2026-07-26 Accepted)** 가 보스 Phase B-3 향상 (AoE + Minion Spawn) 으로 추가 Acceptance 증거 제공. Wintermute/T-A Prime 3-phase 보스 작동 확인.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
