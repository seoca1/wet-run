"""Achievement System (ADR-0176).

60+ achievements across 4 categories (combat, exploration, meta, story).
Increases replay value and recognizes mastery.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Achievement:
    """A persistent achievement earned by the player."""

    id: str
    name: str
    description: str
    category: str
    hidden: bool = False


ACHIEVEMENTS: dict[str, Achievement] = {
    # Combat category (30)
    "first_blood": Achievement("first_blood", "FIRST BLOOD", "Defeat your first ICE", "combat"),
    "kill_10": Achievement("kill_10", "MASS MAKER", "Defeat 10 ICE", "combat"),
    "kill_100": Achievement("kill_100", "CENTURION", "Defeat 100 ICE", "combat"),
    "kill_500": Achievement("kill_500", "EXECUTIONER", "Defeat 500 ICE", "combat"),
    "kill_1000": Achievement("kill_1000", "REAPER", "Defeat 1000 ICE", "combat"),
    "kill_wintermute": Achievement(
        "kill_wintermute", "WINTERMUTE FALLS", "Defeat Wintermute", "combat"
    ),
    "kill_ta_prime": Achievement(
        "kill_ta_prime", "TESSIER FALLS", "Defeat T-A Construct Prime", "combat"
    ),
    "kill_5_wintermute": Achievement(
        "kill_5_wintermute", "WINTERMUTE HUNTER", "Defeat 5 Wintermute variants", "combat"
    ),
    "crit_10": Achievement("crit_10", "CRITICAL EYE", "Deal 10 critical hits", "combat"),
    "crit_100": Achievement("crit_100", "CRITIC MASTER", "Deal 100 critical hits", "combat"),
    "crit_1000": Achievement("crit_1000", "CRITIC SUPREME", "Deal 1000 critical hits", "combat"),
    "combo_5": Achievement("combo_5", "COMBO", "Achieve 5-combo chain", "combat"),
    "combo_10": Achievement("combo_10", "CHAIN", "Achieve 10-combo chain", "combat"),
    "combo_15": Achievement("combo_15", "FLURRY", "Achieve 15-combo chain", "combat"),
    "no_hit_run": Achievement(
        "no_hit_run", "UNTOUCHABLE", "Complete a run without taking damage", "combat"
    ),
    "no_damage_run": Achievement(
        "no_damage_run", "PERFECT RUN", "Complete a run with 0 HP lost", "combat"
    ),
    "boss_phase_5": Achievement(
        "boss_phase_5", "LAST STAND", "Witness a boss reach Phase 5", "combat"
    ),
    "boss_phase_4": Achievement("boss_phase_4", "FINALE", "Witness a boss reach Phase 4", "combat"),
    "multienemy_3": Achievement("multienemy_3", "OUTNUMBERED", "Survive a 1v3 encounter", "combat"),
    "all_ice_kinds": Achievement("all_ice_kinds", "TAXIDERMIST", "Defeat every ICE type", "combat"),
    "boss_no_damage": Achievement(
        "boss_no_damage", "UNTOUCHABLE BOSS", "Defeat a boss without taking damage", "combat"
    ),
    "construct_companion_5": Achievement(
        "construct_companion_5", "BOND", "Use Dixie ally 5 times", "combat"
    ),
    "status_effect_master": Achievement(
        "status_effect_master", "PLAGUE", "Apply all 5 status effects in one run", "combat"
    ),
    "burn_100": Achievement("burn_100", "ARSONIST", "Inflict 100 burn ticks", "combat"),
    "stun_50": Achievement("stun_50", "PARALYZER", "Stun 50 ICE", "combat"),
    "slow_50": Achievement("slow_50", "HONEY", "Slow 50 ICE", "combat"),
    "vulnerable_50": Achievement("vulnerable_50", "EXPOSED", "Vulnerable 50 ICE", "combat"),
    "silence_25": Achievement("silence_25", "MUTED", "Silence 25 ICE", "combat"),
    "boss_perfect": Achievement(
        "boss_perfect", "PERFECT BOSS", "Defeat boss without any status effects applied", "combat"
    ),
    # Exploration category (15)
    "all_zones": Achievement("all_zones", "CARTOGRAPHER", "Visit every zone", "exploration"),
    "every_ice": Achievement(
        "every_ice", "BESTIARY", "Encounter 50 unique ICE types", "exploration"
    ),
    "deep_run": Achievement("deep_run", "DEEPER", "Reach zone depth 5", "exploration"),
    "deeper_run": Achievement("deeper_run", "DEEPEST", "Reach zone depth 10", "exploration"),
    "all_factions": Achievement("all_factions", "DIPLOMAT", "Visit every faction", "exploration"),
    "all_intel": Achievement("all_intel", "INFORMANT", "Collect all intel items", "exploration"),
    "hidden_node": Achievement("hidden_node", "EXPLORER", "Find a hidden node", "exploration"),
    "all_constructs": Achievement(
        "all_constructs", "DIPLOMAT II", "Visit every construct", "exploration"
    ),
    "all_fixes": Achievement("all_fixes", "CONNECTED", "Talk to every fixer", "exploration"),
    "phase_6_visited": Achievement(
        "phase_6_visited", "THE AFTERMATH", "Visit Phase 6 zone", "exploration"
    ),
    "all_mission_archetypes": Achievement(
        "all_mission_archetypes", "VARIETY", "Complete all 4 mission archetypes", "exploration"
    ),
    "all_matrix_events": Achievement(
        "all_matrix_events", "WITNESSED", "Trigger all 6 random matrix events", "exploration"
    ),
    "all_ice_personalities": Achievement(
        "all_ice_personalities", "PSYCHOLOGIST", "Encounter all 4 ICE personalities", "exploration"
    ),
    "dead_drop": Achievement(
        "dead_drop", "DEAD DROP", "Find a hidden data drop", "exploration", hidden=True
    ),
    "ghost_signal": Achievement(
        "ghost_signal", "GHOST", "Receive a ghost signal", "exploration", hidden=True
    ),
    # Meta category (10)
    "win_1": Achievement("win_1", "FIRST WIN", "Win your first run", "meta"),
    "win_5": Achievement("win_5", "VETERAN", "Win 5 runs", "meta"),
    "win_10": Achievement("win_10", "EXPERT", "Win 10 runs", "meta"),
    "win_20": Achievement("win_20", "MASTER", "Win 20 runs", "meta"),
    "win_ng_plus": Achievement("win_ng_plus", "AFTERLIFE", "Win NG+", "meta"),
    "all_mutators": Achievement(
        "all_mutators", "RUNNER", "Complete runs with all 5 mutators", "meta"
    ),
    "all_archetypes": Achievement(
        "all_archetypes", "DIVERSE", "Complete missions of all 4 archetypes", "meta"
    ),
    "hardcore": Achievement("hardcore", "HARDCORE", "Complete Hardcore mode", "meta"),
    "deathless": Achievement("deathless", "DEATHLESS", "Complete a run without flatline", "meta"),
    "all_decks": Achievement("all_decks", "ARCHITECT", "Use all deck presets", "meta"),
    # Story category (5)
    "beat_arc5": Achievement("beat_arc5", "NEUROMANCER", "Complete Arc 5", "story"),
    "phase_6_complete": Achievement("phase_6_complete", "RESIDUE", "Complete Phase 6 Arc", "story"),
    "epilogue": Achievement("epilogue", "EPILOGUE", "Witness the epilogue", "story"),
    "all_endings": Achievement("all_endings", "COLLECTOR", "Witness all 3 endings", "story"),
    "true_ending": Achievement(
        "true_ending", "THE MESSAGE", "Witness the true ending", "story", hidden=True
    ),
}


def get_achievements() -> tuple[Achievement, ...]:
    """Return all achievements."""
    return tuple(ACHIEVEMENTS.values())


def get_achievement_count() -> int:
    """Return the number of registered achievements."""
    return len(ACHIEVEMENTS)


def get_achievement_by_id(ach_id: str) -> Achievement | None:
    """Return achievement by id."""
    return ACHIEVEMENTS.get(ach_id)


def get_achievements_by_category(category: str) -> tuple[Achievement, ...]:
    """Return all achievements in a category."""
    return tuple(a for a in ACHIEVEMENTS.values() if a.category == category)


def get_visible_achievements() -> tuple[Achievement, ...]:
    """Return non-hidden achievements."""
    return tuple(a for a in ACHIEVEMENTS.values() if not a.hidden)


def get_hidden_achievements() -> tuple[Achievement, ...]:
    """Return hidden achievements."""
    return tuple(a for a in ACHIEVEMENTS.values() if a.hidden)


def get_achievement_visibility(ach_id: str) -> bool:
    """Return True if achievement is visible (not hidden)."""
    ach = ACHIEVEMENTS.get(ach_id)
    if ach is None:
        return False
    return not ach.hidden


def get_achievements_count_by_category() -> dict[str, int]:
    """Return count of achievements by category."""
    counts: dict[str, int] = {}
    for a in ACHIEVEMENTS.values():
        counts[a.category] = counts.get(a.category, 0) + 1
    return counts


__all__ = [
    "ACHIEVEMENTS",
    "Achievement",
    "get_achievement_by_id",
    "get_achievement_count",
    "get_achievement_visibility",
    "get_achievements",
    "get_achievements_by_category",
    "get_achievements_count_by_category",
    "get_hidden_achievements",
    "get_visible_achievements",
]
