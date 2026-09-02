# ADR-0040: Death & Restart Cycle (자키 사이클)

> **상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
> **날짜**: 2026-06-20
> **결정자**: 사용자
> **관련**: ADR-0003 (Combat RT-MS), ADR-0006 (Run structure), ADR-0008 (Progression), ADR-0017 (Missions), ADR-0019 (Aftermath), ADR-0021 (Save/Load)

## 1. 컨텍스트

현재 게임에서 플레이어의 HP가 0이 되면 `trigger_death()` → `DEATH` 화면 → `jack_out_to_hub()`로 HUB로 복귀하는 흐름은 구현되어 있음. 하지만 다음이 부족:

**문제점**:
1. **죽은 자키의 기록이 휘발됨** — dead 자키의 이름/등급/통계가 다음 런으로 넘어가지 않음
2. **"The Flatline" 톤 부족** — 깁슨 소설에서는 죽음이 *인격*의 종결. 자키는 단순한 게임 캐릭터가 아닌 *인격체*여야 함
3. **새 자키 선택 흐름 없음** — death 후 같은 캐릭터로만 재시작. 깁슨 톤에선 *다른 자키*가 자기를 고용
4. **통계/아카이브 없음** — 누적 deaths, 평균 grade, 최장 run 등 메타 진행 없음
5. **단일 자키 = 단일 정체성** — 깁슨 소설은 여러 자키가 같은 의뢰를 수행. 게임은 한 번에 한 자키만
6. **deceased_jockeys 표시 부재** — "과거 자키들" 메뉴/리포트 없음

**기존 자산** (살려쓸 것):
- `engine/death.py` — `trigger_death()`, `jack_out_to_hub()`, `render_death_screen()` (이미 동작)
- `engine/state.py` — `is_dead: bool`, `death_reason: str`
- `engine/jack_out_view.py` — JACK_OUT 애니메이션 (death에도 사용)
- `run/state.py` — `Stage.FAILED`, `Stage.DEATH_RESTART` (이미 enum 정의됨)
- `save_manager.py` — slot 3에 death 자동 저장 (이미 동작)

## 2. 목표

| # | 목표 | 효과 |
| --- | --- | --- |
| G1 | 죽은 자키의 *인격*을 보존 (이름, 등급, 죽은 곳, 들고 있던 것) | 깁슨 톤 — 자키는 "data"가 아닌 *사람* |
| G2 | "The Sprawl Remembers" — 사망 시점에 자키 *리포트* 생성 | Pillar 5 (mediated world) |
| G3 | 다음 런에 *다른 자키* 선택 (이전에는 불가) | 로그라이크 정체성 |
| G4 | **Deceased Jockeys Archive** — 누적 사망 자키 목록 | 메타 진행, 진행 회고 |
| G5 | **Runner Statistics** — total_runs, total_deaths, average_grade, longest_run | 게임 정체성 강화 |
| G6 | 같은 캐릭터로 재시작 옵션도 유지 (깁슨 톤 존중 — 자키가 다시 의뢰인에게 나타남) | 유연성 |

## 3. 옵션 비교

### Option A: 자키 사이클 (권장)

| 항목 | 내용 |
|---|---|
| **Death 시점** | 자키 리포트 표시 (이름, 등급, 사망 위치, 가지고 있던 것) |
| **재시작 옵션** | (1) 새 자키 / (2) 같은 자키 / (3) 메인메뉴 |
| **새 자키** | CHARACTER_SELECT 화면으로 → 이전 다른 캐릭터 풀에서 선택 |
| **같은 자키** | HUB로 직접 (현재 흐름) |
| **Archive** | `data/jockeys/deceased.json` — 누적 사망 자키 |
| **Statistics** | AppState에 누적 카운터 |
| **Menu 진입** | MENU [6] "Hall of Dead Jockeys" (선택) |

| 장점 | 단점 |
|---|---|
| ✅ 깁슨 톤 (인격 보존, "Sprawl이 기억한다") | 자키 1명당 메타 진행 분리 |
| ✅ 로그라이크 정체성 (매 런 새 자키) | 새 UI 2-3개 추가 |
| ✅ 메타 진행 가시화 | Archive 데이터 구조 설계 |
| ✅ Pillar 5 강화 | |

### Option B: 현재 흐름 유지 (자키 인격 보존 없음)

| 항목 | 내용 |
|---|---|
| Death → HUB (현재) | 자키 사망 후 즉시 재시작, 인격 보존 없음 |
| 동일 캐릭터로만 진행 | 매번 같은 등급, 같은 이름 |
| 리포트/Archive 없음 | |

| 장점 | 단점 |
|---|---|
| 단순함 | 깁슨 톤 약화 |
| 구현 비용 0 | 로그라이크 정체성 부족 |
| | 자키 = 스킨일 뿐 |

### Option C: 자키 사이클 + 미니게임 (인격 정밀 보존)

| 항목 | 내용 |
|---|---|
| 자키 사망 시 *인터뷰* (NPC가 질문) | |
| 자키 *인격 트레이트* (대담/조심/공격적) | |
| 다음 자키가 이전 자키의 *데이터*를 인계 | |
| 복잡한 시스템 | |

| 장점 | 단점 |
|---|---|
| ✅✅ 가장 깊은 깁슨 톤 | 구현 비용 매우 높음 |
| | 게임플레이가 *대화 게임*화 |

**추천**: **Option A** — 자키 사이클의 핵심 가치 (인격 보존 + 새 자키 선택 + Archive) 를 *적절한 복잡도*로 구현.

## 4. 권장안 (Option A) 상세

### 4.1 화면 흐름

```
COMBAT (HP=0)
    ↓
trigger_death()
    ↓
DEATH (FLATLINE 화면, 2초 정적)
    ↓
JACK_OUT (4프레임 애니메이션)
    ↓
DEATH_SUMMARY (NEW) — 자키 리포트
    - 이름, 등급, 사망 위치
    - 가지고 있던 것 (인벤토리)
    - 런 통계 (미션 수, 데이터, 플레이 시간)
    - Sprawl의 평가 ("You died a wage slave." / "Not bad, for a deckhand.")
    ↓
RESTART_OPTIONS (NEW) — 3 옵션
    [1] 새 자키 (CHARACTER_SELECT로)
    [2] 같은 자키 (HUB로)
    [3] Hall of Dead Jockeys (ARCHIVE 화면)
    [4] 메인메뉴
    ↓
(선택에 따라 분기)
```

### 4.2 데이터 구조

`AppState` 추가 필드:
```python
# Jockey cycle (ADR-0040)
jockey_history: tuple[DeceasedJockey, ...] = ()  # 누적 사망 자키
total_runs: int = 0
total_deaths: int = 0
total_missions_completed: int = 0
longest_run_minutes: int = 0
last_jockey_summary: JockeySummary | None = None  # 방금 죽은 자키
```

새 dataclass:
```python
@dataclass(frozen=True, slots=True)
class DeceasedJockey:
    """A record of a jockey who flatlined (ADR-0040).
    
    Immutable — once added to the archive, never modified.
    """
    jockey_id: str           # 고유 ID (uuid 또는 시간+이름)
    name: str                # "케이 (K) — Novice" 등
    character_id: str       # "novice" / "veteran" / "heretic"
    grade: int               # 최종 등급
    died_at_node: str        # 사망 매트릭스 노드 ID
    died_at_mission: str     # 사망 미션 ID
    died_at_timestamp_ms: int  # 사망 시각 (epoch ms)
    inventory_snapshot: tuple[str, ...]  # 가지고 있던 것
    missions_completed: int  # 이 런에서 완료한 미션
    data_recovered: int      # 이 런에서 회수한 데이터
    playtime_minutes: int    # 이 런 플레이 시간
    epitaph: str             # Sprawl의 평가 (랜덤 선택)
```

### 4.3 Epitaph 풀 (Sprawl의 평가)

깁슨 톤의 짧은 평가 — 캐릭터별 3개씩, 총 9개:
- **Novice (케이)**: "You died a wage slave." / "Sprawl is short on memory." / "Cash for the next, then."
- **Veteran (실)**: "Old scores die hard." / "Mara's not waiting." / "T-A doesn't forget."
- **Heretic (카스)**: "The wheel keeps turning." / "Loa hears you still." / "One spoke, not the wheel."

### 4.4 Hall of Dead Jockeys (Archive 화면)

```
╔══════════════════════════════════════════════╗
║           HALL OF DEAD JOCKEYS               ║
╠══════════════════════════════════════════════╣
║                                              ║
║  You have outlived 7 jockeys.                ║
║  Longest run: 47 minutes (실 — Veteran)     ║
║                                              ║
║  ─── RECENTLY FALLEN ───                    ║
║                                              ║
║  1. 실 (Sil) — Veteran, 3-up                ║
║     TA Payroll · 2026-06-20 14:30          ║
║     "Old scores die hard."                  ║
║                                              ║
║  2. 케이 (K) — Novice, 1-up                ║
║     Chiba 11 · 2026-06-19 23:15            ║
║     "You died a wage slave."                ║
║                                              ║
║  3. 카스 (Kas) — Heretic, 5-up              ║
║     Sense/Net Core · 2026-06-19 11:00     ║
║     "The wheel keeps turning."               ║
║                                              ║
║  [↑/↓] navigate   [ENTER] detail   [ESC] back ║
╚══════════════════════════════════════════════╝
```

### 4.5 통계 표시 (MENU 우측 패널)

```
RUN STATS
─────────
Jockeys outlived: 7
Total runs: 23
Total deaths: 7
Longest run: 47m
Avg missions/run: 2.3
```

### 4.6 새 자키 선택 흐름

DEATH_SUMMARY → RESTART_OPTIONS → [1] 새 자키
    ↓
CHARACTER_SELECT (기존)
    - 새 character_id로 AppState 업데이트
    - player_grade, inventory, mission_progress 초기화
    - player_ppl, player_hp 풀 상태로
    - HUB로

깁슨 톤: "The Finn has a new jockey. You won't be missed. Sprawl's full of them."

### 4.7 같은 자키 재시작

DEATH_SUMMARY → RESTART_OPTIONS → [2] 같은 자키
    ↓
HUB (기존 jack_out_to_hub와 동일)
    - 인벤토리 초기화
    - 미션 진행 초기화
    - HP 풀 회복
    - 등급은 유지 (ADR-0008)

깁슨 톤: "The Finn took you back. Even dead, you owe him."

## 5. 결과 (Consequences)

### 긍정적
- ✅ 깁슨 톤 (Pillar 5) 강화 — 자키 인격 보존
- ✅ 로그라이크 정체성 (매 런 새 자키)
- ✅ 메타 진행 가시화 (Hall of Dead Jockeys)
- ✅ Death 화면의 *서사적 무게* (단순 게임오버 아님)
- ✅ Archive가 자연스러운 *재플레이 동기* (이전 자키를 능가하라)

### 부정적
- ❌ Archive 데이터 구조 (DeceasedJockey) 신규
- ❌ death.py + jack_out_view.py 확장 (~150 lines)
- ❌ engine/jockey_history.py 신규 (~120 lines)
- ❌ ScreenKind 2개 추가 (DEATH_SUMMARY, HALL_OF_DEAD)
- ❌ 테스트 30+ 추가
- ❌ 메타 진행 UI 2개 (Hall of Dead, MENU 통계 패널)

### 중립
- 기존 trigger_death / jack_out_to_hub 로직 *유지* (확장만)
- 자키 ID는 자동 생성 (이름 + 타임스탬프)
- Hall of Dead는 *읽기 전용* (편집 불가, 영구 보존)

## 6. 열린 질문 (Open Questions)

1. **새 자키가 이전 자키의 데이터를 인계?** — 깁슨 톤에선 가능 (ROM construct) but 복잡함
2. **Hall of Dead의 보존 한도?** — 무제한? 또는 최근 20명만?
3. **MENU 통계 표시 여부** — 항상? 옵션?
4. **deceased.json 영구 보존?** — 게임 삭제 시에도 보존? (사용자 데이터 존중)

## 7. 열린 결정 사항

- [ ] 자키 데이터 인계 (1번)
- [ ] Hall of Dead 보존 한도 (2번)
- [ ] MENU 통계 표시 (3번)
- [ ] deceased.json 영구 보존 (4번)

## 8. 다음 단계

사용자 결정 후:
1. `engine/jockey_history.py` 신규 (DeceasedJockey, Hall of Dead 로직)
2. `engine/death.py` 확장 (DEATH_SUMMARY 렌더링, RESTART_OPTIONS)
3. `engine/state.py` — jockey_history 필드, ScreenKind 추가
4. `data/jockeys/deceased.json` 초기 (빈 배열 또는 예시)
5. 메뉴 [6] "Hall of Dead Jockeys" 진입
6. 테스트 30+ (death/restart/archive)
7. `scripts/death_demo.py` (시연)
8. 메타 문서 (index/log/ROADMAP)

## 9. 작업 규모

| 항목 | 라인 |
| --- | --- |
| engine/jockey_history.py | ~150 |
| engine/death.py 확장 | ~80 |
| engine/state.py 확장 | ~10 |
| engine/menu.py 확장 | ~30 |
| 9개 epitaph | ~10 |
| 데이터 파일 | ~30 |
| 테스트 30+ | ~600 |
| **총** | **~900 lines** |
| **예상 소요** | **1.5~2 세션** |

## 결과 (Consequences)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 Accepted 로 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `engine/death.py` (20KB) + `engine/jockey_history.py` (19KB) + `data/jockeys/deceased.json` (12,223 자키 보존). Death → DEATH_SUMMARY → HALL_OF_DEAD → 새 자키 풀 사이클 구현.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
