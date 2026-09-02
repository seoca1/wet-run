#!/usr/bin/env python3
"""
update_search_index_gibson.py — Add Gibson style verification status to search_index.json.

Reads the Gibson verification JSON output and maps it to the search_index.json,
adding a 'gibson_style' field to each story with the verification status.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Paths
DASHBOARD_DATA = Path(__file__).resolve().parent.parent / "data"
SEARCH_INDEX = DASHBOARD_DATA / "search_index.json"
GIBSON_VERIFICATION = Path("/tmp/gibson_verification.json")
FICTION_DERIV = Path(__file__).resolve().parents[2] / "Fiction" / "derivative"

def load_gibson_verification() -> dict[str, dict]:
    """Load Gibson verification results and index by story path."""
    if not GIBSON_VERIFICATION.exists():
        print(f"Warning: {GIBSON_VERIFICATION} not found", file=sys.stderr)
        return {}
    
    with open(GIBSON_VERIFICATION) as f:
        data = json.load(f)
    
    # Index by story path (relative to workspace root)
    index = {}
    for item in data:
        # Convert path to match search_index.json id format
        # Example: "Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_black_ice_dream.md"
        # -> "2026-06-23_black_ice_dream"
        path = Path(item["path"])
        stem = path.stem  # Remove .md extension
        
        # Extract story id from filename (remove date prefix if present)
        # Filename format: YYYY-MM-DD_story_name.md
        parts = stem.split("_", 1)
        if len(parts) > 1 and len(parts[0]) == 10 and parts[0].count("-") == 2:
            story_id = parts[1]  # Remove date prefix
        else:
            story_id = stem
        
        # Get the check statuses
        checks = {c["check"]: c["status"] for c in item.get("checks", [])}
        
        index[story_id] = {
            "overall": item.get("overall", "partial"),
            "passed": item.get("passed", 0),
            "partial": item.get("partial", 0),
            "failed": item.get("failed", 0),
            "checks": checks,
        }
    
    return index

def update_search_index():
    """Update search_index.json with Gibson verification status."""
    # Load search index
    with open(SEARCH_INDEX) as f:
        search_index = json.load(f)
    
    # Load Gibson verification
    gibson_index = load_gibson_verification()
    
    if not gibson_index:
        print("No Gibson verification data found, skipping update", file=sys.stderr)
        return
    
    # Update each story
    updated_count = 0
    for story in search_index["stories"]:
        story_id = story.get("id", "")
        
        # Try to match by story_id
        if story_id in gibson_index:
            gibson = gibson_index[story_id]
            story["gibson_style"] = {
                "overall": gibson["overall"],
                "passed": gibson["passed"],
                "partial": gibson["partial"],
                "failed": gibson["failed"],
                "checks": gibson["checks"],
            }
            updated_count += 1
        else:
            # Try without date prefix
            parts = story_id.split("_", 1)
            if len(parts) > 1 and len(parts[0]) == 10 and parts[0].count("-") == 2:
                short_id = parts[1]
                if short_id in gibson_index:
                    gibson = gibson_index[short_id]
                    story["gibson_style"] = {
                        "overall": gibson["overall"],
                        "passed": gibson["passed"],
                        "partial": gibson["partial"],
                        "failed": gibson["failed"],
                        "checks": gibson["checks"],
                    }
                    updated_count += 1
    
    # Update metadata
    search_index["gibson_style_updated"] = "2026-08-31"
    search_index["gibson_style_stats"] = {
        "total_verified": len(gibson_index),
        "pass": sum(1 for v in gibson_index.values() if v["overall"] == "pass"),
        "partial": sum(1 for v in gibson_index.values() if v["overall"] == "partial"),
        "fail": sum(1 for v in gibson_index.values() if v["overall"] == "fail"),
    }
    
    # Write updated search index
    with open(SEARCH_INDEX, "w") as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {updated_count} stories with Gibson style verification data")
    print(f"Stats: {search_index['gibson_style_stats']}")

if __name__ == "__main__":
    update_search_index()
