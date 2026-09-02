"""Effect parity test (Tier 5.6, ADR-0210).

Reads both:
- prototype/data/effects.json (canonical source)
- wet_run-web/src/data/effects.json (exported artifact)

Asserts both files expose the same set of `kind` names. Fails if the web
copy has drifted from the canonical source (e.g., export script wasn't
re-run after a schema change).

Run after any change to prototype/data/effects.json to verify web is in
sync.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_EFFECTS = REPO_ROOT / "prototype" / "data" / "effects.json"
WEB_EFFECTS = REPO_ROOT / "wet_run-web" / "src" / "data" / "effects.json"


def main() -> int:
    if not PROTOTYPE_EFFECTS.exists():
        print(f"missing: {PROTOTYPE_EFFECTS}", file=sys.stderr)
        return 1
    if not WEB_EFFECTS.exists():
        print(f"missing: {WEB_EFFECTS} — run export_effects.py first", file=sys.stderr)
        return 1

    with PROTOTYPE_EFFECTS.open() as f:
        py_data = json.load(f)
    with WEB_EFFECTS.open() as f:
        web_data = json.load(f)

    py_kinds = {e["kind"] for e in py_data.get("effects", [])}
    web_kinds = {e["kind"] for e in web_data.get("effects", [])}

    if py_kinds != web_kinds:
        only_py = py_kinds - web_kinds
        only_web = web_kinds - py_kinds
        print("EFFECT KINDS MISMATCH:", file=sys.stderr)
        if only_py:
            print(f"  only in prototype (canonical): {sorted(only_py)}", file=sys.stderr)
        if only_web:
            print(f"  only in wet_run-web (drifted): {sorted(only_web)}", file=sys.stderr)
        print("\nFix: run wet_run-web/scripts/export_effects.py to regenerate web copy.", file=sys.stderr)
        return 1

    py_versions = {e.get("duration_ms") for e in py_data.get("effects", [])}
    web_versions = {e.get("duration_ms") for e in web_data.get("effects", [])}
    if py_versions != web_versions:
        print("DURATION_MS MISMATCH between prototype and web copies", file=sys.stderr)
        return 1

    print(f"[effect_parity] OK — {len(py_kinds)} effect kinds match between prototype and web")
    print(f"[effect_parity] kinds: {sorted(py_kinds)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
