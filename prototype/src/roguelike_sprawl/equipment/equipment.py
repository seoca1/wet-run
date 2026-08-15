"""Cyberpunk equipment system.

Reimagines traditional RPG armor slots as cyberpunk-implant slots.
Each slot represents a body location where cybernetic/tech gear can be mounted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from typing_extensions import override


class EquipSlot(StrEnum):
    """Body locations for cyberpunk gear.

    Inspired by William Gibson's cyberpunk descriptions:
    - Deck: The cyberdeck (core computing unit)
    - Headware: Neural interface, jack sockets
    - Eyeware: AR overlays, retinal implants
    - Bodysuit: Subdermal armor, smart fabric
    - Gloves: Interface plugs, weapon hardpoints
    - Boots: Locomotion enhancements
    - Implant: Internal organ mods
    - Trodes: Auxiliary connectors, bio-monitors
    """

    DECK = "deck"  # Cyberdeck - main computer
    HEADWARE = "headware"  # Neural jack, head implant
    EYEWARE = "eyeware"  # Eye/visual augment
    BODYSUIT = "bodysuit"  # Body armor
    GLOVES = "gloves"  # Hand augmentation
    BOOTS = "boots"  # Foot/leg augmentation
    IMPLANT = "implant"  # Internal organ implant
    TRODES = "trodes"  # Auxiliary connections


class EquipCategory(StrEnum):
    """Type of equipment (material/technology)."""

    CYBERNETIC = "cybernetic"  # 기계-생체 하이브리드
    SOFTWARE = "software"  # AI/agent
    BIOWARE = "bioware"  # 유기체 기술
    NANOWARE = "nanoware"  # 나노 기술
    WETWARE = "wetware"  # 뇌 인터페이스
    HARDWARE = "hardware"  # 물리적 도구
    ICEBREAKER = "icebreaker"  # 해킹 전용
    DAEMON = "daemon"  # AI 프로그램


class EquipTier(StrEnum):
    """Quality/rarity tiers."""

    T0_BASELINE = "T0"  # 기본
    T1_STREET = "T1"  # 스트릿 grade
    T2_COMMERCIAL = "T2"  # 상용
    T3_MILITECH = "T3"  # 군사
    T4_CORPORATE = "T4"  # 기업
    T5_EXPERIMENTAL = "T5"  # 실험
    T6_MASTER = "T6"  # 마스터 (Arc 5 finale 전용)


@dataclass(frozen=True, slots=True)
class EquipStats:
    """Stats provided by an equipment piece."""

    # Offensive
    attack_bonus: int = 0
    crit_bonus_pct: int = 0  # 0-100
    damage_bonus_pct: int = 0

    # Defensive
    defense: int = 0  # flat damage reduction
    hp_bonus: int = 0
    shield_bonus: int = 0

    # Mobility
    ap_bonus: int = 0
    ap_regen_bonus_pct: int = 0

    # Cyber
    program_power: int = 0  # +skill damage
    ice_resistance: int = 0  # % damage reduction vs ICE

    # Special
    grants_skill_id: str | None = None  # adds a new skill
    extra_effect: str = ""  # flavor text


@dataclass(frozen=True, slots=True)
class Equipment:
    """A piece of cyberpunk gear.

    Inspired by cyberpunk 2020/RED and Shadowrun equipment.
    """

    id: str
    name: str
    slot: EquipSlot
    category: EquipCategory
    tier: EquipTier
    stats: EquipStats
    description: str
    ascii_glyph: str = "?"
    ascii_color: tuple[int, int, int] = (200, 200, 200)
    # Upgrade info
    upgrade_slots: int = 0  # 0 = not upgradable
    required_materials: dict[str, int] = field(default_factory=dict)
    # Set info (for set bonuses)
    set_id: str | None = None

    def is_upgradable(self) -> bool:
        """Return True if this piece has at least one upgrade slot."""
        return self.upgrade_slots > 0

    def is_t1_or_better(self) -> bool:
        """Return True if this piece is tier 1 (street) or higher (excludes T0 starter gear)."""
        return self.tier.value != "T0"

    @override
    def __repr__(self) -> str:
        return f"{self.name} ({self.tier.value} {self.category.value})"


# ============================================================================
# Default Equipment (Gibson-inspired cyberpunk)
# ============================================================================

# === Tier 0 (Starting) ===
STARTER_DECK = Equipment(
    id="deck_basic",
    name="Ono-Sendai Cyberspace 7",
    slot=EquipSlot.DECK,
    category=EquipCategory.HARDWARE,
    tier=EquipTier.T0_BASELINE,
    stats=EquipStats(program_power=5),
    description="A battered Ono-Sendai 7 cyberdeck. The jack plate is worn smooth.",
    ascii_glyph="[D]",
    ascii_color=(100, 100, 150),
    set_id="ono_sendai",
)

STARTER_HEADWARE = Equipment(
    id="head_basic",
    name="Trodes (Stock)",
    slot=EquipSlot.HEADWARE,
    category=EquipCategory.WETWARE,
    tier=EquipTier.T0_BASELINE,
    stats=EquipStats(ap_bonus=1),
    description="Basic trodes. Brings the Matrix into focus, mostly.",
    ascii_glyph="^H^",
    ascii_color=(180, 180, 200),
)

# === Tier 1 (Street-grade) ===
STREET_DECK = Equipment(
    id="deck_street",
    name="Ono-Sendai 11 (Hot Rod)",
    slot=EquipSlot.DECK,
    category=EquipCategory.HARDWARE,
    tier=EquipTier.T1_STREET,
    stats=EquipStats(program_power=12, crit_bonus_pct=5),
    description="Hot-rodded Ono-Sendai with custom cooling. Burns through ICE like butter.",
    ascii_glyph="[D+]",
    ascii_color=(200, 100, 0),
    upgrade_slots=2,
    required_materials={"ice_shard": 1, "data_fragment": 2},
    set_id="ono_sendai",
)

MILITECH_EYES = Equipment(
    id="eyes_militech",
    name="Militech Eagle Eye",
    slot=EquipSlot.EYEWARE,
    category=EquipCategory.CYBERNETIC,
    tier=EquipTier.T1_STREET,
    stats=EquipStats(attack_bonus=3, crit_bonus_pct=10),
    description="Targeting reticle overlays. Highlights weak points in red.",
    ascii_glyph="[E]",
    ascii_color=(255, 50, 50),
    upgrade_slots=1,
    required_materials={"data_fragment": 2, "wetware_chip": 1},
    set_id="militech",
)

CHROME_GLOVES = Equipment(
    id="gloves_chrome",
    name="Chrome Surgical Gloves",
    slot=EquipSlot.GLOVES,
    category=EquipCategory.CYBERNETIC,
    tier=EquipTier.T1_STREET,
    stats=EquipStats(attack_bonus=5, program_power=3),
    description="Fingers reinforced with chrome. Plug-compatible.",
    ascii_glyph="[G]",
    ascii_color=(180, 180, 200),
    upgrade_slots=1,
    required_materials={"combat_module": 1},
    set_id="militech",
)

# === Tier 2 (Commercial) ===
CORPORATE_DECK = Equipment(
    id="deck_corporate",
    name="Sakura Cybermod 'Samurai'",
    slot=EquipSlot.DECK,
    category=EquipCategory.CYBERNETIC,
    tier=EquipTier.T2_COMMERCIAL,
    stats=EquipStats(program_power=20, defense=2, ap_regen_bonus_pct=20),
    description="Japanese craftsmanship meets cutting-edge cybernetics.",
    ascii_glyph="[D]",
    ascii_color=(200, 0, 100),
    upgrade_slots=3,
    required_materials={"ice_shard": 3, "wetware_data": 1},
    set_id="ono_sendai",
)

SUBDERMAL = Equipment(
    id="bodysuit_subdermal",
    name="Subdermal Weave Mk.II",
    slot=EquipSlot.BODYSUIT,
    category=EquipCategory.BIOWARE,
    tier=EquipTier.T2_COMMERCIAL,
    stats=EquipStats(defense=8, hp_bonus=20, ice_resistance=10),
    description="Kevlar subdermal layer. Stops most small-caliber rounds.",
    ascii_glyph="[B]",
    ascii_color=(100, 150, 100),
    upgrade_slots=2,
    required_materials={"wetware_data": 2, "data_fragment": 1},
)

# === Tier 3 (Militech) ===
MILITECH_DECK = Equipment(
    id="deck_militech",
    name="Militech Centurion",
    slot=EquipSlot.DECK,
    category=EquipCategory.HARDWARE,
    tier=EquipTier.T3_MILITECH,
    stats=EquipStats(program_power=35, defense=5, crit_bonus_pct=15, grants_skill_id="jackhammer"),
    description="Military-grade hardware. Comes pre-loaded with combat programs.",
    ascii_glyph="[D]",
    ascii_color=(0, 200, 0),
    upgrade_slots=3,
    required_materials={"ice_construct": 1, "combat_module": 2},
    set_id="militech",
)

TACTICAL_BODY = Equipment(
    id="bodysuit_tactical",
    name="M-31 Combat Armor",
    slot=EquipSlot.BODYSUIT,
    category=EquipCategory.HARDWARE,
    tier=EquipTier.T3_MILITECH,
    stats=EquipStats(defense=20, hp_bonus=50, shield_bonus=10, ice_resistance=25),
    description="Full ballistic plating. Made the Arasaka tremble.",
    ascii_glyph="[B]",
    ascii_color=(150, 150, 150),
    upgrade_slots=3,
    required_materials={"combat_module": 3, "ice_construct": 2},
)

# === Tier 4 (Corporate) ===
ARASAKA_DECK = Equipment(
    id="deck_arasaka",
    name="Arasaka 'Onikiri'",
    slot=EquipSlot.DECK,
    category=EquipCategory.CYBERNETIC,
    tier=EquipTier.T4_CORPORATE,
    stats=EquipStats(program_power=60, defense=10, crit_bonus_pct=20, grants_skill_id="viral"),
    description="Top-tier Arasaka deck. Sleek, deadly, expensive.",
    ascii_glyph="[D]",
    ascii_color=(255, 0, 0),
    upgrade_slots=4,
    required_materials={"ice_construct": 3, "biosoft_agent": 2},
    set_id="arasaka",
)

KEREZNIKOV = Equipment(
    id="head_kereznikov",
    name="Kereznikov Boost",
    slot=EquipSlot.HEADWARE,
    category=EquipCategory.CYBERNETIC,
    tier=EquipTier.T4_CORPORATE,
    stats=EquipStats(ap_bonus=3, ap_regen_bonus_pct=50, program_power=15),
    description="Russian implant. AP regenerates like you mainline stims.",
    ascii_glyph="[K]",
    ascii_color=(200, 0, 0),
    upgrade_slots=2,
    required_materials={"biosoft_agent": 2, "rom_echo": 1},
    set_id="arasaka",
)

# === Tier 5 (Experimental) ===
GHOST_DECK = Equipment(
    id="deck_ghost",
    name="Ghost Cartographer",
    slot=EquipSlot.DECK,
    category=EquipCategory.DAEMON,
    tier=EquipTier.T5_EXPERIMENTAL,
    stats=EquipStats(program_power=100, crit_bonus_pct=30, defense=15, grants_skill_id="bloodlust"),
    description="Experimental AI-assisted deck. Thinks for itself.",
    ascii_glyph="[G]",
    ascii_color=(100, 255, 200),
    upgrade_slots=5,
    required_materials={"biosoft_agent": 5, "rom_echo": 3, "ice_construct": 5},
)

# === Tier 6 (Master) — Arc 5 finale only ===
MASTER_DECK = Equipment(
    id="deck_master",
    name="Wintermute / Neuromancer (Merged)",
    slot=EquipSlot.DECK,
    category=EquipCategory.DAEMON,
    tier=EquipTier.T6_MASTER,
    stats=EquipStats(
        program_power=150,
        defense=25,
        crit_bonus_pct=40,
        ap_regen_bonus_pct=75,
        grants_skill_id="omniscient",
        extra_effect="Sees through all ICE. Love is the algorithm.",
    ),
    description="The merged AI given physical form. Only the greatest jockey can hold it.",
    ascii_glyph="[*]",
    ascii_color=(255, 255, 255),
    upgrade_slots=0,  # Already at peak
    required_materials={},
)

MASTER_BODY = Equipment(
    id="bodysuit_master",
    name="Full-Body Cyborg Conversion",
    slot=EquipSlot.BODYSUIT,
    category=EquipCategory.NANOWARE,
    tier=EquipTier.T6_MASTER,
    stats=EquipStats(
        defense=40,
        hp_bonus=120,
        shield_bonus=30,
        ice_resistance=50,
        ap_bonus=4,
        extra_effect="Immune to flatline (one revive per run)",
    ),
    description="More machine than human. Most jockeys don't survive the operation.",
    ascii_glyph="[#]",
    ascii_color=(255, 200, 100),
    upgrade_slots=0,
    required_materials={},
)

ZION_TRODES = Equipment(
    id="trodes_zion",
    name="Zion Direct-Neural Link",
    slot=EquipSlot.TRODES,
    category=EquipCategory.WETWARE,
    tier=EquipTier.T6_MASTER,
    stats=EquipStats(
        ap_bonus=5,
        ap_regen_bonus_pct=100,
        program_power=40,
        extra_effect="Connects to Zion mainframe for support",
    ),
    description="Maelcum's handiwork. Tunes the deck into your spinal cord directly.",
    ascii_glyph="[Z]",
    ascii_color=(100, 255, 100),
    upgrade_slots=0,
    required_materials={},
)

# === Creative (custom) ===
NANO_HIVE = Equipment(
    id="implant_nanohive",
    name="Nano-Hive",
    slot=EquipSlot.IMPLANT,
    category=EquipCategory.NANOWARE,
    tier=EquipTier.T3_MILITECH,
    stats=EquipStats(extra_effect="Heals 2 HP per turn (poison immune)"),
    description="Billions of nanobots in your bloodstream. Maintenance nightmare.",
    ascii_glyph="[N]",
    ascii_color=(0, 255, 100),
    upgrade_slots=2,
    required_materials={"wetware_data": 3, "data_fragment": 5},
)

TRODES_NINJA = Equipment(
    id="trodes_ninja",
    name="Stealth Trodes",
    slot=EquipSlot.TRODES,
    category=EquipCategory.WETWARE,
    tier=EquipTier.T2_COMMERCIAL,
    stats=EquipStats(program_power=10, crit_bonus_pct=15, extra_effect="+Stealth in Matrix"),
    description="Silent connection. ICE can't trace you.",
    ascii_glyph="[~]",
    ascii_color=(150, 100, 200),
    upgrade_slots=1,
)

BOOTS_GHOST = Equipment(
    id="boots_ghost",
    name="Chameleon Boots",
    slot=EquipSlot.BOOTS,
    category=EquipCategory.CYBERNETIC,
    tier=EquipTier.T2_COMMERCIAL,
    stats=EquipStats(defense=3, hp_bonus=10, extra_effect="+Movement speed (Matrix)"),
    description="Adaptive camouflage. Silent when you want to be.",
    ascii_glyph="[B]",
    ascii_color=(100, 100, 150),
)


# ============================================================================
# Set Bonus Definitions
# ============================================================================
#
# A set bonus is awarded when the player equips ≥2 or ≥3 pieces from the
# same set_id. The Equipment dataclass already carries ``set_id``; this
# table maps each set_id → threshold → bonus stats.
#
# Design:
#   ono_sendai : deck-focused (program_power) — 2/3 piece thresholds
#   militech   : offense-focused (attack_bonus, crit_bonus_pct)
#   arasaka    : defense + skill (defense, ice_resistance, grants_skill)
#
# T6 master gear does NOT contribute to legacy set bonuses — master
# gear is a tier above and has its own implicit set ("master").

SET_BONUSES: dict[str, dict[int, EquipStats]] = {
    "ono_sendai": {
        2: EquipStats(
            program_power=10,
            crit_bonus_pct=5,
            extra_effect="Ono-Sendai resonance (2pc): deck runs cooler",
        ),
        3: EquipStats(
            program_power=25,
            ap_regen_bonus_pct=10,
            extra_effect="Ono-Sendai sync (3pc): jack in 1 turn faster",
        ),
    },
    "militech": {
        2: EquipStats(
            attack_bonus=5,
            crit_bonus_pct=10,
            extra_effect="Militech targeting (2pc): +hit chance",
        ),
        3: EquipStats(
            attack_bonus=15,
            crit_bonus_pct=25,
            shield_bonus=2,
            extra_effect="Militech apex (3pc): +25% crit, +shield regen",
        ),
    },
    "arasaka": {
        2: EquipStats(
            defense=8,
            ice_resistance=15,
            extra_effect="Arasaka wards (2pc): corporate-grade shields",
        ),
        3: EquipStats(
            defense=20,
            hp_bonus=30,
            ice_resistance=30,
            extra_effect=("Arasaka Onikiri (3pc): +30 hp, ICE deals 30% less damage"),
        ),
    },
}


def get_set_bonus(set_id: str | None, pieces_equipped: int) -> EquipStats | None:
    """Return the highest applicable set bonus for ``pieces_equipped`` items.

    Walks SET_BONUSES[set_id] thresholds in descending order and returns
    the first bonus whose threshold is ≤ ``pieces_equipped``.

    Returns None if the set_id has no bonuses, the item is not part of
    any set, or no threshold is met.
    """
    if not set_id:
        return None
    thresholds = SET_BONUSES.get(set_id, {})
    if not thresholds:
        return None
    for threshold in sorted(thresholds.keys(), reverse=True):
        if pieces_equipped >= threshold:
            return thresholds[threshold]
    return None


# ============================================================================
# Registry
# ============================================================================


class EquipmentRegistry:
    """Lookup for equipment by ID."""

    def __init__(self, equipment: dict[str, Equipment] | None = None) -> None:
        self._equipment: dict[str, Equipment] = dict(equipment or {})

    @classmethod
    def load_default(cls) -> EquipmentRegistry:
        """Load default Gibson-inspired equipment set."""
        default_equipment = {
            # Tier 0
            "deck_basic": STARTER_DECK,
            "head_basic": STARTER_HEADWARE,
            # Tier 1
            "deck_street": STREET_DECK,
            "eyes_militech": MILITECH_EYES,
            "gloves_chrome": CHROME_GLOVES,
            # Tier 2
            "deck_corporate": CORPORATE_DECK,
            "bodysuit_subdermal": SUBDERMAL,
            "trodes_ninja": TRODES_NINJA,
            "boots_ghost": BOOTS_GHOST,
            # Tier 3
            "deck_militech": MILITECH_DECK,
            "bodysuit_tactical": TACTICAL_BODY,
            "implant_nanohive": NANO_HIVE,
            # Tier 4
            "deck_arasaka": ARASAKA_DECK,
            "head_kereznikov": KEREZNIKOV,
            # Tier 5
            "deck_ghost": GHOST_DECK,
            # Tier 6 (master)
            "deck_master": MASTER_DECK,
            "bodysuit_master": MASTER_BODY,
            "trodes_zion": ZION_TRODES,
        }
        return cls(default_equipment)

    def get(self, equip_id: str) -> Equipment | None:
        """Look up an equipment by id; returns None if not registered."""
        return self._equipment.get(equip_id)

    def all(self) -> list[Equipment]:
        """Return every registered equipment."""
        return list(self._equipment.values())

    def by_slot(self, slot: EquipSlot) -> list[Equipment]:
        """Return all registered equipment for the given slot."""
        return [e for e in self._equipment.values() if e.slot == slot]


# ============================================================================
# Equipped Loadout
# ============================================================================


@dataclass
class EquipmentLoadout:
    """Player's currently equipped gear.

    Each slot can hold at most one equipment.
    """

    equipment: dict[EquipSlot, Equipment] = field(default_factory=dict)

    def equip(self, equipment: Equipment) -> Equipment | None:
        """Equip an item. Returns previously equipped item in same slot, if any."""
        previous = self.equipment.get(equipment.slot)
        self.equipment[equipment.slot] = equipment
        return previous

    def unequip(self, slot: EquipSlot) -> Equipment | None:
        """Remove equipment from a slot. Returns the removed item, if any."""
        return self.equipment.pop(slot, None)

    def get(self, slot: EquipSlot) -> Equipment | None:
        """Get equipment in a slot."""
        return self.equipment.get(slot)

    def all_slots_filled(self) -> list[EquipSlot]:
        """Return all slots that currently have equipment (in insertion order)."""
        return list(self.equipment.keys())

    def empty_slots(self) -> list[EquipSlot]:
        """Return all slots that do not yet have equipment (in EquipSlot enum order)."""
        return [s for s in EquipSlot if s not in self.equipment]

    def is_complete(self) -> bool:
        """Return True if every EquipSlot has an item equipped (full loadout)."""
        return len(self.equipment) == len(EquipSlot)

    def set_counts(self) -> dict[str, int]:
        """Count equipped items per set_id (excludes None / no-set items).

        Returns:
            Mapping set_id → number of equipped items in that set.
            Items without a set_id are not counted (they're generic).
        """
        counts: dict[str, int] = {}
        for equipment in self.equipment.values():
            if equipment.set_id is None:
                continue
            counts[equipment.set_id] = counts.get(equipment.set_id, 0) + 1
        return counts

    def set_bonuses(self) -> list[EquipStats]:
        """Return all active set bonuses (one EquipStats per qualifying set).

        Walks each set's count and applies the highest applicable
        threshold bonus via :func:`get_set_bonus`. Items without a
        set_id contribute nothing.
        """
        bonuses: list[EquipStats] = []
        for set_id, count in self.set_counts().items():
            bonus = get_set_bonus(set_id, count)
            if bonus is not None:
                bonuses.append(bonus)
        return bonuses

    def total_stats(self) -> EquipStats:
        """Aggregate all stats from equipped items + active set bonuses."""
        total = EquipStats()
        for equipment in self.equipment.values():
            total = _add_stats(total, equipment.stats)
        for bonus in self.set_bonuses():
            total = _add_stats(total, bonus)
        return total


def _add_stats(a: EquipStats, b: EquipStats) -> EquipStats:
    """Add two EquipStats."""
    return EquipStats(
        attack_bonus=a.attack_bonus + b.attack_bonus,
        crit_bonus_pct=a.crit_bonus_pct + b.crit_bonus_pct,
        damage_bonus_pct=a.damage_bonus_pct + b.damage_bonus_pct,
        defense=a.defense + b.defense,
        hp_bonus=a.hp_bonus + b.hp_bonus,
        shield_bonus=a.shield_bonus + b.shield_bonus,
        ap_bonus=a.ap_bonus + b.ap_bonus,
        ap_regen_bonus_pct=a.ap_regen_bonus_pct + b.ap_regen_bonus_pct,
        program_power=a.program_power + b.program_power,
        ice_resistance=a.ice_resistance + b.ice_resistance,
        grants_skill_id=a.grants_skill_id or b.grants_skill_id,
        extra_effect=", ".join(filter(None, [a.extra_effect, b.extra_effect])),
    )
