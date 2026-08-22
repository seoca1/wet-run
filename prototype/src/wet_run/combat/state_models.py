"""Combat state model dataclasses (ADR-0141 initial split, 2026-07-27).

Extracted from combat/state.py (1075 LOC). Contains pure data classes:
  - SkillEffect: StrEnum for skill effect types
  - Skill: menu skill (ADR-0003)
  - StatusEffect: active status on a combatant
  - CombatStats: cumulative HUD/analytics counters
  - Combatant: participant (player or ICE)
  - CombatState: live combat simulation state

The state machine functions (step_combat, _tick_*, damage calc, etc.)
remain in combat/state.py.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from wet_run.combat.boss import BossProfile

TICK_MS = 100
AUTO_ATTACK_INTERVAL_MS = 2000

__all__ = [
    "AUTO_ATTACK_INTERVAL_MS",
    "CombatState",
    "Combatant",
    "CombatStats",
    "Skill",
    "SkillEffect",
    "StatusEffect",
    "TICK_MS",
]


class SkillEffect(StrEnum):
    """Types of skill effects in combat."""

    ATTACK = "attack"
    HEAVY_ATTACK = "heavy_attack"
    PIERCE = "pierce"
    MULTI_HIT = "multi_hit"
    DOT = "dot"
    SHIELD = "shield"
    REGEN = "regen"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"
    DETECT = "detect"
    STUN = "stun"
    STAGGER = "stagger"
    COUNTER = "counter"
    LIFESTEAL = "lifesteal"
    POISON = "poison"
    SILENCE = "silence"
    SLOW = "slow"
    VULNERABLE = "vulnerable"


@dataclass(frozen=True, slots=True)
class Skill:
    """A menu skill (ADR-0003) with extended effects."""

    id: str
    name: str
    tier: int
    effect: SkillEffect
    ap_cost: int
    damage: int = 0
    shield: int = 0
    heal: int = 0
    dot_damage: int = 0
    dot_duration_ms: int = 0
    buff_amount: int = 0
    buff_duration_ms: int = 0
    stun_duration_ms: int = 0
    hit_count: int = 1
    cooldown_ms: int = 0
    crit_bonus: float = 0.0
    role: str | None = None
    aoe: bool = False
    effect_color: tuple[int, int, int] = (255, 255, 255)
    effect_glyph: str = "*"


@dataclass
class StatusEffect:
    """An active status effect on a combatant."""

    effect_id: str
    remaining_ms: int
    dot_damage: int = 0
    heal_per_tick: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    is_stunned: bool = False
    is_staggered: bool = False
    is_shield: bool = False
    slow_pct: int = 0
    is_silenced: bool = False
    vulnerability_pct: int = 0


@dataclass
class CombatStats:
    """Cumulative combat statistics for HUD and analytics."""

    damage_dealt: int = 0
    damage_received: int = 0
    crits_landed: int = 0
    crits_received: int = 0
    skills_used: int = 0
    max_combo_reached: int = 0
    peak_alarm_level: int = 0
    turns_elapsed: int = 0


@dataclass
class Combatant:
    """A combat participant (player or ICE)."""

    id: str
    name: str
    portrait: str
    color: tuple[int, int, int]
    hp: int
    max_hp: int
    ap: int = 0
    max_ap: int = 6
    auto_attack_damage: int = 5
    skills: tuple[Skill, ...] = ()
    team: Literal["player", "enemy"] = "enemy"
    statuses: list[StatusEffect] = field(default_factory=list)
    base_attack: int = 0
    base_defense: int = 0
    equip_attack_bonus: int = 0
    equip_defense_bonus: int = 0
    equip_hp_bonus: int = 0
    equip_shield_bonus: int = 0
    equip_ap_bonus: int = 0
    equip_program_power: int = 0
    equip_ice_resistance: int = 0
    equip_damage_bonus_pct: int = 0
    equip_crit_bonus_pct: int = 0
    equip_grants_skill_id: str | None = None
    ice_kind: str | None = None
    ice_resistance: float = 0.0
    alarm_speed: float = 1.0
    current_phase: int = 1
    # Aggression tier (ADR-0148). Determines enemy skill use probability.
    # Valid values: "passive" / "standard" / "aggressive" / "boss".
    aggression: str = "standard"
    # Personality archetype (ADR-0161). Determines skill selection +
    # state reactions + pressure dynamics. Independent of aggression.
    # Valid values: "aggressive" / "defensive" / "stealth" / "support".
    personality: str = "aggressive"

    def is_alive(self) -> bool:
        """Return True if HP is greater than zero."""
        return self.hp > 0

    def is_stunned(self) -> bool:
        """Return True if any active status has is_stunned set."""
        return any(s.is_stunned for s in self.statuses)

    def is_staggered(self) -> bool:
        """Return True if any active status has is_staggered set."""
        return any(s.is_staggered for s in self.statuses)

    def consume_stagger(self) -> None:
        """Remove all stagger statuses from this combatant (one-shot clear)."""
        self.statuses = [s for s in self.statuses if not s.is_staggered]

    def get_attack_bonus(self) -> int:
        """Return total attack bonus: buff statuses + equipment attack bonus."""
        buffs = sum(s.attack_bonus for s in self.statuses)
        return buffs + self.equip_attack_bonus

    def get_defense_bonus(self) -> int:
        """Return total defense bonus: buff statuses + equipment defense bonus."""
        buffs = sum(s.defense_bonus for s in self.statuses)
        return buffs + self.equip_defense_bonus

    def get_total_attack(self) -> int:
        """Return effective attack: base auto-attack damage + attack bonus."""
        return self.auto_attack_damage + self.get_attack_bonus()

    def get_ice_resistance_pct(self) -> int:
        """Return ICE resistance percent from equipment (0-100)."""
        return self.equip_ice_resistance

    def get_crit_bonus_pct(self) -> int:
        """Return crit chance bonus percent from equipment."""
        return self.equip_crit_bonus_pct

    def get_damage_bonus_pct(self) -> int:
        """Return damage bonus percent from equipment."""
        return self.equip_damage_bonus_pct

    def get_program_power(self) -> int:
        """Return flat program power bonus from equipment."""
        return self.equip_program_power

    def get_total_shield_bonus(self) -> int:
        """Return shield bonus from equipment."""
        return self.equip_shield_bonus

    def get_total_ap_bonus(self) -> int:
        """Return AP bonus from equipment."""
        return self.equip_ap_bonus

    def get_total_hp_bonus(self) -> int:
        """Return max-HP bonus from equipment."""
        return self.equip_hp_bonus

    def alive_skills_available(self) -> bool:
        """Return True if the combatant has any skills equipped."""
        return bool(self.skills)

    def choose_skill(self, rng: random.Random) -> Skill | None:
        """Pick a random skill from this combatant's skill list.

        Args:
            rng: Deterministic RNG source (use the state's rng for replay).

        Returns:
            The chosen Skill, or None if no skills are equipped.
        """
        if not self.skills:
            return None
        idx = rng.randrange(len(self.skills))
        return self.skills[idx]


@dataclass
class CombatState:
    """Live combat simulation state."""

    player: Combatant
    enemy: Combatant | None = None
    enemies: tuple[Combatant, ...] = ()
    target_index: int = 0
    tick_ms: int = 0
    last_player_attack_ms: int = -AUTO_ATTACK_INTERVAL_MS
    last_enemy_attack_ms: int = -AUTO_ATTACK_INTERVAL_MS
    last_ap_regen_ms: int = 0
    shield: int = 0
    log: list[str] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    finished: bool = False
    outcome: Literal["ongoing", "victory", "defeat"] = "ongoing"
    last_skill_used: Skill | None = None
    skill_cooldowns: dict[str, int] = field(default_factory=dict)
    last_event: str = ""
    last_event_color: tuple[int, int, int] = (255, 255, 255)
    last_event_tick: int = 0
    player_combo: int = 0
    enemy_combo: int = 0
    telemetry: object = None
    boss_phase_tracker: object = None
    deck_size: str = "standard"
    combo_last_hit_ms: int = 0
    boss_profile: BossProfile | None = None
    alarm_level: int = 0
    last_alarm_tick_ms: int = 0
    stats: CombatStats = field(default_factory=CombatStats)
    # Counter-attack window deadline (ADR-0148). 0 = no window open.
    # When tick_ms reaches this value, the window is closed.
    counter_window_open_ms: int = 0
    # Last tick_ms when Dixie companion auto-attacked/skilled.
    # ADR-0148: formal field (was previously dynamic attribute).
    dixie_last_attack_ms: int = -2000
    # Last tick_ms when Wardrone auto-counter fired (ADR-0148).
    wardrone_last_counter_ms: int = -5000
    # Current boss Phase 4 mechanic (ADR-0149). None until triggered.
    boss_phase4_mechanic: str | None = None
    # Phase 17: timestamp (tick_ms) of the most recent boss phase
    # transition. UI uses this to render a brief color-shift on the
    # phase badge so the player notices the change. 0 = no recent
    # transition (or never transitioned).
    phase_change_ms: int = 0
    # Phase 17: color of the most recent phase transition (used by the
    # UI color-shift flash). Defaults to yellow when unset.
    phase_change_color: tuple[int, int, int] = (255, 255, 0)
    # Mission Archetype (ADR-0164): DEFENSE archetype HP pool for the
    # friendly node the player is protecting. 100 default (legacy fallback).
    friendly_node_hp: int = 100

    def __post_init__(self) -> None:
        """Sync the legacy single-enemy field with the enemies tuple.

        Either ``enemy`` or ``enemies`` may be provided at construction; this
        ensures both views stay consistent (the first slot of ``enemies``
        always mirrors ``enemy``).
        """
        if not self.enemies and self.enemy is not None:
            self.enemies = (self.enemy,)
        elif self.enemies and self.enemy is None:
            self.enemy = self.enemies[0]

    @property
    def target(self) -> Combatant | None:
        """Return the currently-targeted enemy (None if no enemies)."""
        if not self.enemies:
            return None
        return self.enemies[self.target_index]

    def push(self, msg: str) -> None:
        """Append a log message, capping the log at 6 entries (FIFO)."""
        self.log.append(msg)
        if len(self.log) > 6:
            self.log.pop(0)
