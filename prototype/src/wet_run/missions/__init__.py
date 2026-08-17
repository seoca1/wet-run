"""Mission subsystem (Arc 1, Phase 5).

A `Mission` describes a single cyberspace run: seed, zone, fixer, rewards.
The `JobBoard` filters missions by player grade (ADR-0008).
"""

from .board import JobBoard
from .mission import Mission

__all__ = ["JobBoard", "Mission"]
