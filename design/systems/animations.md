# System: Animations (전투/이벤트 ASCII 애니메이션)

> **상위 결정**: `../../decisions/0018-combat-animation.md` (Accepted, Draft)
> **관련**: ADR-0002 (Pure ASCII), ADR-0003 (RT-MS), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR)

## 목적

전투와 이벤트의 *ASCII 애니메이션* 명세. **일반 공격**과 **스킬 공격**이 *대비*되어야 함. Pure ASCII, 깁슨 톤.

> **핵심 원칙**: 일반 = 짧고 무채색. 스킬 = 길고 색채.

## Animation 디자인 원칙

| 원칙 | 설명 |
| --- | --- |
| **대비 (Contrast)** | 일반 ↔ 스킬이 *즉시* 구별 가능 |
| **순간성 (Transient)** | 일반 = 짧고 단발. 스킬 = 길고 드라마틱. |
| **색상 (Color)** | 일반 = 무채색. 스킬 = 프로그램별 색상. |
| **프레임 (Frames)** | 60 FPS 기준. 일반 3 프레임, 스킬 6 프레임. |
| **이징 (Easing)** | 일반 = linear. 스킬 = ease-in-out. |
| **깁슨 톤** | 글리치, ASCII 깨짐, 단절된 빛. |

## Normal Attack (일반 공격)

*짧고 무채색*. 자동 공격 (1 attack / 2초).

### 시각

```
Frame 1 (0ms):    ◉P◉         ▲ICE▲
Frame 2 (80ms):   ◉P◉ >       ▲ICE▲  ← attack line
Frame 3 (160ms):  ◉P◉         ▲ICE▲  ← back to rest
```

### 속성

- 3 프레임, 각 80ms = **240ms total**
- 색상: gray `(128, 128, 128)`
- 데미지 숫자: 작게, 흰색 `-5`
- 사운드: (Phase 7+) 짧은 비프

## Skill Attack (메뉴 스킬)

*길고 색채*. 메뉴로 선택한 강력한 공격.

### 시각 (Goliath 예시)

```
Frame 1 (0ms):    ◉P◉         ▲ICE▲
Frame 2 (100ms):  ◉P◉ ⚔       ▲ICE▲  ← charging
Frame 3 (200ms):  ◉P◉ ⚔▓▓▓    ▲ICE▲  ← full power
Frame 4 (300ms):  ◉P◉ ⚔▓▓▓ ⚡  ▲ICE▲  ← impact
Frame 5 (400ms):  ◉P◉         ▲.CE▲  ← ICE glitched
Frame 6 (500ms):  ◉P◉         ▲ICE▲  ← back to rest
```

### 속성

- 6 프레임, 각 100ms = **600ms total**
- 색상: 프로그램별 (Goliath = magenta)
- 데미지 숫자: 크게, 노란색 `-25`
- 화면 흔들림 (1-2 픽셀) — 200ms
- 사운드: (Phase 7+) 더 긴 호

## Skill 종류별 애니메이션

| Program | Type | Animation | Color | Tier |
| --- | --- | --- | --- | --- |
| **Goliath** | Attack | `⚔▓▓▓ ⚡ →▶` | magenta | T3 |
| **Kraken** | Attack | `⚔▓▓▓▓▓▓ ☠ →▶` | red | T5 |
| **Hammer** | Attack | `⚔▓▓ →▶` | yellow | T2 |
| **Virus** | Attack | `☣☣☣ ☣→` | green | T2 |
| **Worm** | Attack | `~>> ~>> ~>>` | yellow | T2 |
| **Wisp** | Defense | `+ + + shield` | cyan | T1 |
| **Wardrone** | Defense | `[counter] ⚔→` | cyan | T4 |
| **Shield** | Defense | `[ ▓▓▓ ] block` | blue | T1 |
| **Watchdog** | Detect | `? ? ? reveal` | yellow | T1 |
| **Probe** | Detect | `?PRB? flash` | yellow | T1 |
| **Hellhound** | Track | `>>> TRACK <<<` | red | T3 |

### Kraken (T5) — 극적 효과

```
Frame 1:  ◉P◉           ▲ICE▲
Frame 2:  ◉P◉ ⚔▓▓▓▓▓▓  ▲ICE▲  ← mass charging
Frame 3:  ◉P◉ ⚔▓▓▓▓▓▓☠ ▲ICE▲  ← kraken sigil
Frame 4:  ◉P◉ ⚔▓▓▓▓▓▓☠⚡▲ICE▲ ← impact
Frame 5:  ◉P◉           █ICE█  ← ICE BLACK (glitched)
Frame 6:  ◉P◉           ▲ICE▲  ← back
```

## Hit / Miss / Critical Feedback

### Hit (명중)

```
Frame N:  ·✦· damage ·✦·  ← sparkle, color flash
Frame N+1: -25 ← damage number floats up
```

### Miss (회피)

```
Frame N:  / /  ← side-step
Frame N+1: MISS
```

### Critical (치명타, Black ICE 등)

```
Frame N:  ███ CRITICAL ███  ← red flash
Frame N+1: ✦✦✦ -50 ✦✦✦
```

## Player Damage (자키 피격)

*짧고 강렬한 빨간 플래시*.

```
Frame 1 (0ms):    ◉P◉         ▲ICE▲
Frame 2 (60ms):   ◉P◉ ←hit    ▲ICE▲  ← damage line, red
Frame 3 (120ms):  ◉Px          ▲ICE▲  ← glitched
Frame 4 (180ms):  ◉P◉         ▲ICE▲  ← recovered
```

### 속성

- 4 프레임, 각 60ms = 240ms
- 색상: red `(255, 0, 64)`
- 화면 흔들림
- HP 바 색 변화 (녹→황→적)

## Death (flatline)

*느리고 긴*. Pillar 3의 무게.

```
Frame 1 (0ms):    ◉P◉
Frame 2 (200ms):  ◉Px
Frame 3 (400ms):  ◉/x
Frame 4 (600ms):  ◉_x
Frame 5 (800ms):  .Xx
Frame 6 (1000ms): XX.
Frame 7 (1200ms): X
[pause 1000ms]
"FLATLINE. Static. Silence."
```

### 속성

- 7 프레임, 각 200ms + 1s pause = **2.4s total**
- 색상: red → dark_red
- 화면 fade
- 메시지: "FLATLINE. Static. Silence."

## ICE 격파

*빠른 페이드아웃*.

```
Frame 1:  ▲ICE▲        (rest)
Frame 2:  ▲.CE▲        ← glitched
Frame 3:  ▲_E_▲        ← dissolving
Frame 4:  . _ .         ← fading
Frame 5:  . . .         ← gone
[Data Salvage 메뉴 표시]
```

## 화면 효과 (Screen Effects)

### Screen shake (강한 피격)

- 1-2 픽셀, 100-200ms
- 빠르게 진동

### Screen flash (치명타)

- 1 프레임 전체 흰색 → 사라짐
- 강렬한 명중

### Matrix glitch (Black ICE 등장)

- 200ms, 화면 전체 글리치
- 랜덤 ASCII 문자, 깁슨 톤

## 데이터 구조

### `data/animations/frames.json`

```json
{
  "normal_attack": {
    "id": "normal_attack",
    "name": "Normal Attack",
    "frames": [
      {"at": 0, "console": [["◉P◉", " ", "▲ICE▲"]]},
      {"at": 80, "console": [["◉P◉", ">", "▲ICE▲"]], "color": [128, 128, 128]},
      {"at": 160, "console": [["◉P◉", " ", "▲ICE▲"]]}
    ],
    "duration_ms": 240,
    "color": [128, 128, 128]
  },
  "goliath_attack": {
    "id": "goliath_attack",
    "name": "Goliath",
    "frames": [
      {"at": 0, "console": [["◉P◉", " ", " ", "▲ICE▲"]]},
      {"at": 100, "console": [["◉P◉", "⚔", " ", "▲ICE▲"]], "color": [255, 0, 255]},
      {"at": 200, "console": [["◉P◉", "⚔▓▓▓", " ", "▲ICE▲"]], "color": [255, 0, 255]},
      {"at": 300, "console": [["◉P◉", "⚔▓▓▓", "⚡", "▲ICE▲"]], "color": [255, 0, 255]},
      {"at": 400, "console": [["◉P◉", " ", " ", "▲.CE▲"]], "color": [255, 0, 0]},
      {"at": 500, "console": [["◉P◉", " ", " ", "▲ICE▲"]]}
    ],
    "duration_ms": 600,
    "color": [255, 0, 255],
    "screen_shake": 2,
    "shake_duration_ms": 200
  },
  "kraken_attack": {
    "id": "kraken_attack",
    "name": "Kraken",
    "frames": [
      {"at": 0, "console": [["◉P◉", " ", "▲ICE▲"]]},
      {"at": 100, "console": [["◉P◉", "⚔▓▓▓▓▓▓", "▲ICE▲"]], "color": [255, 0, 0]},
      {"at": 200, "console": [["◉P◉", "⚔▓▓▓▓▓▓☠", "▲ICE▲"]], "color": [255, 0, 0]},
      {"at": 300, "console": [["◉P◉", "⚔▓▓▓▓▓▓☠", "⚡▲ICE▲"]], "color": [255, 0, 0]},
      {"at": 400, "console": [["◉P◉", " ", "█ICE█"]], "color": [255, 0, 0]},
      {"at": 500, "console": [["◉P◉", " ", "▲ICE▲"]]}
    ],
    "duration_ms": 600,
    "color": [255, 0, 0],
    "screen_shake": 3,
    "screen_flash": true
  }
}
```

## Pillar 정합

- **P1 (The Run)**: 한 전투의 *리듬* — 자동 공격은 *반복적*, 스킬은 *드라마틱*.
- **P2 (The Matrix)**: cyberspace 안의 *데이터 충돌*을 ASCII로 표현. Pillar 2 정합.
- **P3 (The Flatline)**: 죽음 애니메이션 = *느리고 길게*. 무게 표현.
- **P4 (The Build)**: 프로그램별로 *고유한* 애니메이션. 도구 차별화.
- **P5 (The Style)**: 깁슨 cyberpunk 미학. 글리치, ASCII 깨짐, 단절.

## 구현 가이드 (Phase 6+)

### `engine/animations.py`

```python
@dataclass(frozen=True, slots=True)
class Frame:
    at_ms: int
    console: list[list[str]]  # multi-row, multi-col
    color: tuple[int, int, int] | None = None

@dataclass(frozen=True, slots=True)
class Animation:
    id: str
    name: str
    frames: tuple[Frame, ...]
    duration_ms: int
    color: tuple[int, int, int] = (255, 255, 255)
    screen_shake: int = 0
    screen_flash: bool = False

class AnimationPlayer:
    def __init__(self, console: Console): ...
    def play(self, anim: Animation, x: int, y: int) -> None:
        """Play an animation centered at (x, y)."""
```

### `engine/combat.py` 확장

```python
def on_normal_attack(console: Console, x: int, y: int) -> None:
    anim = AnimationRegistry.get("normal_attack")
    AnimationPlayer(console).play(anim, x, y)

def on_skill_attack(console: Console, program: Program, x: int, y: int) -> None:
    anim = AnimationRegistry.get(f"{program.id}_attack")
    AnimationPlayer(console).play(anim, x, y)
```

## Phase 범위

### Phase 5 (현재)

- **문서 + 데이터만**: JSON + design 명세

### Phase 6+

- 애니메이션 플레이어 (60 FPS 프레임 재생)
- 화면 흔들림 / flash
- HP / status 색상 변화
- Death 애니메이션

### Phase 7+

- 사운드 효과 (선택)
- 사운드 + 애니메이션 sync

## 향후 결정

- 프레임 속도 (60/100/200ms — 튜닝 필요)
- 화면 흔들림 강도
- Hit / miss / critical 비율
- Death 애니메이션 길이
- Animation 취소 (interrupt) 정책

## 관련 문서

- `decisions/0018-combat-animation.md` — ADR
- `decisions/0003-combat-system.md` — RT-MS
- `decisions/0011-ascii-portraits.md` — Portraits
- `decisions/0060-dungeon-exploration-redesign.md` — Dungeon (Phase 1-2)
- `decisions/0061-novel-integration-architecture.md` — Novel (Phase 5)
- `design/systems/combat.md` — 전투 시스템
- `design/systems/exploration.md` — Dungeon/BSP
- `testcases/systems/animations.md` — TC-ANIM 시나리오

---

## Phase 1.5 확장 (ADR-0060) — Cinematic VFX 4종

전투 시각 효과 시스템 (`combat/effects.py`) 은 Phase 1.5 에서
**4 종 시네마틱 스포너** 를 추가했습니다. 모두 첫 번째 위치 인자가
`CombatEffects` 컨테이너.

```python
from wet_run.combat.effects import CombatEffects
from wet_run.combat.effects import (
    spawn_jackin_glitch, spawn_room_flash,
    spawn_data_acquired, spawn_jackout_whiteout,
)

fx = CombatEffects()

spawn_jackin_glitch(fx)     # JAC-IN — 글리치 + 슬로모션
spawn_room_flash(fx)        # ICE 처치 — 단색 짧은 플래시
spawn_data_acquired(fx)     # DATA 픽업 — 파티클 + 시네마틱
spawn_jackout_whiteout(fx)  # JAC-OUT — 백색 폭발 + 시네마틱
```

| Spawner | 트리거 | 레이어 | 효과 |
|---|---|---|---|
| `spawn_jackin_glitch` | JAC-IN / 미션 시작 | JACKING | 글리치 글리프 burst + 16ms 슬로모션 |
| `spawn_room_flash` | ICE 처치 / 룸 클리어 | FX | 단색 짧은 플래시 (~80ms) |
| `spawn_data_acquired` | DATA 노드 픽업 | DATA | 파티클 + `>> DATA FRAGMENT RECOVERED` 시네마틱 |
| `spawn_jackout_whiteout` | JAC-OUT / EXIT 도달 | JACKING | 백색 폭발 + `>> JACKING OUT...` 시네마틱 |

`CombatEffects` 는 5-Layer 구조 (hit / skill / ICE / status / cinematic)
를 가지며, 각 spawner 가 적절한 레이어에 기록합니다.
`has_active_effects()` 로 활성 여부 확인.

**관련 데모**:
```bash
PYTHONPATH=src .venv/bin/python scripts/play_vfx_overlay.py
```
