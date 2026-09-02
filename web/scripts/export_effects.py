#!/usr/bin/env python3
"""Export canonical combat VFX schema (effects.json) to wet_run-web.

Single source of truth lives at:
    prototype/data/effects.json

This script:
1. Validates the canonical schema (required fields, no duplicate kinds)
2. Writes a slimmed copy to wet_run-web/src/data/effects.json (no _schema_doc)
3. Writes a TypeScript type declaration to wet_run-web/src/data/effects.d.ts
4. Fails fast with explicit errors if schema is invalid

Usage:
    cd /Users/emilio/projects/Projects/Game/wet_run/wet_run-web
    python3 scripts/export_effects.py

Or from anywhere:
    python3 /path/to/wet_run-web/scripts/export_effects.py

Per ADR-0210: Python prototype is canonical source for combat VFX taxonomy.
wet_run-web consumes the exported JSON + .d.ts as read-only artifacts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_DATA = REPO_ROOT / "prototype" / "data"
EFFECTS_SRC = PROTOTYPE_DATA / "effects.json"

WEB_DATA = Path(__file__).resolve().parents[1] / "src" / "data"
EFFECTS_DST = WEB_DATA / "effects.json"
TYPES_DST = WEB_DATA / "effects.d.ts"

# Status kinds valid in payload (must match StatusIcon enum in Python).
VALID_STATUS_KINDS = {
    "POISON", "BURN", "STUN", "SHIELD", "BUFF", "DEBUFF", "REGEN", "DOT",
}
# ICE types valid in payload (must match IceType enum in Python).
VALID_ICE_TYPES = {
    "standard", "watchdog", "goliath", "black", "construct",
    "wintermute", "ta_construct_prime",
}
# Allowed categories.
VALID_CATEGORIES = {
    "combat.skill", "combat.hit", "combat.aoe",
    "status", "cinematic", "outcome", "matrix.dungeon",
}


def fail(msg: str) -> None:
    """Print error and exit non-zero."""
    print(f"[export_effects] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def validate_schema(data: dict) -> list[dict]:
    """Validate the canonical effects.json. Returns the list of effect entries."""
    if not isinstance(data, dict):
        fail("Root must be an object")
    schema_version = data.get("_schema_version")
    if not schema_version or not isinstance(schema_version, str):
        fail("Missing _schema_version (string required)")
    effects = data.get("effects")
    if not isinstance(effects, list) or len(effects) == 0:
        fail("Missing or empty 'effects' list")

    seen_kinds: set[str] = set()
    for i, entry in enumerate(effects):
        ctx = f"effects[{i}]"
        if not isinstance(entry, dict):
            fail(f"{ctx} must be an object")
        kind = entry.get("kind")
        if not isinstance(kind, str) or not kind:
            fail(f"{ctx}.kind must be non-empty string")
        if kind in seen_kinds:
            fail(f"{ctx}.kind '{kind}' duplicated (kinds must be unique)")
        seen_kinds.add(kind)

        category = entry.get("category")
        if category not in VALID_CATEGORIES:
            fail(f"{ctx} ({kind}).category '{category}' not in {VALID_CATEGORIES}")

        duration_ms = entry.get("duration_ms")
        if not isinstance(duration_ms, int) or duration_ms <= 0:
            fail(f"{ctx} ({kind}).duration_ms must be positive integer")

        color_hint = entry.get("color_hint")
        if not isinstance(color_hint, str):
            fail(f"{ctx} ({kind}).color_hint must be string")

        payload_shape = entry.get("payload_shape", {})
        if not isinstance(payload_shape, dict):
            fail(f"{ctx} ({kind}).payload_shape must be object")

            # Validate enum fields in payload_shape values.
            for field_name, field_type in payload_shape.items():
                base_type = field_type.split("[")[0] if "[" in field_type else field_type
                if base_type not in {
                    "string", "integer", "boolean",
                    "status_kind_enum", "ice_type_enum", "player|ice",
                } and "|" not in field_type:
                    fail(f"{ctx} ({kind}).payload_shape.{field_name} unknown type '{field_type}'")
                if base_type == "status_kind_enum" and field_name != "status_kind":
                    fail(f"{ctx} ({kind}).payload_shape.{field_name}: status_kind_enum must be named 'status_kind'")
                if base_type == "ice_type_enum" and field_name != "ice_type":
                    fail(f"{ctx} ({kind}).payload_shape.{field_name}: ice_type_enum must be named 'ice_type'")

    return effects


def web_payload_types(payload_shape: dict) -> str:
    """Convert payload_shape dict into a TypeScript type literal."""
    parts: list[str] = []
    for name, typ in payload_shape.items():
        ts_type = _payload_type_to_ts(typ)
        parts.append(f"  readonly {name}: {ts_type};")
    return "{\n" + "\n".join(parts) + "\n}" if parts else "Record<string, never>"


def _payload_type_to_ts(typ: str) -> str:
    """Map a schema type descriptor to a TS type."""
    base_type = typ.split("[")[0] if "[" in typ else typ
    mapping = {
        "string": "string",
        "integer": "number",
        "boolean": "boolean",
        "status_kind_enum": "StatusKind",
        "ice_type_enum": "IceType",
        "player|ice": '"player" | "ice"',
    }
    if base_type in mapping:
        return mapping[base_type]
    if "|" in typ:
        return typ
    return "unknown"


def render_d_ts(effects: list[dict]) -> str:
    """Render the effects.d.ts content."""
    kinds_literal = " | ".join(f'"{e["kind"]}"' for e in effects)
    status_kind_literal = " | ".join(f'"{k}"' for k in sorted(VALID_STATUS_KINDS))
    ice_type_literal = " | ".join(f'"{t}"' for t in sorted(VALID_ICE_TYPES))

    effect_entries: list[str] = []
    for e in effects:
        payload = web_payload_types(e.get("payload_shape", {}))
        duration_ticks = (e["duration_ms"] + 15) // 16  # ceil(ms / 16)
        entry = (
            f"export const EFFECT_{e['kind'].upper()}: {{\n"
            f"  readonly kind: \"{e['kind']}\";\n"
            f"  readonly category: \"{e['category']}\";\n"
            f"  readonly duration_ms: {e['duration_ms']};\n"
            f"  readonly duration_ticks: {duration_ticks};\n"
            f"  readonly color_hint: \"{e['color_hint']}\";\n"
            f"  readonly payload: {payload};\n"
            f"}};\n"
        )
        effect_entries.append(entry)

    return (
        "/** GENERATED by prototype/scripts/export_effects.py — do not edit. */\n"
        f"export type EffectKind = {kinds_literal};\n\n"
        f"export type StatusKind = {status_kind_literal};\n\n"
        f"export type IceType = {ice_type_literal};\n\n"
        f"export const EFFECTS: ReadonlyArray<EffectSpec> = [\n"
        + "".join(f"  EFFECT_{e['kind'].upper()},\n" for e in effects)
        + "];\n\n"
        + "export interface EffectSpec {\n"
        + "  readonly kind: EffectKind;\n"
        + "  readonly category: string;\n"
        + "  readonly duration_ms: number;\n"
        + "  readonly duration_ticks: number;\n"
        + "  readonly color_hint: string;\n"
        + "  readonly payload: Readonly<Record<string, unknown>>;\n"
        + "}\n\n"
        + "\n".join(effect_entries)
    )


def main() -> int:
    if not EFFECTS_SRC.exists():
        fail(f"Source file not found: {EFFECTS_SRC}")
    with EFFECTS_SRC.open() as f:
        data = json.load(f)

    effects = validate_schema(data)
    print(f"[export_effects] Validated {len(effects)} effects")

    WEB_DATA.mkdir(parents=True, exist_ok=True)

    # Slim copy for runtime (no _schema_doc/spec — internal metadata only).
    slim = {"_schema_version": data["_schema_version"], "effects": effects}
    EFFECTS_DST.write_text(json.dumps(slim, indent=2) + "\n")
    print(f"[export_effects] Wrote {EFFECTS_DST}")

    TYPES_DST.write_text(render_d_ts(effects))
    print(f"[export_effects] Wrote {TYPES_DST}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
