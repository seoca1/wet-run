# ADR-0131: Faction Reputation Cross-Run Persistence (Meta Progression)

**상태**: Accepted (Option 1)
**날짜**: 2026-07-27
**결정자**: 사용자
**우선순위**: P1 (IMPROVEMENTS.md §369 "다음 세션" 1순위)
**연관**: ADR-0008 (Progression), ADR-0012 (PPL/ZDR), ADR-0017 (Mission-Material), ADR-0040 (Death & Restart), Balance Audit 2026-07-27 §5

---

## 컨텍스트 (Context)

`IMPROVEMENTS.md` §369 + Balance Audit §361-372 식별:

> **Persistence: faction rep 가 run 간 영속화** | 부분 (save/load 만) | P2

현재 상태:
- `state.reputation` (AppState 필드) 는 *단일 세션* + *save/load* 시 영속화 (`engine/save_manager.py:498`)
- `restart_with_new_jockey` (ADR-0040) 호출 시 reputation 명시적 reset **안** 함 — 부수효과로 *같은 세션 내* cross-run은 보존
- **문제**: 새 세션 / 새 save 파일 시작 시 reputation 0 (NEUTRAL) 으로 초기화
- **결과**: faction 관계가 *캐주얼* — 매 런이 평행세계, faction 호감도가 *진짜 누적*되지 않음

**설계 의도 (Pillar 4 재검토)**:

> Pillar 4: "메타 진행은 unlock 중심 (강화 X)"

Faction reputation 은:
- 직접 스탯 증가 X (PPL/ZDR 계산에 미반영)
- 미션 잠금 해제 (rep_threshold) — *unlock* 효과
- NPC dialogue 변형 — *narrative* 효과
- Info Market 가격 할인 — *편의* 효과
- → *unlock*-like 으로 분류 가능. **Pillar 4와 정합**

깁슨 톤 정합:
- Faction 은 *관계* — 일회성이 아닌 누적
- "Hosaka에 빚진 자키" 는 자키가 죽어도 평판이 남아야 자연스러움
- → cross-run persistence 는 *세계관 일관성* 향상

---

## 고려한 옵션

### Option 1: Meta State File (권고)

- **설명**: 별도 `data/saves/meta_state.json` 파일로 faction reputation 등 cross-run 메타 진행 저장. `AppState.reputation` 은 그대로 두고, save/load 시 `meta_state.json` 과 동기화.
- **장점**:
  - Save 파일과 독립 — 신규 save / 다른 슬롯도 평판 공유
  - 확장 가능 (향후 메타 진행 항목: Hall of Dead 누적, achievement 등)
  - Save 파일 마이그레이션과 분리 → 안정성 ↑
  - Pillar 4 정합 (unlock-only)
- **단점**:
  - 새 파일/스키마/로드 로직 필요
  - Save 파일 + meta_state.json 두 곳 동기화 복잡도
  - "Run 간 격리" 옵션이 필요한 경우 (예: hardcore mode) 별도 처리
- **세부 작업**:
  1. `run/meta_state.py` 신규: `MetaState` dataclass (reputation + version + future-proof dict)
  2. `meta_state.json` schema: `{version: 1, reputation: {hosaka: 50, ...}, hall_of_dead: []}`
  3. `engine/meta_state_manager.py` 신규: load/save with atomic write + version migration
  4. `save_manager.py` 수정: save 시 reputation을 meta_state.json 으로 promote (명시적 플래그)
  5. `engine/state.py` 부트스트랩: 새 AppState 생성 시 meta_state.json → state.reputation hydrate
  6. 테스트: `tests/unit/test_meta_state.py` (load/save/migration/legacy/promote)
- **Pillar 정합**:
  - P1 (The Run): 한 런 내 평판 변동은 *변하지 않음* — cross-run *누적*만
  - P3 (The Flatline): 사망 시 평판 일부 손실? (선택) — 깁슨 톤 "flatline reputation loss" 가능
  - P4 (The Build): unlock 효과만 — 강화 X ✓
  - P5 (The Style): Faction 관계 누적 = "Sprawl 의 기억" — 깁슨 톤 정합

### Option 2: Save-Level Reputation Persistence (현 상태 강화)

- **설명**: 현재처럼 save 파일에 reputation 저장. 단, `restart_with_new_jockey` 명시적으로 reputation 보존하도록 코드 보강 + 사망 시 페널티 선택 추가.
- **장점**:
  - 최소 변경 (코드 1~2개 함수 수정)
  - 새 파일/스키마 불필요
  - Save 슬롯별 격리 (한 슬롯의 평판이 다른 슬롯에 영향 X)
- **단점**:
  - Save 파일 삭제 시 평판 손실 (의도 vs 의도 아님)
  - Cross-save-file 메타 진행 부재
  - 확장성 낮음 (다른 메타 진행 추가 어려움)
- **세부 작업**:
  1. `restart_with_new_jockey`: 명시적 reputation 보존 (코드 의도 명확화)
  2. Death hook: 사망 시 faction rep -5~10 (선택, 깁슨 톤 "신뢰 손실")
  3. 테스트: `test_death_preserves_reputation`, `test_death_rep_penalty`
- **Pillar 정합**:
  - P4: unlock-only 유지 ✓
  - P3: 사망 시 페널티 추가 시 *Flatline 무게* 강화 ✓

### Option 3: Hybrid (Meta State + Save-Level)

- **설명**: Option 1 + Option 2 결합. meta_state.json (global) + save 파일 (per-run). 두 곳에 모두 저장하되 meta_state.json 이 권위.
- **장점**:
  - Save 파일만 있어도 동작 (오프라인 시)
  - Meta state 가 canonical
  - 양쪽 동기화로 안전성 ↑
- **단점**:
  - 복잡도 가장 큼
  - 동기화 race condition 가능
  - 디버깅 어려움

### Option 4: Defer (현 상태 유지)

- **설명**: 현재 save/load-only 동작 유지. v1.0.0 이후 별도 사이클.
- **장점**: 변경 없음
- **단점**: IMPROVEMENTS.md "다음 세션" 1순위 미해결

---

## 추천 (Recommendation)

**Option 1 (Meta State File)** 권고.

**근거**:
1. **확장성** — 향후 Hall of Dead 누적, achievement 영속화 등 메타 진행 항목 추가 시 동일 인프라 활용
2. **깁슨 톤** — "Sprawl 의 기억" 으로서 faction 관계는 자키보다 오래 살아남음 — 별도 파일이 세계관적으로 자연스러움
3. **Save 격리** — Save 슬롯별 격리 / cross-slot 공유 중 *사용자 선택* 가능 (옵션화)
4. **Pillar 4 정합** — unlock 효과만 유지, 강화 X
5. **Option 2 의 한계** — Save 파일 삭제 시 메타 진행 손실은 *의도와 무관*하게 발생할 수 있음

**잔존 트레이드오프 (사용자 결정)**:
- Hardcore mode (런 완전 격리) 가 필요한지 — 별도 옵션화
- 사망 시 평판 페널티 (-5~10) — 깁슨 톤 강화, Pillar 3 정합

---

## 사용자 결정 (Decision)

- [x] **Option 1 (Meta State File)** — 사용자 선택 (2026-07-27)
- [ ] Option 2 (Save-Level 강화)
- [ ] Option 3 (Hybrid)
- [ ] Option 4 (Defer)
- [ ] 기타: ___

**세부 옵션** (Option 1 선택 시):
- [x] 사망 시 평판 페널티: **없음** — 깔끔한 첫 출시 우선, v1.1.0+ 검토
- [x] Hardcore mode 격리: **비활성** — v1.1.0+ 검토

---

## 영향 받는 항목 (예정)

수락 시 (Option 1):
- `src/wet_run/run/meta_state.py` (신규) — `MetaState` dataclass
- `src/wet_run/engine/meta_state_manager.py` (신규) — load/save/migration
- `src/wet_run/engine/state.py` — 부트스트랩 hook
- `src/wet_run/engine/save_manager.py` — 명시적 promote (default off, opt-in)
- `tests/unit/test_meta_state.py` (신규) — 30+ tests
- `design/systems/reputation.md` (또는 `progression.md`) — 문서 보강
- `log.md` 기록
- `decisions/README.md` ADR-0131 등재

---

## 결과 (Consequences)

**Option 1 Accepted** (2026-07-27). 세부 옵션: 사망 페널티 없음, Hardcore 격리 비활성.

### 적용된 변경
1. **신규 파일**: `src/wet_run/run/meta_state.py`
   - `MetaState` dataclass: version, reputation, future_buckets
   - `to_dict()` / `from_dict()` roundtrip with forward-compatible future_buckets
   - `promote_from_run()` API: history merge (no double-counting, score clamped per-event ±25)
2. **신규 파일**: `src/wet_run/engine/meta_state_manager.py`
   - `load_meta_state()`: missing/corrupt → empty default
   - `save_meta_state()`: atomic write (temp + rename + fsync)
   - `default_meta_state_path()`: `data/saves/meta_state.json`
   - Future-version defense: schema > runtime → empty default
3. **신규 테스트**: `tests/unit/test_meta_state.py` (27 tests, 5 test classes)
4. **잔존 작업** (v1.1.0+ 후속):
   - `engine/state.py` 부트스트랩 hook (AppState 생성 시 hydrate)
   - `save_manager.py` 명시적 promote hook (default off, opt-in)
   - `design/systems/reputation.md` 보강 (cross-run 의미 명시)

### Pillar 정합 검증
- P1 (The Run): 한 런 내 평판 변동 무영향 ✓
- P3 (The Flatline): 사망 시 페널티 없음 (현재 구현) — 깁슨 톤 "trust persists" 정합
- P4 (The Build): unlock-only 메타 진행 (강화 X) ✓
- P5 (The Style): "Sprawl의 기억" — faction 관계가 자키보다 오래 사는 세계관 정합 ✓

### 회귀 위험
- 새 파일 + 새 모듈 → 기존 코드 영향 없음
- 부트스트랩 hook 미구현 → *opt-in* (사용자가 명시적으로 promote 호출 시에만 cross-run 영속화)
- 향후 부트스트랩 자동화 시 회귀 테스트 필요 (별도 ADR-0132+)

### 검증
- ruff check ✓ / ruff format ✓ / mypy strict ✓ (132 source files)
- 27 unit tests pass (`test_meta_state.py`)
- 23 regression tests pass (`test_regression_phase_b35.py`)

---

## 관련 결정

- ADR-0008 (Progression) — 메타 진행 원칙
- ADR-0040 (Death & Restart) — restart_with_new_jockey
- ADR-0017 (Mission-Material Integration) — rep_threshold
- ADR-0051 (Mission Story Metadata) — fixer → faction 매핑

---

## 변경 이력

- 2026-07-27: Draft 작성 (Phase 3 of 게임성 점검)
- 2026-07-27: **Accepted (Option 1)** — 사용자 선택. 신규 파일 + 27 tests 추가

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented (opt-in by design)

**Evidence**:
- `prototype/src/wet_run/run/meta_state.py:26` — `class MetaState` frozen dataclass (version + reputation + future_buckets)
- `prototype/src/wet_run/run/meta_state.py:46` — `reputation: ReputationState` field (canonical cross-run store)
- `prototype/src/wet_run/run/meta_state.py:49` — `to_dict()` roundtrip with forward-compatible `future_buckets`
- `prototype/src/wet_run/run/meta_state.py:58` — `from_dict()` with defensive parsing (missing/corrupt → empty)
- `prototype/src/wet_run/run/meta_state.py:87` — `promote_from_run(run_reputation)` API: history merge with per-event ±25 clamp, no double-counting
- `prototype/src/wet_run/engine/meta_state_manager.py:26` — `default_meta_state_path(data_dir)` (returns `data/saves/meta_state.json`)
- `prototype/src/wet_run/engine/meta_state_manager.py:38` — `load_meta_state(path)` with missing/corrupt/forward-version defense
- `prototype/src/wet_run/engine/meta_state_manager.py:69` — `save_meta_state(state, path)` with atomic write (temp + rename + fsync)
- `prototype/src/wet_run/engine/meta_state_manager.py:99` — `reset_meta_state(path)`
- `prototype/tests/unit/test_meta_state.py` — 27 unit tests (5 classes) covering load/save/migration/promote/atomic-write

**Notes**:
- Bootstrap hook in `engine/state.py` is **intentionally deferred** (per ADR §"잔존 작업" / v1.1.0+ 후속). Cross-run persistence is opt-in via explicit `promote_from_run()` call from `save_manager.py`.
- Death penalty: **none** (per ADR §사용자 결정 — 깔끔한 첫 출시 우선)
- Hardcore mode isolation: **disabled** (per ADR §사용자 결정 — v1.1.0+ 검토)

**No further action on ADR-0131** — implementation closed (opt-in design satisfied).