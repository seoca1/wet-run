"""Boss Intro Enhancement sub-module (ADR-0150, boss_phase4 split).

3-stage text overlay on boss encounter:
1. Stage 1: [BOSS NAME]
2. Stage 2: role (e.g. WINTERMUTE // neural intruder)
3. Stage 3: warning (e.g. data vulnerable. personal trace detected.)

Pillar 정합 (ADR-0149 §Consequences.7):
- P5 (The Style): 5 unique 깁슨 어휘
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Boss ID aliases for matching (shared with taunts.py).
_BOSS_ALIASES: dict[str, str] = {
    "wintermute": "wintermute",
    "winter": "wintermute",
    "ta_prime": "ta_prime",
    "ta_construct_prime": "ta_prime",
    "ta": "ta_prime",
    "tessier": "ta_prime",
    "neuromancer": "neuromancer",
    "goliath_prime": "goliath_prime",
    "goliath": "goliath_prime",
    "black_ice_lord": "black_ice_lord",
    "black_ice": "black_ice_lord",
    "black": "black_ice_lord",
}


# Intro enhancement per boss (3-stage).
BOSS_INTRO: dict[str, dict[str, str]] = {
    "wintermute": {
        "stage_1": "[WINTERMUTE]",
        "stage_2": "WINTERMUTE // neural intruder",
        "stage_3": "data vulnerable. personal trace detected.",
    },
    "ta_prime": {
        "stage_1": "[T-A PRIME]",
        "stage_2": "TESSIER-ASHPOOL // family construct",
        "stage_3": "bloodline alert. intruder identity unknown.",
    },
    "neuromancer": {
        "stage_1": "[NEUROMANCER]",
        "stage_2": "NEUROMANCER // merge complete",
        "stage_3": "construct identity: ambiguous. operator: missing.",
    },
    "goliath_prime": {
        "stage_1": "[GOLIATH PRIME]",
        "stage_2": "GOLIATH PRIME // security core",
        "stage_3": "perimeter breach. architecture response: authorized.",
    },
    "black_ice_lord": {
        "stage_1": "[BLACK ICE LORD]",
        "stage_2": "BLACK ICE LORD // corrupted construct",
        "stage_3": "signal lost. operator compromised. trace: ongoing.",
    },
}


@dataclass(frozen=True, slots=True)
class BossIntroEnhancement:
    """3-stage text overlay for boss encounter (ADR-0149)."""

    stage_1: str
    stage_2: str
    stage_3: str


def normalize_boss_id(boss_id: str) -> str:
    """Map any boss ID variant to the canonical Phase 4 key.

    Shared helper used by ``mechanics.py`` (trigger) and ``taunts.py``
    (death taunt). Canonical keys: ``wintermute``, ``ta_prime``,
    ``neuromancer``, ``goliath_prime``, ``black_ice_lord``.
    """
    if not boss_id:
        return ""
    return _BOSS_ALIASES.get(boss_id.lower(), boss_id.lower())


def get_boss_intro(boss_id: str) -> BossIntroEnhancement | None:
    """Return the 3-stage intro enhancement for the given boss."""
    canonical = normalize_boss_id(boss_id)
    data = BOSS_INTRO.get(canonical)
    if data is None:
        return None
    return BossIntroEnhancement(
        stage_1=data["stage_1"],
        stage_2=data["stage_2"],
        stage_3=data["stage_3"],
    )


def apply_boss_intro_enhancement(app_state: Any, boss_id: str) -> BossIntroEnhancement | None:
    """Apply the 3-stage intro enhancement to app_state.boss_intro_enhancement.

    Returns the BossIntroEnhancement or None if not a known boss.
    """
    intro = get_boss_intro(boss_id)
    if intro is None:
        return None
    app_state.boss_intro_enhancement = intro
    return intro


__all__ = [
    "BOSS_INTRO",
    "BossIntroEnhancement",
    "apply_boss_intro_enhancement",
    "get_boss_intro",
    "normalize_boss_id",
]
