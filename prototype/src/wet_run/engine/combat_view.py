"""Combat screen: Real-Time with Menu Skills (RT-MS, ADR-0003).

Phase 5+: Integrates combat/ module with unified screen shell (layout).

Combat flow:
  1. Auto-attacks (both sides) every 2s
  2. Player can pause (M) to open skill menu
  3. Skill menu: select a skill (1-9), costs AP
  4. Time resumes after skill use
  5. Victory → Data Salvage (ADR-0014) → Hub
  6. Defeat → Death screen (ADR-0008)

Thin coordinator module after the ADR-0143 v2 split (2026-08-05):
    - combat_view (this file): re-exports + handle_combat_input passthrough
    - combat_view_input: input handling (handle_combat_input)
    - combat_view_render: screen + _draw_* helpers
    - combat_view_skills: skill management (_SKILL_SOUND_MAP, _execute_skill, etc.)
    - combat_view_state: combat state mutations + lifecycle (start_combat, _end_combat)

The original combat_view.py (972 LOC) is split into 4 modules:
    - combat_view_render (NEW, ~530 LOC): render_combat + 6 _draw_* + _hp_bar
    - combat_view_skills (NEW, ~180 LOC): skill execute + VFX + cooldown
    - combat_view_state (NEW, ~280 LOC): start/end + reputation + ICE removal
    - combat_view (this file, ~80 LOC): thin coordinator + re-exports

External imports of ``from wet_run.engine.combat_view import X``
continue to work via re-exports (ADR-0110 + ADR-0143 backward compat).
"""

from __future__ import annotations

from .combat_view_input import handle_combat_input  # noqa: F401 - re-export (only public API)

# Re-exports for backward compat (ADR-0110, ADR-0143).
# All public + previously-private symbols that were importable from combat_view
# remain importable via these re-exports. No external import site needs to change.
from .combat_view_render import (  # noqa: F401 - re-exports for backward compat
    _can_use_skill,
    _draw_action_log,
    _draw_combat_effects,
    _draw_combatants,
    _draw_first_combat_tutorial,
    _draw_skills_menu,
    _draw_vfx_overlay,
    _get_skill_effect_description,
    _hp_bar,
    render_combat,
)
from .combat_view_skills import (  # noqa: F401 - re-exports for backward compat
    _SKILL_SOUND_MAP,
    _execute_skill,
    _report_skill_unavailable,
    _spawn_skill_vfx,
)
from .combat_view_state import (  # noqa: F401 - re-exports for backward compat
    COMBAT_REPUTATION,
    _apply_combat_reputation,
    _check_post_combat_event,
    _defeat_current_ice_node,
    _end_combat,
    _remove_node_from_graph,
    spawn_phase_transition,
    start_combat,
)

__all__ = [
    "COMBAT_REPUTATION",
    "_SKILL_SOUND_MAP",
    "_apply_combat_reputation",
    "_can_use_skill",
    "_check_post_combat_event",
    "_defeat_current_ice_node",
    "_draw_action_log",
    "_draw_combat_effects",
    "_draw_combatants",
    "_draw_first_combat_tutorial",
    "_draw_skills_menu",
    "_draw_vfx_overlay",
    "_end_combat",
    "_execute_skill",
    "_get_skill_effect_description",
    "_hp_bar",
    "_remove_node_from_graph",
    "_report_skill_unavailable",
    "_spawn_skill_vfx",
    "handle_combat_input",
    "render_combat",
    "spawn_phase_transition",
    "start_combat",
]
