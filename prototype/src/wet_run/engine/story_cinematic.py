"""Cinematic story presentation with typing effects and ASCII animations.

Presents story text in a cinematic way with:
  - Typing effect (character-by-character reveal)
  - Glitch effects (random character substitution)
  - Screen flicker / fade
  - Bilingual subtitles (en + ko)
  - ASCII decorative elements

Used for:
  - Prologue
  - Mission briefings
  - NPC dialogues
  - Story events
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import (
    SoundCategory,
    get_sound_config,
    play_theme,
    safe_play,
    stop_theme,
)
from ..i18n import Translator
from .cinematic_art import AsciiArt, resolve_line_art
from .graphic_novel_view import wrap_text_for_novel
from .input_utils import is_confirm_key
from .layout import (
    Region,
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from .state import AppState

# Typing effect speed (characters per second)
TYPING_SPEED_FAST = 60  # 60 chars/sec
TYPING_SPEED_NORMAL = 30  # 30 chars/sec
TYPING_SPEED_SLOW = 15  # 15 chars/sec

# Glitch effect probability (0.0 to 1.0)
GLITCH_PROBABILITY = 0.05

# Glitch characters (random substitution)
GLITCH_CHARS = "█▓▒░▄▀■□▪▫"


class TextSpeed(StrEnum):
    """Typing speed options."""

    INSTANT = "instant"
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"


class EffectKind(StrEnum):
    """Visual effects for text presentation."""

    NONE = "none"
    GLITCH = "glitch"  # Random character corruption
    FLICKER = "flicker"  # Screen brightness flicker
    FADE_IN = "fade_in"  # Fade from dark
    FADE_OUT = "fade_out"  # Fade to dark


@dataclass(frozen=True, slots=True)
class StoryLine:
    """A single line of story text (bilingual)."""

    text_en: str
    text_ko: str
    speaker: str = ""  # NPC speaker ID (e.g., "finn", "dixie")
    portrait: str = ""  # ASCII portrait (e.g., "♠F♠")
    effect: EffectKind = EffectKind.NONE
    speed: TextSpeed = TextSpeed.NORMAL
    pause_ms: int = 500  # Pause after line (milliseconds)


@dataclass(frozen=True, slots=True)
class StoryScene:
    """A collection of story lines (a scene)."""

    id: str
    title_en: str
    title_ko: str
    lines: tuple[StoryLine, ...]
    next_scene: str | None = None  # Next scene ID, or None to exit
    # Background theme (e.g. "matrix_rain"). When the scene starts,
    # story_cinematic plays this theme (if THEME category is enabled).
    theme: str = "matrix_rain"


@dataclass
class CinematicState:
    """Live state for cinematic presentation."""

    scene: StoryScene
    current_line_index: int = 0
    current_char_index: int = 0
    last_char_time_ms: int = 0
    finished: bool = False
    skip_requested: bool = False
    glitch_active: bool = False
    show_korean: bool = True  # Toggle Korean subtitles
    # Time when the current line finished typing (for pause timing).
    # -1 means "not yet completed".
    line_completed_at_ms: int = -1
    # Background theme currently playing (None if no theme started).
    # Set when the scene starts playing its theme.
    current_theme: str | None = None


def _draw_cinematic_art(
    console: tcod.console.Console,
    main_r: Region,
    art: AsciiArt | None,
    current_line: StoryLine | None,
    art_w: int,
) -> None:
    """Draw the ASCII art on the left side, or fall back to a glyph."""
    if art is not None:
        _draw_ascii_art(
            console,
            x=main_r.x + 2,
            y=main_r.y + 3,
            art=art,
            max_w=art_w,
            max_h=main_r.h - 4,
        )
        return
    # Fallback: use the legacy single-glyph portrait inline.
    if current_line is not None and current_line.portrait:
        console.print(
            x=main_r.x + 2,
            y=main_r.y + 3,
            string=current_line.portrait,
            fg=(0, 255, 255),
        )


def _render_cinematic_lines(
    console: tcod.console.Console,
    main_r: Region,
    scene: StoryScene,
    cinematic_state: CinematicState,
    text_x: int,
    text_w: int,
) -> None:
    """Draw the text-and-Korean-subtitle column for every line up to
    and including the current line.  Returns when the row cursor falls
    off the main region (a soft overflow — the caller doesn't need it).
    """
    y = main_r.y + 2
    for i, line in enumerate(scene.lines):
        if i > cinematic_state.current_line_index:
            break

        # Speaker label
        if line.speaker and line.portrait and not line.portrait.startswith("art:"):
            console.print(
                x=text_x,
                y=y,
                string=f"{line.portrait} {line.speaker.upper()}:",
                fg=(0, 255, 255),
            )
            y += 1
        elif line.speaker and (getattr(line, "portrait", "") or "").startswith("art:"):
            console.print(
                x=text_x,
                y=y,
                string=f">> {line.speaker.upper()}:",
                fg=(0, 255, 255),
            )
            y += 1

        # English text — apply typing effect for the current line.
        text_en = line.text_en
        if i == cinematic_state.current_line_index:
            text_en = _apply_typing_effect(
                text_en,
                cinematic_state.current_char_index,
                line.effect,
                cinematic_state.glitch_active,
            )

        wrapped_en = wrap_text_for_novel(
            text_en,
            width=text_w - 2,
            left_margin=0,
            right_margin=0,
        )
        for line_text in wrapped_en:
            console.print(x=text_x + 2, y=y, string=line_text, fg=(255, 255, 255))
            y += 1

        # Korean subtitle (optional).
        if cinematic_state.show_korean:
            text_ko = line.text_ko
            if i == cinematic_state.current_line_index:
                text_ko = _apply_typing_effect(
                    text_ko,
                    cinematic_state.current_char_index,
                    EffectKind.NONE,  # No glitch on Korean
                    False,
                )
            from .font_loader import is_korean_capable

            if is_korean_capable() and text_ko:
                wrapped_ko = wrap_text_for_novel(
                    text_ko,
                    width=text_w - 2,
                    left_margin=0,
                    right_margin=0,
                )
                for ko_line in wrapped_ko:
                    console.print(
                        x=text_x + 2,
                        y=y,
                        string=ko_line,
                        fg=(255, 220, 100),
                    )
                    y += 1
            elif text_ko:
                console.print(
                    x=text_x + 2,
                    y=y,
                    string=f"[KO: {len(text_ko)} chars]",
                    fg=(180, 180, 100),
                )
                y += 1
        y += 1  # spacing between lines


def _render_cinematic_controls(
    console: tcod.console.Console,
    ctrl_r: Region,
    cinematic_state: CinematicState,
    scene: StoryScene,
) -> None:
    """Draw the controls bar at the bottom — different hint depending on
    whether the player is currently mid-typing, between lines, or the
    scene is finished."""
    if cinematic_state.finished:
        draw_controls(
            console,
            ctrl_r,
            lines=["[Enter/Space] Next line  [ESC] Skip  [Q] Quit"],
        )
        return
    if cinematic_state.current_line_index < len(
        scene.lines
    ) and cinematic_state.current_char_index < len(
        scene.lines[cinematic_state.current_line_index].text_en
    ):
        # Currently typing
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "[Enter/Space] Skip typing & advance  [ESC] Skip scene  [Q] Quit",
            ],
        )
    else:
        # Between lines (auto-pausing)
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "[Enter/Space] Advance  [ESC] Skip scene  [Q] Quit",
            ],
        )


def render_cinematic(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    cinematic_state: CinematicState,
    elapsed_ms: int,
) -> None:
    """Render a cinematic story scene with typing effects and large ASCII art.

    Layout (main region split into two columns):
      - Left ~16 cols: Large ASCII portrait (current speaker)
      - Right: Story text with typing effect + Korean subtitle
    """
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    # Clear and draw dividers
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    scene = cinematic_state.scene

    # Title
    draw_title(
        console,
        title_r,
        title=scene.title_en,
        subtitle=scene.title_ko
        + f"  [{cinematic_state.current_line_index + 1}/{len(scene.lines)}]",
    )

    # Resolve current art (per current line, fallback to scene)
    current_line = (
        scene.lines[cinematic_state.current_line_index]
        if cinematic_state.current_line_index < len(scene.lines)
        else None
    )
    art = resolve_line_art(
        current_line.portrait if current_line else "",
        scene.id,
    )

    # Main area split: art on left, text on right
    art_w = 16
    text_x = main_r.x + art_w + 2
    text_w = main_r.w - art_w - 4

    # Art column.
    _draw_cinematic_art(console, main_r, art, current_line, art_w)

    # Text + Korean subtitle column.
    _render_cinematic_lines(console, main_r, scene, cinematic_state, text_x, text_w)

    # Controls (semi-auto mode)
    _render_cinematic_controls(console, ctrl_r, cinematic_state, scene)

    # Footer
    draw_footer(
        console,
        foot_r,
        text=f"Scene: {scene.id}  |  T+{elapsed_ms / 1000:.1f}s",
    )


def _draw_ascii_art(
    console: tcod.console.Console,
    x: int,
    y: int,
    art: AsciiArt,
    max_w: int = 24,
    max_h: int = 20,
) -> None:
    """Draw a multi-line ASCII art piece in a bounded region.

    Applies a subtle frame around the art and renders with the
    art's color and style.
    """
    # Top frame
    frame_w = min(max_w, art.width + 2)
    console.print(
        x=x,
        y=y,
        string="┌" + "─" * (frame_w - 2) + "┐",
        fg=(art.fg[0] // 2, art.fg[1] // 2, art.fg[2] // 2),
    )

    # Apply style-based color modulation
    fg = art.fg
    if art.style.value == "glitch":
        # Random color variation
        random.seed(y)
        if random.random() < 0.3:
            fg = (255, 0, 0)
    elif art.style.value == "ghost":
        # Faded (50% color)
        fg = (art.fg[0] // 2, art.fg[1] // 2, art.fg[2] // 2)
    elif art.style.value == "static":
        # Grayscale
        gray = (art.fg[0] + art.fg[1] + art.fg[2]) // 3
        fg = (gray, gray, gray)

    # Draw art lines
    for i, line in enumerate(art.lines):
        if i + 2 >= max_h - 1:
            break
        # Center the line within the frame
        line_clipped = line[: frame_w - 2] if len(line) > frame_w - 2 else line
        console.print(
            x=x + 1,
            y=y + 1 + i,
            string=line_clipped,
            fg=fg,
        )

    # Bottom frame
    bottom_y = y + min(len(art.lines), max_h - 2) + 1
    if bottom_y < y + max_h:
        console.print(
            x=x,
            y=bottom_y,
            string="└" + "─" * (frame_w - 2) + "┘",
            fg=(art.fg[0] // 2, art.fg[1] // 2, art.fg[2] // 2),
        )


def _apply_typing_effect(
    text: str,
    char_index: int,
    effect: EffectKind,
    glitch_active: bool,
) -> str:
    """Apply typing effect and optional glitch to text."""
    if char_index >= len(text):
        revealed = text
    else:
        revealed = text[:char_index]

    # Apply glitch effect
    if effect is EffectKind.GLITCH and glitch_active and char_index < len(text):
        # Random character corruption
        if random.random() < GLITCH_PROBABILITY:
            glitch_char = random.choice(GLITCH_CHARS)
            revealed = revealed[:-1] + glitch_char if revealed else glitch_char

    return revealed


def step_cinematic(cinematic_state: CinematicState, elapsed_ms: int) -> None:
    """Update the cinematic state (typing progression).

    Semi-auto mode:
      - Typing progresses automatically (time-based, per-line speed)
      - Line complete → auto-advance after pause_ms
      - Player can interrupt any time via ENTER/SPACE (handled in
        handle_cinematic_input) to skip current typing or skip
        the pause and go to the next line immediately.
    """
    # Start the scene's theme if not already started
    _maybe_start_theme(cinematic_state)

    if cinematic_state.finished:
        return

    scene = cinematic_state.scene
    if cinematic_state.current_line_index >= len(scene.lines):
        cinematic_state.finished = True
        return

    current_line = scene.lines[cinematic_state.current_line_index]

    # Speed → chars per second
    speed = current_line.speed
    if speed is TextSpeed.INSTANT:
        chars_per_sec = 1000
    elif speed is TextSpeed.FAST:
        chars_per_sec = TYPING_SPEED_FAST
    elif speed is TextSpeed.SLOW:
        chars_per_sec = TYPING_SPEED_SLOW
    else:
        chars_per_sec = TYPING_SPEED_NORMAL

    char_interval_ms = int(1000 / chars_per_sec)

    if elapsed_ms - cinematic_state.last_char_time_ms >= char_interval_ms:
        # Advance chars based on elapsed time
        elapsed_since_last = elapsed_ms - cinematic_state.last_char_time_ms
        chars_to_add = max(1, elapsed_since_last // char_interval_ms)
        cinematic_state.current_char_index += chars_to_add
        cinematic_state.last_char_time_ms = elapsed_ms

        # Play typing sound (throttled to every few chars)
        if chars_to_add >= 3:
            _play_sound("story/text_typing")

    # Glitch toggle (random)
    if current_line.effect is EffectKind.GLITCH:
        if random.random() < 0.1:
            cinematic_state.glitch_active = not cinematic_state.glitch_active

    # Check if current line is fully revealed
    text_len = len(current_line.text_en)
    if cinematic_state.current_char_index >= text_len:
        # Stamp completion time the first time we see the line finished.
        if cinematic_state.line_completed_at_ms < 0:
            cinematic_state.line_completed_at_ms = elapsed_ms
        # After the pause, advance to the next line.
        elif elapsed_ms - cinematic_state.line_completed_at_ms >= current_line.pause_ms:
            _advance_to_next_line(cinematic_state)


def _advance_to_next_line(cinematic_state: CinematicState) -> None:
    """Advance to the next line; mark finished if at end."""
    scene = cinematic_state.scene
    cinematic_state.current_line_index += 1
    cinematic_state.current_char_index = 0
    cinematic_state.last_char_time_ms = 0
    cinematic_state.line_completed_at_ms = -1  # Reset for next line
    cinematic_state.glitch_active = False

    if cinematic_state.current_line_index >= len(scene.lines):
        cinematic_state.finished = True


def handle_cinematic_input(
    event: object,
    state: AppState,
    cinematic_state: CinematicState,
) -> bool:
    """Handle input during a cinematic (semi-auto mode).

    Controls:
        ENTER / SPACE: Advance.
            - If currently typing: instantly complete current line + advance.
            - If between lines (in pause): advance to next line immediately.
            - If on last line: finish the scene.
        ESC: skip the entire scene (jump to end).
        Q: quit the game.
    """
    if not isinstance(event, KeyDown):
        return True

    if event.sym is KeySym.Q:
        return False

    if event.sym is KeySym.ESCAPE:
        # Skip whole scene — jump to end
        _play_sound("ui/menu_cancel")
        _skip_remaining_scene(cinematic_state)
        return True

    if is_confirm_key(event.sym):
        if cinematic_state.finished:
            return True
        # Semi-auto: ENTER/SPACE always advances.
        # 1) If typing in progress: complete the current line instantly.
        # 2) Then advance to next line (skipping the pause).
        # 3) If on the last line, finish the scene.
        scene = cinematic_state.scene
        if cinematic_state.current_line_index < len(scene.lines):
            current_line = scene.lines[cinematic_state.current_line_index]
            # If not fully revealed, complete the current line
            if cinematic_state.current_char_index < len(current_line.text_en):
                _play_sound("story/dialogue_advance")
                cinematic_state.current_char_index = len(current_line.text_en)
                # Mark the line as complete so the next step's pause
                # timing works correctly. Use last_char_time_ms as the
                # "completion time" sentinel.
                cinematic_state.line_completed_at_ms = 0
                return True
            # Otherwise advance to next line
            _play_sound("story/dialogue_advance")
            _advance_to_next_line(cinematic_state)
        return True

    return True


def _skip_remaining_scene(cinematic_state: CinematicState) -> None:
    """Skip all remaining lines in the current scene."""
    cinematic_state.current_line_index = len(cinematic_state.scene.lines)
    cinematic_state.current_char_index = 0
    cinematic_state.finished = True


def _play_sound(sound_name: str) -> None:
    """Play a sound if sound system is available. Silent fallback."""
    safe_play(sound_name)


def _maybe_start_theme(cinematic_state: CinematicState) -> None:
    """Start the scene's background theme if not already playing.

    Idempotent: if the same theme is already running, does nothing.
    If a different theme is needed, stops the old one and starts the new.
    If the scene has no theme, stops any current theme.
    """
    target_theme = cinematic_state.scene.theme
    current_theme = cinematic_state.current_theme

    # If already playing the right theme, do nothing
    if current_theme == target_theme:
        return

    # If THEME category is disabled, don't start any theme
    config = get_sound_config()
    if not config.is_category_enabled(SoundCategory.THEME):
        cinematic_state.current_theme = None
        return

    # Stop old theme (if any)
    if current_theme is not None and current_theme != target_theme:
        stop_theme()

    # Start new theme (or mark None if scene has no theme)
    if target_theme:
        play_theme(target_theme, config)
        cinematic_state.current_theme = target_theme
    else:
        stop_theme()
        cinematic_state.current_theme = None


def stop_scene_theme(cinematic_state: CinematicState) -> None:
    """Stop the current scene's theme. Used when leaving the cinematic."""
    stop_theme()
    cinematic_state.current_theme = None


# ============================================================================
# Canonical Story Scenes (Neuromancer opening + The Finn briefing)
# ============================================================================
# DEPRECATED: These scenes are for demo scripts only.
# They are NOT part of the actual game narrative flow.
# - Gibson text is in: data/story/chapters/{case,sil,kas}.json (NEW RUN chapter)
#   and data/scenes/{character}/*.json (GN scenes)
# - Finn briefing is in: CHARACTER_SELECT_EVENT (original_story.py)
#   which is shown in CHARACTER_SELECT screen before gameplay.
# Demo scripts that use these: full_demo.py, prologue.py, visual_demo.py, etc.
# ============================================================================

PROLOGUE_SCENE = StoryScene(
    id="prologue_sprawl",
    title_en="PROLOGUE: The Sprawl",
    title_ko="프롤로그: 스프롤",
    theme="chiba",  # Gibson's neon Chiba City
    lines=(
        StoryLine(
            text_en="The sky above the port was the color of television, tuned to a dead channel.",
            text_ko="항구 위의 하늘은 텔레비전의 색이었다. 죽은 채널에 맞춰진.",
            speaker="",
            portrait="art:chiba",
            effect=EffectKind.GLITCH,
            speed=TextSpeed.NORMAL,
            pause_ms=1500,
        ),
        StoryLine(
            text_en="It was a great time to be alive, they said. It was a great time to be twenty-one.",
            text_ko="살기에 좋은 시절이라고 했다. 21세에게도 좋은 시절이라고.",
            speaker="",
            portrait="art:chiba",
            effect=EffectKind.NONE,
            speed=TextSpeed.NORMAL,
            pause_ms=1200,
        ),
        StoryLine(
            text_en="The Sprawl. Boston-Atlanta Metropolitan Axis. A chunk of the eastern seaboard that had grown into a continuous urban fabric.",
            text_ko="스프롤. 보스턴-애틀랜타 메트로폴리스 축. 동부 해안선 일부가 끊임없는 도시 직물로 자라난 곳.",
            speaker="",
            portrait="art:cyberspace",
            effect=EffectKind.FADE_IN,
            speed=TextSpeed.SLOW,
            pause_ms=1500,
        ),
        StoryLine(
            text_en="Case was a console cowboy. The best thief in the matrix. Until he tried to steal from the wrong people.",
            text_ko="케이스는 콘솔 카우보이였다. 매트릭스에서 최고로 훌륭한 도둑. 잘못된 사람들로부터 훔치려 하기 전까지는.",
            speaker="",
            portrait="art:case",
            effect=EffectKind.NONE,
            speed=TextSpeed.NORMAL,
            pause_ms=1800,
        ),
        StoryLine(
            text_en="They damaged his nervous system. Made him unable to jack into cyberspace. Left him on the edge of the Sprawl, dying.",
            text_ko="그들은 그의 신경계를 손상시켰다. 사이버스페이스에 접속할 수 없게 만들었다. 스프롤의 가장자리에서 죽어가고 있게 놔뒀다.",
            speaker="",
            portrait="art:glitch",
            effect=EffectKind.GLITCH,
            speed=TextSpeed.SLOW,
            pause_ms=1500,
        ),
        StoryLine(
            text_en="And then a man named Armitage came. With an offer. A chance to jack back in.",
            text_ko="그리고 아미티지라는 이름의 남자가 왔다. 제안을 가지고. 다시 접속할 기회를 가지고.",
            speaker="",
            portrait="art:armitage",
            effect=EffectKind.NONE,
            speed=TextSpeed.NORMAL,
            pause_ms=1500,
        ),
    ),
    next_scene="briefing_finn_first_jack",
)

# DEPRECATED: BRIEFING_FINN_SCENE duplicates CHARACTER_SELECT_EVENT (original_story.py).
# It is kept for demo scripts only. The actual game Finn briefing is in CHARACTER_SELECT.


BRIEFING_FINN_SCENE = StoryScene(
    id="briefing_finn_first_jack",
    title_en="BRIEFING: The Finn",
    title_ko="브리핑: 더 핀",
    theme="finn_office",  # Finn's underground office
    lines=(
        StoryLine(
            text_en="You're standing in The Finn's office. A cramped room in Chiba City, walls lined with old tech and screens.",
            text_ko="당신은 더 핀의 사무실에 서 있다. 치바 시의 좁은 방, 벽에는 오래된 기술과 화면들이 빼곡하다.",
            speaker="",
            portrait="art:finn_office",
            effect=EffectKind.FADE_IN,
            speed=TextSpeed.NORMAL,
            pause_ms=1200,
        ),
        StoryLine(
            text_en='The Finn: "Got a job for you, cowboy. Sense/Net, first run. Simple data extraction."',
            text_ko='더 핀: "자네를 위한 일이 있네, 카우보이. 센스넷, 첫 실행. 간단한 데이터 추출이야."',
            speaker="finn",
            portrait="art:the_finn",
            effect=EffectKind.NONE,
            speed=TextSpeed.NORMAL,
            pause_ms=1200,
        ),
        StoryLine(
            text_en="\"The data's in a construct. You'll need to find it. ICE will be light - Wisp-class, maybe Hammer.\"",
            text_ko='"데이터는 컨스트럭트 안에 있네. 찾아내야 해. ICE는 가벼울 거야 - 위스프급, 어쩌면 해머급."',
            speaker="finn",
            portrait="art:the_finn",
            effect=EffectKind.NONE,
            speed=TextSpeed.NORMAL,
            pause_ms=1200,
        ),
        StoryLine(
            text_en="\"Don't get fancy. Jack in, find the data, jack out. I'll wire the creds when you deliver.\"",
            text_ko='"화려하게 하지 마. 접속하고, 데이터 찾고, 나오게. 배달하면 크레딧 이체하지."',
            speaker="finn",
            portrait="art:the_finn",
            effect=EffectKind.NONE,
            speed=TextSpeed.NORMAL,
            pause_ms=1500,
        ),
        StoryLine(
            text_en="Dixie's voice crackles through the deck: \"Hey cowboy. You and me, we're gonna have some fun.\"",
            text_ko='딕시의 목소리가 데크를 통해 째깍거린다: "어이 카우보이. 당신과 나, 좀 신나게 놀게 될 거야."',
            speaker="dixie",
            portrait="art:dixie",
            effect=EffectKind.GLITCH,
            speed=TextSpeed.NORMAL,
            pause_ms=2000,
        ),
    ),
    next_scene=None,
)
