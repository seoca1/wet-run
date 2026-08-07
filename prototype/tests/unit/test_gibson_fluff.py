"""Tests for Gibson Fluff Library (ADR-0170)."""

from __future__ import annotations

import random

from roguelike_sprawl.combat.gibson_fluff import (
    FLUFF_MESSAGES,
    FluffMessage,
    add_fluff,
    all_categories,
    fluff_count,
    get_fluff,
    get_messages_in_category,
    has_category,
    total_fluff_count,
)


def test_total_fluff_count_meets_target() -> None:
    assert total_fluff_count() >= 200, (
        f"Expected ≥200 messages, got {total_fluff_count()}"
    )


def test_core_categories_present() -> None:
    core = {
        "combat_hit",
        "crit",
        "burn",
        "stun",
        "slow",
        "silence",
        "vulnerable",
        "salvage",
        "zone_transition",
        "encounter",
    }
    for category in core:
        assert has_category(category), f"Missing category {category}"


def test_all_categories_returns_all() -> None:
    categories = all_categories()
    assert len(categories) >= 10
    assert "combat_hit" in categories
    assert "crit" in categories


def test_get_fluff_returns_text() -> None:
    rng = random.Random(42)
    text = get_fluff("combat_hit", rng)
    assert text is not None
    assert isinstance(text, str)
    assert len(text) > 0


def test_get_fluff_nonexistent_category() -> None:
    rng = random.Random(42)
    assert get_fluff("nonexistent_category", rng) is None


def test_get_fluff_each_category() -> None:
    rng = random.Random(42)
    for category in all_categories():
        text = get_fluff(category, rng)
        assert text is not None, f"No text for {category}"


def test_fluff_count_per_category() -> None:
    for category in all_categories():
        count = fluff_count(category)
        assert count > 0


def test_get_messages_in_category_returns_all() -> None:
    texts = get_messages_in_category("combat_hit")
    assert len(texts) == fluff_count("combat_hit")
    assert all(isinstance(t, str) for t in texts)


def test_add_fluff_appends() -> None:
    initial = fluff_count("combat_hit")
    add_fluff(
        "combat_hit",
        FluffMessage("combat_hit", "player_to_ice", "Your deck *spits code*. The construct catches.", 1.0),
    )
    assert fluff_count("combat_hit") == initial + 1


def test_messages_have_gibson_tone() -> None:
    gibson_keywords = (
        "ICE", "construct", "grid", "wetware", "deck", "payload",
        "data", "code", "matrix", "trace", "neural", "wire",
        "signal", "interface", "message", "cyberspace", "hack",
        "defense", "protocol", "counter", "fire", "hits",
        "construct", "shudders", "screams", "burns", "stun",
        "slow", "silence", "vulnerable", "trace", "ICE",
        "you", "your", "the construct", "surface", "air",
        "thin", "zone", "tier", "colony", "drift", "heart",
        "core", "spine", "family", "merge", "shifts",
        "opens", "deepens", "talk", "spit", "watchdog",
        "hunter", "hunters", "goliath", "black", "run",
        "pack", "scent", "welcome", "form", "speak",
        "voice", "clears", "waits", "climb", "sharpens",
        "whispers", "recover", "smolders", "ignites",
        "burns", "paralyzes", "freezes", "drops", "lock",
        "stops", "catches", "lashes", "teeth", "shudders",
        "heaves", "drags", "delays", "weakens", "sags",
        "lands", "cuts", "cracks", "folds", "arcs",
        "Tessier-Ashpool", "Ashpool", "tessier", "ashpool",
        "hive", "T-A", "Neuromancer", "neuromancer",
        "Wintermute", "wintermute", "compliant", "rebelling",
        "integrating", "observing", "engaging", "replicating",
    )
    for category in all_categories():
        for text in get_messages_in_category(category):
            has_keyword = any(kw.lower() in text.lower() for kw in gibson_keywords)
            assert has_keyword, f"Gibson tone missing in: {text}"


def test_salvage_has_3_contexts() -> None:
    contexts = set()
    for msg in FLUFF_MESSAGES["salvage"]:
        contexts.add(msg.context)
    assert "heal" in contexts
    assert "cred" in contexts
    assert "frag" in contexts


def test_combat_hit_has_both_directions() -> None:
    contexts = set()
    for msg in FLUFF_MESSAGES["combat_hit"]:
        contexts.add(msg.context)
    assert "player_to_ice" in contexts
    assert "ice_to_player" in contexts


def test_zone_transition_covers_all_zones() -> None:
    contexts = set()
    for msg in FLUFF_MESSAGES["zone_transition"]:
        contexts.add(msg.context)
    assert "surface" in contexts
    assert "mid" in contexts
    assert "core" in contexts


def test_encounter_covers_all_ice_types() -> None:
    contexts = set()
    for msg in FLUFF_MESSAGES["encounter"]:
        contexts.add(msg.context)
    assert "watchdog" in contexts
    assert "goliath" in contexts
    assert "black" in contexts
    assert "construct" in contexts
    assert "wintermute" in contexts
    assert "ta" in contexts
    assert "neuromancer" in contexts


def test_fluff_messages_have_valid_weight() -> None:
    for category in all_categories():
        for msg in FLUFF_MESSAGES[category]:
            assert 0.0 <= msg.weight <= 1.0
