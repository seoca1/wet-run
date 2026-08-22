# System: Jockey Avatar (자키 아바타 — 스탯 시각화)

> **상위 결정**: `../../decisions/0016-jockey-avatar.md` (Accepted, Draft)
> **관련**: ADR-0002 (Pure ASCII), ADR-0008 (Progression), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR), ADR-0014 (Data Salvage)

## 목적

자키의 *현재 상태*를 **스틱 피규어 아바타**로 *한눈에* 표현. *수치를 읽는* 대신 *모양을 보는* stat 시각화. Pillar 1 (The Run), 5 (The Style) 정합.

> **깁슨 톤**: 자키 = 사람. 도구 = 팔다리. 데크 = 몸통. 손상 = *몸이 글리치함*. 죽음 = `X`.

## 아바타 해부

5-7행 ASCII 스틱 피규어. *부위별* stat 표현.

```
행 1:  ◉P◉       <- 머리 (HP 무결성)
행 2:  /|\        <- 몸통 (Status 자세)
행 3: ★W★:H:|P:   <- 프로그램 팔 (3 슬롯)
행 4:  ║DK7║     <- 데크 (Tier)
행 5:  ▓▓▓▓      <- 웨웨어 (Tier)
행 6: ◆D◆        <- Construct (있으면 echo)
```

## HP 표현 — 머리 무결성

머리의 *모양*이 HP 비율을 나타냄. 자키의 *육체적 상태*가 곧 데크의 무결성.

| HP 비율 | 모양 | 색상 | 의미 |
| --- | --- | --- | --- |
| 100% | `◉P◉` | green | 완전 무결 |
| 75% | `◉P·` | yellow-green | 약간 손상 |
| 50% | `◉P/` | yellow | 글리치, 기울어짐 |
| 25% | `◉Px` | red | 거의 flatline |
| 0% | `X` | dark_red | dead (flatline) |

**색상 변화**: HP가 떨어질수록 머리가 *붉어짐*. Pillar 3 시각 강화.

## Programs 표현 — 팔 슬롯

각 program이 *한 팔* 슬롯. 최대 3개 (또는 4-6 슬롯, Pillar 4 결정). *등급*이 *두께*로, *소진*이 *테두리*로 표현.

### 등급 (Tier) — 두께

| Tier | 모양 | 의미 |
| --- | --- | --- |
| T5 | `★W★` | starred, 전설 (Kraken-tier) |
| T4 | `▓W▓` | filled, 강력 (Wardrone-tier) |
| T3 | `\|W\|` | double border, 고급 (Goliath-tier) |
| T2 | `:W:` | single border, 일반 (Hammer-tier) |
| T1 | `·W·` | faded, 기본 (Wisp-tier) |

**W** = program ID 첫 글자 (W=Wisp, H=Hammer, G=Goliath, K=Kraken, P=Probe, S=Shield).

### 상태 — 테두리

| 상태 | 모양 | 의미 |
| --- | --- | --- |
| 활성 | 위 grade 마커 (예: `\|W\|`) | 사용 가능 |
| 소진 | `~W~` (일회용 후) | 비활성 |
| 비어있음 | `   ` (공백) | 슬롯 비어있음 |
| 잠김 | `═══` | 메타 진행 미도달 (Phase 6+) |

## Status Pose — 전체 자세

PPL/ZDR 비율에 따라 *몸통* 자세가 변함. 즉각적 시각 피드백.

| Status | 자세 | 의미 |
| --- | --- | --- |
| SAFE | `◉P◉ /|\ \|/` | 직립, 압도적 |
| MATCH | `◉P· /|\ \|/` | 직립 (살짝 기운) |
| TOUGH | `◉P/ /|\ \|/` | 약간 웅크림 |
| DEADLY | `◉Px /\ \/` | 엎드림, 글리치 |
| FUTILE | `◉Px .\ /.` | 흐릿하게 깜빡임, 깨짐 |

**자세의 단계적 변화**: SAFE → MATCH → TOUGH → DEADLY → FUTILE로 갈수록 자세가 *낮아지고 깨짐*.

## Deck & Wetware — 뿌리

- **Deck** (몸통/허리): `║DK7║` (숫자 = tier)
  - `DK4` = T4 deck (Ono-Sendai 7)
  - `DK5` = T5 deck
  - `DK0` = deck 없음 (불가능, Pillar 1)
- **Wetware** (다리): `▓▓▓▓` (filled cells, tier에 비례)
  - T1: `▓` (1칸)
  - T2: `▓▓` (2칸)
  - T3: `▓▓▓` (3칸)
  - T4: `▓▓▓▓` (4칸)
  - T5: `▓▓▓▓▓` (5칸)
- **Construct** (주변 echo, 있으면):
  - Dixie: `◆D◆`
  - Loa: `◯L◯`
  - 3Jane: `▲▲J▲▲`

## 전체 Avatar 예시

### 풀 로드아웃 (PPL 25, HP 100%)

```
═══════════════════════════════════════
  ◉P◉         <- Head (100% HP, green)
  /|\
 ★W★:H:|P:    <- 3 programs (T5, T2, T3)
  \|/
 ╔═══╗
 ║DK7║        <- T4 deck
 ╚═══╝
  ▓▓▓▓        <- T4 wetware
◆D◆            <- Dixie construct (echo)
═══════════════════════════════════════
PPL: 25  HP: 100%  Status: SAFE
```

### 손상 (50% HP, TOUGH)

```
═══════════════════════════════════════
  ◉P/         <- Head tilted (50% HP, yellow)
  /|\
 ·W·:H:|P:    <- Wisp depleted (~W~ or ·W·)
  \|/
 ╔═══╗
 ║DK7║
 ╚═══╝
  ▓▓▓▓
◆D◆
═══════════════════════════════════════
PPL: 25  HP: 50%  Status: TOUGH
```

### 위기 (25% HP, 1 program lost)

```
═══════════════════════════════════════
  ◉Px         <- Head critical (25% HP, red)
  /|\
    :H:|P:    <- Wisp LOST (empty slot)
  \|/
 ╔═══╗
 ║DK7║
 ╚═══╝
  ▓▓▓▓
◆D◆
═══════════════════════════════════════
PPL: 17  HP: 25%  Status: DEADLY
```

## Data Salvage 통합 (ADR-0014)

### HEAL 효과 — 머리 무결성 회복

```
HEAL before:           HEAL after (+20%):
  ◉P/                   ◉P·    <- head recovered
  /|\                   /|\
 ·W·:H:|P:             ·W·:H:|P:
```

머리가 *기울어짐*에서 *정상*으로. 자세도 TOUGH → MATCH.

### FRAG — 부위 강화 (Phase 6+)

- T1 program 획득 시: 빈 슬롯 → `·W·` 채움
- T5 program 획득 시: 기존 슬롯 → `★W★` 교체

### SKIP — 변화 없음

아바타 그대로. 보상 없음.

## 사망 (Pillar 3)

```
═══════════════════════════════════════
   X         <- flatline (0% HP, dark_red)
  /|\
 ·W·:H:|P:
  \|/
 ╔═══╗
 ║DK7║
 ╚═══╝
  ▓▓▓▓
═══════════════════════════════════════
FLATLINE. Static. Silence.
```

*머리*가 `X`로 바뀌고, construct echo가 사라짐. 데크/웨웨어는 *잔해*로 남음 (시각적 강조).

## Pillar 정합

- **P1 (The Run)**: 자키 = *한 사람*의 무게. 아바타가 자키의 *현재*를 보여줌.
- **P2 (The Matrix)**: 아바타는 cyberspace 안의 *자키 representation*. meatspace 인물 묘사 X.
- **P3 (The Flatline)**: 0% HP = `X` (flatline), 시각적으로 명확.
- **P4 (The Build)**: *장비 변경*이 아바타 *시각적 변화*로 표현. 등급 시각화.
- **P5 (The Style)**: 깁슨 cyberpunk aesthetic, monospace, ASCII art.

## 구현 가이드 (Phase 6+)

### `engine/avatar.py`

```python
from dataclasses import dataclass
from ..matrix.ppl import calculate_ppl
from ..matrix.zdr import calculate_status, node_status, node_zdr
from ..matrix.zdr import Status

@dataclass(frozen=True, slots=True)
class Avatar:
    head: str  # "◉P◉", "◉P·", "◉P/", "◉Px", "X"
    body: str  # "/|\\", "/\\", etc.
    programs: tuple[str, ...]  # 3 program slots
    deck: str  # "║DK7║"
    wetware: str  # "▓▓▓▓"
    construct: str | None  # "◆D◆" or None

def render_avatar(
    console: Console,
    x: int,
    y: int,
    player: Player,
    matrix: MatrixGraph | None = None,
    current_node: Node | None = None,
) -> None:
    """Render the avatar at (x, y) based on player state."""
    ...
```

### HP 계산

```python
def head_for_hp(hp: int, max_hp: int) -> tuple[str, tuple[int, int, int]]:
    """Return (head_glyph, color) for current HP ratio."""
    ratio = hp / max_hp if max_hp > 0 else 0
    if ratio > 0.875: return "◉P◉", (0, 255, 0)
    if ratio > 0.625: return "◉P·", (200, 200, 0)
    if ratio > 0.375: return "◉P/", (255, 255, 0)
    if ratio > 0.0:   return "◉Px", (255, 64, 64)
    return "X", (128, 0, 32)
```

### Program 슬롯 렌더링

```python
def program_for_tier(prog: Program | None, depleted: bool = False) -> str:
    """Return program glyph based on tier and state."""
    if prog is None:
        return "   "
    if depleted:
        return f"~{prog.name[0]}~"
    tier_glyph = {
        1: "·", 2: ":", 3: "|", 4: "▓", 5: "★"
    }[prog.tier]
    initial = prog.name[0]
    return f"{tier_glyph}{initial}{tier_glyph}"
```

## Phase 범위

### Phase 5 (현재)

- **문서만**: Avatar 디자인 명세
- **구현 없음**

### Phase 6+

- Avatar 렌더링 (Hub + Matrix)
- HP / Status pose 동적 업데이트
- Program slot 동적 표시
- Tier 시각화 (·W· vs ★W★)
- Data Salvage 통합 (HEAL 효과)
- Construct echo 표시
- 색상 (HP 비율에 따라 머리 색 변화)
- 애니메이션 (글리치, 깜빡임) — Phase 7+

## 향후 결정

- Program 슬롯 수 (3? 4-6? 등급에 따라?)
- Construct echo의 위치 (주변? 옆? 위?)
- 아바타 색상 정책 (HP 색상 외 추가?)
- 아바타 사이즈 (compact 5행 vs detailed 7행)
- 메뉴 화면 표시 여부 (Pillar 2 정합)

## 관련 문서

- `decisions/0016-jockey-avatar.md` — ADR
- `decisions/0002-rendering-style.md` — Pure ASCII
- `decisions/0008-progression-system.md` — Item Tier
- `decisions/0011-ascii-portraits.md` — Portraits
- `decisions/0012-difficulty-rating.md` — PPL/ZDR
- `decisions/0014-data-salvage.md` — Data Salvage (HEAL)
- `design/systems/crafting.md` — Crafting (program 획득)
- `design/systems/combat.md` — Combat (program 손실/소진)
- `testcases/systems/avatar.md` — TC-AVATAR 시나리오
