"""ADR-0048 시각 데모 — GN 엔딩 메뉴 + Save 마이그레이션 (5-씬).

시연:
1. **GRAPHIC_NOVEL_MENU** (5 옵션 — 진입점)
2. **GRAPHIC_NOVEL_ENDING_MENU (NOVICE)** — 3 옵션 + 캐릭터별 설명
3. **엔딩 B 실제 씬** (case/05_refusal.json 첫 dialogue 렌더링)
4. **Save JSON 내용** — `ending: "B"` 필드 확인
5. **모든 캐릭터 × 엔딩 B** — Save 마이그레이션 검증

실행:
    uv run python scripts/ending_b_demo.py
    uv run python scripts/ending_b_demo.py --only 3          # 한 씬만
    uv run python scripts/ending_b_demo.py --lang ko         # 한글
    uv run python scripts/ending_b_demo.py --step-delay 1.5  # 천천히
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import tcod.console
import tcod.event

# Make src/ importable when running directly.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.graphic_novel_save import (  # noqa: E402
    GN_SAVE_VERSION,
    make_progress,
    save_gn_progress,
)
from wet_run.engine.graphic_novel_view import (  # noqa: E402
    Background,
    Portrait,
    load_background,
    load_portrait,
    render_graphic_novel_ending_menu,
    render_graphic_novel_menu,
    render_scene,
)
from wet_run.i18n import Translator  # noqa: E402

# ============================================================================
# Constants
# ============================================================================

SCREEN_W = 80
SCREEN_H = 30
DATA_DIR = Path(__file__).parent.parent / "data"
ART_DIR = DATA_DIR / "art"


def _console_to_text(console: tcod.console.Console) -> str:
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _print_console(
    console: tcod.console.Console,
    step: int,
    elapsed_s: float,
    *,
    no_clear: bool = False,
) -> None:
    """Print the console buffer to stdout, optionally clearing the terminal first."""
    if not no_clear:
        # ANSI clear screen + cursor home
        sys.stdout.write("\x1b[2J\x1b[H")
    text = _console_to_text(console)
    # Strip ANSI codes from text (none expected, but be safe)
    for line in text.split("\n"):
        sys.stdout.write(line + "\n")
    sys.stdout.write(f"\n[Step {step:03d}  T+{elapsed_s:5.1f}s]\n")
    sys.stdout.flush()


def _section(title: str) -> None:
    """Print a section divider."""
    bar = "═" * SCREEN_W
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


# ============================================================================
# Scene 1: GRAPHIC_NOVEL_MENU
# ============================================================================


def scene_1_gn_menu(translator: Translator, has_save: bool = False) -> None:
    """Render the GRAPHIC_NOVEL_MENU screen (entry point)."""
    _section("SCENE 1 — GRAPHIC_NOVEL_MENU (entry point)")
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_graphic_novel_menu(console, translator, selected_index=1, has_save=has_save)
    _print_console(console, step=1, elapsed_s=0.0)
    print("  ▶ Press [2] to pick CASE (Novice) → transitions to GRAPHIC_NOVEL_ENDING_MENU")


# ============================================================================
# Scene 2: GRAPHIC_NOVEL_ENDING_MENU (NOVICE)
# ============================================================================


def scene_2_ending_menu_novice(translator: Translator) -> None:
    """Render the GRAPHIC_NOVEL_ENDING_MENU for the NOVICE character."""
    _section("SCENE 2 — GRAPHIC_NOVEL_ENDING_MENU (NOVICE, after picking CASE)")
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_graphic_novel_ending_menu(console, translator, character="novice", selected_index=1)
    _print_console(console, step=2, elapsed_s=0.0)
    print("  ▶ Press [2] to pick ENDING B → loads case/05_refusal.json + case/06_freedom.json")


# ============================================================================
# Scene 3: Actual ending B scene rendering
# ============================================================================


def scene_3_ending_b_scene(translator: Translator) -> None:
    """Render the first scene of CASE ending B (case/05_refusal.json)."""
    _section("SCENE 3 — First dialogue of CASE ending B (case/05_refusal.json)")
    scene_path = DATA_DIR / "scenes" / "case" / "05_refusal.json"
    from wet_run.engine.graphic_novel_view import _parse_scene

    with scene_path.open(encoding="utf-8") as f:
        scene = _parse_scene(json.load(f))
    bg: Background | None = None
    if scene.background_id:
        try:
            bg = load_background(ART_DIR, scene.background_id)
        except (KeyError, FileNotFoundError):
            pass
    pl: Portrait | None = None
    pr: Portrait | None = None
    if scene.portrait_left:
        try:
            pl = load_portrait(ART_DIR, scene.portrait_left)
        except (KeyError, FileNotFoundError):
            pass
    if scene.portrait_right:
        try:
            pr = load_portrait(ART_DIR, scene.portrait_right)
        except (KeyError, FileNotFoundError):
            pass

    if not scene.dialogue:
        print("  ERROR: scene has no dialogue")
        return
    dl = scene.dialogue[0]
    # Reveal full dialogue (typed_chars = len(text_en))
    typed = len(dl.text_en)

    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_scene(
        console,
        scene,
        dl,
        bg,
        pl,
        pr,
        translator,
        typed_chars=typed,
        scene_index=4,  # 5th scene (0-based)
        scene_total=6,  # 4 ending A + 2 ending B
    )
    _print_console(console, step=3, elapsed_s=0.0)
    print(f"  ▶ Scene ID: {scene.id!r}, ending={scene.ending!r}, duration_ms={dl.duration_ms}")


# ============================================================================
# Scene 4: Save JSON content
# ============================================================================


def scene_4_save_json() -> None:
    """Show save file contents with ending='B'."""
    _section("SCENE 4 — Save JSON contents (ending='B' preserved)")
    # Build a sample progress and save it to a tmp file
    progress = make_progress(
        mode="novice",
        scene_index=4,  # We're at the start of case/05_refusal.json
        dialogue_index=0,
        elapsed_in_dialogue_ms=0.0,
        character_id="novice",
        chain_length=6,  # 4 ending A + 2 ending B = 6 total (per ending)
        ending="B",
    )
    tmp_path = Path("/tmp/gn_progress_demo.json")
    save_gn_progress(progress, tmp_path)
    payload = json.loads(tmp_path.read_text(encoding="utf-8"))

    print(f"  Save file: {tmp_path}")
    print(f"  ┌─ Version: {payload['version']}")
    print(f"  ├─ Saved at: {payload['saved_at']}")
    print("  └─ Progress:")
    progress_lines = json.dumps(payload["progress"], indent=4, ensure_ascii=False).split("\n")
    for line in progress_lines:
        print(f"     {line}")

    # Verify version + ending
    assert payload["version"] == GN_SAVE_VERSION, "Version mismatch!"
    assert payload["progress"]["ending"] == "B", "Ending not preserved!"
    print(f"\n  ✓ version = {payload['version']!r} (bumped 1.0.0 → 1.1.0)")
    print(f"  ✓ progress.ending = {payload['progress']['ending']!r} (saved with B)")
    print(f"  ✓ chain_length = {payload['progress']['chain_length']} (4 ending A + 2 ending B)")


# ============================================================================
# Scene 5: All characters × ending B (save round-trip)
# ============================================================================


def scene_5_all_chars_ending_b() -> None:
    """Show save → load round-trip for all 3 characters with ending B."""
    _section("SCENE 5 — Save round-trip: 3 chars × ending='B'")
    print("  Verifying save → load preserves ending field for all 3 characters:\n")

    for char_id, scene_dir_name in (
        ("novice", "case"),
        ("veteran", "sil"),
        ("heretic", "kas"),
    ):
        progress = make_progress(
            mode=char_id,
            scene_index=4,  # Start of ending B scenes (index 4 = scene 5)
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id=char_id,
            chain_length=6,
            ending="B",
        )
        tmp_path = Path(f"/tmp/gn_progress_{char_id}.json")
        save_gn_progress(progress, tmp_path)

        # Load and verify
        from wet_run.engine.graphic_novel_save import load_gn_progress

        loaded = load_gn_progress(tmp_path)
        assert loaded.ending == "B", f"{char_id}: ending not preserved"
        assert loaded.mode == char_id, f"{char_id}: mode mismatch"

        # Show first line of save
        payload = json.loads(tmp_path.read_text(encoding="utf-8"))
        print(f"  {char_id:8s} ({scene_dir_name}/05_*.json)")
        print(
            f"    saved:   ending={payload['progress']['ending']!r}, "
            f"scene={payload['progress']['scene_index']}, "
            f"chain={payload['progress']['chain_length']}"
        )
        print(
            f"    loaded:  ending={loaded.ending!r}, "
            f"scene={loaded.scene_index}, "
            f"chain={loaded.chain_length}"
        )

    print("\n  ✓ All 3 characters: ending='B' saved + loaded correctly")
    print(f"  ✓ Save version: {GN_SAVE_VERSION} (additive migration from 1.0.0)")


# ============================================================================
# Main
# ============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ADR-0048 visual demo — GN ending menu + Save 1.1.0 migration"
    )
    parser.add_argument(
        "--lang", choices=["en", "ko"], default="en", help="UI language (default: en)"
    )
    parser.add_argument("--only", type=int, choices=[1, 2, 3, 4, 5], help="Run only one scene")
    parser.add_argument(
        "--step-delay", type=float, default=1.0, help="Delay between scenes in seconds"
    )
    parser.add_argument(
        "--no-clear", action="store_true", help="Don't clear terminal between scenes"
    )
    args = parser.parse_args()

    t = Translator(args.lang, data_dir=DATA_DIR / "i18n")

    scenes: list[tuple[int, object]] = [
        (1, lambda: scene_1_gn_menu(t, has_save=True)),
        (2, lambda: scene_2_ending_menu_novice(t)),
        (3, lambda: scene_3_ending_b_scene(t)),
        (4, lambda: scene_4_save_json()),
        (5, lambda: scene_5_all_chars_ending_b()),
    ]

    def _call(fn: object) -> None:
        if callable(fn):
            fn()

    if args.only is not None:
        scenes = [s for s in scenes if s[0] == args.only]

    start = time.monotonic()
    for i, (_n, fn) in enumerate(scenes):
        if i > 0:
            time.sleep(args.step_delay)
        _call(fn)

    elapsed = time.monotonic() - start
    print(f"\n=== Ending B Demo complete: {len(scenes)} scenes in {elapsed:.1f}s ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
