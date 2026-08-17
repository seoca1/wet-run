"""Graphic novel mode auto-play demo (ADR-0032).

Runs the graphic novel view in auto-pilot mode, cycling through scenes
and dialogue lines. Each dialogue has a duration_ms field; this demo
speeds through them at a configurable pace.

Single command:
    uv run python scripts/graphic_novel.py

Options:
    --duration N      Total seconds (default 60)
    --step-delay D    Seconds per tick (default 0.4)
    --no-clear        Don't clear the screen between frames
    --lang {en,ko}    UI language (default en)
    --mode MODE       Mode: prologue|novice|veteran|heretic (default prologue)
    --seed N          Random seed for prologue shuffle (default 42)
    --speed N         Dialogue speed multiplier (default 10x for demo)
    --with-sound      Play scene sound cues (requires audio system)
    --mute            Mute all sounds
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine import graphic_novel_view
from wet_run.engine.graphic_novel_audio import play_once as play_sound_once
from wet_run.engine.graphic_novel_save import (
    GNProgress,
    GNSaveEmptyError,
    list_save_slots,
    load_gn_progress_slot,
    make_progress,
    save_gn_progress_slot,
)
from wet_run.engine.graphic_novel_view import (
    dialogue_typed_chars,
    load_background,
    load_portrait,
    load_prologue_chain,
    load_scene_chain,
    render_chapter_card,
    render_scene,
)
from wet_run.i18n import Translator

# Chapter card timing (ms)
CHAPTER_CARD_DURATION_MS = 2500  # How long the chapter card stays visible
CHAPTER_CARD_FADE_MS = 600  # Fade-in duration


def _console_to_text(console: tcod.console.Console) -> str:
    """Convert a tcod console buffer to plain text."""
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _print_frame(
    console: tcod.console.Console,
    *,
    clear: bool,
    step: int,
    elapsed: float,
    scene_idx: int,
    total: int,
    dialogue_idx: int,
    dialogue_total: int,
    narration: str,
    phase: str = "scene",
) -> None:
    if clear:
        sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(_console_to_text(console))
    sys.stdout.write("\n")
    phase_label = {
        "scene": "Scene",
        "chapter_card": "ChapterCard",
        "transition": "Transition",
    }.get(phase, phase)
    sys.stdout.write(
        f"[Step {step:03d}  T+{elapsed:5.1f}s  Phase: {phase_label:<14} "
        f"Scene {scene_idx + 1}/{total}  "
        f"Dialogue {dialogue_idx + 1}/{dialogue_total}]\n"
    )
    if narration:
        sys.stdout.write(f"> {narration}\n")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--step-delay", type=float, default=0.4)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--lang", default="en", choices=["en", "ko"])
    parser.add_argument(
        "--mode",
        default="prologue",
        choices=["prologue", "novice", "veteran", "heretic"],
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--speed", type=int, default=10, help="Dialogue speed multiplier")
    parser.add_argument("--with-sound", action="store_true", help="Play scene sound cues")
    parser.add_argument("--mute", action="store_true", help="Mute all sounds")
    parser.add_argument(
        "--no-cards",
        action="store_true",
        help="Skip chapter title cards (no transition between scenes)",
    )
    parser.add_argument(
        "--card-ms",
        type=int,
        default=CHAPTER_CARD_DURATION_MS,
        help=f"Chapter card duration in ms (default {CHAPTER_CARD_DURATION_MS})",
    )
    parser.add_argument(
        "--continue",
        dest="continue_reading",
        action="store_true",
        help="Resume from saved graphic novel progress (ADR-0044)",
    )
    parser.add_argument(
        "--slot",
        type=int,
        default=None,
        choices=[1, 2, 3],
        help="GN save slot to use (1, 2, or 3). If not set, uses --slot 1 by default, or --continue finds the most recent.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save progress on exit (used for demos)",
    )
    parser.add_argument(
        "--ending",
        default="A",
        choices=["A", "B", "C"],
        help="Which ending to play: A (default), B (alternate), or C (third ending, ADR-0049)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    scenes_dir = data_dir / "scenes"
    art_dir = data_dir / "art"

    t = Translator(args.lang, data_dir=data_dir / "i18n")

    # Setup audio (if --with-sound and audio available)
    sound_manager = None
    if args.with_sound and not args.mute:
        try:
            from wet_run.audio.sound_manager import SoundManager

            sound_manager = SoundManager(
                sounds_dir=data_dir / "sounds_test",
                volume=0.2,
            )
            if args.mute:
                sound_manager.muted = True
            print(f"[audio] Sound manager initialized: {sound_manager.is_available()}")
            print(f"[audio] Sounds dir: {sound_manager.sounds_dir}")
        except Exception as e:
            print(f"[audio] Failed to initialize: {e}")
            sound_manager = None

    # Load saved progress FIRST (ADR-0044) — before chain, so mode is correct
    # ADR-0051: multi-slot support via --slot argument
    saved_progress: GNProgress | None = None
    gn_save_dir = project_root / "data" / "saves"
    if args.continue_reading:
        try:
            if args.slot is not None:
                saved_progress = load_gn_progress_slot(args.slot, save_dir=gn_save_dir)
                sys.stdout.write(f"[gn-save] Resuming from slot {args.slot}: ")
            else:
                slots = list_save_slots(save_dir=gn_save_dir)
                filled = [s for s in slots if s.get("has_save", False)]
                if not filled:
                    raise GNSaveEmptyError("No GN save found in any slot")
                # Pick most recent by mtime
                most_recent = max(filled, key=lambda s: s.get("mtime", 0))
                args.slot = most_recent["slot_id"]
                saved_progress = load_gn_progress_slot(args.slot, save_dir=gn_save_dir)
                sys.stdout.write(f"[gn-save] Resuming from slot {args.slot} (most recent): ")
            # Apply saved state: override args.mode so the chain loads correctly
            args.mode = saved_progress.mode
            sys.stdout.write(
                f"mode={args.mode}, ending {saved_progress.ending}, "
                f"scene {saved_progress.scene_index + 1}, "
                f"dialogue {saved_progress.dialogue_index + 1}\n"
            )
        except Exception as e:
            sys.stderr.write(f"[gn-save] Could not load: {e}\n")
            saved_progress = None

    # Load scene chain (after --continue mode override)
    # ADR-0048: if --continue, use saved_progress.ending; else use --ending CLI
    effective_ending = args.ending
    if saved_progress is not None and not getattr(args, "ignore_save_ending", False):
        effective_ending = saved_progress.ending

    if args.mode == "prologue":
        chain = load_prologue_chain(scenes_dir, seed=args.seed, ending=effective_ending)
        narration = f"Prologue: 3 characters × {len(chain) // 3} scenes (ending {effective_ending}), seeded {args.seed}"
    else:
        chain = load_scene_chain(scenes_dir, args.mode, ending=effective_ending)
        narration = f"Mode: {args.mode} ending {effective_ending} ({len(chain)} scenes)"
    total_scenes = len(chain)

    if total_scenes == 0:
        sys.stderr.write(f"No scenes found for mode={args.mode!r}\n")
        return 1

    # Apply saved state (after we know total_scenes)
    if saved_progress is not None:
        # Sanity check: chain length should match
        if saved_progress.chain_length != total_scenes:
            sys.stderr.write(
                f"[warn] Saved chain length {saved_progress.chain_length} "
                f"!= current {total_scenes}; starting from beginning.\n"
            )
            saved_progress = None
            scene_idx = 0
            dialogue_idx = 0
            elapsed_in_dialogue = 0.0
        else:
            scene_idx = min(saved_progress.scene_index, total_scenes - 1)
            dialogue_idx = saved_progress.dialogue_index
            elapsed_in_dialogue = saved_progress.elapsed_in_dialogue_ms

    # Pre-load art for all scenes
    bg_cache: dict[str, graphic_novel_view.Background] = {}
    portrait_cache: dict[str, graphic_novel_view.Portrait] = {}
    for scene in chain:
        if scene.background_id and scene.background_id not in bg_cache:
            try:
                bg_cache[scene.background_id] = load_background(art_dir, scene.background_id)
            except (KeyError, FileNotFoundError):
                pass
        for p_id in (scene.portrait_left, scene.portrait_right):
            if p_id and p_id not in portrait_cache:
                try:
                    portrait_cache[p_id] = load_portrait(art_dir, p_id)
                except (KeyError, FileNotFoundError):
                    pass

    console = tcod.console.Console(80, 30, order="F")

    start = time.monotonic()
    step = 0
    if saved_progress is None:
        scene_idx = 0
        dialogue_idx = 0
        elapsed_in_dialogue = 0.0
    scene_elapsed = 0.0
    # Phase state machine: "chapter_card" → "scene" → repeat
    # chapter_card shown before each new scene (except scene_idx 0 if --no-cards-initial)
    phase = "scene"
    card_elapsed = 0

    # Show opening chapter card for the first scene (if not disabled)
    if not args.no_cards and chain:
        phase = "chapter_card"
        card_elapsed = 0

    # Initial render
    scene = chain[scene_idx] if scene_idx < total_scenes else None
    if phase == "scene" and scene and scene.dialogue:
        dialogue = scene.dialogue[dialogue_idx]
        # Play sound cue for this dialogue (once per dialogue id)
        if sound_manager is not None:
            play_sound_once(sound_manager, dialogue.sound)
        bg = bg_cache.get(scene.background_id)
        p_l = portrait_cache.get(scene.portrait_left) if scene.portrait_left else None
        p_r = portrait_cache.get(scene.portrait_right) if scene.portrait_right else None
        typed = dialogue_typed_chars(
            dialogue.duration_ms,
            elapsed_in_dialogue,
            len(dialogue.text_ko if t.lang == "ko" else dialogue.text_en),
        )
        render_scene(
            console,
            scene,
            dialogue,
            bg,
            p_l,
            p_r,
            t,
            typed,
            scene_idx,
            total_scenes,
            paused=False,
        )
    elif phase == "chapter_card" and scene:
        is_last = scene_idx == total_scenes - 1
        render_chapter_card(
            console,
            scene,
            scene_idx,
            total_scenes,
            transition_ms=card_elapsed,
            transition_duration_ms=CHAPTER_CARD_FADE_MS,
            lang=args.lang,
            is_last_scene=is_last,
        )
    _print_frame(
        console,
        clear=not args.no_clear,
        step=step,
        elapsed=0.0,
        scene_idx=scene_idx,
        total=total_scenes,
        dialogue_idx=dialogue_idx,
        dialogue_total=len(scene.dialogue) if scene else 0,
        narration=narration,
        phase=phase,
    )
    step += 1
    time.sleep(args.step_delay)

    while time.monotonic() - start < args.duration and scene_idx < total_scenes:
        elapsed = time.monotonic() - start
        # Step time (in ms)
        step_ms = int(args.step_delay * 1000 * args.speed)

        scene = chain[scene_idx]
        if not scene.dialogue:
            scene_idx += 1
            dialogue_idx = 0
            elapsed_in_dialogue = 0.0
            if not args.no_cards and scene_idx < total_scenes:
                phase = "chapter_card"
                card_elapsed = 0
            continue

        # === Chapter card phase ===
        if phase == "chapter_card":
            card_elapsed += step_ms
            is_last = scene_idx == total_scenes - 1
            render_chapter_card(
                console,
                scene,
                scene_idx,
                total_scenes,
                transition_ms=card_elapsed,
                transition_duration_ms=CHAPTER_CARD_FADE_MS,
                lang=args.lang,
                is_last_scene=is_last,
            )
            if card_elapsed >= args.card_ms:
                phase = "scene"
                dialogue_idx = 0
                elapsed_in_dialogue = 0.0
            _print_frame(
                console,
                clear=not args.no_clear,
                step=step,
                elapsed=elapsed,
                scene_idx=scene_idx,
                total=total_scenes,
                dialogue_idx=0,
                dialogue_total=len(scene.dialogue),
                narration=f"Chapter card: {scene.title_en if t.lang == 'en' else scene.title_ko}",
                phase=phase,
            )
            step += 1
            time.sleep(args.step_delay)
            continue

        # === Scene phase ===
        elapsed_in_dialogue += step_ms
        scene_elapsed += step_ms

        dialogue = scene.dialogue[dialogue_idx]
        # Play sound cue (once per dialogue id) — ADR-0032
        if sound_manager is not None:
            play_sound_once(sound_manager, dialogue.sound)
        text = dialogue.text_ko if t.lang == "ko" else dialogue.text_en
        typed = dialogue_typed_chars(dialogue.duration_ms, elapsed_in_dialogue, len(text))

        bg = bg_cache.get(scene.background_id)
        p_l = portrait_cache.get(scene.portrait_left) if scene.portrait_left else None
        p_r = portrait_cache.get(scene.portrait_right) if scene.portrait_right else None
        render_scene(
            console,
            scene,
            dialogue,
            bg,
            p_l,
            p_r,
            t,
            typed,
            scene_idx,
            total_scenes,
            paused=False,
        )

        if elapsed_in_dialogue >= dialogue.duration_ms:
            # Advance to next dialogue or scene
            dialogue_idx += 1
            elapsed_in_dialogue = 0.0
            if dialogue_idx >= len(scene.dialogue):
                scene_idx += 1
                dialogue_idx = 0
                # Show chapter card for next scene (if any)
                if not args.no_cards and scene_idx < total_scenes:
                    phase = "chapter_card"
                    card_elapsed = 0

        narration = f"{scene.title_en if t.lang == 'en' else scene.title_ko} ({dialogue.speaker})"
        _print_frame(
            console,
            clear=not args.no_clear,
            step=step,
            elapsed=elapsed,
            scene_idx=min(scene_idx, total_scenes - 1),
            total=total_scenes,
            dialogue_idx=dialogue_idx,
            dialogue_total=len(scene.dialogue),
            narration=narration,
            phase=phase,
        )
        step += 1
        time.sleep(args.step_delay)

    # === Save on exit (ADR-0044, ADR-0051 multi-slot) ===
    if not args.no_save:
        try:
            anchor_char = chain[0].character if chain else "novice"
            progress = make_progress(
                mode=args.mode,
                scene_index=min(scene_idx, total_scenes - 1),
                dialogue_index=dialogue_idx,
                elapsed_in_dialogue_ms=elapsed_in_dialogue,
                character_id=anchor_char,
                chain_length=total_scenes,
            )
            slot = args.slot if args.slot is not None else 1
            saved_path = save_gn_progress_slot(progress, slot, save_dir=gn_save_dir)
            sys.stdout.write(f"[gn-save] Saved progress to slot {slot}: {saved_path}\n")
        except Exception as e:
            sys.stderr.write(f"[gn-save] Could not save: {e}\n")
    else:
        sys.stdout.write("[gn-save] Skipped save (--no-save)\n")

    sys.stdout.write(
        f"\n=== Graphic novel complete: {step} steps, "
        f"{scene_idx}/{total_scenes} scenes in {args.duration:.0f}s ===\n"
    )
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stdout.write("\n[interrupted]\n")
        sys.exit(130)
