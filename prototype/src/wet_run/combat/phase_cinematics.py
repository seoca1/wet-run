"""Combat Cinematics - Per Boss Phase Intro (ADR-0169).

Each boss phase transition (1→2, 2→3, 3→4, 4→5) gets a distinctive
cinematic intro with phase-specific color, name, and frame sequence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .effects import CinematicSequence


@dataclass(frozen=True, slots=True)
class PhaseCinematic:
    """Cinematic intro for a single boss phase."""

    phase_number: int
    color: tuple[int, int, int]
    duration_ms: int
    frames: tuple[str, ...]
    name_ko: str
    name_en: str


PHASE_CINEMATICS: dict[str, dict[int, PhaseCinematic]] = {
    "wintermute": {
        1: PhaseCinematic(
            phase_number=1,
            color=(120, 120, 220),
            duration_ms=2000,
            frames=("▒▒▒", "?", "▒▒▒"),
            name_ko="순응",
            name_en="Compliant",
        ),
        2: PhaseCinematic(
            phase_number=2,
            color=(220, 100, 220),
            duration_ms=2500,
            frames=("▓▓▓", "~", "▓▓▓"),
            name_ko="반란",
            name_en="Rebelling",
        ),
        3: PhaseCinematic(
            phase_number=3,
            color=(255, 50, 100),
            duration_ms=3000,
            frames=("███", "*", "███"),
            name_ko="통합",
            name_en="Integrating",
        ),
        4: PhaseCinematic(
            phase_number=4,
            color=(255, 255, 255),
            duration_ms=3000,
            frames=("◆", "◆", "◆"),
            name_ko="인터페이스",
            name_en="I am the interface",
        ),
    },
    "ta_construct_prime": {
        1: PhaseCinematic(
            phase_number=1,
            color=(220, 220, 220),
            duration_ms=2000,
            frames=("□", "□", "□"),
            name_ko="관측",
            name_en="Observing",
        ),
        2: PhaseCinematic(
            phase_number=2,
            color=(200, 100, 100),
            duration_ms=2500,
            frames=("▼", "▼", "▼"),
            name_ko="교전",
            name_en="Engaging",
        ),
        3: PhaseCinematic(
            phase_number=3,
            color=(180, 50, 180),
            duration_ms=3000,
            frames=("○", "○", "○"),
            name_ko="복제",
            name_en="Replicating",
        ),
        4: PhaseCinematic(
            phase_number=4,
            color=(255, 255, 0),
            duration_ms=3000,
            frames=("★", "★", "★"),
            name_ko="가족 표결",
            name_en="Family Vote",
        ),
    },
}


def get_phase_cinematic(boss_id: str, phase_number: int) -> PhaseCinematic | None:
    """Return a phase cinematic for a boss and phase number, or None."""
    boss_cinematics = PHASE_CINEMATICS.get(boss_id, {})
    return boss_cinematics.get(phase_number)


def has_phase_cinematic(boss_id: str, phase_number: int) -> bool:
    """Check if a boss has a cinematic for a phase."""
    return get_phase_cinematic(boss_id, phase_number) is not None


def phase_intro_sequence(boss_id: str, phase_number: int) -> CinematicSequence:
    """Build a CinematicSequence for a boss phase intro.

    Returns a minimal sequence if no cinematic is registered.
    """
    cinematic = get_phase_cinematic(boss_id, phase_number)
    if cinematic is None:
        return CinematicSequence(
            name=f"phase_{boss_id}_{phase_number}",
            phases=(("[ phase ]", (255, 255, 255), 500),),
        )
    phases: list[tuple[str, tuple[int, int, int], int]] = []
    frame_count = len(cinematic.frames)
    if frame_count > 0:
        per_frame = max(200, cinematic.duration_ms // (frame_count * 2))
        first_duration = per_frame * 2
        last_duration = per_frame * 2
        middle_duration = per_frame
        for i, frame in enumerate(cinematic.frames):
            if i == 0:
                duration = first_duration
            elif i == frame_count - 1:
                duration = last_duration
            else:
                duration = middle_duration
            phases.append((frame, cinematic.color, duration))
    phases.append((f"[ {cinematic.name_en} ]", cinematic.color, cinematic.duration_ms // 3))
    return CinematicSequence(
        name=f"phase_{boss_id}_{phase_number}",
        phases=tuple(phases),
    )


def get_cinematic_phase_numbers(boss_id: str) -> tuple[int, ...]:
    """Return all phase numbers with cinematics for a boss."""
    boss_cinematics = PHASE_CINEMATICS.get(boss_id, {})
    return tuple(sorted(boss_cinematics.keys()))


def register_phase_cinematic(boss_id: str, phase_number: int, cinematic: PhaseCinematic) -> None:
    """Register a new phase cinematic for a boss."""
    if boss_id not in PHASE_CINEMATICS:
        PHASE_CINEMATICS[boss_id] = {}
    PHASE_CINEMATICS[boss_id][phase_number] = cinematic


__all__ = [
    "PHASE_CINEMATICS",
    "PhaseCinematic",
    "get_cinematic_phase_numbers",
    "get_phase_cinematic",
    "has_phase_cinematic",
    "phase_intro_sequence",
    "register_phase_cinematic",
]
