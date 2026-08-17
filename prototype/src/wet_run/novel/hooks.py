"""Hooks layer (ADR-0061).

A *hook* describes how a story excerpt translates into a runtime
effect on the game.  Each hook has a *kind* (event, combat, item,
excerpt, cinematic, narrative) and a *payload* (extracted from the
story's content or its mission mapping).

The dispatcher in ``dispatcher.py`` consumes a hook and calls the
associated ``HookAction`` registered in this module.  Actions are
plain Python functions — keeping the registry explicit makes the
novel-to-game surface easy to extend without subclassing.

To add a new hook kind, extend the ``HookKind`` enum and register a
matching action with ``register_hook_action(kind, action)``.  No
existing code has to change; the dispatcher consults the registry at
call time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HookKind(StrEnum):
    """The runtime effect a story can have on a game in progress.

    New kinds may be added without modifying call sites; the registry
    looks up the action by string at dispatch time.
    """

    NARRATIVE = "narrative"  # show on chapter screen
    EXCERPT = "excerpt"  # show inline on dungeon/cyberscape
    EVENT = "event"  # trigger an EventState cutscene
    COMBAT = "combat"  # drive combat_state.ice_kind
    ITEM = "item"  # add inventory / data fragment
    CINEMATIC = "cinematic"  # play a graphic-novel scene


@dataclass(slots=True)
class HookContext:
    """Information passed to a ``HookAction`` at dispatch time.

    Attributes:
        story_stem: The derivative story stem (e.g. ``"case_jackout-30sec"``).
        kind: The hook kind requested.
        language: ``"en"`` or ``"ko"``.
        excerpt: The first paragraph of the excerpt (best-effort).
        mission_id: The mission that triggered this hook, if any.
        payload: Free-form data extending the basic context.
    """

    story_stem: str
    kind: HookKind
    language: str = "en"
    excerpt: str = ""
    mission_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HookResult:
    """What the hook did to the game state.

    The dispatcher writes the result back to ``AppState`` via small,
    well-defined attributes (status messages, cinematic queue, etc.).
    """

    ok: bool = True
    messages: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


# A HookAction is a callable that takes (context, app_state) and
# returns a HookResult.  We accept the AppState dynamically — the
# module does not import the engine package to avoid a cycle.
HookAction = Callable[[HookContext, Any], HookResult]


_HOOK_REGISTRY: dict[HookKind, list[HookAction]] = {kind: [] for kind in HookKind}


def register_hook_action(kind: HookKind, action: HookAction) -> None:
    """Append ``action`` to the registry for ``kind``.

    Actions are invoked in the order they were registered (last call
    wins for layered effects).  Built-in actions are registered in the
    default ``register_default_actions()`` call invoked from the
    package ``__init__``.
    """
    if kind not in _HOOK_REGISTRY:
        raise ValueError(
            f"Unknown HookKind: {kind!r} (must be one of: {[k.name for k in HookKind]})"
        )
    _HOOK_REGISTRY[kind].append(action)


def get_hook_actions(kind: HookKind) -> list[HookAction]:
    """Return all actions currently registered for ``kind``.

    Returned list is a copy; mutating it does not affect the registry.
    """
    return list(_HOOK_REGISTRY.get(kind, []))


def reset_hook_registry() -> None:
    """Clear the registry.  Useful in tests; not part of public API."""
    for actions in _HOOK_REGISTRY.values():
        actions.clear()


# ---------------------------------------------------------------------------
# Default actions
# ---------------------------------------------------------------------------


def _default_narrative_action(context: HookContext, app_state: Any) -> HookResult:
    """Push the excerpt onto ``state.status_messages`` (or equivalent)."""
    msg = f"[{context.kind.value}] {context.story_stem}: {context.excerpt[:80]!r}"
    if hasattr(app_state, "status_messages"):
        app_state.status_messages.append(msg)
    return HookResult(ok=True, messages=[msg])


def _default_excerpt_action(context: HookContext, app_state: Any) -> HookResult:
    """Same as NARRATIVE but tagged differently for renderer filtering."""
    msg = f"…{context.excerpt[:120]!r}…"
    if hasattr(app_state, "status_messages"):
        app_state.status_messages.append(msg)
    return HookResult(ok=True, messages=[msg])


def _default_event_action(context: HookContext, app_state: Any) -> HookResult:
    """Set up an EventState-like placeholder and return its id."""
    placeholder = {
        "kind": context.kind.value,
        "story_stem": context.story_stem,
        "excerpt": context.excerpt,
    }
    if hasattr(app_state, "active_event"):
        app_state.active_event = placeholder
    msg = f"Event triggered by story {context.story_stem}"
    return HookResult(ok=True, messages=[msg], payload=placeholder)


def _default_combat_action(context: HookContext, app_state: Any) -> HookResult:
    """Boost the player's PPL/ZDR or seed combat state with the ICE kind."""
    payload = context.payload
    ice = payload.get("ice_kind", "STANDARD")
    msg = f"Combat primed by {context.story_stem} (ICE={ice})"
    if hasattr(app_state, "status_messages"):
        app_state.status_messages.append(msg)
    if hasattr(app_state, "context_hint"):
        app_state.context_hint = msg
    return HookResult(ok=True, messages=[msg], payload={"ice_kind": ice})


def _default_item_action(context: HookContext, app_state: Any) -> HookResult:
    """Add an inventory entry keyed by the story stem."""
    item_id = context.payload.get("item_id", context.story_stem)
    if hasattr(app_state, "inventory"):
        app_state.inventory[item_id] = app_state.inventory.get(item_id, 0) + 1
    msg = f"Acquired item {item_id!r} from {context.story_stem}"
    return HookResult(ok=True, messages=[msg], payload={"item_id": item_id})


def _default_cinematic_action(context: HookContext, app_state: Any) -> HookResult:
    """Push a cinematic cue — the cinematic view actually renders it."""
    msg = f"Cinematic: {context.story_stem} (lang={context.language})"
    if hasattr(app_state, "status_messages"):
        app_state.status_messages.append(msg)
    return HookResult(ok=True, messages=[msg])


_DEFAULT_ACTIONS: dict[HookKind, HookAction] = {
    HookKind.NARRATIVE: _default_narrative_action,
    HookKind.EXCERPT: _default_excerpt_action,
    HookKind.EVENT: _default_event_action,
    HookKind.COMBAT: _default_combat_action,
    HookKind.ITEM: _default_item_action,
    HookKind.CINEMATIC: _default_cinematic_action,
}


def register_default_actions() -> None:
    """Register all built-in hook actions.  Idempotent."""
    for kind, action in _DEFAULT_ACTIONS.items():
        register_hook_action(kind, action)


# Eager-register the defaults so callers don't need to remember.
register_default_actions()


__all__ = [
    "HookAction",
    "HookContext",
    "HookKind",
    "HookResult",
    "get_hook_actions",
    "register_default_actions",
    "register_hook_action",
    "reset_hook_registry",
]
