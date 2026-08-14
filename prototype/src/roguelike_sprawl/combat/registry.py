"""Combat registry: build combatants from JSON data (ADR-0003, ADR-0008)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from ..matrix.ppl import Loadout, Program
from ..portraits import PortraitManager
from .state import (
    ALARM_SPEED_BY_ICE,
    DEFAULT_ALARM_SPEED,
    Combatant,
    Skill,
    SkillEffect,
)


class ProgramRegistry:
    """Lookup for menu skills (programs) by id."""

    __slots__ = ("_skills",)

    def __init__(self, skills: dict[str, Skill]) -> None:
        """Initialize with a copy of the given skill mapping."""
        self._skills = dict(skills)

    @classmethod
    def load(cls, path: Path) -> ProgramRegistry:
        """Load program skills from a JSON file, falling back to defaults."""
        if not path.exists():
            return cls(_default_skills())
        with path.open(encoding="utf-8") as f:
            raw: object = json.load(f)
        if not isinstance(raw, dict):
            return cls(_default_skills())

        skills: dict[str, Skill] = _default_skills()
        for key, value in raw.items():
            if not isinstance(value, dict):
                continue
            try:
                effect_str = str(value.get("type", "attack"))
                # Convert to SkillEffect enum
                try:
                    effect = SkillEffect(effect_str)
                except ValueError:
                    effect = SkillEffect.ATTACK

                # Color parsing
                color = (255, 255, 255)
                col_raw = value.get("color")
                if isinstance(col_raw, (list, tuple)) and len(col_raw) == 3:
                    color = (int(col_raw[0]), int(col_raw[1]), int(col_raw[2]))

                skills[str(key)] = Skill(
                    id=str(key),
                    name=str(value.get("name", key)),
                    tier=int(value.get("tier", 1)),
                    effect=effect,
                    ap_cost=int(value.get("ap_cost", 1)),
                    damage=int(value.get("damage", 0)),
                    shield=int(value.get("shield", 0)),
                    heal=int(value.get("heal", 0)),
                    dot_damage=int(value.get("dot_damage", 0)),
                    dot_duration_ms=int(value.get("dot_duration_ms", 0)),
                    buff_amount=int(value.get("buff_amount", 0)),
                    buff_duration_ms=int(value.get("buff_duration_ms", 0)),
                    stun_duration_ms=int(value.get("stun_duration_ms", 0)),
                    hit_count=int(value.get("hit_count", 1)),
                    cooldown_ms=int(value.get("cooldown_ms", 0)),
                    crit_bonus=float(value.get("crit_bonus", 0)),
                    role=(str(value["role"]) if value.get("role") is not None else None),
                    effect_color=color,
                    effect_glyph=str(value.get("glyph", "*")),
                )
            except (TypeError, ValueError):
                continue
        return cls(skills)

    def get(self, skill_id: str) -> Skill | None:
        """Look up a skill by id; returns None if not registered."""
        return self._skills.get(skill_id)

    def __iter__(self) -> Iterator[Skill]:
        """Iterate over all registered Skill values."""
        return iter(self._skills.values())

    def __len__(self) -> int:
        """Return the number of registered skills."""
        return len(self._skills)


def _default_skills() -> dict[str, Skill]:
    """Default skill set (used when JSON is missing or as fallback)."""
    skills: dict[str, Skill] = {}
    skills.update(_default_offensive_skills())
    skills.update(_default_defensive_skills())
    skills.update(_default_heal_regen_skills())
    skills.update(_default_buff_debuff_skills())
    return skills


# ------------------------------------------------------------------
# Skill-family helpers — each builds a small subset of the default
# skill roster.  Splitting the long dict into per-category factories
# makes it trivial to find and tune any single skill.
# ------------------------------------------------------------------


def _default_offensive_skills() -> dict[str, Skill]:
    """Direct-damage skills (attack, heavy, pierce, multi-hit, dot)."""
    return {
        "wisp": Skill(
            id="wisp",
            name="Wisp",
            tier=1,
            effect=SkillEffect.ATTACK,
            ap_cost=1,
            damage=8,
            effect_color=(180, 180, 255),
            effect_glyph="*",
        ),
        "goliath": Skill(
            id="goliath",
            name="Goliath",
            tier=1,
            effect=SkillEffect.HEAVY_ATTACK,
            ap_cost=3,
            damage=22,
            cooldown_ms=3000,
            effect_color=(255, 100, 0),
            effect_glyph="◆",
            crit_bonus=0.10,
        ),
        "ice_breaker": Skill(
            id="ice_breaker",
            name="ICE BREAKER",
            tier=1,
            effect=SkillEffect.HEAVY_ATTACK,
            ap_cost=3,
            damage=30,
            cooldown_ms=2000,
            effect_color=(255, 255, 0),
            effect_glyph="▲",
        ),
        "jackhammer": Skill(
            id="jackhammer",
            name="Jackhammer",
            tier=2,
            effect=SkillEffect.MULTI_HIT,
            ap_cost=3,
            damage=7,
            hit_count=3,
            cooldown_ms=4000,
            effect_color=(255, 200, 0),
            effect_glyph="≡",
        ),
        "crowbar": Skill(
            id="crowbar",
            name="Crowbar",
            tier=1,
            effect=SkillEffect.PIERCE,
            ap_cost=2,
            damage=12,
            cooldown_ms=2000,
            effect_color=(255, 50, 50),
            effect_glyph=">",
        ),
        "viral": Skill(
            id="viral",
            name="Viral Spike",
            tier=2,
            effect=SkillEffect.DOT,
            ap_cost=3,
            damage=10,
            dot_damage=4,
            dot_duration_ms=6000,  # 6 seconds
            cooldown_ms=5000,
            effect_color=(0, 255, 0),
            effect_glyph="¤",
        ),
    }


def _default_defensive_skills() -> dict[str, Skill]:
    """Shields, detects, and stuns — utility defence."""
    return {
        "probe": Skill(
            id="probe",
            name="Probe",
            tier=1,
            effect=SkillEffect.SHIELD,
            ap_cost=1,
            shield=15,
            cooldown_ms=2000,
            effect_color=(0, 200, 255),
            effect_glyph="◇",
        ),
        "stun_bolt": Skill(
            id="stun_bolt",
            name="Stun Bolt",
            tier=2,
            effect=SkillEffect.STUN,
            ap_cost=3,
            stun_duration_ms=3000,
            cooldown_ms=6000,
            effect_color=(255, 255, 0),
            effect_glyph="✦",
        ),
        "detect": Skill(
            id="detect",
            name="Detect",
            tier=1,
            effect=SkillEffect.DETECT,
            ap_cost=1,
            cooldown_ms=3000,
            effect_color=(255, 255, 255),
            effect_glyph="?",
        ),
    }


def _default_heal_regen_skills() -> dict[str, Skill]:
    """Direct heal + regen (HoT) skills."""
    return {
        "bandage": Skill(
            id="bandage",
            name="Patch Up",
            tier=1,
            effect=SkillEffect.HEAL,
            ap_cost=2,
            heal=20,
            cooldown_ms=4000,
            effect_color=(0, 255, 0),
            effect_glyph="+",
        ),
        "stim": Skill(
            id="stim",
            name="Stims",
            tier=1,
            effect=SkillEffect.REGEN,
            ap_cost=2,
            heal=30,
            buff_duration_ms=6000,
            cooldown_ms=8000,
            effect_color=(100, 255, 100),
            effect_glyph="♥",
        ),
        "bloodlust": Skill(
            id="bloodlust",
            name="Bloodlust",
            tier=2,
            effect=SkillEffect.LIFESTEAL,
            ap_cost=3,
            damage=18,
            cooldown_ms=4000,
            effect_color=(200, 0, 0),
            effect_glyph="♥",
        ),
    }


def _default_buff_debuff_skills() -> dict[str, Skill]:
    """Self-buff + enemy-debuff skills."""
    return {
        "boost": Skill(
            id="boost",
            name="Boost",
            tier=2,
            effect=SkillEffect.BUFF,
            ap_cost=2,
            buff_amount=8,
            buff_duration_ms=10000,
            cooldown_ms=8000,
            effect_color=(255, 200, 0),
            effect_glyph="↑",
        ),
        "jammer": Skill(
            id="jammer",
            name="Jammer",
            tier=2,
            effect=SkillEffect.DEBUFF,
            ap_cost=2,
            buff_amount=5,
            buff_duration_ms=8000,
            cooldown_ms=6000,
            effect_color=(150, 150, 255),
            effect_glyph="↓",
        ),
    }


class IceRegistry:
    """Lookup for ICE enemy templates."""

    __slots__ = ("_ice",)

    def __init__(self, ice: dict[str, dict[str, int | str]]) -> None:
        """Initialize with a copy of the given ICE template mapping."""
        self._ice = dict(ice)

    @classmethod
    def load(cls, path: Path) -> IceRegistry:
        """Load ICE templates from a JSON file; empty registry if missing."""
        if not path.exists():
            return cls({})
        with path.open(encoding="utf-8") as f:
            raw: object = json.load(f)
        if not isinstance(raw, dict):
            return cls({})
        ice: dict[str, dict[str, int | str]] = {}
        for key, value in raw.items():
            if isinstance(value, dict):
                ice[str(key)] = value
        return cls(ice)

    def get(self, ice_id: str) -> dict[str, int | str] | None:
        """Look up an ICE template by id; returns None if not registered."""
        return self._ice.get(ice_id)

    def __contains__(self, ice_id: object) -> bool:
        """Return True if `ice_id` is a registered ICE template id."""
        return isinstance(ice_id, str) and ice_id in self._ice


def build_default_player(
    *,
    loadout: Loadout | None = None,
    max_hp: int = 100,
    max_ap: int = 6,
    base_damage: int = 5,
    program_ids: tuple[str, ...] = ("wisp", "goliath", "probe", "viral", "stun_bolt"),
    programs: ProgramRegistry | None = None,
) -> Combatant:
    """Build a 1-up player with the given programs."""
    loadout = loadout or Loadout(
        deck_tier=1,
        programs=(Program(id="wisp", name="Wisp", tier=1),),
        wetware_tier=1,
    )
    skills: list[Skill] = []
    if programs is not None:
        for pid in program_ids:
            s = programs.get(pid)
            if s is not None:
                skills.append(s)
    return Combatant(
        id="player",
        name="You",
        portrait="◉P◉",
        color=(0, 255, 0),
        hp=max_hp,
        max_hp=max_hp,
        ap=max_ap,
        max_ap=max_ap,
        auto_attack_damage=base_damage,
        skills=tuple(skills),
        team="player",
    )


def get_scaled_ice_stats(
    data: dict[str, int | str],
    player_grade: int,
) -> tuple[int, int]:
    """Calculate scaled HP/DMG based on player grade.

    HP = hp_base + (hp_per_grade * max(0, player_grade - ice_tier))
    DMG = dmg_base + (dmg_per_grade * max(0, player_grade - ice_tier))
    Minimum scale factor: 0.7 (70%) when player is under-tier
    """
    hp_base = int(data.get("hp_base", data.get("hp", 80)))
    hp_per_grade = int(data.get("hp_per_grade", 0))
    dmg_base = int(data.get("dmg_base", data.get("base_damage", 3)))
    dmg_per_grade = int(data.get("dmg_per_grade", 0))
    ice_tier = int(data.get("tier", 1))

    grade_diff = player_grade - ice_tier

    if grade_diff >= 0:
        hp = hp_base + (hp_per_grade * grade_diff)
        dmg = dmg_base + (dmg_per_grade * grade_diff)
    else:
        scale = 1.0 + (grade_diff * 0.15)
        scale = max(0.7, scale)
        hp = int(hp_base * scale)
        dmg = int(dmg_base * scale)

    return hp, dmg


def build_ice_enemy(
    ice_id: str,
    registry: IceRegistry,
    *,
    portraits: PortraitManager | None = None,
    player_grade: int | None = None,
    program_registry: ProgramRegistry | None = None,
) -> Combatant:
    """Build an ICE enemy from the registry.

    If player_grade is provided, stats are scaled according to the difficulty formula.
    Phase B-1: optional program_registry loads ICE skills from ice_types.json
    "skills" field (currently unused; reserved for future boss/elite ICE).
    """
    data = registry.get(ice_id)
    if data is None:
        available = sorted(registry._ice.keys())
        raise KeyError(
            f"Unknown ICE: {ice_id!r}. "
            f"Available: {available[:10]}{'...' if len(available) > 10 else ''}"
        )
    portrait_id = str(data.get("portrait", "ice.standard"))
    portrait = "▲ICE▲"
    color = (255, 0, 255)
    if portraits is not None and portraits.has(portrait_id):
        p = portraits.get(portrait_id)
        portrait = str(p.get("ascii", portrait))
        col_raw = p.get("color", color)
        if isinstance(col_raw, tuple) and len(col_raw) == 3:
            color = (int(col_raw[0]), int(col_raw[1]), int(col_raw[2]))

    if player_grade is not None:
        hp, dmg = get_scaled_ice_stats(data, player_grade)
    else:
        hp = int(data.get("hp_base", data.get("hp", 80)))
        dmg = int(data.get("dmg_base", data.get("base_damage", 3)))

    # Phase B-1: load ICE skills (currently only used if ice_types.json
    # declares non-empty skills; reserved for boss/elite variants)
    ice_skills: tuple[Skill, ...] = ()
    raw_skills_obj: object = data.get("skills", [])
    raw_skills: list[object] = raw_skills_obj if isinstance(raw_skills_obj, list) else []
    if program_registry is not None:
        loaded: list[Skill] = []
        for sid in raw_skills:
            if isinstance(sid, str) and program_registry.get(sid) is not None:
                skill = program_registry.get(sid)
                if skill is not None:
                    loaded.append(skill)
        ice_skills = tuple(loaded)

    return Combatant(
        id=ice_id,
        name=str(data.get("name", ice_id)),
        portrait=portrait,
        color=color,
        hp=hp,
        max_hp=hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=dmg,
        skills=ice_skills,
        team="enemy",
        ice_kind=str(data.get("ice_kind", ice_id)),
        ice_resistance=float(data.get("resistance", 0.0)),
        alarm_speed=ALARM_SPEED_BY_ICE.get(str(data.get("ice_kind", ice_id)), DEFAULT_ALARM_SPEED),
    )
