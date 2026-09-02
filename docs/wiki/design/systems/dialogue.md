# System: Dialogue & NPCs (대화 · NPC)

> **관련**: [aftermath.md](./aftermath.md) (전투 후일담), [story-events.md](./story-events.md) (이벤트)
> **구현**: `../../prototype/src/wet_run/engine/npc_event.py`, `npc_view.py`
> **데이터**: `../../design/story/event_dialogues.json` (NPC + dialogue catalog)

## 목적

깁슨 스프롤 세계의 **NPC 시스템** — Fixer, Construct, ICE-intelligence,
Hub bartender 등이 자키와 대화. Pillar 2 ("The Matrix is the only
visual space") 준수 — meatspace 절대 묘사 안 함, 모든 NPC 는 텍스트.

## NPC 5 종 (event_dialogues.json)

| ID | 이름 | 역할 | 원작 캐릭터 |
|---|---|---|---|
| `finn` | The Finn | Fixer (의뢰 브로커) | Julius Deane (NM) |
| `dixie` | Dixie Flatline | Construct 동맹 | McCoy Pauley (NM) |
| `maelcum` | Maelcum | Zion 해적/조종사 | Maelcum (NM) |
| `bartender` | Ninsei Bar Bartender | Hub NPC | Chat interlocutor (NM) |
| `ta_rep` | Tessier-Ashpool Rep | Corporate contact | T-A family (NM) |

깁슨 어휘 + 원작 등장인물 정확히 사용 (AGENTS.md §4).

## Dialogue 구조

각 dialogue entry 의 스키마:

```json
{
  "id": "finn_intro",
  "speaker": "finn",
  "kind": "mission_brief",  // mission_brief | warning | postcombat | intro
  "lines": [
    {
      "speaker": "finn",
      "text": "Welcome to the Sprawl, cowboy. Got a job for you.",
      "text_ko": "스프롤에 온 걸 환영해, 카우보이. 자네 작업을 하나 줘야겠어.",
      "conditions": null
    },
    ...
  ],
  "next": "finn_followup"  // optional: chain to next dialogue
}
```

## 대화 트리거

| 트리거 | 시점 | 의도 |
|---|---|---|
| NPC 메뉴 (N 키) | Hub 에서 | 자유 대화 시작 |
| 미션 브리핑 | 의뢰 수락 직후 | Finn/다른 fixer 가 미션 설명 |
| 미션 완료 | 보상 화면 후 | "잘 했어" 반응 |
| Combat 종료 | 전투 victory/defeat | Dixie/ICE 의 축하/경고 |
| Death | 사망 후 | Dixie 의 마지막 말 (Hall of Dead 진입 전) |
| Ending | Arc 5 finale | 엔딩별 narration |

## Dialogue kinds

5 가지 분류 (ADR-0019 + ADR-0031):

| Kind | 의미 | 위치 |
|---|---|---|
| `mission_brief` | 미션 의뢰 설명 | Hub NPC |
| `warning` | 위험 경고 | Dixie / ICE |
| `postcombat` | 전투 후 결과 | Dixie |
| `intro` | NPC 첫 만남 | 모든 NPC |
| `ending` | 엔딩 narration | Arc 5 |

## Construct 동맹 (Dixie)

`dixie_*` dialogue 들은 자키의 *construct 동맹* 으로 기능:
- 전투 중 힌트 제공 (`dixie_warning`)
- 전투 후 보너스 효과 (`dixie_postcombat`)
- 엔딩 시 운명 결정 (`dixie_ending_a_novice` / `_b_novice`)

> Dixie Flatline 은 McCoy Pauley 의 죽은 construct — 자키가
> ROM 에 저장해둔 *죽은 자의 영혼* (깁슨의 핵심 모티프).

## ICE 의 "대화"

ICE 는 적이지만 일부 dialogue 있음:
- `ice_wisp_intro`: 순찰형, 짧은 감지 메시지
- `ice_hammer_intro`: 공격형, 위협
- `ice_black_intro`: Black ICE, 협박

실제 플레이 시 ICE 는 combat mode 로 진입하지만, 도입부 텍스트는 깁슨 톤 유지.

## 구현 위치

| 요소 | 파일 |
|---|---|
| Dialogue catalog | `design/story/event_dialogues.json` |
| NPC view | `engine/npc_view.py` |
| Event handler | `engine/npc_event.py` |
| Hub dialogue | `engine/hub.py` |
| Death dialogue | `engine/death.py` |
| Aftermath | `engine/story_view.py` |
| i18n (en/ko) | `data/i18n/{en,ko}.json` |

## 데이터 검증

`event_dialogues.json` 의 모든 NPC/dialogue 는 `tools/build_dashboard.py`
로 인덱싱되어 `dashboard/data/story_stats.json` 에 노출.
v0.2.0 부터 3명의 파생 소설 NPC (Case/Marly/Kumiko) 추가됨.

## 미래 작업 (Phase 6+)

- **Branching dialogue**: 선택지에 따라 다른 line 표시
- **Persistent reputation**: NPC 별 평판, 미션 가능 여부 영향
- **Construct bonding**: Dixie 와의 관계도에 따라 unlock
- **Faction dialogue**: Hosaka / Maas / Sense-Net 별 별도 fixer