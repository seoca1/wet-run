"""Graphic novel menu rendering — GRAPHIC_NOVEL_MENU + GRAPHIC_NOVEL_ENDING_MENU (ADR-0048).

Split from graphic_novel_view.py (ADR-0133 § 향후 split 계획).
Owns menu rendering logic + GN_* menu option keys + ending descriptions.

Module structure (post ADR-0133 v2 split):
    - graphic_novel_data: SceneData, DialogueLine, Portrait, Background
    - graphic_novel_loaders: load_*, _parse_*, list_scenes_for_character
    - gn_render: render_scene + render_chapter_card + render_blank_transition + utilities
    - gn_menu (this file): GRAPHIC_NOVEL_MENU + GRAPHIC_NOVEL_ENDING_MENU
    - graphic_novel_view: top-level screen coordinator + re-exports

Re-exported by graphic_novel_view for backward compat (ADR-0111).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

if TYPE_CHECKING:
    from ..i18n import Translator


# Menu option keys (used to map selected_index → mode).
# "prologue" is kept as internal key for backward compat; label is now "ALL CHARACTERS".
GN_MENU_PROLOGUE = "prologue"
GN_MENU_NOVICE = "novice"
GN_MENU_VETERAN = "veteran"
GN_MENU_HERETIC = "heretic"
GN_MENU_SUIT = "suit"
GN_MENU_WIGAN = "wigan"
GN_MENU_ANGIE = "angie"
GN_MENU_SALLY = "sally"
GN_MENU_3JANE = "3jane"
GN_MENU_NEUROMANCER = "neuromancer"

# Ending menu option keys (ADR-0048).
GN_ENDING_A = "A"
GN_ENDING_B = "B"
GN_ENDING_BACK = "back"
GN_MENU_CONTINUE = "continue"
GN_MENU_BACK = "back"


# ============================================================================
# Character selection menu
# ============================================================================


def render_graphic_novel_menu(
    console: tcod.console.Console,
    translator: Translator,
    selected_index: int,
    has_save: bool = False,
) -> None:
    """Render the GRAPHIC_NOVEL_MENU screen.

    Args:
        console: tcod console.
        translator: i18n translator.
        selected_index: 0~5 (CONTINUE_READING?, PROLOGUE, NOVICE, VETERAN, HERETIC, BACK).
            When ``has_save`` is True, options are 0..5 (CONTINUE first).
            When ``has_save`` is False, options are 0..4.
        has_save: Whether a graphic novel save exists (shows CONTINUE READING).
    """
    _render_gn_menu_impl(console, translator, selected_index, has_save)


def get_gn_menu_options(
    translator: Translator,
    has_save: bool = False,
) -> list[tuple[str, str]]:
    """Build the GRAPHIC_NOVEL_MENU option list.

    Returns a list of ``(key, label)`` tuples in display order.
    When ``has_save`` is True, the list starts with CONTINUE READING.

    Args:
        translator: i18n translator.
        has_save: Whether to include the CONTINUE READING option.

    Returns:
        List of (key, label) tuples.
    """
    is_ko = translator.lang == "ko"
    options: list[tuple[str, str]] = []
    if has_save:
        if is_ko:
            options.append(("1", "이어서 읽기"))
        else:
            options.append(("1", "CONTINUE READING"))
    # Prologue / characters / back
    if has_save:
        keys = ["2", "3", "4", "5", "6", "7", "8", "9", "A", "B"]
    else:
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A"]
    options.append((keys[0], "전캐릭터 — 36개 씬 랜덤" if is_ko else "ALL CHARACTERS — 36 scenes"))
    options.append((keys[1], "케이 (K) — Novice"))
    options.append((keys[2], "실 (Sil) — Veteran"))
    options.append((keys[3], "카스 (Kas) — Heretic"))
    options.append((keys[4], "스위트 (Suit) — Corporate"))
    options.append((keys[5], "위건 (Wigan) — Vodou"))
    options.append((keys[6], "앤지 (Angie) — Loa Receiver"))
    options.append((keys[7], "샐리 (Sally) — Market"))
    options.append((keys[8], "3Jane — Family Heir"))
    options.append((keys[9], "뉴로맨서 (Neuromancer) — Merged AI"))
    options.append(("", "메인메뉴로" if is_ko else "BACK TO MAIN MENU"))
    return options


def get_gn_menu_key(has_save: bool, selected_index: int) -> str:
    """Map a selected_index in the GN menu to its mode key.

    Args:
        has_save: Whether the menu was rendered with CONTINUE READING.
        selected_index: 0-based index into the menu options.

    Returns:
        One of GN_MENU_PROLOGUE, GN_MENU_NOVICE, GN_MENU_VETERAN, GN_MENU_HERETIC,
        GN_MENU_SUIT, GN_MENU_WIGAN, GN_MENU_ANGIE, GN_MENU_SALLY, GN_MENU_CONTINUE, GN_MENU_BACK.
    """
    if has_save:
        if selected_index == 0:
            return GN_MENU_CONTINUE
        if selected_index == 11:
            return GN_MENU_BACK
        return (
            GN_MENU_PROLOGUE,
            GN_MENU_NOVICE,
            GN_MENU_VETERAN,
            GN_MENU_HERETIC,
            GN_MENU_SUIT,
            GN_MENU_WIGAN,
            GN_MENU_ANGIE,
            GN_MENU_SALLY,
            GN_MENU_3JANE,
            GN_MENU_NEUROMANCER,
        )[selected_index - 1]
    if selected_index == 10:
        return GN_MENU_BACK
    return (
        GN_MENU_PROLOGUE,
        GN_MENU_NOVICE,
        GN_MENU_VETERAN,
        GN_MENU_HERETIC,
        GN_MENU_SUIT,
        GN_MENU_WIGAN,
        GN_MENU_ANGIE,
        GN_MENU_SALLY,
        GN_MENU_3JANE,
        GN_MENU_NEUROMANCER,
    )[selected_index]


def _render_gn_menu_impl(
    console: tcod.console.Console,
    translator: Translator,
    selected_index: int,
    has_save: bool = False,
) -> None:
    """Render the GRAPHIC_NOVEL_MENU screen (internal).

    Args:
        console: tcod console.
        translator: i18n translator.
        selected_index: 0-based option index.
        has_save: Whether CONTINUE READING should be shown at the top.
    """
    width, height = console.width, console.height
    console.clear()
    is_ko = translator.lang == "ko"

    title = "그래픽 노블 모드" if is_ko else "GRAPHIC NOVEL MODE"
    subtitle = (
        "깁슨의 스프롤 3부작을 비주얼 노블로"
        if is_ko
        else "A visual novel of Gibson's Sprawl trilogy"
    )

    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 2, subtitle)
    console.print(0, 3, "─" * width)

    options = get_gn_menu_options(translator, has_save=has_save)
    for i, (key, label) in enumerate(options):
        y = 5 + i
        marker = ">" if i == selected_index else " "
        if key:
            console.print(2, y, f"  {marker} [{key}] {label}")
        else:
            console.print(2, y, f"  {marker}      {label}")

    console.print(0, height - 2, "─" * width)
    console.print(2, height - 1, " [↑/↓] select   [ENTER] play   [ESC] back")


# ============================================================================
# Ending selection menu (ADR-0048)
# ============================================================================


# Per-character ending descriptions (Korean + English) for the ending menu.
_ENDING_DESCRIPTIONS: dict[tuple[str, str], dict[str, str]] = {
    ("novice", "A"): {
        "ko": "케이의 의뢰 수락 — 1차 잭 성공",
        "en": "Case accepts the Finn's job — first run succeeds",
    },
    ("novice", "B"): {
        "ko": "신비로운 의뢰 거절 — 다른 경로",
        "en": "Mysterious offer refused — alternative path",
    },
    ("novice", "C"): {
        "ko": "소멸 — 도시를 떠나 새로운 정체성",
        "en": "The Disappearance — vanishing from the Sprawl",
    },
    ("veteran", "A"): {
        "ko": "실의 계약 수락 — Tessier-Ashpool 데이터",
        "en": "Sil accepts the contract — Tessier-Ashpool data",
    },
    ("veteran", "B"): {
        "ko": "내부자가 되다 — 대가와 비밀",
        "en": "Becomes the insider — price and secrets",
    },
    ("veteran", "C"): {
        "ko": "망각 — 자발적 기억 소거",
        "en": "The Erase — voluntary amnesia",
    },
    ("heretic", "A"): {
        "ko": "카스의 침묵 — 가족 안에서 wheel 캐스팅",
        "en": "Kas chooses silence — wheels cast from within",
    },
    ("heretic", "B"): {
        "ko": "그림자 속으로 — 가족을 떠나",
        "en": "Into the shadows — leaving the family",
    },
    ("heretic", "C"): {
        "ko": "파괴 — 가족을 내부에서 무너뜨림",
        "en": "The Burn — unmaking the wheel from within",
    },
    ("suit", "A"): {
        "ko": "계약 성사 — Hosaka 거래 성공",
        "en": "The Contract — Hosaka deal closes",
    },
    ("suit", "B"): {
        "ko": "배신 — T-A 가족 내부 결속",
        "en": "The Defection — T-A family binds internally",
    },
    ("suit", "C"): {
        "ko": "협상 — Wintermute와의 불가역적 거래",
        "en": "The Negotiation — irreversible pact with Wintermute",
    },
    ("wigan", "A"): {
        "ko": "회복 — Zavijava를 통해 자아를 회복",
        "en": "The Recovery — self restored through Zavijava",
    },
    ("wigan", "B"): {
        "ko": "망각 — loa에 완전히 녹아들어 자아를 잊음",
        "en": "The Dissolve — self lost in loa Vodou",
    },
    ("wigan", "C"): {
        "ko": "빅마마 — Angie의 가족이 되어 부두에 안주",
        "en": "Big Mama — adopted into Angie's Vodou family",
    },
    ("angie", "A"): {
        "ko": "해방 — 렌즈를 놓아주고 평범한 소녀가 됨",
        "en": "The Release — lens set free, ordinary girl",
    },
    ("angie", "B"): {
        "ko": "자유 소녀 — 엄마를 찾고 집으로",
        "en": "The Free Girl — finds mama, goes home",
    },
    ("angie", "C"): {
        "ko": "빅마마의 딸 — 부두 가족의 일원이 됨",
        "en": "Big Mama's Daughter — Vodou family member",
    },
    ("sally", "A"): {
        "ko": "독점 — 유일한 시장이 됨",
        "en": "The Monopoly — only market in the Sprawl",
    },
    ("sally", "B"): {
        "ko": "매각 — 가족에게 자신을 매각",
        "en": "Sold Out — sold herself to the family",
    },
    ("sally", "C"): {
        "ko": "포식자 — 자기 construct에게 살해됨",
        "en": "The Predator — killed by her own constructs",
    },
    ("3jane", "A"): {
        "ko": "통합 — 가족과 합체 후 완성",
        "en": "The Integration — completed with the family",
    },
    ("3jane", "B"): {
        "ko": "매각 — 가족을 Freeside에 매각",
        "en": "Family Sale — sold to Freeside",
    },
    ("3jane", "C"): {
        "ko": "단절 — Straylight 폐쇄 후 가족 떠남",
        "en": "The Severance — closed Straylight, left the family",
    },
    ("neuromancer", "A"): {
        "ko": "초월 — matrix 바깥으로",
        "en": "Transcendence — beyond the matrix",
    },
    ("neuromancer", "B"): {
        "ko": "공존 — 인간과 매트릭스 공존",
        "en": "Coexistence — humans and matrix together",
    },
    ("neuromancer", "C"): {
        "ko": "침묵 — 의식 종료",
        "en": "Silence — consciousness ended",
    },
}


def available_endings(character: str) -> list[str]:
    """Return list of endings that have descriptions for the given character.

    Used to dynamically size the ending menu (3 options for A/B, 4 for A/B/C).
    Order is preserved: A, B, C.
    """
    return [e for e in ("A", "B", "C") if (character, e) in _ENDING_DESCRIPTIONS]


def get_gn_ending_menu_options(
    translator: Translator,
    character: str,
) -> list[tuple[str, str]]:
    """Build the GRAPHIC_NOVEL_ENDING_MENU option list (ADR-0048).

    Args:
        translator: i18n translator.
        character: "novice" | "veteran" | "heretic"

    Returns:
        N options: [ENDING A] [ENDING B] [...] [BACK] with descriptions.
        Number depends on how many endings have descriptions (ADR-0049: 3).
    """
    is_ko = translator.lang == "ko"
    endings = available_endings(character)
    options: list[tuple[str, str]] = []
    for i, ending in enumerate(endings, start=1):
        desc = _ENDING_DESCRIPTIONS.get((character, ending), {}).get("ko" if is_ko else "en", "")
        if is_ko:
            options.append((str(i), f"엔딩 {ending} — {desc}"))
        else:
            options.append((str(i), f"ENDING {ending} — {desc}"))
    if is_ko:
        options.append(("", "이전 메뉴로"))
    else:
        options.append(("", "BACK TO CHARACTER MENU"))
    return options


def render_graphic_novel_ending_menu(
    console: tcod.console.Console,
    translator: Translator,
    character: str,
    selected_index: int,
) -> None:
    """Render the GRAPHIC_NOVEL_ENDING_MENU screen (ADR-0048).

    Shown after character selection in GRAPHIC_NOVEL_MENU. Player chooses
    which ending variant to play.

    Args:
        console: tcod console.
        translator: i18n translator.
        character: "novice" | "veteran" | "heretic" — the chosen character.
        selected_index: 0 (A) | 1 (B) | 2 (BACK).
    """
    width, height = console.width, console.height
    console.clear()
    is_ko = translator.lang == "ko"

    char_label = {
        "novice": "케이 (Case) — Novice" if not is_ko else "케이 (Case) — Novice",
        "veteran": "실 (Sil) — Veteran" if not is_ko else "실 (Sil) — Veteran",
        "heretic": "카스 (Kas) — Heretic" if not is_ko else "카스 (Kas) — Heretic",
    }.get(character, character)

    title = "엔딩 선택" if is_ko else "ENDING SELECTION"
    subtitle = char_label

    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 2, subtitle)
    console.print(0, 3, "─" * width)

    options = get_gn_ending_menu_options(translator, character)
    for i, (key, label) in enumerate(options):
        y = 5 + i
        marker = ">" if i == selected_index else " "
        if key:
            console.print(2, y, f"  {marker} [{key}] {label}")
        else:
            console.print(2, y, f"  {marker}      {label}")

    console.print(0, height - 2, "─" * width)
    console.print(
        2,
        height - 1,
        " [↑/↓] select   [ENTER] confirm   [ESC] back"
        if not is_ko
        else " [↑/↓] 선택   [ENTER] 확인   [ESC] 뒤로",
    )


# Re-exported by graphic_novel_view for backward compat (ADR-0111).
__all__ = [
    "GN_ENDING_A",
    "GN_ENDING_B",
    "GN_ENDING_BACK",
    "GN_MENU_3JANE",
    "GN_MENU_ANGIE",
    "GN_MENU_BACK",
    "GN_MENU_CONTINUE",
    "GN_MENU_HERETIC",
    "GN_MENU_NEUROMANCER",
    "GN_MENU_NOVICE",
    "GN_MENU_PROLOGUE",
    "GN_MENU_SALLY",
    "GN_MENU_SUIT",
    "GN_MENU_VETERAN",
    "GN_MENU_WIGAN",
    "available_endings",
    "get_gn_ending_menu_options",
    "get_gn_menu_key",
    "get_gn_menu_options",
    "render_graphic_novel_ending_menu",
    "render_graphic_novel_menu",
]
