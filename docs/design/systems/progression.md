# System: Progression (종합 진행)

> **상위 결정**: `../../decisions/0008-progression-system.md` (Accepted, Revised)
> **관련**: [grade-progression.md](./grade-progression.md) (등급 단계), [difficulty-rating.md](./difficulty-rating.md) (난이도), [crafting.md](./crafting.md) (제작), [economy.md](./economy.md) (재화)
> **구현**: `../../prototype/src/wet_run/matrix/ppl.py` (PPL 계산)
>
> **Phase 19 audit (2026-08-13)**: Deck Size 선택 (Phase 15, ADR-0178) — LIGHT/STANDARD/HEAVY 3 템플릿. Tier 1 의 *런 시작 시 결정* 모델에 추가.

## 목적

자키가 한 런 안에서 **고정**된 스탯을 가지고, 런 사이에는 **등급 (meta progression)** 으로 성장하는 시스템. Pillar 4 ("The Build") 의 직접적 표현.

## 3-tier 진행 구조

### Tier 1: 런 내 고정 (In-Run, Immutable)

한 번 런을 시작하면 캐릭터의 기본 스탯은 **변하지 않음**.

| 요소 | 정의 | 변경 가능? |
|---|---|---|
| Deck tier | T1~T5 | ❌ (런 시작시 결정) |
| **Deck size** (Phase 15, ADR-0178) | LIGHT / STANDARD / HEAVY | ❌ (런 시작시 결정) |
| Programs | T1~T5 등급 매칭 | ❌ |
| Wetware | T1~T5 | ❌ |
| Construct | T0~T5 (0 = 없음) | ❌ |
| HP / ATK | tier 기반 | ❌ |

런 중 변경 가능한 것은 **인벤토리**와 **장비** (시간 한정 buff) 뿐.

### 1.1 Deck Size Selection (Phase 15, ADR-0178)

> **새로 추가 (Phase 15)**: 런 시작 시 *Deck tier* 외 *Deck size* 템플릿을 선택. 3가지 — LIGHT (얇은 슬롯, 빠른 빌드) / STANDARD (기본) / HEAVY (두꺼운 슬롯, 강력한 빌드).

| Size | 슬롯 | 빌드 철학 | 추천 |
|---|---|---|---|
| **LIGHT** | 6 슬롯 | Wisp / Hammer / Strike 같은 *얇은* T1-T2 위주 | 첫 런, 빠른 클리어, data salvage 우선 |
| **STANDARD** | 8 슬롯 | Goliath / Wisp / Hammer 균형 | 메타 기본값 (default), 모든 zone 진입 가능 |
| **HEAVY** | 10 슬롯 | Kraken / Goliath / Wardrone + Dixie T5 | 후반부, 깊은 zone (CORE / TA), meta unlock 후 |

**구현** (`combat/deck_building.py`):

```python
class DeckSize:
    name: str
    slots: int
    description: str

DECK_SIZES: dict[str, DeckSize] = {
    "light": DeckSize("light", 6, "Quick build, thin slots"),
    "standard": DeckSize("standard", 8, "Balanced — default"),
    "heavy": DeckSize("heavy", 10, "Deep zone access, late game"),
}

def get_deck_size(size: str) -> DeckSize | None: ...
def get_deck_sizes() -> tuple[DeckSize, ...]: ...
```

**AppState 필드**: `state.deck_size: str = "standard"` (default). `engine/menu.py:`의 DECK_SELECT 화면 (Phase 15 신규)에서 LIGHT/STANDARD/HEAVY 3 옵션 — ENTER 로 확정.

**PPL 영향**: Deck size 는 *PPL 에 직접 영향 없음* — 슬롯 수만 변경. 실제 PPL 은 *선택된 program* 에 따라 좌우 (ADR-0012). 단, AVAILABLE 슬롯 수가 program 선택의 *상한* 이 되므로 *간접 효과* — HEAVY 는 강력한 Kraken T5 까지 동시 장착 가능.

**Pillar 정합**:
- **Pillar 1 (The Run)**: 런 *시작* 시 결정 — in-run immutable.
- **Pillar 4 (The Build)**: 빌드 깊이의 *첫 축* — slot count 가 core mechanic.
- **Pillar 5 (The Style)**: 라벨 명확 (`LIGHT` / `STANDARD` / `HEAVY`), UI ASCII 셰이프 (·W· / :W: / |W| / ▓W▓ / ★W★ — 기존 등급 게이팅과 동일).

**Cross-reference**: [`design/systems/combat.md ## Deck Size Selection`](combat.md), [decisions/0178-deck-building.md](../../decisions/0178-deck-building.md).

### Tier 2: 메타 진행 (Meta Progression, 자키 등급)

자키가 죽으면 (`Stage.FAILED` → `Stage.DEATH_RESTART`) **새 자키** 등장.
새 자키는 이전 자키보다 한 단계 높은 등급으로 시작.

| 자키 순번 | 등급 | 시작 데크 | 비고 |
|---|---|---|---|
| 1번째 | 1-up | T1 Wisp/Strike | 신참 |
| 2번째 | 2-up | T2 Wisp/Hammer | 일반 |
| 3번째 | 3-up | T3 Wisp/Goliath | 숙련 |
| 4번째 | 4-up | T4 Wisp/Goliath/Wardrone | 베테랑 |
| 5번째 | 5-up | T5 Kraken/Goliath/Wisp/Wardrone + Dixie construct | 전설 |

> 메타 진행은 **unlock 만** (ADR-0006). 자키는 절대 잃지 않지만,
> 새 자키는 더 강하게 시작할 뿐.

### Tier 3: 아이템 티어 (Item Tier T1~T5)

매 런 안에서 **재료 → 컴포넌트 → 최종 아이템**으로 제작 (ADR-0015).
티어가 높을수록 stats 가 좋지만, **사용 횟수** 도 늘어남.

```
T1 (재료 5개) → T2 컴포넌트 (4개) → T3+ 프로그램/아이템/construct
```

## PPL 공식 (ADR-0012)

```python
PPL = deck_tier * 3 + sum(programs * 2) + wetware_tier + construct_tier * 3
```

예시 (Grade 1): `PPL = 1*3 + (1+1)*2 + 1 + 0 = 8`
예시 (Grade 5): `PPL = 5*3 + (5+5+5+5)*2 + 5 + 5*3 = 75`

PPL 은 ICE 의 ZDR 과 비교되어 Status (SAFE/MATCH/TOUGH/DEADLY/FUTILE) 결정.

## 런 사이 전이 (Death Cycle, ADR-0040)

```
MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → DEBRIEF → COMPLETE
                                                       ↓ (사망)
                                                    FAILED → DEATH_RESTART
                                                              ↓ (새 자키 선택)
                                                          PENDING (next grade)
```

## NG+ 라이프사이클 (Post-Salvation Meta Unlock)

> **Cycle 4 polish (2026-08-03, ADR-0140 partial)**: Pillar 4 (The Build)의 *unlock-only meta-progression*을 구현하는 메커니즘 — Salvation Phase 완료가 *구조적 replay*를 unlock한다.

**Lifecycle** (4단계):

```
[Salvation Phase 완료 (Epilogue 선택)]
        ↓ unlock hook
state.ng_plus_unlocked = True
        ↓ 메인 메뉴 / CHARACTER_SELECT
[N키 토글 가능]
        ↓ 캐릭터 선택
state.ng_plus_active = True (locked일 시 자동 False)
        ↓ 새 런 시작
[NG+ 런 — keep unlocks, fresh stats]
        ↓ 사망 또는 완전 종료
[메인 메뉴 — NG+ unlock 유지]
```

**구현 포인트** (`engine/`):

| 위치 | 동작 |
| --- | --- |
| `engine/salvation_view.py::handle_salvation_epilogue_input` | ENTER/SPACE로 epilogue 선택 확정 시 `state.ng_plus_unlocked = True` 세팅 (Salvation Epilogue 화면 진입 직후). *메타 unlock trigger*. |
| `engine/menu.py::handle_character_select_input` | unlocked 상태에서 N키 토글 — `state.ng_plus_active = not state.ng_plus_active`. 캐릭터 확정 시 locked일 경우 force False (lock gate). |
| `engine/menu.py::render_character_select` | unlocked 상태에서 `"NG+ MODE: ON/OFF"` 인디케이터 + 푸터에 `[N] NG+` 힌트 표시. |
| `state.ng_plus_unlocked` (AppState) | False (default). Salvation Epilogue 확정 후 True. Pillar 4 준수 — AppState() 재생성 시 reset. |
| `state.ng_plus_active` (AppState) | False (default). N키 토글 또는 locked일 시 False force. � 시작 시점에 snapshot, *unlock 자체는 보존*. |

**Pillar 4 (The Build) 준수**:
- *Unlock-only meta-progression* — NG+는 unlock 대상이 아니라 *replay escalation*.
- *No stat boost* — NG+ 런도 동일 stats (HP/AP/equipment). 테스트로 검증: `test_ng_plus_does_not_modify_player_stats`.
- *Ephemeral preference* — `ng_plus_active`는 런 시작 시점에 결정, 사망 시 reset. `ng_plus_unlocked`만 보존.

**Lock gate** (enforcement):
```python
# engine/menu.py::handle_character_select_input (simplified)
if not state.ng_plus_unlocked:
    state.ng_plus_active = False  # locked runs cannot start NG+
```
locked 상태에서 `ng_plus_active = True`가 stale하게 남아있어도 캐릭터 확정 시 강제 False — *잠긴 모드로 NG+ 시작 불가*.

**Salvation Phase와의 관계** (cross-ref):
- *Salvation은 narrative culmination* — 9자 × epilogue 씬으로 끝나는 메인 스토리.
- *NG+는 mechanical aftermath* — Salvation 완료가 structural replay를 unlock.
- *둘은 직교* — Salvation 완료 없이도 unlock 자체는 가능 (이론상), 단 v1.1.0에서는 Salvation 경로만 trigger.

**Test coverage** (`tests/unit/test_ng_plus.py`, 18 passed):

| Test Class | Coverage |
| --- | --- |
| `TestNGPlusFields` (5) | unlock/active defaults + independence |
| `TestPillar4Compliance` (3) | no meta_state write, doesn't persist across resets, no stat boost |
| `TestNGPlusBehavior` (2) | locked cannot be active (stub), unlocked not yet active valid |
| `TestNGPlusUnlockHook` (4) | default locked, unlock pattern after Salvation Epilogue, idempotent, active starts False |
| `TestNGPlusMenuUI` (4) | locked forces active False on confirm, unlocked preserves toggle, N-key toggles when unlocked, N-key noop when locked |
| `TestNGPlusMenuRender` (3) | render smoke tests (locked/unlocked-off/unlocked-on) |

**의도적 제약** (구현 단순화):
- NG+는 *Salvation 완료 후에만 unlock* — 별도 메뉴 unlock 경로 없음
- NG+ 런은 *stat 변경 없음* (unlocks만 유지)
- NG+ difficulty modifier 없음 — Hardcore과 *독립*

**Future extensions** (v1.2.0+ backlog):
- NG+ difficulty scaling (적 HP ×1.5 등)
- NG+ exclusive unlocks (post-Salvation 콘텐츠)
- NG+ counter (몇 회차 NG+ 진행했는지)

## 진행 동기

- **신규 자키 unlock**: 처음 등급의 자키만 사용 가능 → 죽으면 다음 등급 해금
- **데크 업그레이드**: 각 등급마다 새로운 프로그램 슬롯 unlock (Wardrone, Kraken)
- **Construct**: T5 만 Dixie construct 동행 가능

## 구현 위치

| 요소 | 파일 |
|---|---|
| PPL 계산 | `src/wet_run/matrix/ppl.py:42-57` |
| Status 결정 | `src/wet_run/matrix/zdr.py:84-100` |
| 메타 진행 | `src/wet_run/engine/death.py:220-267` (restart_with_new_jockey) |
| 등급 곡선 | `design/systems/grade-progression.md` |
| 제작 티어 | `src/wet_run/programs/` + `data/crafting/` |
| **Deck Size** (Phase 15) | `src/wet_run/combat/deck_building.py:15-99` (DeckSize, DECK_SIZES) |
| **Deck Size UI** | `src/wet_run/engine/menu.py:DECK_SELECT` (Phase 15) |
| **State.field** | `src/wet_run/engine/state.py:222` (`deck_size: str = "standard"`) |

## 미래 작업 (Phase 6+)

- **Persistent unlocks**: 자키 도감을 Hall of Dead 에서 영구 보존
- **Custom deck editor**: 런 시작 전 데크 슬롯 자유 조합
- **Achievement 보상**: 특정 조건 달성 시 추가 티어 unlock

---

## Phase 19 Audit Trail (2026-08-13)

Phase 19 audit 결과 — Deck Size Selection (Phase 15, ADR-0178) 가 Tier 1 표에 누락되어 본 섹션 1.1 로 추가.

### 추가된 섹션

- **Section 1.1**: Deck Size Selection — 3 템플릿 (LIGHT 6 / STANDARD 8 / HEAVY 10).

### 검증 위치

- `src/wet_run/combat/deck_building.py` — `DeckSize` / `DECK_SIZES` / `get_deck_size` / `get_deck_sizes` 4 API.
- `src/wet_run/engine/state.py:222` — `deck_size: str = "standard"` AppState 필드.
- `src/wet_run/engine/menu.py` — DECK_SELECT 화면 (Phase 15 통합 진입).

### 변경 영향

- **Tier 1 표**: `Deck size` 행 *추가* (기존 Deck tier / Programs / Wetware / Construct / HP&ATK 와 동일 결정 시점).
- **PPL 공식**: *unchanged* — Deck size 는 *슬롯 수* 만 변경, PPL 계산과 직교.
- **Cross-reference**: [decisions/0178-deck-building.md](../../decisions/0178-deck-building.md), [design/systems/combat.md ## Deck Size Selection](combat.md).

### 의도적 비-변경

- NG+ lifecycle (Section "NG+ 라이프사이클") — unchanged.
- Hardcore Mode (death-restart.md ## 6.5) — unchanged.
- 등급 곡선 (grade-progression.md) — unchanged.