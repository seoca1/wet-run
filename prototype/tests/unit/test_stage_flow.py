"""Pytest-compatible regression test for stage flow data integrity."""

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("/Users/emilio/projects/Projects/Game/wet_run")
DATA_FILE = PROJECT_ROOT / "design/systems/stage_structure.json"
VALIDATOR = PROJECT_ROOT / "scripts/validate_stage_structure.py"


def test_validator_passes():
    """Stage flow validator returns exit 0 after ADR-0146 Option 3 fix."""
    r = subprocess.run(
        ["uv", "run", "python", str(VALIDATOR)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert r.returncode == 0, f"Validator failed (exit {r.returncode}):\n{r.stdout}\n{r.stderr}"
    assert "All validations passed" in r.stdout


def test_main_flow_stages_reachable_from_pending():
    """Main flow stages reachable from pending; black_market excluded (hub-side)."""
    main_flow = {
        "briefing",
        "travel",
        "meet_npc",
        "extract_data",
        "defeat_ice",
        "jack_out",
        "reward",
        "bypass_security",
    }
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    from collections import defaultdict

    graph = defaultdict(list)
    for t in data["transitions"]:
        graph[t["from"]].append(t["to"])

    visited = {"pending"}
    queue = ["pending"]
    while queue:
        s = queue.pop()
        for nxt in graph[s]:
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    unreachable_main = main_flow - visited
    assert not unreachable_main, f"Main flow stages unreachable from pending: {unreachable_main}"
    assert "black_market" not in visited, "black_market is hub-side (ADR-0146), not in main flow"


def test_black_market_to_pending_transition():
    """ADR-0146 Option 3: black_market → pending transition exists."""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    found = any(t["from"] == "black_market" and t["to"] == "pending" for t in data["transitions"])
    assert found, "Missing transition: black_market → pending (ADR-0146)"


def test_ghost_encounter_is_terminal():
    """ADR-0146 Option 3: ghost_encounter.is_terminal == true."""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for s in data["stages"]:
        if s["id"] == "ghost_encounter":
            assert s.get("is_terminal") is True, (
                "ghost_encounter.is_terminal must be true (ADR-0146)"
            )
            return
    raise AssertionError("ghost_encounter stage not found")


def test_transitions_have_required_fields():
    """Each transition has the required fields per validator schema."""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    required = {"from", "to", "trigger_en", "trigger_ko", "system"}
    for i, t in enumerate(data["transitions"]):
        missing = required - set(t.keys())
        assert not missing, (
            f"Transition {i} ({t.get('from', '?')} → {t.get('to', '?')}) missing fields: {missing}"
        )
