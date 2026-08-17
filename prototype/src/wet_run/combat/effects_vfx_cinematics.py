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
from .palette import DAMAGE_COLOR, GLITCH_COLOR


def ice_intro_sequence(ice_type: IceType, name: str) -> CinematicSequence:
    """A scripted intro sequence unique to each ICE type."""
    if ice_type == IceType.STANDARD:
        return CinematicSequence(
            name="standard_intro",
            phases=(
                (f"[ {name} ]", (180, 180, 200), 300),
                (f"[· {name} ·]", (200, 200, 220), 250),
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
                ("WOOF!", (255, 100, 100), 120),
                (f"·{name}·", (255, 150, 100), 200),
                (f"·{name}·", (255, 200, 100), 800),
            ),
        )
    if ice_type == IceType.GOLIATH:
        return CinematicSequence(
            name="goliath_intro",
            phases=(
                ("...", (100, 100, 120), 300),
                (f"[ {name} ]", (150, 150, 170), 200),
                (f"[ {name} ]", (200, 100, 100), 100),
                (f"··[{name}]··", (255, 80, 80), 100),
                (f"··[{name}]··", (255, 50, 50), 1000),
            ),
        )
    if ice_type == IceType.BLACK:
        return CinematicSequence(
            name="black_intro",
            phases=(
                ("·▓▓▓·", (200, 200, 200), 200),
                ("·█▓█▓█·", (180, 180, 180), 150),
                ("▓█▓▓█▓", (160, 160, 160), 150),
                (f"[{name}]", GLITCH_COLOR, 100),
                (f"[{name}]", (100, 100, 100), 100),
                (f"[{name}]", (200, 0, 200), 100),
                (f"[{name}]", (80, 80, 80), 1200),
            ),
        )
    # ADR-0050: Boss ICE multi-phase intros (BEFORE construct fall-through)
    if ice_type == IceType.WINTERMUTE:
        return CinematicSequence(
            name="wintermute_intro",
            phases=(
                ("...", (80, 80, 120), 300),
                ("·?·", (100, 100, 150), 200),
                (f"[ {name} ]", (120, 120, 220), 300),
                (f"[ {name} ]", (140, 140, 240), 200),
                (f"[ {name} ]", (160, 160, 255), 800),
                ("PHASE 1/3: COMPLIANT", (120, 120, 220), 600),
            ),
        )
    if ice_type == IceType.TA_CONSTRUCT_PRIME:
        return CinematicSequence(
            name="ta_construct_prime_intro",
            phases=(
                ("·[ ⚙ ]·", (150, 150, 180), 200),
                ("·[ ⚙⚙ ]·", (180, 180, 200), 200),
                (f"[ {name} ]", (200, 200, 220), 300),
                (f"[ {name} ]", (220, 220, 240), 300),
                (f"[ {name} ]", (240, 240, 255), 800),
                ("PHASE 1/3: OBSERVING", (220, 220, 220), 600),
            ),
        )
    # construct
    return CinematicSequence(
        name="construct_intro",
        phases=(
            ("·[ ⚙ ]·", (150, 150, 180), 200),
            ("·[ ⚙ ]·", (180, 180, 200), 150),
            ("[ ⚙⚙⚙ ]", (200, 200, 220), 200),
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
                    ("▓▓▓", (200, 200, 200), 100),
                    ("▓█▓█▓", (220, 100, 220), 100),
                    ("[ ADAPTING ]", (220, 100, 220), 300),
                    (f"PHASE {phase}/{total_phases}: REBELLING", (220, 100, 220), 600),
                    (f"PHASE {phase}/{total_phases}: REBELLING", (255, 50, 200), 600),
                ),
            )
        # phase 3
        return CinematicSequence(
            name="wintermute_phase_3_transition",
            phases=(
                ("█▓█▓█", (200, 200, 200), 100),
                ("▓█▓▓█▓", (255, 50, 100), 100),
                ("[ INTEGRATING ]", (255, 50, 100), 300),
                (f"PHASE {phase}/{total_phases}: INTEGRATING", (255, 50, 100), 600),
                (f"PHASE {phase}/{total_phases}: INTEGRATING", (255, 0, 50), 800),
            ),
        )
    if ice_type == IceType.TA_CONSTRUCT_PRIME:
        if phase == 2:
            return CinematicSequence(
                name="ta_construct_prime_phase_2_transition",
                phases=(
                    ("⚙⚙⚙", (220, 220, 220), 200),
                    ("⚙REPLICATING⚙", (200, 100, 100), 300),
                    (f"PHASE {phase}/{total_phases}: ENGAGING", (200, 100, 100), 600),
                    (f"PHASE {phase}/{total_phases}: ENGAGING", (255, 50, 50), 600),
                ),
            )
        return CinematicSequence(
            name="ta_construct_prime_phase_3_transition",
            phases=(
                ("⚙⚙⚙", (220, 220, 220), 200),
                ("⚙OVERRIDING⚙", (180, 50, 180), 300),
                (f"PHASE {phase}/{total_phases}: REPLICATING", (180, 50, 180), 600),
                (f"PHASE {phase}/{total_phases}: REPLICATING", (220, 0, 220), 800),
            ),
        )
    # Unknown boss — generic
    return CinematicSequence(
        name=f"{ice_type.value}_phase_{phase}_transition",
        phases=(
            (f"PHASE {phase}/{total_phases}", (200, 200, 200), 600),
            (f"PHASE {phase}/{total_phases}", (240, 240, 240), 600),
        ),
    )


def ice_death_sequence(ice_type: IceType) -> CinematicSequence:
    """A scripted death sequence unique to each ICE type."""
    if ice_type == IceType.STANDARD:
        return CinematicSequence(
            name="standard_death",
            phases=(
                ("[X_X]", DAMAGE_COLOR, 100),
                ("[>_>]", (200, 100, 100), 100),
                ("[X_X]", (150, 150, 150), 100),
                ("·[·]·", (200, 200, 200), 150),
                ("· · ·", (180, 180, 180), 200),
            ),
        )
    if ice_type == IceType.WATCHDOG:
        return CinematicSequence(
            name="watchdog_death",
            phases=(
                ("woof...?", (220, 180, 100), 200),
                ("[X_O]", (200, 150, 100), 150),
                ("[X_X]", (180, 100, 100), 150),
                ("[X_X]", (150, 80, 80), 200),
                ("· · ·", (200, 200, 200), 300),
            ),
        )
    if ice_type == IceType.GOLIATH:
        return CinematicSequence(
            name="goliath_death",
            phases=(
                ("[X_X]", (255, 100, 100), 100),
                ("[X!X]", (255, 50, 50), 100),
                ("[#_#]", (200, 100, 100), 150),
                ("·[·]·", (200, 200, 200), 200),
                ("· · ·", (180, 180, 180), 300),
            ),
        )
    if ice_type == IceType.BLACK:
        return CinematicSequence(
            name="black_death",
            phases=(
                (f"[{GLITCH_COLOR}]", GLITCH_COLOR, 100),
                ("[ERR]", (255, 0, 0), 100),
                ("[___]", (100, 100, 100), 100),
                ("[XXX]", (80, 80, 80), 150),
                ("· · ·", (200, 200, 200), 300),
            ),
        )
    # construct
    if ice_type == IceType.WINTERMUTE:
        return CinematicSequence(
            name="wintermute_death",
            phases=(
                ("[▓▓▓]", (200, 100, 220), 100),
                ("[???]", (255, 50, 200), 100),
                ("[XXX]", (200, 50, 100), 150),
                ("·▓▓▓·", (100, 100, 100), 200),
                ("· · ·", (200, 200, 200), 300),
            ),
        )
    if ice_type == IceType.TA_CONSTRUCT_PRIME:
        return CinematicSequence(
            name="ta_construct_prime_death",
            phases=(
                ("[⚙⚙⚙]", (200, 100, 100), 100),
                ("[⚠⚠⚠]", (180, 50, 180), 100),
                ("[___]", (150, 150, 150), 150),
                ("·[ ]·", (180, 180, 180), 200),
                ("· · ·", (200, 200, 200), 300),
            ),
        )
    return CinematicSequence(
        name="construct_death",
        phases=(
            ("[⚙X⚙]", (255, 100, 100), 100),
            ("[⚠⚠⚠]", (255, 200, 100), 100),
            ("[___]", (200, 200, 200), 150),
            ("·[ ]·", (180, 180, 180), 200),
            ("· · ·", (200, 200, 200), 300),
        ),
    )


__all__ = [
    "boss_phase_transition_sequence",
    "ice_death_sequence",
    "ice_intro_sequence",
]
