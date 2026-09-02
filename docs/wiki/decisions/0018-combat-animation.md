# ADR-0018: Combat Animation (전투 ASCII 애니메이션)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0002 (Pure ASCII), ADR-0003 (RT-MS), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR)

## 컨텍스트

사용자 결정 (2026-06-18):
> "전투는 일반공격과 스킬공격 효과가 대비되도록 아스키 애니메이션을 적용하고 싶어."

요구:
- ASCII 애니메이션
- **일반 공격 vs 스킬 공격** 시각 대비
- Pure ASCII 유지 (ADR-0002)

기존:
- 자동 공격 = "ASCII 깜빡임, 사이드 이동, 데미지 숫자" (ADR-0003)
- 스킬 = "0.5초 효과 (브래킷 변경, 색 변화, 큰 데미지)" (ADR-0003)
- *대비* 명시 X, 디자인 모호

## 결정

### Animation 디자인 원칙

| 원칙 | 설명 |
| --- | --- |
| **대비 (Contrast)** | 일반 ↔ 스킬이 *즉시* 구별 가능 |
| **순간성 (Transient)** | 일반 = 짧고 단발. 스킬 = 길고 드라마틱. |
| **색상 (Color)** | 일반 = 무채색. 스킬 = 프로그램별 색상. |
| **프레임 (Frames)** | 60 FPS 기준. 일반 3 프레임, 스킬 6 프레임. |
| **이징 (Easing)** | 일반 = linear. 스킬 = ease-in-out. |
| **깁슨 톤** | 글리치, ASCII 깨짐, 단절된 빛. |

### Normal Attack (일반 공격)

*짧고 무채색*. 자동 공격 (1 attack / 2초).

**시각**:
```
Frame 1:  ◉P◉         ▲ICE▲
Frame 2:  ◉P◉ >       ▲ICE▲  ← attack line, gray
Frame 3:  ◉P◉         ▲ICE▲  ← back to rest
```

**속성**:
- 3 프레임, 각 80ms = **240ms total**
- 색상: gray `(128, 128, 128)`
- 데미지 숫자: 작게, 흰색
- 사운드: (Phase 7+) 짧은 비프

### Skill Attack (메뉴 스킬)

*길고 색채*. 메뉴로 선택한 강력한 공격.

**시각 (Goliath 예시)**:
```
Frame 1:  ◉P◉         ▲ICE▲
Frame 2:  ◉P◉ ⚔       ▲ICE▲  ← charging
Frame 3:  ◉P◉ ⚔▓▓▓    ▲ICE▲  ← full power
Frame 4:  ◉P◉ ⚔▓▓▓⚡  ▲ICE▲  ← impact
Frame 5:  ◉P◉         ▲.CE▲  ← ICE glitched, -25 HP
Frame 6:  ◉P◉         ▲ICE▲  ← back to rest
```

**속성**:
- 6 프레임, 각 100ms = **600ms total**
- 색상: 프로그램별 (Goliath = magenta)
- 데미지 숫자: 크게, 노란색
- 화면 흔들림 (1-2 픽셀) — 200ms
- 사운드: (Phase 7+) 더 긴 호

### Skill 종류별 애니메이션

| Program | Type | Animation | Color |
| --- | --- | --- | --- |
| **Goliath** | Attack | `⚔▓▓▓ ⚡ →▶` | magenta |
| **Kraken** | Attack | `⚔▓▓▓▓▓▓ ☠ →▶` | red |
| **Hammer** | Attack | `⚔▓▓ →▶` | yellow |
| **Virus** | Attack | `☣☣☣ ☣→` | green |
| **Worm** | Attack | `~>> ~>> ~>>` | yellow |
| **Wisp** | Defense | `+ + + shield` | cyan |
| **Wardrone** | Defense | `[counter] ⚔→` | cyan |
| **Shield** | Defense | `[ ▓▓▓ ] block` | blue |
| **Watchdog** | Detect | `? ? ? reveal` | yellow |
| **Probe** | Detect | `?PRB? flash` | yellow |
| **Hellhound** | Track | `>>> TRACK <<<` | red |

### Hit/Miss Feedback

**Hit (명중)**:
```
Frame N:  ·✦· damage ·✦·  ← sparkle, color flash
Frame N+1: -25 ← damage number floats up
```

**Miss (회피)**:
```
Frame N:  / /  ← side-step
Frame N+1: MISS
```

**Critical (치명타, Black ICE 등)**:
```
Frame N:  ███ CRITICAL ███  ← red flash
Frame N+1: ✦✦✦ -50 ✦✦✦
```

### Player Damage (자키 피격)

*짧고 강렬한 빨간 플래시*.

```
Frame 1:  ◉P◉         ▲ICE▲  ← rest
Frame 2:  ◉P◉ ←hit    ▲ICE▲  ← damage line, red
Frame 3:  ◉Px          ▲ICE▲  ← glitched, -HP
Frame 4:  ◉P◉         ▲ICE▲  ← recovered
```

**속성**:
- 4 프레임, 각 60ms = 240ms
- 색상: red `(255, 0, 64)`
- 화면 흔들림
- HP 바 색 변화 (녹→황→적)

### Death (flatline)

*느리고 긴*. Pillar 3의 무게.

```
Frame 1:  ◉P◉
Frame 2:  ◉Px
Frame 3:  ◉/x
Frame 4:  ◉_x
Frame 5:  .Xx
Frame 6:  XX.
Frame 7:  X
[pause 1s]
"FLATLINE. Static. Silence."
```

**속성**:
- 7 프레임, 각 200ms + 1s pause = **2.4s total**
- 색상: red → dark_red
- 화면 fade
- 메시지: "FLATLINE. Static. Silence."

### 화면 효과

**Screen shake (강한 피격)**:
- 1-2 픽셀, 100-200ms, 빠르게 진동

**Screen flash (치명타)**:
- 1 프레임 전체 흰색 → 사라짐

**Matrix glitch (Black ICE 등장)**:
- 200ms, 화면 전체 글리치 (랜덤 문자)

## 결과 (Consequences)

### Pillar 정합

- **P1 (The Run)**: 한 전투의 *리듬* — 자동 공격은 *반복적*, 스킬은 *드라마틱*.
- **P2 (The Matrix)**: cyberspace 안의 *데이터 충돌*을 ASCII로 표현. Pillar 2 정합.
- **P3 (The Flatline)**: 죽음 애니메이션 = *느리고 길게*. 무게 표현.
- **P4 (The Build)**: 프로그램별로 *고유한* 애니메이션. 도구 차별화.
- **P5 (The Style)**: 깁슨 cyberpunk 미학. 글리치, ASCII 깨짐, 단절.

### 기존 ADR 영향

- **ADR-0002 (Pure ASCII)**: 보강. ASCII 애니메이션 = *움직이는 ASCII art*.
- **ADR-0003 (RT-MS)**: 시각 효과 명세 보강.
- **ADR-0011 (Portraits)**: 애니메이션 중 portrait *변형* (글리치, 손상).

### 디자인 영향

- **`design/systems/animations.md`** (신규) — 애니메이션 시스템 명세
- **`design/systems/combat.md`** (확장) — 전투에 애니메이션 명세 통합
- **`testcases/systems/animations.md`** (신규) — TC-ANIM-001~008
- **`data/animations/frames.json`** (신규) — 프레임 정의 데이터

### 구현 영향 (Phase 6+)

- `engine/animations.py` (신규) — `Animation`, `AnimationPlayer`, `play_animation(console, frame_seq, ...)`
- `engine/combat.py` 확장 — 공격/스킬 발동 시 애니메이션 트리거
- `data/animations/frames.json` (신규) — 프레임 데이터
- 60 FPS 게임 루프 (기존, ADR-0001)

### Phase 5 범위

- **문서 + 데이터만**: JSON + design 명세
- **구현 없음**: Phase 6+

### Phase 6+ 범위

- 애니메이션 플레이어 (60 FPS 프레임 재생)
- 화면 흔들림 / flash
- HP / status 색상 변화
- Death 애니메이션

### Phase 7+ 범위

- 사운드 효과 (선택)
- 사운드 + 애니메이션 sync

## 향후 결정

- 프레임 속도 (60/100/200ms — 튜닝 필요)
- 화면 흔들림 강도
- Hit / miss / critical 비율
- Death 애니메이션 길이
- Animation 취소 (interrupt) 정책
- Sound 통합 시점 (Phase 7+)

## 영향 받는 항목

- `design/systems/animations.md` (신규)
- `design/systems/combat.md` (확장)
- `data/animations/frames.json` (신규)
- `testcases/systems/animations.md` (신규)

## 관련 결정

- ADR-0002 (Accepted) — Pure ASCII
- ADR-0003 (Accepted, Revised) — RT-MS
- ADR-0011 (Accepted) — Portraits
- ADR-0012 (Accepted) — PPL/ZDR

## 변경 이력

- 2026-06-18: Draft 작성

## 결과 (Consequences)

본 ADR은 substance 전부 구현된 상태. 원본 ADR이 참조한 모듈 이름은 split cycle (ADR-0112 / 0144 / 0145) 후 변경됨.

**구현 증거 (2026-08-05)**:
- `combat/effects_vfx_animations.py` (8.8KB) — 14 스킬 애니메이션 generator
- `combat/effects_vfx_cinematics.py` (9.9KB) — ICE intro/death 시퀀스
- `combat/effects_vfx_compose.py` (11.7KB) — CombatEffects + 10 spawn function
- `combat/effects_data.py` (14.7KB) — 12 data class
- `data/animations/frames.json` (4.7KB) — frame 정의

**연관 ADR (이미 Accepted)**:
- ADR-0018 본체 (ASCII 애니메이션, 5-Layer VFX)
- ADR-0112 (effects.py partial split 정당화)
- ADR-0118 (VFX 5-Layer 시스템, ADR-0112 의 후속)
- ADR-0144 (effects.py 데이터 추출)
- ADR-0145 (effects_vfx 3-way split)

ADR-0018 의 contrast (normal vs skill) + Gibson tone (글리치, ASCII 깨짐, 단절된 빛) 디자인 원칙은 effects_vfx_animations.py 의 `critical_hit_animation`, `get_animation_for_effect` 등에서 실현됨.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
