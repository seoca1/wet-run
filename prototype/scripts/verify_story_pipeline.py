#!/usr/bin/env uv run python
"""
Story → Stage → Demo Verification Pipeline
============================================

단편소설 작성 (expanded.json)
    ↓ story_beats 매핑
스테이즈 (chapter_flow.json phases)
    ↓ phases 내 beats 미구현
이벤트 (arc.json)
    ↓ 아직 미연결
데모 검증 (play.py / tests)

Usage:
    uv run python scripts/verify_story_pipeline.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROTOTYPE = Path(__file__).parent.parent
DASHBOARD = PROTOTYPE.parent / "dashboard"


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def verify_story_data() -> dict:
    """Step 1: Verify expanded.json story data."""
    print("\n" + "=" * 80)
    print("STEP 1: 단편소설 검증 (expanded.json)")
    print("=" * 80)

    results = {"status": "PASS", "stories": {}}

    for char in ["case", "sil", "kas"]:
        path = PROTOTYPE / f"data/story/chapters/{char}_expanded.json"
        data = load_json(path)

        episodes = data.get("episodes", [])
        total_beats = sum(len(e.get("beats", [])) for e in episodes)
        total_combats = sum(
            1 for e in episodes for b in e.get("beats", []) if b.get("type") == "combat"
        )
        en_chars = sum(sum(len(b.get("text_en", "")) for b in e.get("beats", [])) for e in episodes)
        ko_chars = sum(sum(len(b.get("text_ko", "")) for b in e.get("beats", [])) for e in episodes)

        # Verify Ch5 endings exist
        ch5_eps = [
            e for e in episodes if 21 <= int(e.get("episode_id", "ep_0").split("_")[1]) <= 25
        ]
        has_ending = len(ch5_eps) == 5

        results["stories"][char] = {
            "episodes": len(episodes),
            "beats": total_beats,
            "combats": total_combats,
            "en_chars": en_chars,
            "ko_chars": ko_chars,
            "ch5_complete": has_ending,
        }

        status_icon = "✅" if len(episodes) == 25 and total_beats > 0 else "❌"
        print(
            f"  {status_icon} {char.upper()}: {len(episodes)} eps, {total_beats} beats, {total_combats} combats"
        )
        print(
            f"      EN {en_chars:,} / KO {ko_chars:,} chars | Ch5 endings: {'YES' if has_ending else 'NO'}"
        )

    return results


def verify_chapter_flow() -> dict:
    """Step 2: Verify chapter_flow.json mapping."""
    print("\n" + "=" * 80)
    print("STEP 2: 스테이즈 검증 (chapter_flow.json)")
    print("=" * 80)

    results = {"status": "PASS", "characters": {}}

    cf_path = DASHBOARD / "data/story/arcs/chapter_flow.json"
    cf = load_json(cf_path)

    for char in ["case", "sil", "kas"]:
        data = cf.get(char, {})
        chapters = data.get("chapters", [])
        total_phases = sum(len(ch.get("phases", [])) for ch in chapters)
        total_story_beats = sum(
            len(ph.get("story_beats", [])) for ch in chapters for ph in ch.get("phases", [])
        )

        # Verify phases have story_beats references
        phases_without_beats = sum(
            1 for ch in chapters for ph in ch.get("phases", []) if not ph.get("story_beats")
        )

        results["characters"][char] = {
            "chapters": len(chapters),
            "phases": total_phases,
            "story_beats": total_story_beats,
            "phases_without_beats": phases_without_beats,
        }

        status_icon = "✅" if len(chapters) == 5 and total_phases > 0 else "❌"
        print(
            f"  {status_icon} {char.upper()}: {len(chapters)} ch, {total_phases} phases, {total_story_beats} story_beats"
        )
        print(f"      phases without beats: {phases_without_beats}")

    return results


def verify_arc_data() -> dict:
    """Step 3: Verify arc.json implementation status."""
    print("\n" + "=" * 80)
    print("STEP 3: 이벤트 검증 (arc.json)")
    print("=" * 80)

    results = {"status": "FAIL", "characters": {}}

    for char in ["case", "sil", "kas"]:
        path = PROTOTYPE / f"data/story/arcs/{char}_arc.json"
        data = load_json(path)

        chapters = data.get("chapters", [])
        total_phases = sum(len(ch.get("phases", [])) for ch in chapters)
        total_beats = sum(
            len(ph.get("beats", [])) for ch in chapters for ph in ch.get("phases", [])
        )

        # Check if beats are implemented
        beats_implemented = total_beats > 0

        results["characters"][char] = {
            "chapters": len(chapters),
            "phases": total_phases,
            "beats": total_beats,
            "beats_implemented": beats_implemented,
        }

        status_icon = "✅" if beats_implemented else "⚠️"
        print(
            f"  {status_icon} {char.upper()}: {len(chapters)} ch, {total_phases} phases, {total_beats} beats"
        )
        print(f"      beats implemented: {'YES' if beats_implemented else 'NO (needs mapping)'}")

    if all(r["beats_implemented"] for r in results["characters"].values()):
        results["status"] = "PASS"

    return results


def verify_html_output() -> dict:
    """Step 4: Verify HTML story output."""
    print("\n" + "=" * 80)
    print("STEP 4: HTML 출력 검증 (dashboard/stories/)")
    print("=" * 80)

    results = {"status": "PASS", "files": {}}

    stories_dir = DASHBOARD / "stories"
    for char in ["case", "sil", "kas"]:
        for lang in ["en", "ko"]:
            path = stories_dir / f"{char}_{lang}.html"
            if path.exists():
                size = path.stat().st_size
                results["files"][f"{char}_{lang}"] = {"exists": True, "size": size}
                print(f"  ✅ {char}_{lang}.html: {size:,} bytes")
            else:
                results["files"][f"{char}_{lang}"] = {"exists": False, "size": 0}
                results["status"] = "FAIL"
                print(f"  ❌ {char}_{lang}.html: NOT FOUND")

    return results


def verify_combat_system() -> dict:
    """Step 5: Verify combat system."""
    print("\n" + "=" * 80)
    print("STEP 5:Combat 시스템 검증 (ice_types.json + registry)")
    print("=" * 80)

    results = {"status": "PASS", "ice_types": 0, "registry_functions": []}

    # Check ice_types.json
    ice_path = PROTOTYPE / "data/combat/ice_types.json"
    ice_data = load_json(ice_path)
    ice_types = [k for k in ice_data.keys() if isinstance(ice_data[k], dict)]
    results["ice_types"] = len(ice_types)

    print(f"  ✅ ice_types: {len(ice_types)} types ({', '.join(ice_types)})")

    # Check registry functions
    registry_path = PROTOTYPE / "src/wet_run/combat/registry.py"
    content = registry_path.read_text()
    functions = [line.strip() for line in content.splitlines() if "def " in line]
    results["registry_functions"] = functions

    print(f"  ✅ registry functions: {len(functions)}")
    for fn in functions:
        print(f"      - {fn.strip()}")

    return results


def generate_summary(steps: list[dict]) -> dict:
    """Generate overall summary."""
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "story_data": steps[0],
        "chapter_flow": steps[1],
        "arc_data": steps[2],
        "html_output": steps[3],
        "combat_system": steps[4],
        "overall": "PASS",
    }

    # Check overall status
    if any(s.get("status") == "FAIL" for s in steps):
        summary["overall"] = "FAIL"
    elif any(s.get("status") == "WARN" for s in steps):
        summary["overall"] = "WARN"

    statuses = {
        "PASS": "✅",
        "FAIL": "❌",
        "WARN": "⚠️",
    }

    print(f"\n  Overall Status: {statuses.get(summary['overall'], '?')} {summary['overall']}")
    print(f"  Timestamp: {summary['timestamp']}")

    print("\n  Pipeline Status:")
    for i, step in enumerate(steps, 1):
        status = step.get("status", "UNKNOWN")
        print(f"    Step {i}: {statuses.get(status, '?')} {status}")

    # Gap analysis
    print("\n  Gap Analysis:")
    story_beats = sum(s["stories"][c]["beats"] for c in ["case", "sil", "kas"] for s in [steps[0]])
    arc_beats = sum(s["characters"][c]["beats"] for c in ["case", "sil", "kas"] for s in [steps[2]])

    print(f"    Story beats: {story_beats}")
    print(f"    Arc beats:   {arc_beats}")
    print(f"    Gap:         {story_beats - arc_beats} beats unmapped")

    return summary


def main():
    print("=" * 80)
    print("STORY → STAGE → DEMO VERIFICATION PIPELINE")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)

    # Run verification steps
    steps = []

    steps.append(verify_story_data())  # Step 1
    steps.append(verify_chapter_flow())  # Step 2
    steps.append(verify_arc_data())  # Step 3
    steps.append(verify_html_output())  # Step 4
    steps.append(verify_combat_system())  # Step 5

    # Generate summary
    summary = generate_summary(steps)

    # Save report
    report_path = PROTOTYPE / "scripts" / "verification_report.json"
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Report saved to: {report_path}")

    # Return exit code based on status
    if summary["overall"] == "FAIL":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
