"""오리지널 Sprawl Jockey story (ADR-0022, ADR-0031).

3명의 오리지널 주인공 + 단편 챕터 + 2개 엔딩 골격.
character_select → chapter (단편 인용) → prologue (per-character) → ending A/B.

References:
    design/scenario/README.md
    design/scenario/chapter-1-novice.md
    design/scenario/chapter-2-veteran.md
    design/scenario/chapter-3-heretic.md
    data/story/chapters/{case,sil,kas}.json
    ../../../Fiction/derivative/sprawl-trilogy/short-stories/2026-06-20_*.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .npc_event import ChoiceEffect, DialogueChoice, DialogueLine, NPCEvent

if TYPE_CHECKING:
    from ..audio.config import SoundConfig

CHAPTER_INFO: dict[str, dict[str, str]] = {
    "novice": {
        "character": "novice",
        "id": "chapter_novice",
        "title_en": "The First Jack",
        "title_ko": "첫 잭인",
        "portrait": "art:case",
        "theme": "matrix_rain",
        "json_file": "case.json",
    },
    "veteran": {
        "character": "veteran",
        "id": "chapter_veteran",
        "title_en": "The Old Score",
        "title_ko": "오래된 의문",
        "portrait": "art:marly",
        "theme": "cyberspace",
        "json_file": "sil.json",
    },
    "heretic": {
        "character": "heretic",
        "id": "chapter_heretic",
        "title_en": "The Declaration",
        "title_ko": "선언",
        "portrait": "art:kumiko",
        "theme": "sense_net",
        "json_file": "kas.json",
    },
}


def get_chapter_info(character: str) -> dict[str, str]:
    """Return chapter info for the chosen character.

    Args:
        character: "novice" | "veteran" | "heretic"

    Returns:
        Dict with keys: id, title_en, title_ko, portrait, theme, json_file
    """
    return CHAPTER_INFO.get(character, CHAPTER_INFO["novice"])


def list_characters() -> list[str]:
    """Return all character ids in novice/veteran/heretic order."""
    return ["novice", "veteran", "heretic"]


# ============================================================================
# Character Selection
# ============================================================================

CHARACTER_SELECT_EVENT = NPCEvent(
    id="character_select",
    npc_name="The Finn",
    npc_name_ko="더 핀",
    npc_portrait="♠F♠",
    description="Choose your jockey",
    description_ko="자키를 선택하세요",
    lines=[
        DialogueLine(
            speaker="The Finn",
            speaker_ko="더 핀",
            text="I need a jockey. Sense/Net, first run, simple data extraction. ICE is light. Wisp-class, maybe Hammer.",
            text_ko="자키가 필요해. 센스넷, 첫 실행, 간단한 데이터 추출. ICE는 가벼울 거야. 위스프급, 어쩌면 해머급.",
            portrait="♠F♠",
            choices=[
                DialogueChoice(
                    key="1",
                    text="I'm new. I just need the money.",
                    text_ko="저는 신참이에요. 돈만 필요합니다.",
                    effect=ChoiceEffect.CONTINUE,
                    response="Good. K is your call sign. Don't get cocky.",
                    response_ko="좋아. 케이가 네 콜사인이야. 건방 떨지 마.",
                    log_message="Selected: 케이 (K) — Novice",
                    effect_data={"character": "novice"},
                ),
                DialogueChoice(
                    key="2",
                    text="I've been around. I know the risks.",
                    text_ko="경험은 있어요. 위험도 알고 있고요.",
                    effect=ChoiceEffect.CONTINUE,
                    response="Sil. Good to have a veteran on board. Tessier-Ashpool owes you nothing, remember.",
                    response_ko="실. 베테랑이 합류해줘서 다행이네. 테시에-애스풀은 네게 빚진 게 없어.",
                    log_message="Selected: 실 (Sil) — Veteran",
                    effect_data={"character": "veteran"},
                ),
                DialogueChoice(
                    key="3",
                    text="I'm here to burn it all down.",
                    text_ko="난 다 태우러 왔어.",
                    effect=ChoiceEffect.CONTINUE,
                    response="Kas. Maelcum spoke of you. Don't make him a liar.",
                    response_ko="카스. 멜컴이 자네 얘기를 했어. 그를 사기꾼으로 만들지 마.",
                    log_message="Selected: 카스 (Kas) — Heretic",
                    effect_data={"character": "heretic"},
                ),
            ],
        ),
    ],
)


# ============================================================================
# Common: Jack-In
# ============================================================================


def _make_jackin_line(character: str) -> DialogueLine:
    """Jack-In scene (shared). Different flavor text per character."""
    flavor = {
        "novice": "Case's hands shake on the deck. Wisp T1. Cheap. But it's all you've got.",
        "veteran": "Sil's been here before. Hammer T2. The ICE doesn't know what's coming.",
        "heretic": "Kas's viral isn't a weapon. It's a sermon. \"I cast you out.\"",
    }
    ko_flavor = {
        "novice": "케이의 손이 떨린다. Wisp T1. 싸구려. 하지만 이게 전부다.",
        "veteran": "실은 여기 와본 적이 있다. Hammer T2. ICE가 뭘 올지 모른다.",
        "heretic": '카스의 viral은 무기가 아니다. 설교다. "나는 너를 추방한다."',
    }
    return DialogueLine(
        speaker="",
        speaker_ko="",
        text=f"{flavor.get(character, '')} The Sprawl is hot tonight. You can feel the data streams in your teeth.",
        text_ko=f"{ko_flavor.get(character, '')} 스프롤이 오늘 밤 뜨겁다. 데이터 스트림을 이빨로 느낄 수 있다.",
        portrait="art:cyberspace",
        next_line_index=None,  # End of dialogue (transitions to combat)
    )


def _make_data_extract_line(character: str) -> DialogueLine:
    """Data extraction scene (shared)."""
    flavor = {
        "novice": "You pull the data from the Sense/Net node. It's a list of names. Employee IDs.",
        "veteran": "The data drops into your deck. Names. Dates. The shape of Tessier-Ashpool's payroll.",
        "heretic": "The data is a list of names. Tessier-Ashpool's payroll. You cast it into your Loa channel.",
    }
    ko_flavor = {
        "novice": "센스넷 노드에서 데이터를 꺼낸다. 이름 목록. 직원 ID.",
        "veteran": "데이터가 데크에 떨어진다. 이름. 날짜. 테시에-애스풀의 급여 명세서 형태.",
        "heretic": "데이터는 이름 목록이다. 테시에-애스풀의 급여. 로아 채널에 투사한다.",
    }
    return DialogueLine(
        speaker="",
        speaker_ko="",
        text=f"{flavor.get(character, '')} Nothing you'd normally pay for.",
        text_ko=f"{ko_flavor.get(character, '')} 보통이라면 그런 걸 살 사람은 없다.",
        portrait="",
        next_line_index=None,
    )


# ============================================================================
# Case (Novice) Prologue + Endings
# ============================================================================

NOVICE_PROLOGUE_EVENT = NPCEvent(
    id="prologue_novice",
    npc_name="케이 (K) — Novice",
    npc_name_ko="케이 (K) — 초짜",
    npc_portrait="◉P◉",
    description="The first run",
    description_ko="첫 실행",
    lines=[
        DialogueLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            text="Hey cowboy. You got the data. Now what you gonna do with it?",
            text_ko="어이 카우보이. 데이터 손에 넣었네. 이제 어쩔 건데?",
            portrait="art:dixie",
            choices=[
                DialogueChoice(
                    key="1",
                    text="I burn it. I just wanted the money.",
                    text_ko="태워버릴 거야. 돈만 필요했어.",
                    effect=ChoiceEffect.GOODBYE,
                    response="Smart. The Sprawl has a short memory for those who don't make waves.",
                    response_ko="현명하네. 물결을 일으키지 않는 자들에 대해 스프롤은 금방 잊어버려.",
                    log_message="케이 — 엔딩 A: Jockey Lives (burned data)",
                    effect_data={"ending": "A", "character": "novice"},
                ),
                DialogueChoice(
                    key="2",
                    text="I keep it. I might need it someday.",
                    text_ko="지켜둘 거야. 언젠가 필요할지 모르니까.",
                    effect=ChoiceEffect.GOODBYE,
                    response="Then Finn will find you. Tonight. Maybe sooner.",
                    response_ko="그러면 핀이 자네를 찾을 거야. 오늘 밤. 어쩌면 그보다 더 빨리.",
                    log_message="케이 — 엔딩 B: Jockey Flatlines (kept data)",
                    effect_data={"ending": "B", "character": "novice"},
                ),
            ],
        ),
    ],
)


# ============================================================================
# Sil (Veteran) Prologue + Endings
# ============================================================================

VETERAN_PROLOGUE_EVENT = NPCEvent(
    id="prologue_veteran",
    npc_name="실 (Sil) — Veteran",
    npc_name_ko="실 (Sil) — 베테랑",
    npc_portrait="◆P◆",
    description="The old score",
    description_ko="오래된 의문",
    lines=[
        DialogueLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            text="Sil. I know who you are. I knew Mara. Tessier-Ashpool took her. You know that now.",
            text_ko="실. 넌 누구인지 알아. 나도 마라(Mara)를 알았어. 테시에-애스풀은 그녀를 데려갔지. 이제 알잖아.",
            portrait="art:dixie",
            choices=[
                DialogueChoice(
                    key="1",
                    text="I leak the data. Tessier-Ashpool dies by a thousand cuts.",
                    text_ko="데이터를 폭로한다. 테시에-애스풀은 천 번의 상처로 죽는다.",
                    effect=ChoiceEffect.GOODBYE,
                    response="Revenge. The oldest story in the Sprawl. Make it count.",
                    response_ko="복수. 스프롤에서 가장 오래된 이야기. 의미있게 해.",
                    log_message="실 — 엔딩 A: Jockey Lives (data leaked)",
                    effect_data={"ending": "A", "character": "veteran"},
                ),
                DialogueChoice(
                    key="2",
                    text="I take the contract. Tessier-Ashpool pays well for silence.",
                    text_ko="계약을 받는다. 테시에-애스풀은 침묵에 대해 후하게 값을 치른다.",
                    effect=ChoiceEffect.GOODBYE,
                    response="Then Mara's death is just business. Sprawl respects that, but Tessier-Ashpool won't.",
                    response_ko="그러면 마라의 죽음은 그저 사업이 되네. 스프롤은 그걸 존중하지만, 테시에-애스풀은 그러지 않을 거야.",
                    log_message="실 — 엔딩 B: Jockey Flatlines (took contract)",
                    effect_data={"ending": "B", "character": "veteran"},
                ),
            ],
        ),
    ],
)


# ============================================================================
# Kas (Heretic) Prologue + Endings
# ============================================================================

HERETIC_PROLOGUE_EVENT = NPCEvent(
    id="prologue_heretic",
    npc_name="카스 (Kas) — Heretic",
    npc_name_ko="카스 (Kas) — 이단자",
    npc_portrait="◇K◇",
    description="The declaration",
    description_ko="선언",
    lines=[
        DialogueLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            text="Kas. Maelcum told me you'd come. He says you're the one to break the wheel.",
            text_ko="카스. 멜컴이 자네가 올 거라고 했어. 자네가 바퀴를 부수러 왔다고.",
            portrait="art:dixie",
            choices=[
                DialogueChoice(
                    key="1",
                    text="I cast the data into the Loa network. The Sprawl will hear it.",
                    text_ko="데이터를 로아 네트워크에 투사한다. 스프롤이 들을 거야.",
                    effect=ChoiceEffect.GOODBYE,
                    response="Then the wheel breaks. Or you do. Either way, the Sprawl changes.",
                    response_ko="그러면 바퀴가 부서지네. 아니면 자네가 부서지거나. 어느 쪽이든, 스프롤은 변해.",
                    log_message="카스 — 엔딩 A: Jockey Changes Sprawl (Loa network)",
                    effect_data={"ending": "A", "character": "heretic"},
                ),
                DialogueChoice(
                    key="2",
                    text="I take it for myself. Power corrupts. Always.",
                    text_ko="내 것으로 삼는다. 권력은 부패시켜. 늘 그래왔지.",
                    effect=ChoiceEffect.GOODBYE,
                    response="Then you become what you hate. Tessier-Ashpool made you. Welcome home.",
                    response_ko="그러면 자네가 미워하던 것이 되네. 테시에-애스풀이 자네를 만들었어. 집에 오신 걸 환영해.",
                    log_message="카스 — 엔딩 B: Jockey Silenced (took data)",
                    effect_data={"ending": "B", "character": "heretic"},
                ),
            ],
        ),
    ],
)


# ============================================================================
# Public API
# ============================================================================

ALL_ORIGINAL_EVENTS = (
    CHARACTER_SELECT_EVENT,
    NOVICE_PROLOGUE_EVENT,
    VETERAN_PROLOGUE_EVENT,
    HERETIC_PROLOGUE_EVENT,
)


def get_prologue_for_character(character: str) -> NPCEvent:
    """Return the prologue event for the chosen character."""
    if character == "novice":
        return NOVICE_PROLOGUE_EVENT
    if character == "veteran":
        return VETERAN_PROLOGUE_EVENT
    if character == "heretic":
        return HERETIC_PROLOGUE_EVENT
    return NOVICE_PROLOGUE_EVENT  # Default


# Endings
def get_ending_description(character: str, ending: str) -> str:
    """Return the human-readable description for an ending."""
    endings = {
        ("novice", "A"): "케이가 데이터를 태우고 Sprawl을 떠남. 새로운 자키로 살아남음.",
        ("novice", "B"): "케이가 데이터를 지키려다 Finn의 추적에 당함. Flatline.",
        ("veteran", "A"): "실이 Tessier-Ashpool의 데이터를 폭로. 복수 성공. 새로운 적 생성.",
        ("veteran", "B"): "실이 Tessier-Ashpool의 계약에 응함. 마라의 죽음이 그저 사업이 됨.",
        ("heretic", "A"): "카스가 Loa 네트워크에 선언문 배포. Sprawl 변화 시작.",
        ("heretic", "B"): "카스가 데이터를 자기 것으로 삼음. Tessier-Ashpool이 됨.",
    }
    return endings.get((character, ending), "Unknown ending")


# Theme for each original story scene / game screen (background music)
# Maps screen_kind (ScreenKind value) → theme name
SCENE_THEMES: dict[str, str] = {
    # Screens
    "menu": "finn_office",
    "character_select": "finn_office",
    "hub": "finn_office",
    "cyberspace_browser": "finn_office",
    "cyberspace_map": "finn_office",
    "matrix": "matrix_rain",
    "combat": "industrial",
    "cinematic": "matrix_rain",
    "story": "broadcast",
    "event": "broadcast",
    "npc": "chiba",
    "death": "hammer_alert",
    "death_summary": "loa_drum_fade",
    "hall_of_dead": "loa_channel",
    "jack_out": "loa_drum",
    "reward": "chiba",
    "debrief": "finn_office",
    "settings": "finn_office",
    "help": "finn_office",
    "save_load": "finn_office",
    # Original story prologues
    "prologue_novice": "matrix_rain",
    "prologue_veteran": "cyberspace",
    "prologue_heretic": "sense_net",
    # Graphic novel
    "graphic_novel_menu": "finn_office",
    "graphic_novel": "sense_net",
    "saved_progress": "broadcast",
    "graphic_novel_ending_menu": "broadcast",
    "chapter": "chiba",
    "save_slot_select": "finn_office",
}


def get_theme_for_scene_id(scene_id: str) -> str:
    """Get the background theme for a given scene id.

    Returns the default 'matrix_rain' if scene_id is unknown.
    """
    return SCENE_THEMES.get(scene_id, "matrix_rain")


_screen_theme_tracker: str | None = None


def update_screen_theme(screen_name: str, config: SoundConfig | None = None) -> None:
    """Play the appropriate BGM theme when screen changes.

    Called from app.py _render() on every screen transition.
    Uses a module-level tracker to avoid re-triggering the same theme.
    """
    global _screen_theme_tracker
    if _screen_theme_tracker == screen_name:
        return
    _screen_theme_tracker = screen_name
    if config is None:
        return
    theme_name = get_theme_for_scene_id(screen_name)
    try:
        from ..audio import play_theme as _play_theme

        _play_theme(theme_name, config)
    except Exception:
        pass
