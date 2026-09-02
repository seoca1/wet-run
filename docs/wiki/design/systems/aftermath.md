# System: Combat Aftermath & Subtitles (전투 후일담 & 자막)

> **상위 결정**: `../../decisions/0019-combat-aftermath-subtitles.md` (Accepted, Draft)
> **관련**: ADR-0009 (Story), ADR-0010 (i18n), ADR-0013 (Events), ADR-0014 (Data Salvage), ADR-0017 (Mission), ADR-0018 (Animation)

## 목적

중요한 전투 종료 시 *에필로그* (후일담) + *소설 인물 반응* 표시. 모든 이벤트 메시지는 *한글 자막* 형식 (en + ko). Pillar 5 (The Style) — 깁슨 톤, cinematic 몰입감.

> **핵심**: "사이버펑크는 *읽는* 장르다" — 깁슨의 가장 큰 미덕은 *묘사*. 게임도 그러해야.

## Combat Aftermath (전투 후일담)

### 4단계 중요도

| Level | 트리거 | 길이 | 표시 |
| --- | --- | --- | --- |
| `minor` | 일반 ICE 격파 | — | 표시 X (즉시 매트릭스 복귀) |
| `notable` | 강 ICE / 다중 격파 | 1-2 문장 | 짧은 snippet |
| **`major`** | **Black ICE / Construct 격파** | **2-3 문단** | **풀 snippet + character reaction** |
| `legendary` | Named boss (3Jane, etc.) | 4+ 문단 + multiple reactions | Special ending hook |

### 트리거 (Trigger) 종류

```python
class AftermathTrigger:
    COMBAT_DEFEAT_BLACK_ICE = "combat.defeat.black_ice"
    COMBAT_DEFEAT_CONSTRUCT = "combat.defeat.construct"
    COMBAT_DEFEAT_NAMED = "combat.defeat.named"  # e.g., "Asp Model 3"
    COMBAT_RATIO_EXTREME = "combat.ratio.extreme"  # PPL/ZDR > 3.0
    ZONE_FIRST_TIME_CORE = "matrix.zone.core_first_time"
    ZONE_FIRST_TIME_TA = "matrix.zone.ta_first_time"
    MISSION_COMPLETE_FIRST = "mission.complete.first"
    MISSION_COMPLETE_ARC = "mission.complete.arc"
```

### 표시 흐름

```
[전투 종료: ICE 격파, importance = major]
  ↓
[Data Salvage 메뉴 (ADR-0014) — 시간 정지]
  ↓
[선택 후]
  ↓
[Aftermath 표시 — 4-6초]
  |
  > [Aftermath]
  > ────────────────────────
  > Somewhere in the matrix, the Black ICE's
  > last packet dissolves. The construct that
  > housed it — a memory of someone's cruelty —
  > flickers. Static. Silence.
  > 
  > You have a moment of vertigo. Then it's gone.
  > 매트릭스 어딘가에서, 블랙 ICE의 마지막 패킷이
  > 흩어진다. 그것을 담고 있던 구성체 — 누군가의
  > 잔혹함에 대한 기억 — 이 깜빡인다. 정적. 침묵.
  > ────────────────────────
  ↓
[Character Reaction 표시 — 3-4초]
  |
  > [Dixie Flatline]
  > ◊D◊
  > "야, 잘 했어. 근데 조심해 — 그건 그냥
  > sentry였어. T-A가 더 큰 거 가지고 있어."
  > ────────────────────────
  ↓
[Hub 복귀]
```

## Character Reactions (소설 인물 반응)

### 7명의 캐릭터 (원작 + 톤)

| Character | 원작 | 톤 | Portrait |
| --- | --- | --- | --- |
| `dixie` | Neuromancer — Dixie Flatline (ROM construct) | 기술적, 비꼬는, ROM | `◊D◊` cyan |
| `finn` | Neuromancer — The Finn (fixer) | 비즈니스, 간결 | `♠F♠` magenta |
| `molly` | Neuromancer — Molly Millions (razor girl) | 직접적, 강렬 | `X_X` red |
| `case` | Neuromancer — Case (console cowboy) | 내성적, 피로 | `◉P◉` green |
| `3jane` | Neuromancer/MLO — 3Jane (Tessier-Ashpool) | 차가움, 미스터리 | `▲▲J▲▲` white |
| `maelcum` | Neuromancer — Maelcum (Zionite) | 철학적, 평온 | `◯M◯` yellow |
| `slick_henry` | MLO — Slick Henry (artist) | 예술적, 호기심 | `★H★` magenta |

### 캐릭터 말투 가이드 (Gibson 톤)

**Dixie** (ROM construct, 약간 비꼬는):
> "야, 잘 했어. 근데 그건 그냥 sentry였어. 본체는 T-A Straylight 어딘가에 — 훨씬 더러운 코드."
- 짧은 문장, 기술 용어, 비꼬는 유머

**Finn** (fixer, 비즈니스):
> "5-up. Standard. Don't make a habit of it. The market's saturated with cowboy types."
- 거래 관점, 간결, dry

**Molly** (razor girl, 직접적):
> "Black ICE. Nice. T-A's gonna notice. Move fast."
- 짧고 강렬, 명령조

**Case** (console cowboy, 내성적):
> "Your hands are shaking. The deck's warm. You jack out, and the shaking doesn't stop."
- 자기성찰, 감각 묘사, 길고 느린 문장

**3Jane** (T-A heir, 차가움):
> "I see you. The construct I sent was a test. The next will not be."
- aristocratic, minimal, 위협

**Maelcum** (Zionite, 철학적):
> "The matrix is vast. You are small. But the small can dream, and the dream is not small."
- 평온, 시적, 자연 비유

**Slick Henry** (artist, 호기심):
> "A Black ICE? I'd like to paint that. The data it ate, the construct it killed — beautiful, in a way."
- 예술적, 미적, slightly creepy

## Immersive Subtitles (한글 자막)

### 표시 형식

**Stack (en + ko, 두 줄)**:
```
> You jack in. The world goes gray.
> 잭인. 세계가 회색이 된다.
```

**Fade alternate (한 줄씩)**:
```
> You jack in. The world goes gray.
  (1초 후)
> 잭인. 세계가 회색이 된다.
```

**Phase 5+ 권장**: Stack 형식 (영화 자막처럼). 글리치/페이드 효과는 Phase 7+.

### 색상

- 영어: 흰색 `(255, 255, 255)` — 원본 톤, dominant
- 한글: 노란색-주황 `(255, 220, 100)` — 의역, 살짝 dim

### 적용 범위

| 화면 | 자막 적용? | 이유 |
| --- | --- | --- |
| **Combat Aftermath** | ✓ | 몰입감 핵심 |
| **Story Events (ADR-0013)** | ✓ | narrative 부분만 |
| **Mission briefings** | ✓ | 픽서 dialogue |
| **Hub 픽서 dialogue** | ✓ | construct 말풍선 |
| **News / Story Archive** | ✓ | 뉴스/이야기 |
| HUD 수치 (PPL, ZDR, HP) | ✗ | 시스템 메시지 |
| 메뉴 라벨 | ✗ | 시스템 메시지 |
| Combat log (데미지 숫자) | ✗ | 빠른 읽기 필요 |

### i18n 키 구조 (ADR-0010 확장)

`data/i18n/en.json`:
```json
{
  "aftermath": {
    "black_ice_v1": {
      "narrative": "Somewhere in the matrix, the Black ICE's last packet dissolves. ...",
      "reaction_dixie": "야, 잘 했어. 근데 조심해 — 그건 sentry였어. ..."
    }
  }
}
```

`data/i18n/ko.json`:
```json
{
  "aftermath": {
    "black_ice_v1": {
      "narrative": "매트릭스 어딘가에서, ...",
      "reaction_dixie": "야, 잘 했어. 근데 조심해 — ..."
    }
  }
}
```

`data/story/aftermath.json` (구조):
```json
{
  "aftermath_black_ice": {
    "id": "aftermath_black_ice",
    "importance": "major",
    "trigger": "combat.defeat.black_ice",
    "duration_ms": 5000,
    "narrative_en": "Somewhere in the matrix...",
    "narrative_ko": "매트릭스 어딘가에서...",
    "reactions": ["dixie_react_black_ice", "case_react_black_ice"]
  }
}
```

`data/story/reactions.json`:
```json
{
  "dixie_react_black_ice": {
    "id": "dixie_react_black_ice",
    "character": "dixie",
    "text_en": "야, 잘 했어. 근데 조심해 — ...",
    "text_ko": "야, 잘 했어. 근데 조심해 — ...",
    "portrait": "construct.dixie"
  }
}
```

## 데이터 구조 (전체)

### `data/story/aftermath.json`

```json
{
  "aftermath_black_ice": {
    "id": "aftermath_black_ice",
    "importance": "major",
    "trigger": "combat.defeat.black_ice",
    "duration_ms": 5000,
    "narrative_en": "Somewhere in the matrix, the Black ICE's last packet dissolves. The construct that housed it — a memory of someone's cruelty — flickers. Static. Silence.\n\nYou have a moment of vertigo. Then it's gone.",
    "narrative_ko": "매트릭스 어딘가에서, 블랙 ICE의 마지막 패킷이 흩어진다. 그것을 담고 있던 구성체 — 누군가의 잔혹함에 대한 기억 — 이 깜빡인다. 정적. 침묵.\n\n잠시 현기증이 찾아온다. 그리고 사라진다.",
    "reactions": ["dixie_react_black_ice", "case_react_black_ice"]
  },
  "aftermath_construct_first": {
    "id": "aftermath_construct_first",
    "importance": "legendary",
    "trigger": "combat.defeat.construct.first",
    "duration_ms": 7000,
    "narrative_en": "...",
    "narrative_ko": "...",
    "reactions": ["dixie_react_construct", "3jane_react_intrusion"]
  }
}
```

### `data/story/reactions.json`

```json
{
  "dixie_react_black_ice": {
    "id": "dixie_react_black_ice",
    "character": "dixie",
    "trigger": "combat.defeat.black_ice",
    "text_en": "야, 잘 했어. 근데 조심해 — 그건 그냥 sentry였어. T-A가 더 큰 거 가지고 있어.",
    "text_ko": "야, 잘 했어. 근데 조심해 — 그건 그냥 sentry였어. T-A가 더 큰 거 가지고 있어.",
    "portrait": "construct.dixie"
  },
  "finn_react_mission_first": {
    "id": "finn_react_mission_first",
    "character": "finn",
    "trigger": "mission.complete.first",
    "text_en": "First jack, eh. Don't make a habit of dying. The Finn pays for results, not for funerals.",
    "text_ko": "첫 잭이야, 어. 죽는 데 익숙해지지 마. The Finn은 결과를 사고, 장례식이 아니라.",
    "portrait": "construct.finn"
  }
}
```

## Pillar 정합

- **P1 (The Run)**: 후일담 = 한 런의 *의미* 부여. 무게 강화.
- **P2 (The Matrix)**: 후일담은 매트릭스 안의 *데이터*. Pillar 2 정합.
- **P3 (The Flatline)**: 후일담은 *승리의 보상* (Pillar 3 일부 완화, ADR-0014와 정합).
- **P4 (The Build)**: 메타 진행과 별개. *서사*의 강화.
- **P5 (The Style)**: 깁슨 톤, 소설 어휘, cinematic 자막 — *가장 직접적* Pillar 5 표현.

## 구현 가이드 (Phase 6+)

### `story/aftermath.py`

```python
from dataclasses import dataclass
from enum import StrEnum

class Importance(StrEnum):
    MINOR = "minor"
    NOTABLE = "notable"
    MAJOR = "major"
    LEGENDARY = "legendary"

@dataclass(frozen=True, slots=True)
class Aftermath:
    id: str
    importance: Importance
    trigger: str
    duration_ms: int
    narrative_en: str
    narrative_ko: str
    reaction_ids: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class CharacterReaction:
    id: str
    character: str
    trigger: str
    text_en: str
    text_ko: str
    portrait: str

class AftermathRegistry:
    def __init__(self, aftermaths: dict[str, Aftermath],
                 reactions: dict[str, CharacterReaction]): ...
    def get_for_trigger(self, trigger: str) -> Aftermath | None: ...
    @classmethod
    def load(cls, aftermath_path: Path, reactions_path: Path) -> AftermathRegistry: ...
```

### `story/subtitles.py`

```python
def render_subtitle(
    console: Console,
    x: int, y: int,
    text_en: str,
    text_ko: str,
    *,
    en_color: tuple[int, int, int] = (255, 255, 255),
    ko_color: tuple[int, int, int] = (255, 220, 100),
) -> None:
    """Render an en + ko subtitle stack at (x, y)."""
    console.print(x=x, y=y, string=f"> {text_en}", fg=en_color)
    console.print(x=x, y=y + 1, string=f"> {text_ko}", fg=ko_color)
```

### `engine/combat.py` 확장

```python
def on_combat_victory(console, state, player, importance) -> None:
    # 1. Data Salvage (ADR-0014)
    ...
    # 2. Aftermath (ADR-0019)
    if importance in (Importance.MAJOR, Importance.LEGENDARY):
        aftermath = AftermathRegistry.get_for_trigger(state.last_trigger)
        if aftermath:
            render_aftermath(console, aftermath)
    # 3. Hub 복귀
```

## Phase 범위

### Phase 5 (현재)

- **데이터 + 문서만**: JSON + ADR + design/testcases
- **UI 없음**

### Phase 6+

- Aftermath 렌더링 (Combat 종료 후, Hub 복귀 전)
- Character reaction 표시 (portrait + 자막)
- 자막 모드 기본 활성화 (이벤트 화면)
- Story Archive 통합 (aftermath 저장)

### Phase 7+

- 사운드 (목소리 톤)
- 자막 타이핑 효과
- 비주얼 노이즈 / 글리치

## 향후 결정

- 후일담 표시 시간 (3초? 5초? 사용자 조절?)
- 자막 페이드인/아웃 속도
- 캐릭터 음성 매칭 (Dixie = glitched, Finn = smoky)
- Legendary 트리거 (어떤 적이 *legendary*?)
- Story Archive 통합 정책 (aftermath 영구 저장?)

## 관련 문서

- `decisions/0019-combat-aftermath-subtitles.md` — ADR
- `decisions/0009-story-news-system.md` — Story Archive
- `decisions/0010-i18n-content-pipeline.md` — i18n
- `decisions/0013-story-events.md` — Story Events
- `decisions/0014-data-salvage.md` — Data Salvage
- `design/systems/combat.md` — Combat
- `design/systems/i18n.md` (향후)
- `testcases/systems/aftermath.md` — TC-AFTER 시나리오
