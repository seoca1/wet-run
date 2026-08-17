"""Game engine: tcod integration, rendering, input, main loop."""

from .npc_greeting import (
    NPC_GREETINGS,
    ReputationGreeting,
    get_greeting,
    get_greeting_text,
)
from .save_manager import (
    DEFAULT_SLOT,
    MAX_SLOTS,
    SAVE_FORMAT_VERSION,
    SaveCorruptedError,
    SavedRun,
    SaveError,
    SaveManager,
    SaveMetadata,
    SaveSlotEmptyError,
    SaveVersionMismatchError,
)
from .state import AppState, ScreenKind

__all__ = [
    "AppState",
    "NPC_GREETINGS",
    "ReputationGreeting",
    "ScreenKind",
    "SaveManager",
    "SaveMetadata",
    "SavedRun",
    "SaveError",
    "SaveSlotEmptyError",
    "SaveVersionMismatchError",
    "SaveCorruptedError",
    "MAX_SLOTS",
    "SAVE_FORMAT_VERSION",
    "DEFAULT_SLOT",
    "get_greeting",
    "get_greeting_text",
]
