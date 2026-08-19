"""Story link validator (R2).

`missions.json`의 `story.source` 필드가 실제 단편 파일과 매핑되는지 검증.
CI / pre-commit 훅 통합 가능.

사용법:
    python verify_story_links.py                 # vault 루트에서 실행
    python verify_story_links.py --json          # JSON 출력
    python verify_story_links.py --missing-only  # 누락된 항목만
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 프로젝트 루트: 이 스크립트는 prototype/scripts/ 아래에 있으므로 4단계 상위
ROOT = Path(__file__).resolve().parents[3]  # scripts -> prototype -> wet_run -> Game
ROOT = ROOT.parent  # Game의 부모 = Projects/

sys.path.insert(0, str(ROOT / "Game" / "wet_run" / "prototype" / "src"))

from wet_run.data.story_resolver import (  # type: ignore[import-not-found]  # noqa: E402
    list_available_stems,
    validate_game_mission_id_links,
    validate_mission_sources,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate mission→story source links")
    parser.add_argument(
        "--missions",
        type=Path,
        default=ROOT / "Game" / "wet_run" / "prototype" / "data" / "missions" / "missions.json",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--missing-only", action="store_true", help="Only show issues")
    args = parser.parse_args()

    if not args.missions.exists():
        print(f"ERROR: missions.json not found at {args.missions}", file=sys.stderr)
        return 2

    with args.missions.open(encoding="utf-8") as f:
        missions = json.load(f)

    report = validate_mission_sources(missions, ROOT)
    available = list_available_stems(ROOT)
    gmi_report = validate_game_mission_id_links(missions, ROOT)

    blocking_mission_count = sum(1 for r in report if r.get("severity") == "blocking")
    info_mission_count = sum(1 for r in report if r.get("severity") == "info")
    gmi_issue_count = sum(1 for r in gmi_report if r["issues"])
    any_blocking = blocking_mission_count > 0 or gmi_issue_count > 0

    if args.json:
        output = {
            "missions_total": len(missions),
            "stories_available": len(available),
            "issues": {
                "mission_sources_blocking": blocking_mission_count,
                "mission_sources_info": info_mission_count,
                "game_mission_id_orphans": gmi_issue_count,
            },
            "report": report,
            "game_mission_id_report": gmi_report,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1 if any_blocking else 0
    else:
        print(f"Missions: {len(missions)}")
        print(f"Available stories: {len(available)}")
        print()
        print(f"{'미션':<22} {'source':<28} {'EN':<8} {'KO':<8} {'issues'}")
        print("-" * 80)
        for r in report:
            en = "✓" if r["en_path"] else "✗"
            ko = "✓" if r["ko_path"] else "✗"
            issues = ",".join(r["issues"]) if r["issues"] else "OK"
            if args.missing_only and not r["issues"]:
                continue
            print(f"  {r['mission_id']:<20} {r['source']:<28} {en:<8} {ko:<8} {issues}")
        print()
        print("Cross-project: Fiction → wet_run mission links")
        gmi_issues = sum(1 for r in gmi_report if r["issues"])
        gmi_ok = len(gmi_report) - gmi_issues
        print(f"  Fiction stories with game_mission_id: {len(gmi_report)}")
        print(f"  Resolved (mission exists): {gmi_ok}")
        print(f"  Orphan (mission missing): {gmi_issues}")
        if gmi_issues > 0:
            print()
            print(f"  {'file':<60} {'game_mission_id':<22} {'issues'}")
            print("  " + "-" * 90)
            for r in gmi_report:
                if not r["issues"]:
                    continue
                print(
                    f"  {str(r['file']):<60} {str(r['game_mission_id']):<22} {','.join(r['issues'])}"
                )
        print()
        blocking_count = sum(1 for r in report if r.get("severity") == "blocking")
        info_count = sum(1 for r in report if r.get("severity") == "info")
        if info_count > 0:
            print(f"ℹ️  {info_count} missions intentionally have no Fiction source (out-of-scope)")
        if blocking_count > 0:
            print(f"⚠️  {blocking_count} missions have blocking source issues")
            return 1
        if gmi_issues > 0:
            print(f"⚠️  {gmi_issues} Fiction→mission cross-refs are orphans")
            return 1
        print("✓ All mission sources resolve correctly")
        print("✓ All Fiction→mission cross-refs resolve correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
