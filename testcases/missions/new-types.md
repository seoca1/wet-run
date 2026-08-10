# Phase 11 Mission Tests — New Types + Chains

**상태**: Active (Phase 11 implementation)
**우선순위**: P1
**작성일**: 2026-08-08
**연결 명세**: `design/systems/mission-types.md`, `design/systems/mission-chains.md`, `decisions/0188-mission-expansion.md`

This document covers test scenarios for 5 new mission types + 1 example chain introduced in Phase 11.

---

## TC-MISSION-INVESTIGATION-001: Investigation Mission (TA — Kumiko's Intel)

**상태**: Active
**우선순위**: P1
**연결 명세**: `mission-types.md` §Type 1 (Investigation)

## 목적 (Purpose)

Verify the new Investigation mission type works correctly: multi-stage intel-gathering without combat, evidence collection, and outcome branching.

## 전제 조건 (Preconditions)

- 플레이어가 캐스 자키 (case) 선택
- TA reputation ≥ tier 3 (trustworthy)
- 플레이어 grade 4-5
- 케이스에게 스캔/디크립트 프로그램 (utility 카테고리) 장착

## 단계 (Steps)

1. 미션 보드에서 `ta_investigate_3jane_initiative` 선택
2. 미션 설명 + TNF (Tessier-Ashpool 가족) 대화 출력
3. 플레이어가 매트릭스 진입 (no combat — investigation only)
4. 4개 evidence 노드 (testimony, audit, data_fragment, witness) 순서대로 진입
5. 각 노드에서 스캔 실행 → evidence fragment 수집
6. 4개 모두 수집 → SUCCESS
7. 또는 50% detection → COMBAT_TRIGGER (mission change to infiltrate)

## 예상 결과 (Expected)

- [ ] 4개 evidence 모두 수집 → SUCCESS → CRED 5500 + ta_construct + salvage_fragment × 2
- [ ] Detection ≥ 50% → mission type changes to `infiltrate` (combat enabled)
- [ ] Failed investigation → partial reward (no ta_construct)
- [ ] 모두 0회 → mission failure (no follow-up mission)

## 실패 시 (Failure Protocol)

- Detection 로직이 의도치 않게 트리거됨 → mission-types.md §Type 1 (Investigation) 실패 정의 확인
- Evidence 수집 순서 강제 → random synthesis 검증

---

## TC-MISSION-DEFENSE-002: Defense Mission (TA — Straylight Perimeter)

**상태**: Active
**우선순위**: P1
**연결 명세**: `mission-types.md` §Type 2 (Defense)

## 목적 (Purpose)

Verify the Defense mission type: survive N waves, protect NPC, node HP tracking.

## 전제 조건 (Preconditions)

- 플레이어 grade 5-6 (hard mission)
- 수트 자키 (suit) 또는 케이스 (case)
- Shield/defense programs 장착
- 3제인 픽서 선택

## 단계 (Steps)

1. `ta_defend_straylight_perimeter` 선택
2. 매트릭스 진입 → 6 waves 진행
3. Wave 1: tier 2 ICE × 3
4. Wave 2: tier 3 ICE × 4
5. Wave 3: tier 4 ICE × 5
6. Wave 4: tier 4 ICE × 5 + 보스 wave 예고
7. Wave 5: tier 5 ICE × 6
8. Wave 6: tier 5 ICE × 6 + construct_proxy
9. NPC (쿠미코) 생존 유지
10. 노드 HP ≥ 50% final wave 종료

## 예상 결과 (Expected)

- [ ] 6 waves SURVIVE → CRED 7000 + ta_construct × 2 + shield_program
- [ ] 쿠미코 사망 → DEFEAT (no rewards)
- [ ] 노드 HP < 50% → partial reward (CRED only)
- [ ] Wave 6 construct_proxy 처치 → bonus + reputation

## 실패 시 (Failure Protocol)

- Wave spawn 타이밍 오류 → verify wave_intensity scaling
- NPC 생존 로직 오류 → check NPC hp tracking

---

## TC-MISSION-DUAL-OBJECTIVE-003: Dual-Objective Mission (TA — Ashpool Vote)

**상태**: Active
**우선순위**: P1
**연결 명세**: `mission-types.md` §Type 3 (Dual-Objective)

## 목적 (Purpose)

Verify dual-objective mechanics: both extraction AND defeat must complete within time limit.

## 전제 조건 (Preconditions)

- 플레이어 grade 5-6
- 케이스 자키 (case)
- 2가지 objective 동시 처리 능력 (multi-task)
- Time limit 600초 (10분)

## 단계 (Steps)

1. `ta_dual_objective_ashpool_vote` 선택
2. 동시 objectives: extract `ta_vote_record` AND defeat `ice.boss.construct_proxy`
3. 플레이어가 extraction 시작 (5분)
4. 동시 construct_proxy 등장 (combat 시작)
5. 플레이어가 둘 다 시도
6. 10분 timer 만료
7. 둘 다 완료 → FULL_REWARD
8. 하나만 → PARTIAL
9. 둘 다 미완 → FAIL

## 예상 결과 (Expected)

- [ ] 둘 다 완료 → CRED 9000 + ta_construct × 2 + construct_key
- [ ] Extraction만 → CRED 4500 + 1 reward
- [ ] Defeat만 → CRED 4500 + 1 reward
- [ ] 둘 다 미완 → mission failure
- [ ] 10분 timer 정확히 만료

## 실패 시 (Failure Protocol)

- Time limit이 너무 짧거나 김 → adjust per balance
- one objective completion이 다른 걸 block → verifies objective_lock

---

## TC-MISSION-EXTRACTION-V2-004: High-Risk Extraction (TA — Aleph Chip)

**상태**: Active
**우선순위**: P1
**연결 명세**: `mission-types.md` §Type 4 (Extraction_v2)

## 목적 (Purpose)

Verify high-risk extraction with timer and penalty on failure (construct_loss).

## 전제 조건 (Preconditions)

- 플레이어 grade 6 (최고 난이도)
- 케이스 (case) 또는 Neuromancer 자키
- T3+ programs (high-tier)
- Wintermute 픽서 (paradox: extract from own family)

## 단계 (Steps)

1. `ta_extract_aleph_chip` 선택
2. **120초 (2분) timer** 시작
3. Aleph_chip_fragment 추출 시도
4. 4× evade events (ice.black_construct 등장)
5. 120초 안에 추출 성공 → SUCCESS
6. 시간 초과 → 실패 → construct_loss

## 예상 결과 (Expected)

- [ ] 120초 내 추출 → CRED 15000 + t5_program + aleph_construct
- [ ] 시간 초과 → CRED 0 + aleph_construct 손실 (1개)
- [ ] 3회 evade 실패 → 추가 손실
- [ ] Construct_loss는 recoverable (다음 mission에서 복구 가능)

## 실패 시 (Failure Protocol)

- Timer가 게임 일시정지 시 멈추지 않음 → verify pause behavior
- Construct_loss가 영구적 → verify recoverable flag

---

## TC-MISSION-STEALTH-005: Stealth Mission (TA — Construct Chamber)

**상태**: Active
**우선순위**: P1
**연결 명세**: `mission-types.md` §Type 5 (Stealth)

## 목적 (Purpose)

Verify stealth mission: no combat allowed, detection threshold, alert system.

## 전제 조건 (Preconditions)

- 플레이어 grade 5-6
- 케이스 자키 (case)
- Cloak/decrypt programs 필수
- 0 alert 목표

## 단계 (Steps)

1. `ta_stealth_construct_chamber` 선택
2. Construct chamber core 도달
3. Detection meter (0-100) 추적
4. 0 alert → STEALTH_SUCCESS
5. 1+ alert → MISSION_FAIL (no combat allowed)
6. construct_chamber_key 추출

## 예상 결과 (Expected)

- [ ] 0 alert → CRED 8000 + cloaking_program + construct_key
- [ ] 1+ alert → mission auto-fails (no combat)
- [ ] Detection > 50% then alert → instant fail
- [ ] No combat ever triggers (combat 금지)

## 실패 시 (Failure Protocol)

- Detection meter overflow → verify threshold
- Combat accidentally enabled → STRICT enforcement

---

## TC-MISSION-CHAIN-006: Mission Chain (TA — Succession)

**상태**: Active
**우선순위**: P1
**연결 명세**: `mission-chains.md` (ta_succession chain)

## 목적 (Purpose)

Verify full chain progression: 5 missions in order, midpoint save, chain-wide rewards.

## 전제 조건 (Preconditions)

- 플레이어 grade 4-6
- TA reputation ≥ tier 3
- Arc 3 progress ≥ 50%
- 모든 5개 mission 정의됨

## 단계 (Steps)

1. `ta_succession` chain unlock
2. Mission 1: `ta_investigate_3jane_initiative` (investigation)
3. Mission 2: `ta_defend_straylight_perimeter` (defense) — **midpoint save**
4. Mission 3: `ta_dual_objective_ashpool_vote` (dual-objective)
5. Mission 4: `ta_extract_aleph_chip` (extraction_v2)
6. Mission 5: `ta_stealth_construct_chamber` (stealth)
7. All complete → chain_reward

## 예상 결과 (Expected)

- [ ] 5 missions 순차 unlock
- [ ] Mission 2 이후 save point (midpoint)
- [ ] Mission 4 실패 → Mission 3부터 retry 가능 (with midpoint save)
- [ ] Mission 5 실패 → chain fail (no retry)
- [ ] Full chain complete → ta_construct_full + reputation +25 + 50000 credits + achievement

## 실패 시 (Failure Protocol)

- Chain unlock이 너무 쉬움/어려움 → adjust unlock_condition
- Midpoint save 안됨 → check save logic
- Chain-wide reward 누락 → check reward_spec

---

## Related testcases

- TC-MISSION-LEGACY-001~010: 기존 111 미션 호환성 (Phase 11 후에도 valid)
- TC-MISSION-CONSISTENCY-001: 5 new types의 schema 일관성
- TC-MISSION-BALANCE-001: 5 new types 사이의 보상 균형

## Notes

- 5 new types 모두 Pillar 1 (The Run) variety 강화
- 1 sample chain (TA Succession) — 7 more chains 미래 phase에서 추가
- 6 testcases 정의 (one per new type + chain)
