"""App state (ADR-0006, ADR-0009, design/systems/hacking.md).

A single mutable ``AppState`` is shared by all screens. Screens are
implemented as functions over the state.
"""

from __future__ import annotations

from collections import UserList
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from typing_extensions import override

from ..combat.effects import CombatEffects
from ..combat.state import CombatState
from ..lore import ConstructWhisper, MemoryFragmentTracker
from ..matrix.exploration import ExplorationState
from ..matrix.graph import MatrixGraph
from ..matrix.ppl import Loadout, Program
from ..missions import JobBoard, Mission
from ..run.memory_bank import MemoryBank
from ..run.reputation import ReputationState

# Maximum number of status messages retained in AppState.status_messages.
# When the cap is exceeded, the oldest messages are dropped first.
# Prevents unbounded memory growth across long sessions (P2 #17).
STATUS_MESSAGES_MAX = 100


class StatusMessageList(UserList[str]):
    """List subclass that auto-truncates to ``STATUS_MESSAGES_MAX`` entries.

    Behaves like a normal ``list[str]`` for reads, indexing, iteration,
    and ``len()``. Writes via ``append``, ``extend``, ``insert``, and
    ``__setitem__`` enforce the cap by dropping the oldest entries first.
    """

    def __init__(self, iterable: Iterable[str] | None = None) -> None:
        """Initialize the list, optionally seeding from an iterable."""
        super().__init__()
        if iterable:
            self.data = list(iterable)
        self._enforce_cap()

    def _enforce_cap(self) -> None:
        """Trim the list to ``STATUS_MESSAGES_MAX``, dropping the oldest entries first."""
        if len(self.data) > STATUS_MESSAGES_MAX:
            self.data = self.data[-STATUS_MESSAGES_MAX:]

    @override
    def append(self, item: str) -> None:
        """Append a single message, then enforce the cap."""
        self.data.append(item)
        self._enforce_cap()

    @override
    def extend(self, items: Iterable[str]) -> None:
        """Extend with multiple messages, then enforce the cap."""
        self.data.extend(items)
        self._enforce_cap()

    @override
    def insert(self, i: int, item: str) -> None:
        """Insert at position ``i``, then enforce the cap."""
        self.data.insert(i, item)
        self._enforce_cap()

    @override
    def __setitem__(self, i: int | slice, value: str | Iterable[str]) -> None:  # type: ignore[override]
        """Assign by index or slice, then enforce the cap."""
        self.data[i] = value  # type: ignore[index,assignment]
        self._enforce_cap()

    @override
    def __iadd__(self, other: Iterable[str]) -> StatusMessageList:
        """In-place add (e.g. ``lst += other``), then enforce the cap."""
        self.data.extend(other)
        self._enforce_cap()
        return self


if TYPE_CHECKING:
    from ..audio import SoundConfig
    from ..combat.boss_phase4.intro import BossIntroEnhancement
    from ..combat.performance_integration import PerfTracker
    from ..combat.telemetry_integration import TelemetryIntegrator
    from ..cyberspace.world import WorldMap
    from ..equipment.equipment import EquipmentLoadout
    from ..run.state import RunState
    from .chapter_cutscene import ArcData, ChapterCutsceneState
    from .chapter_view import ChapterData
    from .event_story import EventRegistry, EventState
    from .graphic_novel_view import SceneData
    from .hacking_view import HackingState
    from .npc_event import NPCState
    from .salvation import SalvationRunner, SalvationSelection
    from .story_cinematic import CinematicState


class ScreenKind(StrEnum):
    """Top-level screens of the game (ADR-0006, ADR-0009, ADR-0031, ADR-0032, ADR-0040)."""

    MENU = "menu"
    GRAPHIC_NOVEL_MENU = "graphic_novel_menu"  # Graphic novel entry menu (ADR-0032)
    GRAPHIC_NOVEL_ENDING_MENU = "graphic_novel_ending_menu"  # Ending A/B selection (ADR-0048)
    SAVE_SLOT_SELECT = "save_slot_select"  # 3-slot picker (ADR-0051 infra + ADR-0104 extension)
    GRAPHIC_NOVEL = "graphic_novel"  # Auto-play graphic novel scenes (ADR-0032)
    SAVED_PROGRESS = "saved_progress"  # Save progress card after graphic novel (ADR-0032)
    CHARACTER_SELECT = "character_select"  # Original jockey pick (ADR-0031)
    DECK_SELECT = "deck_select"  # Choose deck size (ADR-0178)
    CHAPTER = "chapter"  # Short-story chapter display (ADR-0031)
    HUB = "hub"
    MATRIX = "matrix"
    CYBERSPACE_BROWSER = "cyberspace_browser"  # Browse worlds/sectors/servers
    CYBERSPACE_MAP = "cyberspace_map"  # World/sector map view
    COMBAT = "combat"  # Real-Time with Menu Skills (ADR-0003)
    CINEMATIC = "cinematic"  # Story presentation with typing effects (Phase 5+)
    STORY = "story"  # Aftermath / narrative / character reactions (ADR-0019)
    DEATH = "death"  # FLATLINE screen (ADR-0040)
    DEATH_SUMMARY = "death_summary"  # Jockey report after flatline (ADR-0040)
    HALL_OF_DEAD = "hall_of_dead"  # Archive of deceased jockeys (ADR-0040)
    NPC = "npc"  # NPC encounter with dialogue choices
    HACK = "hack"  # System probe hacking minigame (Phase 6+)
    EVENT = "event"  # Event story (cutscene with character art)
    JACK_OUT = "jack_out"  # Matrix disconnect animation (Stage.JACK_OUT)
    REWARD = "reward"  # Mission rewards screen (Stage.REWARD)
    DEBRIEF = "debrief"  # Optional narrative between REWARD and COMPLETE
    ENDING = "ending"  # Ending A/B display (ADR-0031)
    ARC_PHASE = "arc_phase"  # Arc phase with beats (Story → Stage → Event pipeline)
    SALVATION_INTRO = "salvation_intro"  # Epilogue character selection (Phase 9)
    SALVATION_EPILOGUE = "salvation_epilogue"  # Epilogue scene playback (Phase 9)
    SALVATION_ENDING = "salvation_ending"  # Post-epilogue ending choice (Phase 9)
    SAVE_LOAD = "save_load"  # Save/Load slot browser (Hub)
    HELP = "help"  # Help screen — controls, concepts, how to play
    SETTINGS = "settings"  # Settings screen — audio, colorblind, keymap (Phase 7)
    ENDINGS_BROWSER = "endings_browser"  # Browse unlocked endings (Phase 15)
    TELEMETRY_STATS = "telemetry_stats"  # Aggregated player stats (Phase 17)


# A grade-1 (1-up) loadout: Ono-Sendai 4 (T1) + Wisp (T1) + Standard (T1).
# PPL = 1*3 + 1*2 + 1 = 6. Matches the ADR-0012 example.
DEFAULT_LOADOUT_T1 = Loadout(
    deck_tier=1,
    programs=(Program(id="wisp", name="Wisp", tier=1),),
    wetware_tier=1,
)


def _default_equipment_loadout() -> EquipmentLoadout:
    """Default factory for equipment_loadout (Phase 15)."""
    from ..equipment.equipment import EquipmentLoadout

    return EquipmentLoadout()


@dataclass
class AppState:
    """Mutable game state shared by all screens."""

    screen: ScreenKind = ScreenKind.MENU
    player_grade: int = 1
    player_loadout: Loadout = field(default_factory=lambda: DEFAULT_LOADOUT_T1)
    job_board: JobBoard = field(default_factory=JobBoard)
    current_mission: Mission | None = None
    matrix: MatrixGraph | None = None
    current_node_id: str | None = None
    # Matrix node navigation cursor (↑/↓ to select adjacent node, Enter to move)
    matrix_nav_index: int = 0
    hub_selected_index: int = 0
    menu_selected_index: int = 0
    character_select_index: int = 0
    message: str = ""
    # Fog of war / exploration state (ADR-0020). None until a matrix
    # is loaded. Owned by the matrix screen.
    exploration: ExplorationState | None = None
    # Combat state (ADR-0003). None until combat starts.
    combat_state: CombatState | None = None
    # Action menu state (Phase 5). True when action menu is open.
    action_menu_open: bool = False
    # Action menu navigation (arrow key selection)
    action_menu_index: int = 0
    # Combat skill menu navigation (arrow key selection)
    combat_skill_index: int = 0
    # Cinematic state (Phase 5+). None until cinematic starts.
    cinematic_state: CinematicState | None = None
    # NPC encounter state. None until NPC encounter starts.
    npc_state: NPCState | None = None
    hack_state: HackingState | None = None
    hack_node_label: str = ""
    # NPC choice navigation (arrow key selection)
    npc_choice_index: int = 0
    # Event story state (cutscenes with character art)
    active_event: EventState | None = None
    # Set of shown event IDs (one-time events)
    shown_events: set[str] = field(default_factory=set)
    # Story flags (for event conditions)
    story_flags: set[str] = field(default_factory=set)
    # Event registry (initialized lazily)
    _event_registry: EventRegistry | None = None
    # Player inventory (item_id -> count)
    inventory: dict[str, int] = field(default_factory=dict)
    # Equipped loadout (cyberpunk gear)
    equipment_loadout: EquipmentLoadout = field(
        default_factory=_default_equipment_loadout
    )  # EquipmentLoadout
    # Defeated nodes (node_id set) - removed from dungeon after combat
    defeated_nodes: set[str] = field(default_factory=set)
    # Extracted data nodes (node_id set) - data already collected
    extracted_nodes: set[str] = field(default_factory=set)
    # Cyberspace layout (node_id -> (x, y, depth)) for scrolling view
    cyberspace_layouts: dict[str, object] | None = None
    # World map (World → Sector → Server hierarchy)
    world_map: WorldMap | None = None
    # Current server's subgraph (the explorable graph)
    server_subgraph: tuple[MatrixGraph, dict[str, object]] | None = None
    # Server list (for the server browser)
    available_servers: list[str] = field(default_factory=list)
    # Selected server in browser
    selected_server_index: int = 0
    # Server view mode (browsing vs exploring)
    in_server_browser: bool = True
    # Story event fields (ADR-0019)
    story_aftermath_id: str = "aftermath_black_ice"
    story_importance: str = "major"
    # Deck size (ADR-0178): light / standard / heavy
    # Controls program slots + AP regen + cooldown modifiers.
    deck_size: str = "standard"
    # Telemetry session (ADR-0184): opt-in only, aggregated data only
    telemetry: TelemetryIntegrator | None = None
    # Display fields (filled by the demo / shell)
    player_ppl: int = 0
    player_hp: int = 0
    player_max_hp: int = 0
    demo_step: int = 0
    demo_elapsed_s: float = 0.0
    # Status messages (shown in footer or side panel).
    # Bounded ring: oldest dropped when STATUS_MESSAGES_MAX exceeded.
    status_messages: StatusMessageList = field(default_factory=StatusMessageList)
    # Current context hint (what to do now)
    context_hint: str = ""
    # Player credits (wallet)
    credits: int = 0
    # Mission progress: objective_type -> count
    # (e.g. {"extract_data": 1, "defeat": 2})
    mission_progress: dict[str, int] = field(default_factory=dict)
    # Completed mission IDs (so we don't re-offer them)
    completed_missions: set[str] = field(default_factory=set)
    # Phase E-2: first-combat tutorial overlay (dismissed on Space)
    show_first_combat_tutorial: bool = True
    reputation: ReputationState = field(default_factory=ReputationState)
    memory_bank: MemoryBank = field(default_factory=MemoryBank)
    memory_fragment_tracker: MemoryFragmentTracker = field(default_factory=MemoryFragmentTracker)
    construct_whisper_tracker: ConstructWhisper = field(default_factory=ConstructWhisper)
    anomaly_triggered: set[str] = field(default_factory=set)
    # Run Mutators (ADR-0163): optional rules applied at run start.
    active_mutators: tuple[str, ...] = ()
    # Mutator effect fields (avoid full passthrough for perf).
    alarm_speed_multiplier: float = 1.0
    encounter_multiplier: int = 1
    heal_disabled: bool = False
    skill_filter: str | None = None
    # Mission Archetypes (ADR-0164): rules applied per-mission.
    active_archetype: str | None = None
    # Random Matrix Events (ADR-0165): mid-run surprises.
    active_events: tuple[str, ...] = ()
    event_log: list[str] = field(default_factory=list)
    near_miss_triggered: bool = False
    faction_tension_triggered: set[str] = field(default_factory=set)
    alarm_level: int = 0
    tempo_mode: str = "normal"
    # In-run salvage fragments (ADR-0147). Reset on death (Pillar 4 in-run only).
    salvage_fragments: int = 0
    # Pending salvage menu flag (ADR-0147). Set by _end_combat on victory.
    pending_salvage: bool = False
    # Boss Phase 4 one-shot guard (ADR-0149). Set true on Phase 4 trigger.
    phase4_triggered: bool = False
    # Current boss Phase 4 mechanic name (ADR-0149). None until triggered.
    boss_phase4_mechanic: str | None = None
    # Boss death taunt (ADR-0149). Set on player death by boss. None otherwise.
    death_taunt: str | None = None
    # Boss intro enhancement (ADR-0149). Set on boss encounter. None otherwise.
    boss_intro_enhancement: BossIntroEnhancement | None = None
    # Purchased intel item ids (ADR-0151). One-shot per item_id per run.
    # Pillar 4 in-run only — reset on death.
    purchased_intel_items: list[str] = field(default_factory=list)
    # Faction event probability boost (ADR-0151). Set by faction_rumor item.
    faction_tension_probability_boost: float = 0.0
    # Player is dead (flatline); True until reset
    is_dead: bool = False
    # Death reason (e.g. "Combat", "ICE breach", "Jack-out failure")
    death_reason: str = ""
    # Run progress (stages + current target). The single source of truth
    # for "what should the player be doing right now?"
    run_state: RunState | None = None
    # Sound configuration (per-category on/off + master volume)
    sound_config: SoundConfig | None = None
    # v0.5: Data Fragment collection (collectible lore from missions)
    # Set of collected fragment_ids. Each unlocks wiki lore and a discovery flag.
    data_fragments: set[str] = field(default_factory=set)
    # v0.5: Movement stats (mobility feedback in matrix/dungeon view)
    # Total cardinal-direction steps taken in current run.
    movement_step_count: int = 0
    # Set of node_ids visited during current run (for visited-count display).
    nodes_visited: set[str] = field(default_factory=set)
    # Jack Out animation state (Stage.JACK_OUT)
    jack_out_started_at: float = 0.0
    jack_out_frame_index: int = 0
    # Debrief state (Stage.DEBRIEF)
    debrief_character: str = "novice"
    debrief_index: int = 0
    # Save/Load browser state (ScreenKind.SAVE_LOAD)
    save_load_selected: int = 1
    # Combat visual effects (animations, particles, screen shake, etc.)
    combat_effects: CombatEffects = field(default_factory=CombatEffects)
    # Original scenario state (ADR-0031) — character_id, chapter_id, ending
    character_id: str = "novice"  # "novice" | "veteran" | "heretic"
    chapter_id: str = "chapter_novice"
    chapter_progress: float = 0.0  # 0.0 ~ 1.0 typing progress
    chapter_elapsed_ms: float = 0.0
    chapter_typed_chars: int = 0
    chapter_portrait: str = "art:case"
    chapter_data: ChapterData | None = None  # loaded chapter for current character
    ending_choice: str = ""  # "A" | "B" | "" (pending)
    # Chapter cutscene state (for chapter-internal cutscene playback)
    chapter_cutscene_state: ChapterCutsceneState | None = None
    # Arc phase state (for Story → Stage → Event pipeline)
    current_arc: ArcData | None = None  # ArcData
    current_chapter_index: int = 0
    current_phase_index: int = 0
    current_beat_index: int = 0
    phase_typed_chars: int = 0
    phase_elapsed_ms: float = 0.0
    ending_elapsed_ms: float = 0.0  # Auto-return from ENDING screen
    # Graphic novel state (ADR-0032)
    gn_scene_index: int = 0  # current scene in chain
    gn_menu_selected: int = 0  # selected index in GRAPHIC_NOVEL_MENU
    gn_dialogue_index: int = 0  # current dialogue in scene
    gn_scenes: list[SceneData] = field(default_factory=list)  # list[SceneData] — loaded scenes
    gn_elapsed_ms: float = 0.0  # time in current dialogue
    gn_paused: bool = False
    gn_typed_chars: int = 0  # typing progress in current dialogue
    gn_mode: str = "prologue"  # "prologue" | "novice" | "veteran" | "heretic"
    gn_scene_chain: list[str] = field(default_factory=list)  # scene IDs in order
    gn_ending_choice: str = "A"  # "A" | "B" — which ending variant (ADR-0048)
    gn_save_slot_selected: int = (
        0  # 0=none, 1..3 for slot picker (ADR-0051 infra + ADR-0104 extension)
    )
    # Jockey cycle (ADR-0040) — Hall of Dead Jockeys
    jockey_history_loaded: bool = False  # whether archive is loaded from disk
    total_runs: int = 0
    total_deaths: int = 0
    last_jockey_summary_id: str = ""  # ID of the most recent DeceasedJockey
    # Death flow options (after DEATH_SUMMARY)
    death_cause: str = "Combat"  # "Combat" / "Black ICE" / "T-A ICE" / "Black ICE breach"
    hall_of_dead_selected: int = 0  # selected index in HALL_OF_DEAD screen
    # Settings screen state (Phase 7)
    settings_selected: int = 0  # selected option index in SETTINGS screen
    colorblind_mode: bool = False  # colorblind-friendly palette toggle
    telemetry_opt_in: bool = False  # telemetry opt-in toggle (Phase 15)
    perf_hud_enabled: bool = False  # performance HUD toggle (Phase 15)
    # Phase 17: rule_id of the random_rules entry that fired on the
    # last JobBoard.select_weighted call. None until first selection.
    last_rule_id: str | None = None
    # Phase 17: dev/debug flag — when True, the Hub shows the active
    # rules in the side panel (in addition to the selected mission's
    # rule annotation). Default False: rule metadata is opt-in.
    show_active_rules: bool = False
    perf_tracker: PerfTracker | None = None  # PerfTracker (Phase 15)
    deck_select_index: int = 1  # selected index in DECK_SELECT screen (Phase 15)
    endings_selected: int = 0  # selected index in ENDINGS_BROWSER screen (Phase 15)
    # Accessibility settings (Cycle 3 polish)
    font_size: str = "normal"  # "small" / "normal" / "large"
    high_contrast: bool = False  # high-contrast palette toggle
    # Keymap customization flag (Pillar 4 ephemeral)
    keymap_customized: bool = False  # True if user has modified key bindings
    # Hardcore mode (Cycle 4: Pillar 3 reinforcement)
    hardcore_mode: bool = False  # 1-life permadeath (Pillar 4 compliant: ephemeral)
    # New Game+ (Cycle 4: Pillar 4 unlock-only meta-progression)
    ng_plus_unlocked: bool = False  # True after completing an ending (Pillar 4 compliant)
    ng_plus_active: bool = False  # True for current run's New Game+ mode (Pillar 4 ephemeral)
    # Construct companion (Cycle 4: Pillar 5 actual combat ally)
    construct_companion_active: bool = False  # Dixie as actual combat ally (dialog-only by default)
    # Help screen state (Phase 7)
    help_page: int = 0  # current help page index (0-based)
    # Salvation Phase state (ADR-0090 Phase 9)
    salvation_runner: SalvationRunner | None = None
    salvation_selection: SalvationSelection | None = None
    salvation_scene_data: SceneData | None = None
    salvation_epilogue_elapsed_ms: float = 0.0
    salvation_epilogue_typed_chars: int = 0
    salvation_epilogue_dialogue_index: int = 0
