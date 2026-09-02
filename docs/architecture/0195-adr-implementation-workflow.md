# ADR-0195: Accepted ADR Implementation Status Workflow

**상태**: **Accepted (Option 1 + Option 3 하이브리드)** — Draft → Accepted 2026-08-26 (this session; user-approved via clarification Q1)
**날짜**: 2026-08-20 (Draft), 2026-08-26 (Accepted)
**결정자**: 사용자
**우선순위**: P3 (The Build, 프로세스 명료화)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0141 — 추가 모듈 스플릿](./0141-additional-module-splits.md), `AGENTS.md §3.2`

## 컨텍스트 (Context)

2026-08-20 게임 품질 audit 결과 (Plan `.omo/plans/QUALITY_UPGRADE_PLAN_2026-08-20.md` §Q1):

> **ADR implementation debt**: 30+ ADRs (0147–0193) marked Accepted with **no verified implementation status**

문제:
- `decisions/0147-*.md` ~ `0193-*.md` 까지 47개 ADR 중 40개가 `## Implementation Status` 섹션 없음
- 2026-08-18 Axis closure sweep 에서 7개 ADR (0156/0157/0158/0159/0188/0189/0191) 에 **ad-hoc** 로 추가됨
- ADR 작성 시점 (2026-08-07~08) 과 실제 구현 시점 사이에 시간차 존재 → "Accepted = 구현됨" 가정 위배
- 신규 진입자가 ADR list 를 보고 "이게 shipped 됐나?" 판단 불가

근본 원인:
- ADR workflow (`AGENTS.md §3.2`) 가 "Draft → Accepted" 만 정의하고 "Implementation status" 단계가 없음
- ADR-0110 / 0111 / 0112 / 0113 같은 Accepted 모듈 분할 결정은 **implementation status** 가 필수지만 강제되지 않음

영향:
- Silent scope creep — Accepted 인 줄 알았는데 미구현
- False confidence — README 가 "구현됨" 으로 표시
- 작업 우선순위 왜곡 — 어디가 진짜 구현됐는지 모름

## 고려한 옵션

### Option 1: Implementation Status 섹션 의무화 (현실 추적) — **추천**

- **설명**: 모든 신규/기존 Accepted ADR 에 `## Implementation Status (YYYY-MM-DD)` 섹션 추가 의무화. status 4종 + evidence file:line 인용 필수. **구현 = shipped 코드 + 테스트 + 데이터 모두 확인 후** ✅ 표시.
- **장점**:
  - 1회 sweep 으로 전체 ledger 정합화 (현재 30+ ADR 의 진실 상태 가시화)
  - 신규 ADR 작성 시 workflow 에 status 결정 단계 추가 → 자동 추적
  - 코드-문서 동기화 보장 (drift 방지)
  - 기존 0156/0188 format 이 이미 검증됨
- **단점**:
  - 기존 40개 ADR 에 status block 추가 작업 (1-2 sessions, Track A.1)
  - 신규 ADR 작성 시 status 결정 부담 (옵션 1개 추가)
- **Pillar 정합**:
  - P1 (The Run): 중립
  - P2 (The Matrix): 중립
  - P3 (The Flatline): 중립
  - P4 (The Build): ✅ (코드 건강 / 빌드 추적)
  - P5 (The Style): 중립

### Option 2: ADR Status 에 "Implemented" 단계 추가

- **설명**: ADR Status enum 에 `Accepted → Implemented` 단계 추가. 모든 ADR 이 Implemented 로 전이되어야 "done".
- **장점**: 단순한 단계 모델
- **단점**:
  - 기존 95개 Accepted ADR 의 status 변경 부담
  - "Implementation" 이 binary 가 아닐 수 있음 (Partial 케이스 ADR-0147 등)
  - Accepted 의미 자체가 변질 — "Accepted = 결정됐고 곧 구현" 의미인데 Implemented 가 되면 "구현 강제" 가 됨
- **Pillar 정합**:
  - P4 (The Build): ✅ 약함 (binary 상태만 표현)
  - 다른 Pillar: 중립

### Option 3: 인덱스 표 추가 (ADR README 동기화)

- **설명**: `decisions/README.md` 의 ADR 목록 표에 "Impl" 컬럼 추가. 모든 ADR 의 status 를 한눈에.
- **장점**:
  - 한 곳에서 가시화
  - 기존 ADR 변경 부담 없음
- **단점**:
  - ADR 본문과 인덱스 동기화 부담 (drift 위험)
  - Status 의 4종 표현이 표에서 한 컬럼에 압축되어 detail 손실
- **Pillar 정합**:
  - P4 (The Build): ✅ (메타 진행 가시화)

### Option 4: 현상 유지 (no-op)

- **설명**: ADR Implementation status 추적 안 함. 필요 시 ad-hoc 으로 추가.
- **장점**: 작업 부담 0
- **단점**:
  - 30+ ADR 의 정합성 미해결
  - Silent scope creep 지속
  - Track A.1 의 작업이 일회성 ad-hoc 으로 끝남
- **Pillar 정합**:
  - 모든 Pillar: 중립

## 추천 (Recommendation)

**Option 1 (Implementation Status 섹션 의무화) + Option 3 (인덱스 Impl 컬럼) 하이브리드**

이유:
1. **Option 1** 은 ADR 본문에 정식 status + evidence 기록 → 코드-문서 동기화
2. **Option 3** 은 인덱스에 한눈에 가시화 → 신규 진입자 navigation 개선
3. 두 옵션은 보완적이며 충돌 없음
4. 기존 0156/0188 의 검증된 format 재사용 → 신규 학습 부담 없음

## 구현 계획

### Phase 1 (Track A.1, 즉시)

40개 Accepted ADR (0147–0171, 0172–0187, 0190, 0192, 0193) 에 `## Implementation Status (2026-08-20)` 섹션 추가:
- ✅ Implemented — fully wired, evidence in multiple files
- 🟡 Partial — some components shipped, list missing
- ❌ Not started — no code/data/test evidence
- 🟢 Deferred — explicitly noted as future work

Format (0156/0188 검증):

```markdown
## Implementation Status (YYYY-MM-DD)

**Status**: [✅ Implemented | 🟡 Partial | ❌ Not started | 🟢 Deferred]

**Evidence**:
- `path/to/file.py:LINE` — [description]

**Notes**: [caveats]

**No further action on ADR-XXXX** — implementation closed. (or **Open items**: list)
```

### Phase 2 (workflow integration, 즉시)

`AGENTS.md §3.2` 갱신 — Decision 단계에 status 결정 추가:

> ### 3.2 게임 디자인 변경 (갱신)
> 1. `decisions/` 에 새 ADR 작성 또는 기존 ADR Status 변경
> 2. **Implementation status 결정** (Accepted 시점 필수):
>    - ✅ Implemented: 이미 shipped (코드 + 테스트 + 데이터 모두 확인)
>    - 🟡 Partial: 일부만 shipped, 나머지 backlog
>    - ❌ Not started: 미구현 (backlog 명시)
>    - 🟢 Deferred: 의도적으로 미래로 연기
> 3. 영향 받는 `design/systems/*.md` 갱신
> 4. `testcases/` 에 회귀 테스트 추가/갱신
> 5. `design/GDD.md` 의 본문 또는 Open Questions 갱신
> 6. `log.md` 에 기록

### Phase 3 (인덱스 동기화, Track A 완료 후)

`decisions/README.md` 의 ADR 표에 `Impl` 컬럼 추가:

| 번호 | 제목 | 상태 | Impl | 날짜 | 우선순위 |
| --- | --- | --- | --- | --- | --- |
| 0147 | Data Salvage Phase 6+ | Accepted | ✅ | 2026-08-07 | P1 |
| 0160 | Status Effects v2 | Accepted | 🟡 | 2026-08-07 | P2 |
| 0175 | Tutorial System | Accepted | ❌ | 2026-08-08 | P2 |

## 사용자 결정 요청

- [ ] **Option 1 + 3 (추천)** — Implementation Status 섹션 의무화 + 인덱스 Impl 컬럼
- [ ] **Option 1 only** — 섹션만, 인덱스 없음
- [ ] **Option 2** — Status 단계 추가 (Accepted → Implemented)
- [ ] **Option 4** — 현상 유지
- [ ] 기타: ___
- [ ] Defer

## 결과 (Consequences)

### 2026-08-26 — Option 1 + Option 3 채택 (Draft → Accepted)

**핵심 결정**: 두 보완적 옵션을 결합:
- **Option 1**: 모든 신규/기존 Accepted ADR 에 `## Implementation Status (YYYY-MM-DD)` 섹션 추가 의무화
- **Option 3**: `decisions/README.md` ADR 표에 `Impl` 컬럼 추가 — 한눈에 가시화

### Status 4종 정의 (Accepted 시점 필수)

| Status | 의미 | Evidence 요구 |
|---|---|---|
| ✅ **Implemented** | shipped: 코드 + 테스트 + 데이터 모두 확인 | `path/to/file.py:LINE` 다중 인용 |
| 🟡 **Partial** | 일부만 shipped, 나머지 backlog | shipped 부분 + missing 부분 명시 |
| ❌ **Not started** | 미구현 | backlog 명시 |
| 🟢 **Deferred** | 의도적으로 미래로 연기 | ADR 본문에 defer 사유 명시 |

**구현 = shipped 코드 + 테스트 + 데이터 모두 확인 후** ✅ 표시. ADR Accepted 시점이 곧 Implemented 아님.

### Format (0156/0188 검증된 양식 재사용)

```markdown
## Implementation Status (YYYY-MM-DD)

**Status**: [✅ Implemented | 🟡 Partial | ❌ Not started | 🟢 Deferred]

**Evidence**:
- `path/to/file.py:LINE` — [description]

**Notes**: [caveats]

**No further action on ADR-XXXX** — implementation closed.
(또는 **Open items**: list)
```

### Phase 1: 기존 Accepted ADR sweep (Track A.1, 즉시 적용)

대상: 40+ Accepted ADR (0147–0171, 0172–0187, 0190, 0192, 0193) 중 Implementation Status 섹션 미보유 항목
- 각 ADR 파일에 `## Implementation Status (YYYY-MM-DD)` 섹션 추가
- ✅ / 🟡 / ❌ / 🟢 status 결정 + evidence 인용
- Phase 1 완료 후 인덱스 Impl 컬럼 동기화

### Phase 2: AGENTS.md §3.2 workflow 갱신 (즉시)

신규 ADR 작성 workflow에 status 결정 단계 추가:

```markdown
### 3.2 게임 디자인 변경 (갱신)
1. `decisions/` 에 새 ADR 작성 또는 기존 ADR Status 변경
2. **Implementation status 결정** (Accepted 시점 필수):
   - ✅ Implemented: 이미 shipped (코드 + 테스트 + 데이터 모두 확인)
   - 🟡 Partial: 일부만 shipped, 나머지 backlog
   - ❌ Not started: 미구현 (backlog 명시)
   - 🟢 Deferred: 의도적으로 미래로 연기
3. 영향 받는 `design/systems/*.md` 갱신
4. `testcases/` 에 회귀 테스트 추가/갱신
5. `design/GDD.md` 의 본문 또는 Open Questions 갱신
6. `log.md` 에 기록
```

### Phase 3: 인덱스 Impl 컬럼 추가

`decisions/README.md` ADR 표에 `Impl` 컬럼 추가:

| 번호 | 제목 | 상태 | **Impl** | 날짜 | 우선순위 |
| --- | --- | --- | --- | --- | --- |
| 0147 | Data Salvage Phase 6+ | Accepted | ✅ | 2026-08-07 | P1 |
| 0160 | Status Effects v2 | Accepted | 🟡 | 2026-08-07 | P2 |
| 0175 | Tutorial System | Accepted | ❌ | 2026-08-08 | P2 |

### Phase 4: template.md 갱신 (신규 ADR 작성 시 적용)

`decisions/template.md` 의 "게임 디자인 변경" 섹션에 Implementation Status 결정 단계 명시

### 우선순위 (Track A 완료 후 작업)

본 ADR Accepted 후 즉시 Phase 1~4 모두 적용 권장. 단 Track A.1 (40+ ADR sweep) 은 별도 세션 분담 가능 (작업량 큼).

### 거부된 옵션

- **Option 2** (Status에 Implemented 단계 추가): 기존 95개 Accepted ADR status 변경 부담 + "Accepted = 곧 구현" 의미 변질 위험
- **Option 4** (현상 유지): silent scope creep 지속, 30+ ADR 정합성 미해결

### 후속 작업 (별도 commit 필요)

1. **Phase 1 sweep**: 40+ ADR 파일에 `## Implementation Status` 섹션 추가 (별도 세션, ~2-3h)
2. **Phase 2**: `AGENTS.md §3.2` 갱신 (1 commit)
3. **Phase 3**: `decisions/README.md` ADR 표 `Impl` 컬럼 추가 (1 commit)
4. **Phase 4**: `decisions/template.md` 갱신 (1 commit)
5. **인덱스 상태 갱신**: 0195 줄 `Draft → Accepted (Option 1+3)`

## 영향 받는 항목

- `AGENTS.md §3.2` — workflow 갱신
- `decisions/README.md` — Impl 컬럼 추가
- 40+ ADR 파일 — Implementation Status 섹션 추가 (Phase 1)
- `decisions/template.md` — 신규 ADR 작성 시 status 결정 단계 명시

## 관련 결정

- **ADR-0110** (Accepted) — 모듈 사이즈 정책 (이 ADR 의 Implementation Status 가 본 ADR 의 model)
- **ADR-0141** (Accepted) — 추가 모듈 스플릿 (Implementation Status 의무화 시 적용)
- **AGENTS.md §3.2** — 게임 디자인 변경 workflow (본 ADR 이 직접 수정)

## 향후 결정

- 본 ADR Accepted 후:
  - Track A.1 의 40+ ADR sweep 본 ADR 의 첫 적용 사례
  - 신규 ADR 작성 시 template 에 Implementation Status 단계 추가
  - 인덱스 Impl 컬럼 동기화

## 변경 이력

- 2026-08-20: Draft 작성 (game quality audit 의 Q1 해결)
- 2026-08-26: Draft → **Accepted (Option 1+3 하이브리드)** — 본 세션, v1.4.0 Operational Release 후속 작업. Implementation Status 섹션 의무화 + 인덱스 Impl 컬럼 추가. Consequences 섹션 + Phase 1~4 후속 작업 5건 명시.