# Death & Restart Cycle (자키 사이클)

> **이 문서는 [`../../decisions/0040-death-restart-cycle.md`](../../decisions/0040-death-restart-cycle.md)의 디자인 명세.**
> 플레이어 자키가 HP 0이 되면 *인격이 보존된 채로* 사망 → 새 자키 또는 같은 자키로 재시작.
>
> **Phase 19 audit (2026-08-13)**: Telemetry wiring (Phase 16), ending_choice persistence (Phase 16, ADR-0192), TELEMETRY_STATS data-source (Phase 17, ADR-0184) cross-references added.

## 1. 개요

깁슨 소설에서 자키는 단순한 도구가 아닌 *인격체*다. "The Flatline"이라는 말은 단순한 게임오버가 아니라 *인격의 종결*을 의미한다. 이 디자인은 죽음을 서사적 무게로 다룬다.

| 단계 | 화면 | 내용 |
| --- | --- | --- |
| 1 | COMBAT | HP 0 |
| 2 | DEATH | FLATLINE 화면, X 머리, 2초 정적 |
| 3 | JACK_OUT | 4프레임 애니메이션 |
| 4 | **DEATH_SUMMARY** (신규) | 자키 리포트, 런 통계, Sprawl의 평가 |
| 5 | **RESTART_OPTIONS** (신규) | 새 자키 / 같은 자키 / Hall of Dead / 메뉴 |
| 6 | CHARACTER_SELECT or HUB or MENU | 선택에 따라 분기 |

## 2. DEATH_SUMMARY 화면

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    > FLATLINE <                            ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   ┌─────────────┐                                            ║
║   │  X  (X head) │   실 (Sil) — Veteran                    ║
║   │  ▲▲▲        │   Grade: 3-up                            ║
║   │  ║║║  ███   │   Run #7                                  ║
║   └─────────────┘   Died: TA Payroll                       ║
║                       Time: 47 minutes                      ║
║                                                              ║
║   ═══ RUNTIME STATS ═══                                     ║
║   Missions completed: 3 / 5                                ║
║   Data recovered: 234 / 500                                ║
║   Programs used: hammer, wisp, virus                       ║
║   Inventory: 2 materials, 1 program                        ║
║                                                              ║
║   ═══ INVENTORY AT DEATH ═══                                ║
║   - Jack-in Zapper (T2)                                     ║
║   - 3× raw_credit_chips                                     ║
║                                                              ║
║   ──────────────────────────────────────────                ║
║                                                              ║
║      "Old scores die hard. Mara's not waiting."           ║
║                                                              ║
║   ──────────────────────────────────────────                ║
║                                                              ║
║      [1] 새 자키 (다른 자키 선택)                          ║
║      [2] 같은 자키 (HUB로)                                  ║
║      [3] Hall of Dead Jockeys                               ║
║      [4] 메인메뉴                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## 3. Hall of Dead Jockeys 화면

```
╔══════════════════════════════════════════════════════════════╗
║                HALL OF DEAD JOCKEYS                          ║
║                                                              ║
║   "The Sprawl remembers everyone."                          ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   You have outlived 7 jockeys.                               ║
║   Longest run: 47m (Sil — Veteran)                          ║
║                                                              ║
║   ─── RECENTLY FALLEN ───                                  ║
║                                                              ║
║   > 1. 실 (Sil) — Veteran, 3-up                            ║
║       TA Payroll · 2026-06-20 14:30                        ║
║       "Old scores die hard."                                ║
║                                                              ║
║     2. 케이 (K) — Novice, 1-up                             ║
║       Chiba 11 · 2026-06-19 23:15                          ║
║       "You died a wage slave."                              ║
║                                                              ║
║     3. 카스 (Kas) — Heretic, 5-up                           ║
║       Sense/Net Core · 2026-06-19 11:00                   ║
║       "The wheel keeps turning."                            ║
║                                                              ║
║   ─── ARCHIVE STATS ───                                    ║
║   Total runs: 23                                            ║
║   Total deaths: 7                                           ║
║   Survival rate: 70%                                        ║
║   Avg missions/run: 2.3                                     ║
║                                                              ║
║   [↑/↓] navigate   [ENTER] detail   [ESC] back            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## 4. Epitaph 풀 (Sprawl의 평가)

깁슨 톤 — 짧고 냉소적. 캐릭터별 3개씩, 총 9개.

### Novice (케이, K)
- "You died a wage slave."
- "Sprawl is short on memory."
- "Cash for the next, then."

### Veteran (실, Sil)
- "Old scores die hard."
- "Mara's not waiting."
- "T-A doesn't forget."

### Heretic (카스, Kas)
- "The wheel keeps turning."
- "Loa hears you still."
- "One spoke, not the wheel."

## 5. 데이터 구조

`engine/jockey_history.py`:
```python
@dataclass(frozen=True, slots=True)
class DeceasedJockey:
    """A record of a jockey who flatlined (ADR-0040)."""
    jockey_id: str
    name: str
    character_id: str
    grade: int
    died_at_node: str
    died_at_mission: str
    died_at_timestamp_ms: int
    inventory_snapshot: tuple[str, ...]
    missions_completed: int
    data_recovered: int
    playtime_minutes: int
    epitaph: str

class JockeyHistory:
    """Manages the Hall of Dead Jockeys archive."""
    def __init__(self, save_path: Path | None = None) -> None: ...
    def add(self, jockey: DeceasedJockey) -> None: ...
    def all(self) -> list[DeceasedJockey]: ...
    def recent(self, n: int = 10) -> list[DeceasedJockey]: ...
    def stats(self) -> JockeyStats: ...
    def save(self) -> None: ...
    def load(self) -> None: ...
    def render_lines(self, jockey: DeceasedJockey, lang: str = "en") -> list[str]: ...
```

## 6. AppState 확장

```python
# Jockey cycle (ADR-0040)
jockey_history: tuple[DeceasedJockey, ...] = ()
total_runs: int = 0
total_deaths: int = 0
total_missions_completed: int = 0
longest_run_minutes: int = 0
last_jockey_summary: DeceasedJockey | None = None
death_cause: str = ""  # "Combat" / "Black ICE" / "T-A ICE" / "Black ICE breach"
```

`ScreenKind` 추가:
- `DEATH_SUMMARY` (자키 리포트)
- `HALL_OF_DEAD` (Archive)

## 6.5 Hardcore Mode Override (1-life permadeath)

> **Cycle 4 polish (2026-08-03, ADR-0140 partial)**: Pillar 3 (The Flatline)을 강화하는 *difficulty modifier* — Hardcore 모드가 활성화되면 모든 revival 경로가 차단되고 자키는 1회 death 후 영구 사망한다.

**Activation**: `state.hardcore_mode` (default `False`). 토글 위치는 v1.2.0+ backlog (현재는 settings/character select 옵션 후보).

**Behavior contract** (구현: `engine/death.py`):

| 코드 위치 | 동작 |
| --- | --- |
| `restart_with_new_jockey(state, char_id)` | `state.hardcore_mode`가 True이면 `ValueError("Hardcore mode (1-life permadeath): restart_with_new_jockey blocked. Caller must route player to MENU.")` raise. Revival 차단. |
| `handle_death_summary_choice(state, choice)` | `hardcore_mode=True` + choice ∈ {`new_jockey`, `same_jockey`} 일 때 자동으로 MENU로 라우팅 (`hall_of_dead` / `menu` choice는 허용). |
| `handle_death_input(event, state)` | `hardcore_mode=True`일 때 ENTER/SPACE/KP_ENTER → `advance_to_death_summary()` 대신 MENU 직접 라우팅. Q/+/-/M/category 키는 unchanged. |
| `render_death_screen(console, state)` | `hardcore_mode=True`일 때 title `"FLATLINE"` → `"PERMANENT DEATH"`, subtitle `"Static. Silence."` → `"1-life permadeath. No revival."`, option1 `"[ENTER] Continue — See Summary"` → `"[ENTER] Return to Menu"`. |

**Death flow (Hardcore active)**:
```
COMBAT (HP=0)
    ↓ trigger_death()
DEATH (X 머리, "PERMANENT DEATH" 표시)
    ↓ ENTER/SPACE → MENU로 직접 라우팅 (DEATH_SUMMARY skip)
    ↓ Q → quit game

[MENU] ← 영구 사망. 새 런 시작 시 hardcore_mode를 다시 토글해야 함.
```

**Death flow (Hardcore inactive)**:
기존 ADR-0040 flow 그대로 — DEATH → DEATH_SUMMARY → new_jockey / same_jockey / hall_of_dead / menu 중 선택.

**Pillar 정합**:
- **Pillar 3 (The Flatline) 강화**: death has real weight — 1-life permadeath는 *되돌릴 수 없는* death를 의미.
- **Pillar 4 (The Build) 준수**: ephemeral session preference (AppState() 재생성 시 자동 reset). unlock-only meta-progression — Hardcore 모드 자체는 unlock 대상 아님 (preference).
- **Pillar 5 (The Style)**: 깁슨 톤 유지 — death는 *narrative moment*, 모드 선택이 이를 강화.

**Test coverage** (`tests/unit/test_hardcore_mode.py`, 21 passed):

| Test Class | Coverage |
| --- | --- |
| `TestHardcoreModeField` (4) | default False, can enable/disable, type check |
| `TestPillar4Compliance` (3) | no meta_state write, doesn't persist across resets, type check |
| `TestHardcoreModeBehavior` (3) | default allows revival, restart raises in hardcore, restart works when disabled |
| `TestHardcoreDeathSummaryIntegration` (5) | locked routes new/same jockey → MENU, allows hall_of_dead/menu, non-hardcode proceeds |
| `TestHardcoreDeathScreenInput` (5) | hardcore ENTER/SPACE/KP_ENTER → MENU, Q quits, normal flow regression |
| `TestHardcoreDeathScreenRender` (2) | render smoke tests (hardcore + normal) |

**의도적 제약** (구현 단순화):
- Hardcore 모드는 *런 시작 시* 결정 (런 중 토글 불가)
- Hardcore는 meta-progression 우회 없음 — death 후 메인 메뉴 복귀
- 다른 difficulty modifier (예: 적 강화, 자원 감소)는 v1.2.0+ backlog

## 6.6 Phase 16 — Telemetry Wiring (2026-08-13)

> **새로 추가 (ADR-0184 + Phase 16)**: DEATH / DEATH_SUMMARY flow 가 telemetry 이벤트를 발생시켜, 옵트인 사용자의 *집계형* 사망 통계가 TELEMETRY_STATS 메뉴에 반영된다.

### 6.6.1 trigger_death() 통합

`engine/death.py::trigger_death()` (구현, line 169-178) — `_emit_telemetry_event` helper (line 42) 로 두 이벤트를 *graceful* 트리거:

```python
# engine/death.py
def _emit_telemetry_event(state, name, fn):
    """Defense-in-depth: gate by opt-in, swallow exceptions."""
    if not state.telemetry_opt_in:
        return
    try:
        integrator = TelemetryIntegrator.from_state(state)
        fn(integrator)
    except Exception:
        pass  # telemetry failure must not break death flow

# trigger_death (line 169-178)
_emit_telemetry_event(state, "record_death",
    lambda i: i.record_death(reason))
_emit_telemetry_event(state, "record_run_completed",
    lambda i: i.record_run_completed(outcome="failed", ...))
```

### 6.6.2 데이터 흐름

```
[사망]
   ↓ trigger_death()  (engine/death.py:169-178)
   ↓ _emit_telemetry_event (gated by state.telemetry_opt_in)
combat.TelemetryIntegrator.record_death(...)
combat.TelemetryIntegrator.record_run_completed(outcome="failed")
   ↓
AppState.telemetry_session.events += (2 events,)
   ↓
[메인메뉴 [8] STATS] (telemetry_opt_in == True)
   ↓ aggregate_death_rates(session) → dict[ice_kind, count]
TELEMETRY_STATS 화면 렌더
```

### 6.6.3 Ending Choice 와의 관계

`state.ending_choice` (엔딩 A/B/C, ADR-0192 Phase 16) 와 *death flow* 는 직교 — DEATH_SUMMARY 에서 *엔딩 B/C (flatline)* 선택 시:
- `state.ending_choice = "B"` (또는 "C") 저장
- `engine/save_manager.py::SaveManager._serialize_metadata()` (line 502-509) 가 `metadata["ending_choice"]` 에 직렬화
- `restore_state()` (line 570-573) 가 legacy save 호환 — 없는 키는 default 빈 string 으로 fallback
- *죽은 자키* 의 `DeceasedJockey.ending_choice` 는 *Hall of Dead* 표시용으로 보존

### 6.6.4 검증 (test_telemetry_triggers.py, 21 tests)

| Test Class | Coverage |
| --- | --- |
| `TestRecordDeathWiring` (3) | `_emit_telemetry_event` 정상 호출, defense-in-depth (no-op when opt_out), 실패 격리 (예외 발생 안 함) |
| `TestRecordRunCompletedWiring` (3) | `record_run_completed` 호출, outcome="failed" 페이로드, death 직후 트리거 |
| `TestRecordDeckChosenWiring` (1) | deck picker 의 record_deck_chosen 트리거 |
| `TestRecordMissionCompletedWiring` (2) | mission completion 의 record_mission_completed 트리거 |
| `TestRecordBossReachedWiring` (2) | boss combat 진입 시 record_boss_reached |
| `TestRecordKillWiring` (2) | combat damage 시 record_kill |
| `TestTelemetryEndToEnd` (8) | 전체 lifecycle: trigger_death → menu → STATS → aggregate + payload schema |

### 6.6.5 의도적 제약

- **DEATH_SUMMARY 진입 시점에만 트리거** — death *flow* 진입 자체는 telemetry 와 무관 (spec).
- **Graceful failure**: `_emit_telemetry_event` 가 예외를 raise 하지 않음 — telemetry 시스템 fail 이 death flow 자체를 깨지 않도록 defense-in-depth.
- **옵트인 의무**: `state.telemetry_opt_in == False` 면 모든 record_* 함수가 no-op — death 자체는 항상 진행.
- **세션 ephemeral**: telemetry_session / telemetry_opt_in / deck_size 는 *save metadata* 에 저장되지 않음 (Pillar 4 정합) — 매 런 새로 시작.

### 6.6.6 Pillar 정합

- **Pillar 3 (The Flatline)**: death 의 *무게* 를 *집계 데이터* 로 강화 — 죽음이 *통계* 가 됨.
- **Pillar 4 (The Build)**: 옵트인만 — 사용자가 *자기 메타 진행* 의 일부로만 노출.
- **Pillar 5 (The Style)**: telemetry 이벤트는 *death event* 코드 경로 외 노출 안 됨 — Pillar 5 의 *추상적 메타* 톤 유지.

---

## 7. 화면 흐름 (상태 머신)

```
COMBAT (HP=0)
    ↓ trigger_death()
DEATH (FLATLINE, X 머리, 2초)
    ↓ 자동 전환
JACK_OUT (4프레임 애니메이션)
    ↓ 자동 전환
DEATH_SUMMARY (자키 리포트)
    ↓ [1] 새 자키 / [2] 같은 자키 / [3] Hall of Dead / [4] 메뉴
    ├── [1] → CHARACTER_SELECT → HUB (새 자키)
    ├── [2] → HUB (같은 자키, 인벤토리/미션 초기화)
    ├── [3] → HALL_OF_DEAD (Archive)
    └── [4] → MENU

HALL_OF_DEAD
    ↓ [ENTER] detail / [ESC] back
    └── [ESC] → DEATH_SUMMARY (다시)
```

## 8. MENU 통계 패널

MENU 우측에 누적 통계 표시:
```
RUN STATS
─────────
Jockeys outlived: 7
Total runs: 23
Total deaths: 7
Longest run: 47m
Avg missions/run: 2.3

[6] Hall of Dead Jockeys
```

## 9. 의존성

- `engine/death.py` — 기존 trigger_death / jack_out_to_hub 확장
- `engine/state.py` — jockey_history, ScreenKind 추가
- `engine/jack_out_view.py` — JACK_OUT 후 DEATH_SUMMARY로 전환
- `data/jockeys/deceased.json` — 누적 데이터 (영구 보존)
- `engine/jockey_history.py` (신규) — Archive 관리

## 10. 완료 조건 (Acceptance Criteria)

### Phase 1: 데이터
- [ ] `engine/jockey_history.py` 신규 (DeceasedJockey + JockeyHistory)
- [ ] `data/jockeys/deceased.json` 초기 (빈 배열)
- [ ] `AppState`에 jockey_history, total_runs, total_deaths 등 추가

### Phase 2: 화면
- [ ] `engine/death.py` — `render_death_summary()` 신규
- [ ] `engine/death.py` — `render_restart_options()` 신규
- [ ] `engine/death.py` — `render_hall_of_dead()` 신규
- [ ] `engine/state.py` — ScreenKind 2개 추가

### Phase 3: 입력 처리
- [ ] DEATH_SUMMARY에서 [1/2/3/4] 선택 처리
- [ ] HALL_OF_DEAD에서 [↑/↓/ENTER/ESC] 처리
- [ ] 새 자키 선택 시 player_grade, inventory 등 초기화

### Phase 4: 메뉴 확장
- [ ] MENU 5 옵션 → 6 옵션 (Hall of Dead 추가)
- [ ] MENU 우측에 RUN STATS 패널

### Phase 5: 테스트 (30+)
- [ ] DeceasedJockey 생성 / 직렬화 (5 tests)
- [ ] JockeyHistory add/all/recent/stats (8 tests)
- [ ] Epitaph 선택 (3 tests)
- [ ] DEATH_SUMMARY 렌더 (3 tests)
- [ ] HALL_OF_DEAD 렌더 (3 tests)
- [ ] 입출력 핸들러 (5 tests)
- [ ] 통합 시나리오 (3 tests)

### Phase 6: 데모
- [ ] `scripts/death_demo.py` — 자키 사망 → DEATH_SUMMARY → 새 자키 시연

### Phase 7: 메타 문서
- [ ] `index.md` 갱신
- [ ] `log.md` 갱신
- [ ] `ROADMAP.md` 갱신
- [ ] `dashboard/graphic-novel.html` (없으면 안 해도 됨)

## 11. 열린 결정 사항

- [ ] 자키 데이터 인계 여부 (ROM construct)
- [ ] Hall of Dead 보존 한도 (무제한 vs 최근 20)
- [ ] MENU 통계 표시 (항상 vs 옵션)
- [ ] deceased.json 영구 보존 (게임 삭제 시)

## 12. 다음 단계

1. 결정 사항 확정
2. `jockey_history.py` 구현
3. `death.py` 확장 (DEATH_SUMMARY, RESTART_OPTIONS, HALL_OF_DEAD)
4. AppState 확장
5. 메뉴 [6] 옵션 추가 (HALL_OF_DEAD, Phase 7에서 [7] HELP 추가, Phase 17에서 [8] STATS 옵트인)
6. 테스트 30+ 추가
7. `death_demo.py` 시연
8. 메타 문서 동기화

---

## 13. Phase 19 Audit Trail (2026-08-13)

Phase 19 감사 (Phase 16 telemetry + Phase 16 ending_choice + Phase 17 TELEMETRY_STATS) 결과.

### 13.1 추가된 시스템

- **Section 6.6**: Phase 16 telemetry wiring — `trigger_death()` → `record_death` + `record_run_completed(outcome="failed")`. 
  - `engine/death.py:_emit_telemetry_event` helper 가 defense-in-depth (옵트인 + 예외 격리).
- **Cross-reference**: `state.ending_choice` (ADR-0192) 가 Hall of Dead 의 *flatline ending B/C* 와 직교 — 두 시스템이 *공존*.

### 13.2 검증 위치

- `tests/unit/test_telemetry_triggers.py` (21 tests) — Section 6.6.4 표 참조.
- `tests/unit/test_endings_persistence.py` (8 tests) — ADR-0192 engine 통합.
- `tests/unit/test_hardcore_mode.py` (21 tests) — Section 6.5 cross-check (telemetry 와 격리).

### 13.3 의도적 비-변경 사항

- DEATH 화면 흐름 자체는 *unchanged* — Phase 16 telemetry wiring 은 *이벤트 추가* 일 뿐, death UX 는 변하지 않음.
- Hall of Dead 화면 레이아웃 / 키 매핑 *unchanged* — `ending_choice` 필드만 *optional 추가*.
- Hardcore Mode (Section 6.5) 도 *unchanged* — telemetry 와 *직교*.

### 13.4 Cross-reference

- [`design/scenario/graphic-novel.md ## 12.3 Ending Choice 영속성`](graphic-novel.md) — GN 의 엔딩 변종과 main flow 엔딩의 분리.
- [`design/systems/combat.md ## F.4 Boss Phase 4`](../systems/combat.md) — 보스 phase transition (death 흐름 진입 *전* 에 발생).
- [`design/systems/inventory.md`](../systems/inventory.md) — wetware stacking (death 시 인벤토리 손실 처리과 무관, 별도).
- [`decisions/0184-telemetry.md`](../../decisions/0184-telemetry.md) — ADR 본문.
- [`decisions/0192-ending-expansion.md`](../../decisions/0192-ending-expansion.md) — ADR 본문.
