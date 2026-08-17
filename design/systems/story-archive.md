# System: Story Archive (이야기 아카이브)

> **관련**: [aftermath.md](./aftermath.md) (전투 후일담), [story-events.md](./story-events.md) (이벤트), `engine/jockey_history.py` (자키 이력)
> **구현**: `../../prototype/src/wet_run/engine/story_view.py`, `event_story.py`
> **ADR**: 0009 (Story/News 전달 시스템), 0019 (Combat Aftermath), 0031 (Original Scenario)

## 목적

자키가 경험한 **모든 이야기의 영구 기록** — 전투 후일담, 이벤트,
엔딩, 미션 브리핑 로그. Pillar 5 ("Mediated World") 핵심 구현.

깁슨 톤: meatspace 는 절대 보이지 않음. **모든 외부 세계는 텍스트/뉴스/이야기로만** 전달.

## Story Archive 의 5 종류

| 종류 | 트리거 | 위치 |
|---|---|---|
| Aftermath | 전투 종료 | `story_view.py` |
| Event | NPC/Construct 만남 | `event_story.py` |
| Mission Brief | 미션 수락 | `event_dialogues.json` |
| Ending | Arc 5 finale | `chapter_view.py` |
| Cinematic | 챕터/그래픽 노블 | `chapter_cutscene.py` |

## 데이터 구조

```python
@dataclass
class StoryArchive:
    entries: list[StoryEntry]

@dataclass
class StoryEntry:
    id: str
    kind: StoryKind  # aftermath / event / brief / ending / cinematic
    arc: int  # 1..5
    timestamp_ms: int
    importance: StoryImportance  # minor / major / critical / ending
    title: str
    text_en: str
    text_ko: str
    characters_involved: list[str]  # NPC IDs
    mission_id: str | None
    session_id: str  # run ID
```

## Importance Levels (ADR-0019)

| Level | 효과 |
|---|---|
| **MINOR** | 단순 로그, 사이드 패널에만 |
| **MAJOR** | 풀스크린 표시 + 사이드 패널 |
| **CRITICAL** | 모달 표시, ENTER 필수 |
| **ENDING** | 엔딩 시퀀스, 메뉴 잠금 |

## Reactions 시스템 (7명 NPC)

전투 후 / 사망 시 7명이 *reactions.json* 에서 무작위 응답:

```json
{
  "characters": {
    "finn": {
      "victory": ["Good work, cowboy.", "You came back. I bet."],
      "death": ["Shit. ...", "I'll find another."]
    },
    "dixie": {...},
    "case": {...},
    "molly": {...},
    "wintermute": {...},
    "bartender": {...},
    "construct": {...}
  }
}
```

깁슨 어휘 정확: Finn = fixer, Dixie = construct, Case = Neuromancer.

## Hall of Dead (ADR-0040)

`engine/jockey_history.py` 가 사망한 자키를 영구 보존:

```python
@dataclass
class JockeyRecord:
    jockey_id: str  # UUID
    name: str
    character_id: str  # novice/veteran/heretic
    grade: int
    cause_of_death: str  # "Combat" / "ICE breach" / "Jack-out failure"
    mission_id: str
    survived_ms: int
    credits_at_death: int
    inventory_snapshot: dict
    timestamp_iso: str
```

→ 사망한 자키는 `data/jockeys/deceased.json` 에 atomic 저장.

## Cinematic System (chapter_cutscene.py)

챕터 / 엔딩 표시 시스템:

```
ChapterData → CutsceneRef → SceneData (graphics_novel 호환)
    ↓
typing 효과 (30ms/char) + fade transitions + 챕터 카드 (I-XII)
    ↓
ENDING 표시 후 SAVED_PROGRESS 화면
```

## Story Statistics (Dashboard)

`tools/build_dashboard.py` 가 다음을 자동 집계:

- 총 story lines (`prologue_data.json` + `chapter_data.json`)
- NPC 별 등장 횟수 (`event_dialogues.json`)
- 평균 후일담 길이 (`aftermath.json`)
- 엔딩 분포 (A/B/C × 캐릭터 × arc)

→ `dashboard/story.html` / `stories.html` / `play.html` 에 자동 반영.

## 구현 위치

| 요소 | 파일 |
|---|---|
| StoryArchive | `engine/story_view.py` |
| EventStory | `engine/event_story.py` |
| Aftermath | `data/story/aftermath.json` |
| Reactions | `data/story/reactions.json` |
| Event Dialogues | `design/story/event_dialogues.json` |
| Jockey History (Hall of Dead) | `engine/jockey_history.py` |
| Atomic 저장 | `data/jockeys/deceased.json` |
| Cinematic Engine | `engine/chapter_cutscene.py` |

## 미래 작업 (Phase 6+)

- **News feed**: 자키의 모험이 *Sprawl BBS* 에 글로 올라감
- **Persistent across runs**: 사망해도 일부 엔트리는 보존
- **Player-curated archive**: 플레이어가 직접 중요 엔트리 표시
- **Export to markdown**: 자키의 이야기를 파일로 export