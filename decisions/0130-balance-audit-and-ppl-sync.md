# ADR-0130: Balance Audit + PPL/보상 동기화 (Phase 1 정리)

**상태**: Accepted (Option 1)
**날짜**: 2026-07-27
**결정자**: 사용자
**우선순위**: P1
**연관**: Balance Audit 2026-07-27, ADR-0008 (Progression), ADR-0012 (PPL/ZDR), ADR-0014 (Data Salvage), F1-1 rebalance (2026-07-22)

---

## 컨텍스트 (Context)

`docs/audits/2026-07-27_balance.md` 의 게임성 점검 결과, **3가지 critical drift** 발견:

1. **PPL 곡선 표 drift** — 3개 문서가 모두 다른 Grade 5 PPL 값을 표기
   - `matrix/ppl.py` (코드): **65**
   - `design/balance/ppl_zdr_balance.md`: **75** (F1-1 미반영)
   - `design/systems/grade-progression.md`: **60** (코드와 5 차이)
2. **미션 보상 필드 drift** — `reward_credits` (top) vs `rewards.credits` (nested) 가 5.7~11x 차이
3. **Arc 1 보상 미달** — first_jack, ice_run 등 75 credit (공식 800의 9%)

추가로 P2/P3 등급 이슈:
- Grade 5→6 성장 1.20x (다른 등급은 1.5~2.0x) — master tier 정체
- 14 missions with `grade_max=6` 중 9개가 진짜 Arc 5 finale인지 불명
- Status threshold 0.499 vs 0.500 비선형 (실제 영향 제한적)

**Pillar 정합 검토**:
- Pillar 1 (The Run): PPL/ZDR 표시 정합성 깨짐 → 신뢰도 저하
- Pillar 4 (The Build): 성장 곡선 정체로 *성장감* 약화
- Pillar 5 (The Style): 깁슨 톤 "빡빡한 런" 유지하려면 보상 곡선 정직 필요

---

## 고려한 옵션

### Option 1: 동기화만 (Sync Only)

- **설명**: PPL 공식/곡선 표 3개 동기화, 보상 필드 단일화, Arc 1 보상 표기 정정. 게임플레이 변경 없음.
- **장점**:
  - 변경 범위 최소 (문서 + JSON 데이터)
  - 기존 회귀 테스트 100% 유지
  - SESSION_SUMMARY §10 "다음 세션: v1.0.0 final" 와 정합 (출시 전 정리)
- **단점**:
  - Grade 6 master 정체성 미해결 (Pillar 4 약화 잔존)
  - 보상 곡선 "공식 vs 실제" 괴리 해소 안 됨
- **세부 작업**:
  1. `ppl_zdr_balance.md`: Grade 5 PPL 75→65, Grade 6 PPL 120+→78 (또는 공식화)
  2. `grade-progression.md`: Grade 5 PPL 60→65
  3. `combat_grades.py` comment §451 "PPL climbs 6 → 63" → 8→65 갱신
  4. `rewards.credits` 권위화 (코드 확인 후) → `reward_credits` (top) 필드 deprecated 또는 alias
  5. `bigend_laney_lunch`, `coolhunter_laney_tokyo` 보상 미설정 → 0 또는 placeholder 제거
  6. Arc 1 미션 보상 재검토: `first_jack`, `ice_run`, `tutorial_maze` 등 75→500
- **Pillar 정합**:
  - P1 (The Run): PPL 표시 일관성 회복 ✓
  - P2 (The Matrix): 영향 없음
  - P3 (The Flatline): 영향 없음
  - P4 (The Build): 곡선 표 sync ✓, 정체성은 별도
  - P5 (The Style): 보상 곡선 정직 ✓ (Arc 1 깁슨 톤 "빡빡함" 유지)

### Option 2: 동기화 + Grade 6 강화

- **설명**: Option 1 + Grade 6 PPL 공식 강화 (예: T6 deck 6×3 → 7×3, construct 1×→2×)
- **장점**:
  - Master tier *특별함* 회복 (Pillar 4 정합)
  - Arc 5 finale 의 미션 의도 ("Neuromancer merger") 와 정합
- **단점**:
  - 신규 테스트 필요 (PPL 계산 회귀)
  - Grade 5→6 성장 1.20x → 1.50~2.0x (다시 가속)
  - 향후 Grade 7+ 추가 시 또 조정 필요
  - F1-1 rebalance 의도와 충돌 (master 강해짐)
- **세부 작업**:
  - Option 1 전부 +
  - `matrix/ppl.py`: T6 deck 가중치 +0.5 또는 construct_multiplier = 2.0 (parameter화)
  - `equipment/equipment.py`: Grade 6 master loadout 보강 (T6 program 5종 추가?)
  - 신규 테스트 `test_grade_6_master_outperforms_grade_5`
- **Pillar 정합**:
  - P1: PPL 표시 일관성 회복 ✓
  - P4: *성장감* 회복 ✓ (master가 진짜 master)
  - P5: Arc 5 finale 미션의 "Neuromancer merger" 위협감 회복 ✓
  - Pillar 충돌: F1-1 rebalance 의도(5-up 압축)와 부분 충돌 → ADR-0008 재검토 필요

### Option 3: 동기화 + Grade 6 강화 + 보상 곡선 재설계

- **설명**: Option 2 + 미션 보상 공식 `credits = arc*800 + (grade-1)*300` 재검증 (공식 vs 실제 비율 7~16% → 60~80%로 조정)
- **장점**:
  - 보상 곡선 정직 (깁슨 톤 유지하면서 인센티브 확보)
  - 메타 진행 (unlock) 과 런 보상의 *균형*
- **단점**:
  - 광범위한 JSON 데이터 수정 (111 missions)
  - 보상 곡선 변경 → 인플레이션/디플레 영향 분석 필요
  - "빡빡함" (Pillar 5) 과 "보람" (메타 진행) trade-off
  - 사용자 결정 + 디자인 검토 필요 (단독 결정 어려움)
- **세부 작업**:
  - Option 2 전부 +
  - 보상 공식: `credits = arc*800 + (grade-1)*300` → 재검증 (예: `arc*500 + grade*200`)
  - 111 미션 `rewards.credits` 일괄 재계산 (data-driven)
  - 신규 밸런스 시뮬레이션: Info Market 가격 × 0.7 (Faction rep 할인) 등 후속효과
- **Pillar 정합**:
  - P1: PPL 표시 일관성 회복 ✓
  - P3: *보상* 강화로 사망 후 재시작 동기 약화 가능 ⚠
  - P4: *성장감* 회복 ✓
  - P5: 깁슨 톤 vs 보상 trade-off

### Option 4: Defer (다음 사이클로)

- **설명**: 이번 v0.9.0 사이클에서는 동기화만 하고, Option 2/3는 v1.0.0 이후 별도 사이클
- **장점**: v1.0.0 final 발행 우선 (SESSION_SUMMARY §10)
- **단점**: 게임성 정체성 (Master tier) 미해결 잔존

---

## 추천 (Recommendation)

**Option 1: 동기화만** 권고.

**근거**:
1. v0.9.0 → v1.0.0 final 발행이 즉시 다음 단계 (SESSION_SUMMARY §10 "PyPI v1.0.0 final"). *출시 전 정리*로 적절.
2. 변경 범위 최소 → 회귀 위험 최소.
3. Grade 6 강화는 F1-1 rebalance (2026-07-22) 의도와 충돌. *별도 사이클* (예: v1.1.0 "Post-Release Rebalance") 에서 신중히.
4. 보상 곡선 재설계 (Option 3) 는 디자인 + 경제 시뮬레이션 필요. v1.0.0 출시 후 player feedback 기반 조정 권장.
5. Option 1 적용 후에도 *게임 정체성* (깁슨 톤, Pillar 정합) 은 유지됨.

**잔존 이슈 (별도 사이클로)**:
- Grade 6 master 정체성 (Option 2)
- 보상 곡선 재설계 (Option 3)
- 둘 다 v1.0.0+ 후 ADR-0131+ 로 분리

---

## 사용자 결정 (Decision)

- [x] **Option 1 (동기화만)** — 사용자 선택 (2026-07-27)
- [ ] Option 2 (동기화 + Grade 6 강화)
- [ ] Option 3 (동기화 + Grade 6 강화 + 보상 곡선 재설계)
- [ ] Option 4 (Defer — v0.9.0 출시만 우선)
- [ ] 기타: ___

---

## 영향 받는 항목 (예정)

수락 시 적용 (Option 1):
- `design/balance/ppl_zdr_balance.md`: Grade 5 PPL 75→65, Grade 6 PPL 공식화
- `design/systems/grade-progression.md`: Grade 5 PPL 60→65, Grade 6 표 추가
- `prototype/scripts/combat_grades.py` §451: 코멘트 "8 → 65" 갱신
- `data/missions/missions.json`: 보상 필드 단일화, Arc 1 보상 조정
- `testcases/`: 보상 회귀 테스트 보강
- `log.md`: `[2026-07-27] docs(balance) | PPL 곡선 sync (F1-1 반영)` 기록

---

## 결과 (Consequences)

**Option 1 Accepted** (2026-07-27). 적용된 변경:

### 1. PPL 곡선 표 동기화 (3 문서)
- `design/balance/ppl_zdr_balance.md`:
  - Grade 5 PPL: 75 → **65**
  - Grade 6 PPL: 120+ → **78** (공식 결과 명시)
  - 성장 곡선 표: 5단계 모두 코드 기준 값으로 갱신
  - 보상 곡선 표: `rewards.credits` (nested) 권위 명시
- `design/systems/grade-progression.md`:
  - Grade 5 PPL: 60 → **65**
  - Grade 6 row 추가 (T6 deck/progs/wetware/construct, PPL=78)
  - F1-1 rebalance 주석: "75 → 60" → "75 → 65"
- `prototype/scripts/combat_grades.py` §451: "PPL climbs 6 → 63 (10x)" → "8 → 65 (~8x)"

### 2. 보상 필드 권위 명시
- 권위: `rewards.credits` (nested) — `missions/board.py:246 _parse_rewards(value.get("rewards"))` 가 먼저 시도
- `reward_credits` (top-level) 는 fallback — JSON 정합성 위해 동일 값 권장, 향후 deprecation 검토 (P3)
- 데이터 검증: `first_jack` `rewards.credits`=500 (정상), `reward_credits`(top)=75 (fallback dead) — 런타임 무관

### 3. 잔존 이슈 (별도 ADR)
- Grade 5→6 성장 정체 (1.20x) — Option 2 범위, **ADR-0131+ 에서 분리**
- 보상 곡선 "공식 vs 실제" 55~96% — Option 3 범위, **ADR-0132+ 에서 분리**
- Bridge/Blue Ant era 미션 (bigend_laney_lunch, coolhunter_laney_tokyo) 보상 None 상태 — 코드 fallback 0 으로 동작, 콘텐츠 미완 표시 (P3)

### 4. 회귀 위험 평가
- 문서 + 코멘트만 변경 → 회귀 위험 0
- 게임플레이 변경 없음 → 기존 테스트 100% 유지
- 다음 사이클 (v1.0.0 final) 발행 시 동기화된 문서가 *single source of truth*

---

## 관련 결정

- ADR-0008 (Progression System) — Item Tier, Jockey Grade
- ADR-0012 (Difficulty Rating) — PPL/ZDR
- ADR-0014 (Data Salvage) — HEAL 보상
- ADR-0111/0112/0113 (모듈 사이즈)
- F1-1 rebalance (2026-07-22, grade-progression.md §28) — construct multiplier 3×→1×

---

## 변경 이력

- 2026-07-27: Draft 작성 (Phase 1 of 게임성 점검)
- 2026-07-27: **Accepted (Option 1)** — 사용자 선택. 문서 sync 적용, ADR-0131+/0132+ 로 잔존 이슈 분리