#!/usr/bin/env uv run python
"""Arc Phase Demo — renders arc.json phases with beats using tcod.

Demonstrates Story → Stage → Event → Demo pipeline with actual tcod rendering:
    expanded.json (story beats)
        ↓
    chapter_flow.json (phases)
        ↓
    arc.json (playable events with beats)
        ↓
    phase_view.py (tcod rendering)
        ↓
    Demo playback

Usage:
    uv run python scripts/play_arc_phase.py
    uv run python scripts/play_arc_phase.py --character case --phase 1 --lang en
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console
import tcod.context
import tcod.event

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.chapter_cutscene import load_arc
from wet_run.engine.phase_view import render_arc_phase, tick_arc_phase
from wet_run.i18n import Translator


class PhaseDemoState:
    def __init__(self, arc, chapter_num: int, is_ko: bool, char_delay_ms: float = 30):
        self.arc = arc
        self.chapter_num = chapter_num
        self.is_ko = is_ko
        self.char_delay_ms = char_delay_ms

        self.chapter = arc.chapters[chapter_num - 1]
        self.phase_index = 0
        self.beat_index = 0
        self.typed_chars = 0
        self.beat_elapsed_ms = 0.0
        self.phase_elapsed_ms = 0.0
        self.last_time = time.time()

        self.running = True
        self.advance_beat = False

    @property
    def current_phase(self):
        if self.phase_index >= len(self.chapter.phases):
            return None
        return self.chapter.phases[self.phase_index]

    def tick(self, dt_ms: float) -> bool:
        if not self.current_phase:
            return False

        self.beat_elapsed_ms += dt_ms
        self.phase_elapsed_ms += dt_ms

        new_typed, should_advance = tick_arc_phase(
            self.current_phase,
            self.beat_index,
            self.beat_elapsed_ms,
            self.typed_chars,
            self.char_delay_ms,
        )

        if should_advance:
            self.advance_to_next_beat()
        else:
            self.typed_chars = new_typed

        return self.running

    def advance_to_next_beat(self):
        if not self.current_phase:
            return

        if self.beat_index < len(self.current_phase.beats) - 1:
            self.beat_index += 1
            self.typed_chars = 0
            self.beat_elapsed_ms = 0.0
        elif self.phase_index < len(self.chapter.phases) - 1:
            self.phase_index += 1
            self.beat_index = 0
            self.typed_chars = 0
            self.beat_elapsed_ms = 0.0
        else:
            self.running = False

    def handle_event(self, event: tcod.event.Event) -> bool:
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.KeySym.RETURN:
                self.advance_to_next_beat()
            elif event.sym == tcod.event.KeySym.SPACE:
                if self.current_phase:
                    self.typed_chars = len(self.current_phase.beats[self.beat_index].text_en)
            elif event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.q):
                self.running = False
        return self.running


def run_demo(
    arc,
    chapter_num: int,
    lang: str,
    char_delay_ms: float,
    width: int = 80,
    height: int = 24,
) -> None:
    is_ko = lang == "ko"
    translator = Translator(lang)

    state = PhaseDemoState(arc, chapter_num, is_ko, char_delay_ms)

    with tcod.context.new_terminal(
        width=width,
        height=height,
        title="Arc Phase Demo",
        renderer=tcod.context.RENDERER_SDL2,
    ) as context:
        console = tcod.console.Console(width, height)

        while state.running:
            current_time = time.time()
            dt_ms = (current_time - state.last_time) * 1000
            state.last_time = current_time

            for event in tcod.event.get():
                context.convert_event(event)
                state.handle_event(event)

            state.tick(dt_ms)

            render_arc_phase(
                console,
                state.current_phase,
                state.beat_index,
                state.typed_chars,
                state.beat_elapsed_ms,
                state.phase_elapsed_ms,
                translator,
                char_delay_ms,
            )

            context.present(console, keep_aspect=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Arc Phase Demo with tcod rendering")
    parser.add_argument(
        "--character",
        "-c",
        choices=["case", "sil", "kas"],
        default="case",
        help="Character arc",
    )
    parser.add_argument(
        "--chapter",
        "-ch",
        type=int,
        default=1,
        help="Chapter number (1-5)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        choices=["en", "ko"],
        default="en",
        help="Language",
    )
    parser.add_argument(
        "--char-delay",
        "-d",
        type=float,
        default=30,
        help="Typing delay in ms (default 30)",
    )
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    arc_path = data_dir / "story" / "arcs" / f"{args.character}_arc.json"

    print(f"Loading arc: {arc_path}")
    arc = load_arc(arc_path)

    print(f"Playing Chapter {args.chapter}: {arc.chapters[args.chapter - 1].title_en}")
    print(f"Phases: {len(arc.chapters[args.chapter - 1].phases)}")
    print("Controls: ENTER=next beat, SPACE=skip beat, ESC=exit")

    try:
        run_demo(arc, args.chapter, args.lang, args.char_delay)
    except Exception as e:
        print(f"\nDemo error (tcod may not be available in headless): {e}")
        print("Use scripts/play_arc_chapter.py for console-based demo")


if __name__ == "__main__":
    main()
