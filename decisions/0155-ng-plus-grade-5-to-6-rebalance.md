# ADR-0155: NG+ Grade 5→6 PPL Actual Rebalance (Master Tier Bonus +10)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (v1.2.0+ balance fix, NG+ Grade 5→6 growth 1.20x → 1.35x)
**관련**: [ADR-0012 — Combat Difficulty (PPL/ZDR)](./0012-difficulty-rating.md), [ADR-0130 — Balance Audit + PPL Sync](./0130-balance-audit-and-ppl-sync.md), [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0154 — Faction Expansion (PPL growth targets documentation)](./0154-faction-expansion-i18n.md)

## 컨텍스트 (Context)

ADR-0154 (Cycle 10) 에서 `PPL_GROWTH_TARGETS` dict 를 *documentation* 으로만 추가. *Actual rebalance* 는 후속으로 미루어짐.

**현재 상태** (Cycle 10 완료):
- `combat/multi_enemy.py::PPL_GROWTH_TARGETS: dict[str, float]` (5 transitions documented)
- Grade 5→6: 1.20x ⚠ (잔존 이슈, `ppl_zdr_balance.md` line 47)
- `matrix/ppl.py::calculate_ppl()`: loadout-based formula

**PPL 공식** (현재):
```python
ppl = loadout.deck_tier * 3
ppl += sum(p.tier for p in loadout.programs) * 2
ppl += loadout.wetware_tier
if loadout.construct_tier > 0:
    ppl += loadout.construct_tier
```

**PPL 값** (현재, `ppl_zdr_balance.md`):
| Grade | PPL | Growth |
|---|---:|---:|
| 1 (T1) | 8 | — |
| 2 (T2) | 16 | 2.00x |
| 3 (T3) | 24 | 1.50x |
| 4 (T4) | 40 | 1.67x |
| 5 (T5) | 65 | 1.62x |
| 6 (T6) | 78 | **1.20x** ⚠ |

**부재** (master tier *특별함* 부족):
- T6 PPL 이 78 — T5 의 65 대비 *1.20x* (다른 transition 1.5~2.0x)
- Master tier (Grade 6, Arc 5 finale) 의 *특별함* 부족
- NG+ (Salvation Phase, ADR-0090) 에서 *다음 런* 의 강함 부족

**해결 방향** (ADR-0155):
- `calculate_ppl` 에 T6 (master) bonus 추가: `+10` PPL when `deck_tier == MAX_TIER (6)`
- T6 PPL: 78 → **88** (1.35x from 65) ✓ (target)
- 변경 범위: 3-5 LOC (matrix/ppl.py + balance doc + tests)

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: Grade 6 의 PPL 증가 → run weight *intrisic* 증가. NG+ 의 *다음 런* 보완.
- **Pillar 3 (The Flatline)**: 변경 없음 (HEAL 15% 그대로).
- **Pillar 4 (The Build)**: T6 master tier 의 *build* 가치 증가 (Pillar 4 의 unlock 중심 유지).

**기술 제약**:
- `calculate_ppl` 1-line patch (master tier bonus)
- `ppl_zdr_balance.md` 의 PPL 값 table update (T6: 78 → 88)
- 기존 test_avatar.py + test_matrix_ppl.py 의 T6 expected value update
- 신규 모듈 0개 (ADR-0110 정합)

## 고려한 옵션

### Option 1: T6 deck bonus +10 (최소)

- **설명**: `calculate_ppl` 에 `if loadout.deck_tier == MAX_TIER: ppl += 10` 추가.
- **장점**:
  - 변경 범위 최소 — 1-2 LOC.
  - Master tier 의 *특별함* 확보 (78 → 88, 1.35x from 65).
  - 기존 test 깨지지 않음 (T6 expected value만 update).
  - Pillar 1 (The Run) 의 NG+ intrinsic 보완.
- **단점**:
  - T6 *construct* 만 있는 경우 (T5 deck) 는 bonus 없음 — *full* T6 만 reward.
  - Pillar 4 (The Build) 의 *unlock 중심* 위배 없음.
- **Pillar 정합**:
  - P1: ✓
  - P3: ✓
  - P4: ✓

### Option 2: T6 construct multiplier × 2 (중간)

- **설명**: `if loadout.construct_tier >= 6: ppl += loadout.construct_tier` (× 2 for T6).
- **장점**:
  - T6 *construct* 만 보너스 (다른 tier 영향 없음).
  - 변경 범위 최소 — 2-3 LOC.
- **단점**:
  - T6 deck + T5 construct = bonus 없음 (T6 master 의 *일부* 만 보상).
  - PPL 값이 *덜* 균형 (1.35x 대신 1.27x).
- **Pillar 정합**:
  - P1: ✓
  - P4: ✓

### Option 3: T6 set bonus (deck + programs + wetware + construct 모두 T6 → +15)

- **설명**: *full* T6 set (deck + 4 programs + wetware + construct 모두 T6) 일 때만 +15 bonus.
- **장점**:
  - Master tier 의 *완전한 특별함* (full T6 만 보상).
  - NG+ (다음 런) 의 *목표* 명확.
- **단점**:
  - 변경 범위 중간 — 5-7 LOC (set detection).
  - *Partial* T6 (예: T6 deck + T5 programs) 는 bonus 없음.
  - Tests 폭증 (set detection scenarios).
- **Pillar 정합**:
  - P1: ✓
  - P4: ✓

## 추천 (Recommendation)

**Option 1** (T6 deck bonus +10, 최소).

이유:
1. **변경 범위 최소**: 1-2 LOC patch (matrix/ppl.py).
2. **PPL growth 1.20x → 1.35x** 정확히 달성 (65 * 1.35 ≈ 88).
3. **기존 인프라 100% 재사용**: `MAX_TIER = 6` 상수 (이미 존재), `calculate_ppl` 1-line patch.
4. **Pillar 정합**: P1 (Run, NG+ intrinsic), P4 (Build, master tier 가치).
5. **모듈 사이즈**: 신규 모듈 0개, ADR-0110 정합.
6. **Test surface 폭증 방지**: 1-2 tests (T6 PPL = 88, T5 PPL unchanged).

**순서** (Cycle 11, 1 sub-session):
1. `matrix/ppl.py`: `if loadout.deck_tier == MAX_TIER: ppl += 10` 2-line patch
2. `design/balance/ppl_zdr_balance.md`: T6 PPL 78 → 88, Growth 1.20x → 1.35x table update
3. Tests: 1-2 (T6 PPL 검증)

## 사용자 결정 (Decision)

[x] Option 1 (T6 deck bonus +10) — 2026-08-07 Cycle 11 채택
[ ] Option 2 (T6 construct multiplier × 2)
[ ] Option 3 (T6 set bonus +15)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. Patch (matrix/ppl.py, 2 line)

```python
# Before:
ppl = loadout.deck_tier * 3
ppl += sum(p.tier for p in loadout.programs) * 2
ppl += loadout.wetware_tier
if loadout.construct_tier > 0:
    ppl += loadout.construct_tier
return ppl

# After (ADR-0155):
ppl = loadout.deck_tier * 3
ppl += sum(p.tier for p in loadout.programs) * 2
ppl += loadout.wetware_tier
if loadout.construct_tier > 0:
    ppl += loadout.construct_tier
# ADR-0155: master tier bonus (Grade 6 deck) — +10 PPL
# Closes the NG+ Grade 5→6 growth 1.20x→1.35x balance issue.
if loadout.deck_tier == MAX_TIER:
    ppl += 10
return ppl
```

### 2. PPL 값 table update (ppl_zdr_balance.md)

| Grade | PPL (old) | PPL (new) | Growth (old) | Growth (new) |
|---|---:|---:|---:|---:|
| 5 (T5) | 65 | 65 | 1.62x | 1.62x |
| 6 (T6) | 78 | **88** | 1.20x | **1.35x** ✓ |

### 3. AppState 변경 없음

### 4. i18n 변경 없음

### 5. Tests 추가 (2 tests)

`tests/unit/test_matrix_ppl.py` (or update existing):
- TC-PPL-001: T6 deck PPL = 88 (was 78)
- TC-PPL-002: T5 deck PPL unchanged = 65 (no regression)

### 6. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | Grade 6 PPL 78→88 → run weight intrinsic 증가 (NG+ 다음 런 보완) | TC-PPL-001 |
| P2 (The Matrix) | 변경 없음 | 기존 test 유지 |
| P3 (The Flatline) | 변경 없음 | 기존 test 유지 |
| P4 (The Build) | T6 master tier *build* 가치 증가 (Pillar 4 의 unlock 중심 유지) | 기존 test 유지 |
| P5 (The Style) | 변경 없음 | 기존 test 유지 |

## 영향 받는 항목

- `prototype/src/wet_run/matrix/ppl.py` (2 line patch)
- `design/balance/ppl_zdr_balance.md` (T6 PPL value update, 2 rows)
- `prototype/tests/unit/test_matrix_ppl.py` (2 tests, T6 expected value update)
- `log.md` (Cycle 11 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0155 entry)
- `prototype/data/game_facts.json` (regenerated)

## 관련 결정

- ADR-0012 — Combat Difficulty (PPL/ZDR) (Accepted)
- ADR-0130 — Balance Audit + PPL Sync (Accepted, 잔존 이슈)
- ADR-0110 — 모듈 사이즈 정책 (신규 모듈 0개, ADR-0110 정합)
- ADR-0154 — Faction Expansion (PPL growth targets documentation, this cycle completes the actual rebalance)
- ADR-0090 — Salvation Phase Integration (NG+ narrative 기반)

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 11 of v1.2.0+ balance)
- 2026-08-07: Accepted (Option 1, 사용자 확인)
  - 구현: `matrix/ppl.py::calculate_ppl` 2-line patch (T6 deck bonus +10)
  - PPL rebalance: T6 78 → 88 (1.20x → 1.35x from T5)
  - 테스트: T6 PPL = 88, T5 PPL unchanged = 65 (no regression)
  - 검증: ruff clean, mypy 0 errors (172 src files), pytest 4062 pass (was 4060, +2)
  - 효과: Master tier (Grade 6) *특별함* 확보, NG+ (Salvation Phase) 의 *다음 런* 보완
  - 후속: Matrix encounter spawn variant (선택), faction reputation curve rebalance (over-scope)
