"""Combat visual effects — cinematic sequences (ADR-0145 module split).

Extracted from combat/effects_vfx.py to reduce that module below the
856 LOC threshold. Provides scripted multi-phase cinematics for ICE
intro/death + boss phase transitions (ADR-0050).

Module structure (post ADR-0145):
  - combat/effects_vfx_animations: 14 animation generators + factory
  - combat/effects_vfx_cinematics (this file): ICE intro/death + boss phase
  - combat/effects_vfx_compose: CombatEffects class + 10 spawn functions
  - combat/effects_vfx: thin re-export facade

Each cinematic is a CinematicSequence (from effects_data) with phase tuples
(text, color, duration_ms). The sequence advances automatically via
CombatEffects.step().
"""

from __future__ import annotations

from .effects_data import CinematicSequence, IceType
from .palette import (
    COMBO_BAR_RED,
    DAMAGE_COLOR,
    DAMAGE_FLASH_COLOR,
    DEFAULT_COLOR,
    DYING_COLOR,
    GLITCH_COLOR,
    GOLIATH_PARTICLE_COLOR,
    GRAY_160,
    GRAY_BRIGHT,
    GRAY_LIGHT,
    GRAY_MID,
    GRAY_MID_DARK,
    ICE_FADE_BROWN,
    ICE_GRAY_BLUE,
    ICE_GRAY_LIGHT,
    ICE_RED_PINK,
    ICE_TYPE_PATROL_COLOR,
    ICE_TYPE_WATCHDOG_COLOR,
    MAGENTA_DEEP,
    MAGENTA_PINK,
    PURPLE_DEEP,
    TA_CONSTRUCT_P1_COLOR,
    TA_CONSTRUCT_P2_COLOR,
    TA_CONSTRUCT_P3_COLOR,
    WINTERMUTE_FADE,
    WINTERMUTE_P1_COLOR,
    WINTERMUTE_P2_COLOR,
    WINTERMUTE_P3_COLOR,
)


def ice_intro_sequence(ice_type: IceType, name: str) -> CinematicSequence:
    """A scripted intro sequence unique to each ICE type."""
    if ice_type == IceType.STANDARD:
        return CinematicSequence(
            name="standard_intro",
            phases=(
                (f"[ {name} ]", ICE_TYPE_PATROL_COLOR, 300),
                (f"[· {name} ·]", GRAY_BRIGHT, 250),
                (f"·· {name} ··", (220, 220, 240), 200),
                (f"·· {name} ··", (240, 240, 255), 800),
            ),
        )
    if ice_type == IceType.WATCHDOG:
        return CinematicSequence(
            name="watchdog_intro",
            phases=(
                ("[ grrr... ]", (200, 150, 100), 250),
                (f"[ {name} ]", (220, 170, 100), 200),
                ("WOOF!", GOLIATH_PARTICLE_COLOR, 120),
                (f"·{name}·", (255, 150, 100), 200),
                (f"·{name}·", (255, 200, 100), 800),
            ),
        )
    if ice_type == IceType.GOLIATH:
        return CinematicSequence(
            name="goliath_intro",
            phases=(
                ("...", (100, 100, 120), 300),
                (f"[ {name} ]", ICE_GRAY_BLUE, 200),
                (f"[ {name} ]", TA_CONSTRUCT_P2_COLOR, 100),
                (f"··[{name}]··", COMBO_BAR_RED, 100),
                (f"··[{name}]··", DAMAGE_FLASH_COLOR, 1000),
            ),
        )
    if ice_type == IceType.BLACK:
        return CinematicSequence(
            name="black_intro",
            phases=(
                ("·▓▓▓·", DEFAULT_COLOR, 200),
                ("·█▓█▓█·", (180, 180, 180), 150),
                ("▓█▓▓█▓", GRAY_160, 150),
                (f"[{name}]", GLITCH_COLOR, 100),
                (f"[{name}]", GRAY_MID, 100),
                (f"[{name}]", MAGENTA_DEEP, 100),
                (f"[{name}]", GRAY_MID_DARK, 1200),
            ),
        )
    # ADR-0050: Boss ICE multi-phase intros (BEFORE construct fall-through)
    if ice_type == IceType.WINTERMUTE:
        return CinematicSequence(
            name="wintermute_intro",
            phases=(
                ("...", (80, 80, 120), 300),
                ("·?·", (100, 100, 150), 200),
                (f"[ {name} ]", WINTERMUTE_P1_COLOR, 300),
                (f"[ {name} ]", (140, 140, 240), 200),
                (f"[ {name} ]", (160, 160, 255), 800),
                ("PHASE 1/3: COMPLIANT", WINTERMUTE_P1_COLOR, 600),
            ),
        )
    if ice_type == IceType.TA_CONSTRUCT_PRIME:
        return CinematicSequence(
            name="ta_construct_prime_intro",
            phases=(
                ("·[ ⚙ ]·", (150, 150, 180), 200),
                ("·[ ⚙⚙ ]·", ICE_TYPE_PATROL_COLOR, 200),
                (f"[ {name} ]", GRAY_BRIGHT, 300),
                (f"[ {name} ]", (220, 220, 240), 300),
                (f"[ {name} ]", (240, 240, 255), 800),
                ("PHASE 1/3: OBSERVING", TA_CONSTRUCT_P1_COLOR, 600),
            ),
        )
    # construct
    return CinematicSequence(
        name="construct_intro",
        phases=(
            ("·[ ⚙ ]·", (150, 150, 180), 200),
            ("·[ ⚙ ]·", ICE_TYPE_PATROL_COLOR, 150),
            ("[ ⚙⚙⚙ ]", GRAY_BRIGHT, 200),
            (f"[ {name} ]", (220, 220, 240), 250),
            (f"[ {name} ]", (240, 240, 255), 1000),
        ),
    )


def boss_phase_transition_sequence(
    ice_type: IceType, phase: int, total_phases: int = 3
) -> CinematicSequence:
    """Cinematic for a boss transitioning to a new phase.

    Args:
        ice_type: The boss's IceType (WINTERMUTE or TA_CONSTRUCT_PRIME).
        phase: The new phase number (2 or 3).
        total_phases: Total phases (default 3).
    """
    if ice_type == IceType.WINTERMUTE:
        # Glitchy pink/purple
        if phase == 2:
            return CinematicSequence(
                name="wintermute_phase_2_transition",
                phases=(
                    ("▓▓▓", DEFAULT_COLOR, 100),
                    ("▓█▓█▓", WINTERMUTE_P2_COLOR, 100),
                    ("[ ADAPTING ]", WINTERMUTE_P2_COLOR, 300),
                    (f"PHASE {phase}/{total_phases}: REBELLING", WINTERMUTE_P2_COLOR, 600),
                    (f"PHASE {phase}/{total_phases}: REBELLING", MAGENTA_PINK, 600),
                ),
            )
        # phase 3
        return CinematicSequence(
            name="wintermute_phase_3_transition",
            phases=(
                ("█▓█▓█", DEFAULT_COLOR, 100),
                ("▓█▓▓█▓", WINTERMUTE_P3_COLOR, 100),
                ("[ INTEGRATING ]", WINTERMUTE_P3_COLOR, 300),
                (f"PHASE {phase}/{total_phases}: INTEGRATING", WINTERMUTE_P3_COLOR, 600),
                (f"PHASE {phase}/{total_phases}: INTEGRATING", (255, 0, 50), 800),
            ),
        )
    if ice_type == IceType.TA_CONSTRUCT_PRIME:
        if phase == 2:
            return CinematicSequence(
                name="ta_construct_prime_phase_2_transition",
                phases=(
                    ("⚙⚙⚙", TA_CONSTRUCT_P1_COLOR, 200),
                    ("⚙REPLICATING⚙", TA_CONSTRUCT_P2_COLOR, 300),
                    (f"PHASE {phase}/{total_phases}: ENGAGING", TA_CONSTRUCT_P2_COLOR, 600),
                    (f"PHASE {phase}/{total_phases}: ENGAGING", DAMAGE_FLASH_COLOR, 600),
                ),
            )
        return CinematicSequence(
            name="ta_construct_prime_phase_3_transition",
            phases=(
                ("⚙⚙⚙", TA_CONSTRUCT_P1_COLOR, 200),
                ("⚙OVERRIDING⚙", TA_CONSTRUCT_P3_COLOR, 300),
                (f"PHASE {phase}/{total_phases}: REPLICATING", TA_CONSTRUCT_P3_COLOR, 600),
                (f"PHASE {phase}/{total_phases}: REPLICATING", WINTERMUTE_FADE, 800),
            ),
        )
    # Unknown boss — generic
    return CinematicSequence(
        name=f"{ice_type.value}_phase_{phase}_transition",
        phases=(
            (f"PHASE {phase}/{total_phases}", DEFAULT_COLOR, 600),
            (f"PHASE {phase}/{total_phases}", ICE_GRAY_LIGHT, 600),
        ),
    )


def ice_death_sequence(ice_type: IceType) -> CinematicSequence:
    """A scripted death sequence unique to each ICE type."""
    if ice_type == IceType.STANDARD:
        return CinematicSequence(
            name="standard_death",
            phases=(
                ("[X_X]", DAMAGE_COLOR, 100),
                ("[>_>]", TA_CONSTRUCT_P2_COLOR, 100),
                ("[X_X]", GRAY_LIGHT, 100),
                ("·[·]·", DEFAULT_COLOR, 150),
                ("· · ·", (180, 180, 180), 200),
            ),
        )
    if ice_type == IceType.WATCHDOG:
        return CinematicSequence(
            name="watchdog_death",
            phases=(
                ("woof...?", ICE_TYPE_WATCHDOG_COLOR, 200),
                ("[X_O]", (200, 150, 100), 150),
                ("[X_X]", ICE_RED_PINK, 150),
                ("[X_X]", ICE_FADE_BROWN, 200),
                ("· · ·", DEFAULT_COLOR, 300),
            ),
        )
    if ice_type == IceType.GOLIATH:
        return CinematicSequence(
            name="goliath_death",
            phases=(
                ("[X_X]", GOLIATH_PARTICLE_COLOR, 100),
                ("[X!X]", DAMAGE_FLASH_COLOR, 100),
                ("[#_#]", TA_CONSTRUCT_P2_COLOR, 150),
                ("·[·]·", DEFAULT_COLOR, 200),
                ("· · ·", (180, 180, 180), 300),
            ),
        )
    if ice_type == IceType.BLACK:
        return CinematicSequence(
            name="black_death",
            phases=(
                (f"[{GLITCH_COLOR}]", GLITCH_COLOR, 100),
                ("[ERR]", DYING_COLOR, 100),
                ("[___]", GRAY_MID, 100),
                ("[XXX]", GRAY_MID_DARK, 150),
                ("· · ·", DEFAULT_COLOR, 300),
            ),
        )
    # construct
    if ice_type == IceType.WINTERMUTE:
        return CinematicSequence(
            name="wintermute_death",
            phases=(
                ("[▓▓▓]", PURPLE_DEEP, 100),
                ("[???]", MAGENTA_PINK, 100),
                ("[XXX]", (200, 50, 100), 150),
                ("·▓▓▓·", GRAY_MID, 200),
                ("· · ·", DEFAULT_COLOR, 300),
            ),
        )
    if ice_type == IceType.TA_CONSTRUCT_PRIME:
        return CinematicSequence(
            name="ta_construct_prime_death",
            phases=(
                ("[⚙⚙⚙]", TA_CONSTRUCT_P2_COLOR, 100),
                ("[⚠⚠⚠]", TA_CONSTRUCT_P3_COLOR, 100),
                ("[___]", GRAY_LIGHT, 150),
                ("·[ ]·", (180, 180, 180), 200),
                ("· · ·", DEFAULT_COLOR, 300),
            ),
        )
    return CinematicSequence(
        name="construct_death",
        phases=(
            ("[⚙X⚙]", GOLIATH_PARTICLE_COLOR, 100),
            ("[⚠⚠⚠]", (255, 200, 100), 100),
            ("[___]", DEFAULT_COLOR, 150),
            ("·[ ]·", (180, 180, 180), 200),
            ("· · ·", DEFAULT_COLOR, 300),
        ),
    )


__all__ = [
    "boss_phase_transition_sequence",
    "ice_death_sequence",
    "ice_intro_sequence",
]
