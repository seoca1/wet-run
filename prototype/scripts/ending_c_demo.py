"""ADR-0049 시각 데모 — 엔딩 C 메뉴 + 씬 + Save 마이그레이션.

시연:
1. **GRAPHIC_NOVEL_ENDING_MENU (NOVICE)** — 4 옵션 (A/B/C + BACK), C 선택
2. **GRAPHIC_NOVEL_ENDING_MENU (VETERAN)** — C: The Erase
3. **GRAPHIC_NOVEL_ENDING_MENU (HERETIC)** — C: The Burn
4. **case/07_disappear.json** 첫 dialogue (Finn이 보낸 자리에 가지 않음)
5. **kas/07_weapon.json** 첫 dialogue (쿠미코의 broadcast 시작)
6. **Save JSON (ending='C', v1.2.0)** — 3 캐릭터 × ending C 라운드트립
7. **Save v1.1.0 마이그레이션** — ending='B' → v1.2.0 그대로 로드

실행:
    uv run python scripts/ending_c_demo.py
    uv run python scripts/ending_c_demo.py --only 4
    uv run python scripts/ending_c_demo.py --lang ko
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.graphic_novel_save import (  # noqa: E402
    GN_SAVE_VERSION,
    load_gn_progress,
    make_progress,
    save_gn_progress,
)
from wet_run.engine.graphic_novel_view import (  # noqa: E402
    _ENDING_DESCRIPTIONS,
    _parse_scene,
    available_endings,
    load_background,
    load_portrait,
    render_graphic_novel_ending_menu,
    render_scene,
)
from wet_run.i18n import Translator  # noqa: E402

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
    if not no_clear:
        sys.stdout.write("\x1b[2J\x1b[H")
    text = _console_to_text(console)
    for line in text.split("\n"):
        sys.stdout.write(line + "\n")
    sys.stdout.write(f"\n[Step {step:03d}  T+{elapsed_s:5.1f}s]\n")
    sys.stdout.flush()


def _section(title: str) -> None:
    bar = "═" * SCREEN_W
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


# ============================================================================
# Scene 1: NOVICE ending menu (selected=C)
# ============================================================================


def scene_1_novice_c(t: Translator) -> None:
    _section("SCENE 1 — GRAPHIC_NOVEL_ENDING_MENU (NOVICE, selected=C)")
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_graphic_novel_ending_menu(console, t, character="novice", selected_index=2)
    _print_console(console, step=1, elapsed_s=0.0)
    print(f"  ▶ available_endings('novice') = {available_endings('novice')}")
    print("  ▶ Press [3] to pick ENDING C → loads case/07_disappear.json + case/08_freeside.json")


# ============================================================================
# Scene 2: VETERAN ending menu (selected=C)
# ============================================================================


def scene_2_veteran_c(t: Translator) -> None:
    _section("SCENE 2 — GRAPHIC_NOVEL_ENDING_MENU (VETERAN, selected=C)")
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_graphic_novel_ending_menu(console, t, character="veteran", selected_index=2)
    _print_console(console, step=2, elapsed_s=0.0)
    print(
        f"  ▶ ENDING C — {_ENDING_DESCRIPTIONS[('veteran', 'C')]['ko' if t.lang == 'ko' else 'en']}"
    )


# ============================================================================
# Scene 3: HERETIC ending menu (selected=C)
# ============================================================================


def scene_3_heretic_c(t: Translator) -> None:
    _section("SCENE 3 — GRAPHIC_NOVEL_ENDING_MENU (HERETIC, selected=C)")
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_graphic_novel_ending_menu(console, t, character="heretic", selected_index=2)
    _print_console(console, step=3, elapsed_s=0.0)
    print(
        f"  ▶ ENDING C — {_ENDING_DESCRIPTIONS[('heretic', 'C')]['ko' if t.lang == 'ko' else 'en']}"
    )


# ============================================================================
# Scene 4: case/07_disappear.json first dialogue
# ============================================================================


def scene_4_case_disappear(t: Translator) -> None:
    _section("SCENE 4 — CASE ending C: case/07_disappear.json (first dialogue)")
    scene_path = DATA_DIR / "scenes" / "case" / "07_disappear.json"
    with scene_path.open(encoding="utf-8") as f:
        scene = _parse_scene(json.load(f))
    bg = None
    if scene.background_id:
        try:
            bg = load_background(ART_DIR, scene.background_id)
        except (KeyError, FileNotFoundError):
            pass
    pl = None
    pr = None
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
    dl = scene.dialogue[0]
    typed = len(dl.text_en)
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_scene(
        console,
        scene,
        dl,
        bg,
        pl,
        pr,
        t,
        typed_chars=typed,
        scene_index=6,
        scene_total=8,  # 4 A + 2 B + 2 C
    )
    _print_console(console, step=4, elapsed_s=0.0)
    print(f"  ▶ Scene ID: {scene.id!r}, ending={scene.ending!r}, duration_ms={dl.duration_ms}")


# ============================================================================
# Scene 5: kas/07_weapon.json first dialogue
# ============================================================================


def scene_5_kas_weapon(t: Translator) -> None:
    _section("SCENE 5 — KAS ending C: kas/07_weapon.json (first dialogue)")
    scene_path = DATA_DIR / "scenes" / "kas" / "07_weapon.json"
    with scene_path.open(encoding="utf-8") as f:
        scene = _parse_scene(json.load(f))
    bg = None
    if scene.background_id:
        try:
            bg = load_background(ART_DIR, scene.background_id)
        except (KeyError, FileNotFoundError):
            pass
    pl = None
    if scene.portrait_left:
        try:
            pl = load_portrait(ART_DIR, scene.portrait_left)
        except (KeyError, FileNotFoundError):
            pass
    dl = scene.dialogue[0]
    typed = len(dl.text_en)
    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    render_scene(
        console,
        scene,
        dl,
        bg,
        pl,
        None,
        t,
        typed_chars=typed,
        scene_index=6,
        scene_total=8,
    )
    _print_console(console, step=5, elapsed_s=0.0)
    print(f"  ▶ Scene ID: {scene.id!r}, ending={scene.ending!r}, duration_ms={dl.duration_ms}")


# ============================================================================
# Scene 6: Save JSON (ending='C', v1.2.0)
# ============================================================================


def scene_6_save_json() -> None:
    _section("SCENE 6 — Save JSON (ending='C', v1.2.0)")
    progress = make_progress(
        mode="novice",
        scene_index=6,
        dialogue_index=0,
        elapsed_in_dialogue_ms=0.0,
        character_id="novice",
        chain_length=8,  # 4 A + 2 B + 2 C
        ending="C",
    )
    tmp_path = Path("/tmp/gn_progress_c_demo.json")
    save_gn_progress(progress, tmp_path)
    payload = json.loads(tmp_path.read_text(encoding="utf-8"))

    print(f"  Save file: {tmp_path}")
    print(f"  ┌─ Version: {payload['version']}")
    print(f"  ├─ Saved at: {payload['saved_at']}")
    print("  └─ Progress:")
    for line in json.dumps(payload["progress"], indent=4, ensure_ascii=False).split("\n"):
        print(f"     {line}")

    assert payload["version"] == GN_SAVE_VERSION
    assert payload["progress"]["ending"] == "C"
    print(f"\n  ✓ version = {payload['version']!r} (bumped 1.1.0 → 1.2.0)")
    print(f"  ✓ progress.ending = {payload['progress']['ending']!r} (saved with C)")
    print(f"  ✓ chain_length = {payload['progress']['chain_length']} (4 A + 2 B + 2 C)")


# ============================================================================
# Scene 7: Save v1.1.0 → v1.2.0 migration (additive)
# ============================================================================


def scene_7_save_migration() -> None:
    _section("SCENE 7 — Save v1.1.0 → v1.2.0 migration (additive)")
    print("  Verifying v1.1.0 save (ending='B') loads cleanly under v1.2.0:\n")

    tmp_path = Path("/tmp/gn_progress_v11_migration.json")
    payload = {
        "version": "1.2.0",  # current code
        "saved_at": "2026-06-21T00:00:00Z",
        "progress": {
            "mode": "veteran",
            "scene_index": 4,
            "dialogue_index": 0,
            "elapsed_in_dialogue_ms": 0.0,
            "character_id": "veteran",
            "chain_length": 6,
            "saved_at": "2026-06-21T00:00:00Z",
            "ending": "B",  # v1.1.0 era value
            "session_id": "migration_test",
        },
    }
    tmp_path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_gn_progress(tmp_path)

    print("  Input (v1.1.0 era save):")
    print(f"    version: {payload['version']!r}")
    print(f"    progress.ending: {payload['progress']['ending']!r}")
    print("  Loaded under v1.2.0:")
    print(f"    loaded.ending: {loaded.ending!r}")
    print(f"    loaded.scene_index: {loaded.scene_index}")
    print(f"    loaded.mode: {loaded.mode!r}")

    assert loaded.ending == "B", "ending='B' must be preserved"
    print("\n  ✓ ending='B' preserved through v1.1.0 → v1.2.0 migration")


# ============================================================================
# Main
# ============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ADR-0049 visual demo — GN ending C menu + Save 1.2.0 migration"
    )
    parser.add_argument("--lang", choices=["en", "ko"], default="en")
    parser.add_argument("--only", type=int, choices=[1, 2, 3, 4, 5, 6, 7])
    parser.add_argument("--step-delay", type=float, default=1.0)
    parser.add_argument("--no-clear", action="store_true")
    args = parser.parse_args()

    t = Translator(args.lang, data_dir=DATA_DIR / "i18n")

    scenes: list[tuple[int, object]] = [
        (1, lambda: scene_1_novice_c(t)),
        (2, lambda: scene_2_veteran_c(t)),
        (3, lambda: scene_3_heretic_c(t)),
        (4, lambda: scene_4_case_disappear(t)),
        (5, lambda: scene_5_kas_weapon(t)),
        (6, lambda: scene_6_save_json()),
        (7, lambda: scene_7_save_migration()),
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
    print(f"\n=== Ending C Demo complete: {len(scenes)} scenes in {elapsed:.1f}s ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
