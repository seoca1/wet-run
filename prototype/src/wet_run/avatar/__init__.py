"""Jockey avatar system (ADR-0016).

Renders a 5-7 line ASCII stick-figure avatar visualizing player state:
- Head shape: HP integrity (◉P◉ → X)
- Body pose: Status (SAFE → FUTILE)
- Arms: Program slots (tier 1-5, depleted/active)
- Torso: Deck (║DK7║)
- Legs: Wetware (▓▓▓▓)
- Surrounding echo: Construct companion (if any)
"""

from __future__ import annotations

from .renderer import build_avatar_state, render_avatar, render_avatar_lines
from .state import (
    AvatarLines,
    AvatarState,
    ConstructKind,
    ProgramSlot,
    Status,
)

__all__ = [
    "AvatarLines",
    "AvatarState",
    "ConstructKind",
    "ProgramSlot",
    "Status",
    "render_avatar",
    "render_avatar_lines",
    "build_avatar_state",
]
