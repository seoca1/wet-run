"""Skill combo system for combat.

Players chain 3-7 skills within a time window (3.5s by default) for
cumulative bonuses:

  Stage 0 (1-2 hits): WARMUP     - no bonus
  Stage 1 (3 hits):   CHAIN       - +20% damage, "3x CHAIN!"
  Stage 2 (4 hits):   FLURRY      - +50% damage, +1 AP, "4x FLURRY!"
  Stage 3 (5 hits):   RAMPAGE     - +100% damage, +2 AP, "5x RAMPAGE!"
  Stage 4 (6+ hits):  ANNIHILATION - +200% damage, +3 AP, "6x ANNIHILATION!"

Features:
  - Window-based: combo resets after 3.5s without a hit
  - Per-stage visual: counter color escalates, screen shake on high stages
  - Stage-up cinematic: brief text callout on reaching new stage
  - End visual: "콤보 종료" with bonus summary
  - Integration: apply bonus damage/AP to skill resolution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .palette import COMBO_STAGE_COLORS

if TYPE_CHECKING:
    pass


# ----------------------------------------------------------------------------
# Combo stage definitions
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ComboStage:
    """A stage in the combo progression.

    Activated when combo count reaches `min_count`. Provides:
    - Display label (e.g. "3x CHAIN!")
    - Damage bonus percentage
    - AP regen on hit
    - Screen shake intensity
    - Color for the counter display
    - Korean name for stage-up callout
    """

    index: int
    name: str
    name_ko: str
    min_count: int
    damage_bonus_pct: int
    ap_regen: int
    screen_shake: float
    color: tuple[int, int, int]
    label: str


# 5 combo stages
WARMUP = ComboStage(
    index=0,
    name="WARMUP",
    name_ko="웜업",
    min_count=1,
    damage_bonus_pct=0,
    ap_regen=0,
    screen_shake=0.0,
    color=COMBO_STAGE_COLORS[0],
    label="",
)

CHAIN = ComboStage(
    index=1,
    name="CHAIN",
    name_ko="연쇄",
    min_count=3,
    damage_bonus_pct=20,
    ap_regen=0,
    screen_shake=0.5,
    color=COMBO_STAGE_COLORS[1],
    label="CHAIN!",
)

FLURRY = ComboStage(
    index=2,
    name="FLURRY",
    name_ko="폭주",
    min_count=4,
    damage_bonus_pct=50,
    ap_regen=1,
    screen_shake=1.5,
    color=COMBO_STAGE_COLORS[2],
    label="FLURRY!",
)

RAMPAGE = ComboStage(
    index=3,
    name="RAMPAGE",
    name_ko="섬멸",
    min_count=5,
    damage_bonus_pct=100,
    ap_regen=2,
    screen_shake=2.5,
    color=COMBO_STAGE_COLORS[3],
    label="RAMPAGE!",
)

ANNIHILATION = ComboStage(
    index=4,
    name="ANNIHILATION",
    name_ko="초월",
    min_count=6,
    damage_bonus_pct=200,
    ap_regen=3,
    screen_shake=4.0,
    color=COMBO_STAGE_COLORS[4],
    label="ANNIHILATION!",
)

ALL_STAGES: tuple[ComboStage, ...] = (
    WARMUP,
    CHAIN,
    FLURRY,
    RAMPAGE,
    ANNIHILATION,
)


# ----------------------------------------------------------------------------
# Combo state
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class CombatCombo:
    """Tracks the current combo in combat.

    Hits within `window_ms` of each other accumulate. Each hit
    increases the count; the current stage is the highest stage
    whose min_count is ≤ the count.
    """

    count: int = 0
    last_hit_ms: int = 0
    current_stage: ComboStage = WARMUP
    previous_stage: ComboStage = WARMUP
    # Visual state
    elapsed_ms: int = 0  # Time since last hit
    window_ms: int = 3500
    stage_up_pending: bool = False  # True for 1 frame when stage changes
    just_ended: bool = False  # True for 1 frame when combo ends
    # Stats
    total_damage_dealt: int = 0
    total_ap_gained: int = 0
    max_combo_reached: int = 0

    def register_hit(
        self,
        current_ms: int,
        damage_dealt: int = 0,
    ) -> ComboStage:
        """Register a hit; returns the (possibly new) current stage.

        If the window has expired, count resets to 1. Otherwise count
        increments. Stage changes trigger stage_up_pending.
        """
        if current_ms - self.last_hit_ms > self.window_ms:
            # Window expired — reset
            self.count = 1
        else:
            self.count += 1

        self.last_hit_ms = current_ms
        self.elapsed_ms = 0
        self.total_damage_dealt += damage_dealt
        self.max_combo_reached = max(self.max_combo_reached, self.count)

        # Update stage
        new_stage = self._stage_for_count(self.count)
        if new_stage.index > self.current_stage.index:
            self.previous_stage = self.current_stage
            self.current_stage = new_stage
            self.stage_up_pending = True
        else:
            self.stage_up_pending = False

        # Apply AP regen (cumulative across hits in the same stage)
        # Note: AP is given to the player, not stored in combo
        return new_stage

    def step(self, dt_ms: int) -> None:
        """Step the combo forward. Detect window expiry."""
        self.elapsed_ms += dt_ms
        # Clear one-shot flags
        if self.stage_up_pending:
            # stays True for 1 step
            pass
        # Window check
        if self.count > 0 and self.elapsed_ms > self.window_ms:
            # Combo ended
            self.just_ended = True
            self.count = 0
            self.current_stage = WARMUP
            self.previous_stage = WARMUP
            self.elapsed_ms = 0
        else:
            self.just_ended = False

    def consume_stage_up(self) -> ComboStage | None:
        """Consume stage_up flag. Returns the new stage if it was just raised."""
        if self.stage_up_pending:
            self.stage_up_pending = False
            return self.current_stage
        return None

    def consume_just_ended(self) -> bool:
        """Consume just_ended flag. Returns True if combo just ended."""
        if self.just_ended:
            self.just_ended = False
            return True
        return False

    def reset(self) -> None:
        """Reset the combo (e.g. on combat end)."""
        self.count = 0
        self.current_stage = WARMUP
        self.previous_stage = WARMUP
        self.elapsed_ms = 0
        self.stage_up_pending = False
        self.just_ended = False

    def _stage_for_count(self, count: int) -> ComboStage:
        """Get the highest stage whose min_count is ≤ count."""
        stage = WARMUP
        for s in ALL_STAGES:
            if count >= s.min_count:
                stage = s
        return stage

    @property
    def display_count(self) -> int:
        """Count to show in the UI (max 99)."""
        return min(self.count, 99)

    @property
    def display_label(self) -> str:
        """Full combo label e.g. '3x CHAIN!'."""
        if self.count < 2:
            return ""
        return f"{self.display_count}x {self.current_stage.label}"

    @property
    def window_progress(self) -> float:
        """0.0 to 1.0 progress through the combo window.

        Used to show a "draining" timer bar.
        """
        if self.count == 0 or self.window_ms == 0:
            return 0.0
        return min(1.0, self.elapsed_ms / self.window_ms)

    @property
    def window_remaining_pct(self) -> int:
        """0-100 percent of window remaining."""
        return int((1.0 - self.window_progress) * 100)

    def apply_damage_bonus(self, base_damage: int) -> int:
        """Apply the current stage's damage bonus to a base damage value."""
        bonus = base_damage * self.current_stage.damage_bonus_pct // 100
        return base_damage + bonus

    def get_ap_regen(self) -> int:
        """AP regen amount for the current stage."""
        return self.current_stage.ap_regen


# ----------------------------------------------------------------------------
# Combo visual state
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class ComboVisual:
    """Visual state for the combo display.

    Drives the top-center combo counter and any stage-up cinematic.
    """

    counter_text: str = ""
    counter_color: tuple[int, int, int] = (200, 200, 200)
    counter_pulse_ms: int = 0  # Pulses when new hit registered
    counter_pulse_max_ms: int = 200
    # Stage-up cinematic
    stage_up_text: str = ""
    stage_up_color: tuple[int, int, int] = (200, 200, 200)
    stage_up_ms: int = 0
    stage_up_max_ms: int = 800
    # End cinematic
    end_text: str = ""
    end_ms: int = 0
    end_max_ms: int = 1500


def update_combo_visual(
    visual: ComboVisual,
    combo: CombatCombo,
) -> None:
    """Update the visual state from combo state."""
    visual.counter_text = combo.display_label
    visual.counter_color = combo.current_stage.color

    # Decay pulses
    if visual.counter_pulse_ms > 0:
        visual.counter_pulse_ms = max(0, visual.counter_pulse_ms - 16)
    if visual.stage_up_ms > 0:
        visual.stage_up_ms = max(0, visual.stage_up_ms - 16)
    if visual.end_ms > 0:
        visual.end_ms = max(0, visual.end_ms - 16)

    # Stage-up cinematic
    new_stage = combo.consume_stage_up()
    if new_stage is not None:
        visual.stage_up_text = f"▸ {new_stage.name_ko} 단계 돌입 ({new_stage.label})"
        visual.stage_up_color = new_stage.color
        visual.stage_up_ms = visual.stage_up_max_ms
        visual.counter_pulse_ms = visual.counter_pulse_max_ms

    # End cinematic
    if combo.consume_just_ended():
        max_combo = combo.max_combo_reached
        total_dmg = combo.total_damage_dealt
        visual.end_text = f"[ 콤보 종료 ]  최대 {max_combo} 히트, {total_dmg} 데미지"
        visual.end_ms = visual.end_max_ms
        visual.counter_text = ""
        visual.counter_pulse_ms = 0


# ----------------------------------------------------------------------------
# Combo display rendering
# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# High-level spawner
# ----------------------------------------------------------------------------


def spawn_combo_hit(
    combo: CombatCombo,
    visual: ComboVisual,
    current_ms: int,
    damage_dealt: int = 0,
) -> ComboStage:
    """Register a combo hit, update visual, return new stage.

    This is the main entry point. combat_view calls this on every
    successful player skill use.
    """
    new_stage = combo.register_hit(current_ms, damage_dealt)
    if new_stage.index > 0:
        visual.counter_pulse_ms = visual.counter_pulse_max_ms
    update_combo_visual(visual, combo)
    return new_stage


# ----------------------------------------------------------------------------
# Stage Avatar (per-stage icon)
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StageAvatar:
    """ASCII icon for a combo stage.

    Each stage has 3 frames (idle, pulse, special) for animation.
    """

    stage: ComboStage
    icon_idle: str
    icon_pulse: str
    icon_special: str
    frame_label: str  # e.g. "1/5", "2/5"

    def get_frame(self, pulse_active: bool = False, special: bool = False) -> str:
        if special:
            return self.icon_special
        if pulse_active:
            return self.icon_pulse
        return self.icon_idle


# Per-stage avatars
AVATAR_WARMUP = StageAvatar(
    stage=WARMUP,
    icon_idle="◦",
    icon_pulse="○",
    icon_special="◉",
    frame_label="1/5",
)
AVATAR_CHAIN = StageAvatar(
    stage=CHAIN,
    icon_idle="⫶",
    icon_pulse="⫷⫸",
    icon_special="⫴",
    frame_label="2/5",
)
AVATAR_FLURRY = StageAvatar(
    stage=FLURRY,
    icon_idle="⚡",
    icon_pulse="⚡⚡",
    icon_special="✦⚡",
    frame_label="3/5",
)
AVATAR_RAMPAGE = StageAvatar(
    stage=RAMPAGE,
    icon_idle="☠",
    icon_pulse="☠☠",
    icon_special="☠✦",
    frame_label="4/5",
)
AVATAR_ANNIHILATION = StageAvatar(
    stage=ANNIHILATION,
    icon_idle="✦",
    icon_pulse="✦✦✦",
    icon_special="✦★✦",
    frame_label="5/5",
)

AVATAR_BY_STAGE: dict[ComboStage, StageAvatar] = {
    WARMUP: AVATAR_WARMUP,
    CHAIN: AVATAR_CHAIN,
    FLURRY: AVATAR_FLURRY,
    RAMPAGE: AVATAR_RAMPAGE,
    ANNIHILATION: AVATAR_ANNIHILATION,
}


def get_avatar_for_stage(stage: ComboStage) -> StageAvatar:
    """Get the avatar for a stage. Falls back to WARMUP if unknown."""
    return AVATAR_BY_STAGE.get(stage, AVATAR_WARMUP)


# ----------------------------------------------------------------------------
# Timing bar
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class TimingBar:
    """Visual timing bar for the combo window.

    Renders a horizontal bar that drains from full to empty
    over the combo window. Color changes as time runs out:
    - > 50%: green (safe)
    - 50-25%: yellow (warning)
    - < 25%: red (urgent)
    - < 10%: pulsing red
    """

    width: int = 20
    last_pulse_ms: int = 0
    pulse_period_ms: int = 200

    def render(self, combo: CombatCombo) -> str:
        """Render the timing bar string."""
        if combo.count == 0:
            return ""

        pct_remaining = 1.0 - combo.window_progress
        filled = int(round(pct_remaining * self.width))
        empty = self.width - filled

        # Color tier drives character selection
        if pct_remaining > 0.5:
            bar_chars = "█" * filled + "░" * empty
        elif pct_remaining > 0.25:
            bar_chars = "▓" * filled + "░" * empty
        else:
            bar_chars = "▓" * filled + "·" * empty

        result = f"[{bar_chars}] {int(pct_remaining * 100)}%"
        return result

    def get_color(self, combo: CombatCombo) -> tuple[int, int, int]:
        """Get the bar color based on time remaining."""
        from .palette import COMBO_BAR_GREEN, COMBO_BAR_RED, COMBO_BAR_YELLOW

        if combo.count == 0:
            return (100, 100, 100)
        pct_remaining = 1.0 - combo.window_progress
        if pct_remaining > 0.5:
            return COMBO_BAR_GREEN
        if pct_remaining > 0.25:
            return COMBO_BAR_YELLOW
        return COMBO_BAR_RED

    def is_urgent(self, combo: CombatCombo) -> bool:
        """True if combo is about to expire (< 25% remaining)."""
        return 0.0 < (1.0 - combo.window_progress) < 0.25


# ----------------------------------------------------------------------------
# Combo Finishers (special moves at high stages)
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ComboFinisher:
    """A special finisher move unlocked at a high combo stage.

    Activated by player input (e.g. spacebar) when combo is at
    the right stage. Provides massive damage/utility.
    """

    id: str
    name: str
    name_ko: str
    required_stage: ComboStage
    damage_multiplier: float  # e.g. 2.0 = 200% of base damage
    ap_cost: int  # 0 for free, but consumes a skill slot
    cooldown_ms: int  # Reuse cooldown
    description: str
    color: tuple[int, int, int]
    icon: str  # ASCII icon
    visual_animation: str  # Animation name from effects


FINISHER_QUICK_SLASH = ComboFinisher(
    id="quick_slash",
    name="QUICK SLASH",
    name_ko="빠른 참격",
    required_stage=FLURRY,
    damage_multiplier=2.0,
    ap_cost=0,
    cooldown_ms=5000,
    description="FLURRY 단계에서 사용 가능. 3회 빠른 참격 (대상 1명).",
    color=(255, 200, 80),
    icon="⚡",
    visual_animation="multi_hit",
)

FINISHER_RAMPAGE_BURST = ComboFinisher(
    id="rampage_burst",
    name="RAMPAGE BURST",
    name_ko="섬멸 폭발",
    required_stage=RAMPAGE,
    damage_multiplier=3.0,
    ap_cost=0,
    cooldown_ms=8000,
    description="RAMPAGE 단계에서 사용 가능. 광역 폭발 (모든 적).",
    color=(255, 100, 80),
    icon="☠",
    visual_animation="heavy_attack",
)

FINISHER_FINAL_STRIKE = ComboFinisher(
    id="final_strike",
    name="FINAL STRIKE",
    name_ko="최후의 일격",
    required_stage=ANNIHILATION,
    damage_multiplier=5.0,
    ap_cost=0,
    cooldown_ms=12000,
    description="ANNIHILATION 단계에서 사용 가능. 즉사급 데미지 + 화면 클리어.",
    color=(255, 30, 30),
    icon="✦",
    visual_animation="critical_hit",
)

ALL_FINISHERS: tuple[ComboFinisher, ...] = (
    FINISHER_QUICK_SLASH,
    FINISHER_RAMPAGE_BURST,
    FINISHER_FINAL_STRIKE,
)


def get_finisher_for_stage(stage: ComboStage) -> ComboFinisher | None:
    """Get the finisher available at a stage, or None."""
    for finisher in ALL_FINISHERS:
        if finisher.required_stage.index == stage.index:
            return finisher
    return None


# ----------------------------------------------------------------------------
# Full combo HUD (avatar + counter + timing bar)
# ----------------------------------------------------------------------------


# Re-export rendering functions from combo_window.py for backwards compat
from .combo_window import (  # noqa: E402,F401
    render_combo_counter,
    render_combo_end,
    render_combo_full,
    render_combo_stage_up,
    render_timing_bar,
)

__all__ = [
    "ALL_STAGES",
    "ANNIHILATION",
    "CHAIN",
    "CombatCombo",
    "ComboFinisher",
    "ComboStage",
    "ComboVisual",
    "FLURRY",
    "RAMPAGE",
    "StageAvatar",
    "TimingBar",
    "WARMUP",
    "get_avatar_for_stage",
    "get_finisher_for_stage",
    "render_combo_counter",
    "render_combo_end",
    "render_combo_full",
    "render_combo_stage_up",
    "render_timing_bar",
    "spawn_combo_hit",
    "update_combo_visual",
]
