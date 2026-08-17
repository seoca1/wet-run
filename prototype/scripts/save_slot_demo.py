"""GN Save Slot demo (ADR-0104).

Demonstrates the 3-slot graphic novel save system:
    - List all 3 slots with metadata
    - Save to an empty slot
    - Load from a slot
    - Delete from a slot
    - Migrate legacy single-slot save (gn_progress.json → slot_1)

Single command:
    uv run python scripts/save_slot_demo.py

⚠️  WARNING — DATA-DESTRUCTIVE
    The default action (--action auto) MODIFIES real save data in
    data/saves/. The fill/delete/migrate actions also touch real data.
    Use --save-dir /tmp/save_slot_demo to test in an isolated directory:

        uv run python scripts/save_slot_demo.py --save-dir /tmp/save_slot_demo --action auto

Options:
    --action {list,fill,load,delete,migrate,auto}  What to do (default auto)
    --slot N         Slot number 1..3 (default 1)
    --mode MODE      Mode: prologue|novice|veteran|heretic (default prologue)
    --character-id   novice|veteran|heretic|suit|... (default novice)
    --scene N        Scene index (default 0)
    --save-dir DIR   Override save directory (default: data/saves)
    --quiet          Only print final state
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.graphic_novel_save import (
    GN_SAVE_SLOTS,
    GNProgress,
    GNSaveEmptyError,
    delete_gn_progress_slot,
    has_gn_save_slot,
    list_save_slots,
    load_gn_progress_slot,
    make_progress,
    save_gn_progress_slot,
)

DEFAULT_SAVE_DIR = Path("data/saves")


def _print_slot(slot: dict[str, Any]) -> str:
    """Format a single slot entry for display."""
    if not slot.get("has_save"):
        return f"  SLOT {slot['slot_id']}: [EMPTY]"

    progress: GNProgress = slot["progress"]
    saved_at = slot.get("saved_at") or "?"
    return (
        f"  SLOT {slot['slot_id']}: {progress.mode}/{progress.character_id} "
        f"ending={progress.ending} scene={progress.scene_index}/{progress.chain_length} "
        f"({saved_at})"
    )


def _print_all_slots(save_dir: Path) -> None:
    """Print all 3 slots in a uniform format."""
    slots = list_save_slots(save_dir=save_dir)
    print(f"--- {len(slots)} slots ({GN_SAVE_SLOTS} total) in {save_dir} ---")
    for slot in slots:
        print(_print_slot(slot))
    print()


def action_list(args: argparse.Namespace) -> int:
    """Just list the slots."""
    _print_all_slots(args.save_dir)
    return 0


def action_fill(args: argparse.Namespace) -> int:
    """Save a fresh GNProgress to the chosen slot."""
    if not has_gn_save_slot(args.slot, save_dir=args.save_dir):
        progress = make_progress(
            mode=args.mode,
            scene_index=args.scene,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id=args.character_id,
            chain_length=12,  # 9자 × ~4 scenes (prologue default)
        )
        path = save_gn_progress_slot(progress, args.slot, save_dir=args.save_dir)
        print(f"Saved slot {args.slot} → {path}")
    else:
        print(f"Slot {args.slot} already filled — overwriting")
        progress = make_progress(
            mode=args.mode,
            scene_index=args.scene,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id=args.character_id,
            chain_length=12,
        )
        path = save_gn_progress_slot(progress, args.slot, save_dir=args.save_dir)
        print(f"Overwrote slot {args.slot} → {path}")
    _print_all_slots(args.save_dir)
    return 0


def action_load(args: argparse.Namespace) -> int:
    """Load GNProgress from the chosen slot."""
    try:
        progress = load_gn_progress_slot(args.slot, save_dir=args.save_dir)
    except GNSaveEmptyError:
        print(f"Slot {args.slot} is empty — nothing to load")
        return 1
    print(
        f"Loaded slot {args.slot}: "
        f"mode={progress.mode} char={progress.character_id} "
        f"scene={progress.scene_index}/{progress.chain_length} "
        f"ending={progress.ending}"
    )
    return 0


def action_delete(args: argparse.Namespace) -> int:
    """Delete the chosen slot."""
    deleted = delete_gn_progress_slot(args.slot, save_dir=args.save_dir)
    if deleted:
        print(f"Deleted slot {args.slot}")
    else:
        print(f"Slot {args.slot} was already empty")
    _print_all_slots(args.save_dir)
    return 0


def action_migrate(args: argparse.Namespace) -> int:
    """Run legacy single-slot → slot_1 migration."""
    # Note: migrate_legacy_single_slot() uses hardcoded Path("data/saves").
    # For non-default save_dir, we do an inline equivalent.
    legacy = args.save_dir / "gn_progress.json"
    slot1 = args.save_dir / "gn_progress_slot_1.json"
    if not legacy.exists():
        print(f"No legacy file at {legacy}")
    elif slot1.exists():
        print(f"Slot 1 already exists at {slot1} — leaving legacy untouched")
    else:
        slot1.parent.mkdir(parents=True, exist_ok=True)
        legacy.rename(slot1)
        print(f"Migrated {legacy} → {slot1}")
    _print_all_slots(args.save_dir)
    return 0


def action_auto(args: argparse.Namespace) -> int:
    """Run a full demo: list → fill → list → load → delete → list.

    This is the default — exercises the entire 3-slot API in one pass.
    """
    save_dir: Path = args.save_dir
    print("=" * 60)
    print("GN SAVE SLOT DEMO (ADR-0104)")
    print(f"Save directory: {save_dir}")
    print("=" * 60)

    # Step 1: initial state
    print("\n[1] Initial slot state:")
    _print_all_slots(save_dir)

    # Step 2: fill slot 1
    print("[2] Filling slot 1 with prologue/suit/ending=A/scene=2:")
    progress = make_progress(
        mode=args.mode,
        scene_index=args.scene,
        dialogue_index=0,
        elapsed_in_dialogue_ms=0.0,
        character_id=args.character_id,
        chain_length=12,
    )
    path = save_gn_progress_slot(progress, 1, save_dir=save_dir)
    print(f"   → wrote {path}")
    _print_all_slots(save_dir)

    # Step 3: fill slot 3 (skip 2 to show non-sequential)
    print("[3] Filling slot 3 with prologue/sil/ending=B/scene=5:")
    progress_b = make_progress(
        mode=args.mode,
        scene_index=5,
        dialogue_index=0,
        elapsed_in_dialogue_ms=0.0,
        character_id="veteran",
        chain_length=12,
        ending="B",
    )
    path = save_gn_progress_slot(progress_b, 3, save_dir=save_dir)
    print(f"   → wrote {path}")
    _print_all_slots(save_dir)

    # Step 4: load slot 1
    print("[4] Loading slot 1:")
    loaded = load_gn_progress_slot(1, save_dir=save_dir)
    print(
        f"   → mode={loaded.mode} char={loaded.character_id} "
        f"scene={loaded.scene_index} ending={loaded.ending}"
    )

    # Step 5: try to load empty slot 2 (clear it first to ensure empty)
    print("\n[5] Loading slot 2 — first clearing to test GNSaveEmptyError:")
    if has_gn_save_slot(2, save_dir=save_dir):
        print("   → slot 2 had pre-existing data, deleting for test isolation")
        delete_gn_progress_slot(2, save_dir=save_dir)
    try:
        load_gn_progress_slot(2, save_dir=save_dir)
        print("   → UNEXPECTED: load succeeded after delete")
        return 1
    except GNSaveEmptyError as e:
        print(f"   → caught expected error: {e}")

    # Step 6: delete slot 3
    print("\n[6] Deleting slot 3:")
    deleted = delete_gn_progress_slot(3, save_dir=save_dir)
    print(f"   → deleted={deleted}")
    _print_all_slots(save_dir)

    # Step 7: run migration check
    print("[7] Checking for legacy single-slot migration:")
    action_migrate(args)

    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GN Save Slot demo (ADR-0104)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--action",
        choices=["list", "fill", "load", "delete", "migrate", "auto"],
        default="auto",
        help="What to do (default: auto — runs the full demo)",
    )
    parser.add_argument(
        "--slot",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Slot number 1..3 (default 1)",
    )
    parser.add_argument(
        "--mode",
        choices=["prologue", "novice", "veteran", "heretic"],
        default="prologue",
        help="Save mode (default prologue)",
    )
    parser.add_argument(
        "--character-id",
        default="novice",
        help="Character ID (novice/veteran/heretic/suit/...)",
    )
    parser.add_argument(
        "--scene",
        type=int,
        default=0,
        help="Scene index (default 0)",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=DEFAULT_SAVE_DIR,
        help="Save directory (default: data/saves) — use /tmp/... for safe testing",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print final state",
    )
    args = parser.parse_args()

    actions = {
        "list": action_list,
        "fill": action_fill,
        "load": action_load,
        "delete": action_delete,
        "migrate": action_migrate,
        "auto": action_auto,
    }
    return actions[args.action](args)


if __name__ == "__main__":
    sys.exit(main())
