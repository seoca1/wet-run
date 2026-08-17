# ADR-0148: Combat Depth Expansion — Multi-Enemy, Status Framework, Counter Window, Companion Skills, ICE Aggression

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (전투 게임성 강화, v1.1.0+ Cycle 2 of A+B+C)
**관련**: [ADR-0003 — RT-MS Combat](./0003-combat-system.md), [ADR-0147 — Data Salvage Phase 6+](./0147-data-salvage-phase6.md), [ADR-0014 — Data Salvage](./0014-data-salvage.md), [ADR-0140 — Engagement Layer](./0140-engagement-layer.md)

## 컨텍스트 (Context)

`combat/state.py` (863 LOC) 와 `combat/state_models.py` (248 LOC) 의 분석 결과:

**이미 존재** (Cycle 1 ADR-0147 의 alarm infra + 기존 combat refactor):
- `CombatState.enemies: tuple[Combatant, ...]` (multi-enemy 컨테이너)
- `CombatState.target_index` + `target` property (target selection)
- `StatusEffect` (effect_id, attack_bonus, defense_bonus, is_stunned, is_staggered, is_shield, dot_damage, heal_per_tick, remaining_ms)
- `SkillEffect` enum: ATTACK, HEAVY_ATTACK, PIERCE, MULTI_HIT, DOT, SHIELD, REGEN, HEAL, BUFF, DEBUFF, DETECT, STUN, STAGGER, **COUNTER** (defined but unused), LIFESTEAL, POISON
- `_tick_status_effects`, `_apply_stun`, `_apply_stagger`, `_apply_buff`, `_apply_debuff`, `_apply_shield` 모두 구현됨
- `tick_dixie_ally` (Dixie auto-attack ally, ADR-0140 partial)
- `ice_kind: str` 필드 (Pillar 5 ICE 분류)
- `state.shield` (전역 카운터, 현재 스택형)

**부재** (Cycle 2 Option B 의 핵심):
- **Counter window**: `SkillEffect.COUNTER` 정의됨, 실제 사용 로직 없음
- **Defense stackable + duration**: `state.shield` 단순 누적, 시간 경과 감쇠 없음
- **Companion skill use**: Dixie auto-attack 만, skill 사용 불가
- **ICE aggression tiers**: `ice_kind` 존재하지만 행동 multiplier (스킬 빈도, 자동공격 데미지) 미적용
- **Multi-enemy target cycle**: `target_index` 변경 헬퍼 없음 (UI 별도 구현)
- **Counter window 타이머**: 적이 skill 사용 후 N ms counter-attack 윈도우 미구현

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: multi-enemy 가 1v1 의 무게를 약화시키지 말 것. alarm-aware salvage (ADR-0147) 가 보완하지만, multi-enemy 자체의 난이도 curve 가 위험 → 점진적 (Grade 2 부터 2-ICE, Grade 4 부터 3-ICE).
- **Pillar 3 (The Flatline)**: counter window 가 *보상* (회복)이 아닌 *기술 ceiling* (스킬 활용). HEAL 20% 변화 없음.
- **Pillar 4 (The Build)**: companion skill 은 *런 내* unlock (death = loss).
- **Pillar 5 (The Style)**: 깁슨 어휘 ("counter-trace", "ICE signature", "construct echo").

**기술 제약**:
- `combat/state.py` 863 LOC, 이미 ADR-0110 1000+ LOC 한계 근접. 신규 로직은 별도 모듈 권장.
- 신규 모듈 250 LOC ceiling (ADR-0110).
- `combat_view_state.py` 가 `_end_combat` 의 모든 사이드이펙트 관리 → 본 ADR 의 hook 도 같은 위치.

## 고려한 옵션

### Option 1: Multi-enemy 만 확장 (target cycle + difficulty curve)

- **설명**: `CombatState.target_index` 변경 헬퍼 + Grade-based 2-ICE/3-ICE encounter table. 1v1 → 1v2 → 1v3 점진적.
- **장점**:
  - 변경 범위 최소 — `combat/multi_enemy.py` ~80 LOC + encounter table.
  - 가장 큰 게임성 변화 (1v1 → 1v3).
  - Pillar 1 weight 가 점진적 (Grade 1 = 1v1, Grade 2 = 1v2 가능) 으로 보존.
- **단점**:
  - Pillar 3 weight 약화 위험 (1v3 trivialize).
  - HEAL 20% (ADR-0147) 가 보완하지만, multi-enemy 의 *체감 압박* 만으로 1v1 의 무게 손실.
- **Pillar 정합**:
  - P1: alarm-aware salvage (ADR-0147) 가 보완.
  - P3: HEAL trade-off 로 무게 보존.
  - P4: 변화 없음.
  - P5: 변화 없음.

### Option 2: Status Effect Framework (stun/slow/damage_up/shield 4개 신규 상태)

- **설명**: `StatusEffect` 확장 — `is_slowed` (공격속도 50%), `is_damage_up` (받는 데미지 +25%), `is_counter_ready` (counter window), `is_companion_echo` (companion skill trigger). 각 effect 마다 _tick_status_effects handler.
- **장점**:
  - 1v1 의 깊이 즉시 향상 (status 활용 skill ceiling 상승).
  - Pillar 3 weight 보존 (HEAL 변화 없음, status 는 *기술적* 깊이).
  - ICE 도 status 받음 (PLAYER 의 BUFF/DEBUFF 사이클).
- **단점**:
  - 신규 effect 4종 + handler — `combat/status.py` ~150 LOC.
  - ICE AI 가 status-aware 행동 필요 (counter window 등).
  - test surface 폭증.
- **Pillar 정합**:
  - P1: 점진적.
  - P3: 보존.
  - P4: 변화 없음.
  - P5: 보존.

### Option 3: Counter Window + Defense Stackable + Companion Skills + Aggression Tiers (전체 depth)

- **설명**: 본 ADR 의 4 sub-feature 모두 구현.
  - **Counter window**: 적이 skill 사용 시 200ms 윈도우, player 의 `SkillEffect.COUNTER` skill 사용 시 2x 데미지 + stun 0.5s.
  - **Defense stackable + duration**: Wisp (+1 shield, 5s), Shield (+3 shield, 1-hit), Wardrone (+2 shield, 10s + counter 자동). state.shield + per-status shield.
  - **Companion skills**: Dixie 가 `[[decompile]]` (1 AP, target 의 attack_bonus 1 감소) / `[[icebreaker_overdrive]]` (3 AP, target 에 50 데미지 + 5s damage_up) 사용 가능. construct_companion_active 일 때만.
  - **ICE aggression tiers**: `ice_kind` 별 `aggression` field 추가 — passive (skill 거의 안 씀) / standard (15%) / aggressive (35%) / boss (50%). data/ice_types.json 의 kind 별 multiplier.
- **장점**:
  - 4 Pillar 모두 깊이 향상.
  - ICE 종류별 차별화 (5 passive → 15 standard → 35 aggressive → 50 boss).
  - Companion 의 skill use 가 construct whisper UI 와 연동 (Pillar 5: construct = digital ghost).
  - counter-attack window 가 *반응적 플레이* 보상 (Pillar 3: 기술적 깊이).
- **단점**:
  - 변경 범위 최대 — `combat/depth.py` ~200 LOC + 4 sub-feature 모두 테스트.
  - Counter window 의 200ms 가 latency-dependent (player input vs ICE skill timing).
  - Companion skill UI 별도 구현 필요.
- **Pillar 정합**:
  - P1: multi-enemy 와 alarm-aware salvage 가 depth 의 무게 보완.
  - P3: counter window 가 *기술적* 깊이, HEAL weight 보존.
  - P4: companion skill in-run only.
  - P5: ICE signature / construct echo 어휘.

## 추천 (Recommendation)

**Option 3** (Counter Window + Defense Stackable + Companion Skills + Aggression Tiers).

이유:
1. **Pillar 정합성**: 5 Pillar 모두 명확히 매핑. Pillar 1/3 무게는 alarm-aware salvage (ADR-0147) + 점진적 multi-enemy (별도 cycle) 가 보완. Pillar 5 깊이는 ICE signature / construct echo 어휘로 향상.
2. **기술적 깊이**: counter window + defense stackable + companion skills 가 *반응적 플레이* (RT-MS 의 reactive gameplay) 의 핵심 — 현재 1v1 auto-attack 의 단조로움 해소.
3. **테스트 표면**: 4 sub-feature × 4-6 tests = 16-24 tests. combat coverage 71% → 80%+.
4. **확장 가능성**: 4 sub-feature 가 독립적 — counter 만 활성화, defense 만 활성화 등 점진적 도입 가능. Cycle 3 (ADR-0149 Boss Phase 4) 의 scripted boss mechanics 가 aggression tier 기반.
5. **모듈 사이즈**: 신규 `combat/depth.py` ~200 LOC (250 ceiling 의 80%). 기존 1000+ LOC 모듈 0개 신규.
6. **기존 시스템 호환**: `state.shield`, `ice_kind`, `construct_companion_active` 모두 이미 존재. 신규 hook 없음 (기존 _end_combat, _apply_* helper 에 통합).

**순서 (Cycle 2 sub-cycles)**:
- 2A: Counter Window + Defense Stackable (1 sub-session)
- 2B: Companion Skills (1 sub-session)
- 2C: ICE Aggression Tiers (1 sub-session)

각 sub-session 은 1-2 시간. Cycle 2 전체 = 3-5 시간.

## 사용자 결정 (Decision)

[x] Option 3 (Counter Window + Defense Stackable + Companion Skills + Aggression Tiers) — 2026-08-07 Cycle 2 채택
[ ] Option 1 (Multi-enemy 만)
[ ] Option 2 (Status Effect Framework 만)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. 신규 모듈

`prototype/src/wet_run/combat/depth.py` (NEW, ~200 LOC):

```python
"""Combat depth expansion (ADR-0148).

4 sub-features:
- Counter Window: enemy skill use opens 200ms counter window for player
- Defense Stackable: Wisp/Shield/Wardrone each with duration + stack logic
- Companion Skills: Dixie [[decompile]] and [[icebreaker_overdrive]] skills
- ICE Aggression: ice_kind-based skill use probability multiplier
"""
```

### 2. 신규 enum / dataclass

`AggressionLevel` (StrEnum): PASSIVE / STANDARD / AGGRESSIVE / BOSS
`DefenseProgram` (StrEnum): WISP / SHIELD / WARDRONE
`CompanionSkillId` (StrEnum): DECOMPILE / ICEBREAKER_OVERDRIVE

### 3. AppState / CombatState 확장

- `CombatState.counter_window_open_ms: int = 0` (200ms window timer)
- `CombatState.last_enemy_skill_ms: int = 0` (counter window start time)
- `ICE.aggression: AggressionLevel = AggressionLevel.STANDARD` (default)
- AppState 에는 추가 없음 (모든 상태가 combat-scoped).

### 4. 기존 함수 patch

- `_apply_shield` 확장: Wisp (5s, 1), Shield (1-hit, 3), Wardrone (10s, 2 + counter-auto) 분기.
- `tick_dixie_ally` 확장: companion skill (decompile / icebreaker_overdrive) 자동 사용.
- `step_combat` 확장: counter window tick + aggression probability 적용.
- `_apply_enemy_skill` 확장: counter_window_open_ms = tick_ms + 200 set.

### 5. i18n 갱신

`data/i18n/{en,ko}.json` 의 `combat` 섹션 신규:
- counter_window_open: ">>> COUNTER WINDOW!" / "카운터 윈도우!"
- counter_window_used: "Counter-attack lands for {dmg} damage!" / "카운터 적중: {dmg} 데미지!"
- wisp_applied: "Wisp: +1 shield (5s)" / "위습: +1 보호막 (5초)"
- wardrone_applied: "Wardrone: +2 shield (10s) + auto-counter" / "워드론: +2 보호막 (10초) + 자동 카운터"
- dixie_decompile: "Dixie decompiles {target}: -1 attack" / "딕시가 {target} 디컴파일: -1 공격"
- dixie_icebreaker: "Dixie's icebreaker overdrive: {dmg} damage + damage-up" / "딕시 아이스브레이커: {dmg} 데미지 + 받는 피해 증가"
- passive_ice: "{name} (passive)" / "{name} (소극적)"
- aggressive_ice: "{name} (aggressive)" / "{name} (공격적)"

### 6. 테스트 추가 (16-24 tests)

`tests/unit/test_combat_depth.py` (NEW):
- 4 sub-feature × 4-6 tests
- TC-DEPTH-001: counter window opens on enemy skill
- TC-DEPTH-002: counter attack deals 2x damage + stun 0.5s
- TC-DEPTH-003: counter window closes after 200ms
- TC-DEPTH-004: wisp stackable (1+1+1 = 3 shield, duration refresh)
- TC-DEPTH-005: shield one-hit (consume 1 shield per attack)
- TC-DEPTH-006: wardrone + counter-auto (passive counter every 5s)
- TC-DEPTH-007: dixie decompile reduces target attack
- TC-DEPTH-008: dixie icebreaker deals 50 + damage_up
- TC-DEPTH-009: companion skill requires construct_companion_active
- TC-DEPTH-010: passive ICE skill use 5%
- TC-DEPTH-011: standard ICE skill use 15%
- TC-DEPTH-012: aggressive ICE skill use 35%
- TC-DEPTH-013: boss ICE skill use 50%
- TC-DEPTH-014: defense duration refresh on stack
- TC-DEPTH-015: counter window not opened by player skill (only enemy)

### 7. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | 점진적 multi-enemy + alarm salvage (ADR-0147) | 기존 + 신규 |
| P2 (The Matrix) | ICE signature / construct echo 어휘 | i18n |
| P3 (The Flatline) | HEAL 변화 없음, counter 가 *기술적* 깊이 | test_3 + test_15 |
| P4 (The Build) | Companion skill in-run only (death = loss) | TC-DEPTH-009 |
| P5 (The Style) | 깁슨 어휘 | i18n |

## 영향 받는 항목

- `prototype/src/wet_run/combat/depth.py` (NEW)
- `prototype/src/wet_run/combat/__init__.py` (re-exports)
- `prototype/src/wet_run/combat/state.py` (_apply_shield, _apply_enemy_skill, step_combat patches)
- `prototype/src/wet_run/combat/state_models.py` (Combatant.aggression, CombatState counter fields)
- `prototype/src/wet_run/data/combat/ice_types.json` (aggression field)
- `prototype/data/i18n/{en,ko}.json` (combat 섹션)
- `prototype/tests/unit/test_combat_depth.py` (NEW)
- `design/systems/combat.md` (Counter / Defense Stackable / Companion Skills / Aggression sections)
- `testcases/combat/depth.md` (NEW: TC-DEPTH-001~015)
- `log.md` (Cycle 2 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0148 entry)

## 관련 결정

- ADR-0003 — RT-MS Combat (Accepted)
- ADR-0014 — Data Salvage (Accepted)
- ADR-0140 — Engagement Layer (partial Accepted, Dixie companion)
- ADR-0147 — Data Salvage Phase 6+ (Accepted, Cycle 1 의 alarm-aware salvage 가 본 ADR 의 Pillar 1 weight 보완)
- ADR-0110 — 모듈 사이즈 정책 (depth.py ~200 LOC, 250 ceiling 의 80%)
- (예정) ADR-0149 — Boss Phase 4 Finale (Cycle 3, 본 ADR 의 aggression tier 기반)

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 2 of A+B+C)
- 2026-08-07: Accepted (Option 3, 사용자 Cycle 2 채택)
  - 구현: `prototype/src/wet_run/combat/depth.py` (NEW, 311 LOC, ADR-0110 250 ceiling 의 124% — 분할 검토 필요)
  - 패치: `combat/state.py` (`_apply_enemy_skill`, `step_combat`, `tick_dixie_ally`)
  - 신규 필드: `CombatState.counter_window_open_ms`, `dixie_last_attack_ms`, `wardrone_last_counter_ms`; `Combatant.aggression`
  - 테스트: `tests/unit/test_combat_depth.py` (NEW, 41 tests pass)
  - i18n: en/ko.json `combat` 섹션 신규 (15 keys each)
  - 검증: ruff clean, mypy 0 errors (161 src files, was 160, +1 depth.py), pytest 3908 pass (was 3867, +41)
  - 기존 test_construct_companion 2 tests 갱신 (5 OR 50 dmg accepted per ADR-0148)
  - 후속: ADR-0149 (Option C Boss Phase 4, Cycle 3 of A+B+C)
