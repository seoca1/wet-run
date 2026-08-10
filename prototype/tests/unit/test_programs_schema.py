"""Tests for programs.json schema (P2 #20).

Every program should have:
- id (implicit, JSON key)
- name: human-readable name
- tier: 1-5
- type: attack | defense | detect | utility
- role: burst | strike | sustain | guard | utility
- ap_cost: 1-3 (affordable in single turn)
- description: short text

The role field is data-driven (not code-inferred) so it can be tuned
without code changes.
"""

from __future__ import annotations

import json
from pathlib import Path

VALID_TYPES = {"attack", "defense", "detect", "utility", "support"}
VALID_ROLES = {"burst", "strike", "sustain", "guard", "utility", "support"}


def test_every_program_has_role_field(data_dir: Path) -> None:
    programs_path = data_dir / "programs" / "programs.json"
    with programs_path.open(encoding="utf-8") as f:
        programs = json.load(f)
    missing = [pid for pid, prog in programs.items() if "role" not in prog or prog["role"] is None]
    assert not missing, f"Programs missing 'role' field: {missing}"


def test_every_program_role_is_valid(data_dir: Path) -> None:
    programs_path = data_dir / "programs" / "programs.json"
    with programs_path.open(encoding="utf-8") as f:
        programs = json.load(f)
    invalid = [
        (pid, prog["role"]) for pid, prog in programs.items() if prog.get("role") not in VALID_ROLES
    ]
    assert not invalid, f"Programs with invalid role: {invalid}"


def test_role_aligns_with_type(data_dir: Path) -> None:
    """Role semantics:
    - attack type → burst | strike | sustain (offensive)
    - defense type → guard
    - detect type → utility
    """
    programs_path = data_dir / "programs" / "programs.json"
    with programs_path.open(encoding="utf-8") as f:
        programs = json.load(f)

    expected_role_categories: dict[str, set[str]] = {
        "attack": {"burst", "strike", "sustain"},
        "defense": {"guard"},
        "detect": {"utility"},
        "support": {"support"},
        "utility": {"utility"},
    }

    mismatches = []
    for pid, prog in programs.items():
        type_ = prog.get("type")
        role = prog.get("role")
        if type_ not in expected_role_categories:
            mismatches.append(f"{pid}: unknown type {type_!r}")
            continue
        if role not in expected_role_categories[type_]:
            mismatches.append(f"{pid}: type={type_} but role={role!r}")
    assert not mismatches, f"Role/type mismatches: {mismatches}"


def test_burst_programs_have_high_damage(data_dir: Path) -> None:
    """Burst role → dmg >= 12 (heavy single hit)."""
    programs_path = data_dir / "programs" / "programs.json"
    with programs_path.open(encoding="utf-8") as f:
        programs = json.load(f)
    bursts = [p for p in programs.values() if p.get("role") == "burst"]
    assert bursts, "Expected at least one burst program"
    for prog in bursts:
        assert prog.get("damage", 0) >= 12, (
            f"{prog['name']} marked burst but damage={prog.get('damage')}"
        )


def test_guard_programs_have_shield(data_dir: Path) -> None:
    """Guard role → shield > 0."""
    programs_path = data_dir / "programs" / "programs.json"
    with programs_path.open(encoding="utf-8") as f:
        programs = json.load(f)
    guards = [p for p in programs.values() if p.get("role") == "guard"]
    assert guards, "Expected at least one guard program"
    for prog in guards:
        assert prog.get("shield", 0) > 0, (
            f"{prog['name']} marked guard but shield={prog.get('shield')}"
        )


def test_role_distribution_covers_diversity(data_dir: Path) -> None:
    """The catalog should have at least 3 distinct roles for loadout diversity."""
    programs_path = data_dir / "programs" / "programs.json"
    with programs_path.open(encoding="utf-8") as f:
        programs = json.load(f)
    roles_present = {prog.get("role") for prog in programs.values()}
    assert len(roles_present) >= 3, f"Too few distinct roles: {roles_present}"
