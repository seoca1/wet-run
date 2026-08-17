"""Save progress summary (ADR-0032).

Provides a unified interface for querying the player's actual game
progress. Used by the Saved Progress card (SAVED_PROGRESS screen)
after the graphic novel mode ends.

Reads from:
    - save_manager (most recent save)
    - run/state (current run if any)
    - achievements (count)
    - credits (current wallet)

Returns:
    - ProgressSummary dataclass with character, grade, missions,
      data, last_mission, last_zone
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .save_manager import SaveManager


@dataclass(frozen=True, slots=True)
class ProgressSummary:
    """Immutable view of the player's current progress.

    Attributes:
        has_save: Whether any save exists.
        character_name: "K (Novice)" | "Sil (Veteran)" | "Kas (Heretic)" | ""
        character_id: "novice" | "veteran" | "heretic" | ""
        grade: Player grade (1~5). 0 if no save.
        grade_label: Short label (e.g. "3-up")
        missions_completed: Total missions completed. 0 if no save.
        missions_total: Total missions in current grade (estimate 30).
        data_recovered: Total data extracted.
        data_total: Estimate of total data.
        last_mission_id: ID of last played mission ("" if no save).
        last_zone: Last visited zone (e.g. "Tessier-Ashpool HQ").
        credits: Current credits in wallet.
        playtime_minutes: Total playtime in minutes.
    """

    has_save: bool
    character_name: str
    character_id: str
    grade: int
    grade_label: str
    missions_completed: int
    missions_total: int
    data_recovered: int
    data_total: int
    last_mission_id: str
    last_zone: str
    credits: int
    playtime_minutes: int


def _empty_summary() -> ProgressSummary:
    """Return an empty progress summary (no save)."""
    return ProgressSummary(
        has_save=False,
        character_name="",
        character_id="",
        grade=0,
        grade_label="-",
        missions_completed=0,
        missions_total=30,
        data_recovered=0,
        data_total=500,
        last_mission_id="",
        last_zone="",
        credits=0,
        playtime_minutes=0,
    )


_CHARACTER_LABELS: dict[str, str] = {
    "novice": "K — Novice",
    "veteran": "Sil — Veteran",
    "heretic": "Kas — Heretic",
}


def _grade_label(grade: int) -> str:
    """Return human-readable grade label (e.g. "3-up")."""
    if grade <= 0:
        return "-"
    return f"{grade}-up"


def get_progress_summary(
    save_manager: SaveManager | None = None,
    save_dir: Path | None = None,
) -> ProgressSummary:
    """Build a progress summary from the most recent save.

    Args:
        save_manager: Optional SaveManager instance. If None, will
            create one from save_dir.
        save_dir: Optional save directory. Defaults to None.

    Returns:
        ProgressSummary with current progress (or empty if no save).
    """
    if save_manager is None:
        from .save_manager import SaveManager

        save_manager = SaveManager(save_dir or Path("saves"))

    latest_meta = _find_latest_save(save_manager)
    if latest_meta is None:
        return _empty_summary()

    try:
        latest = save_manager.load(latest_meta.slot)
    except Exception:
        return _summary_from_metadata(latest_meta)

    return _summary_from_save(latest_meta, latest)


# ------------------------------------------------------------------
# get_progress_summary helpers
# ------------------------------------------------------------------


def _find_latest_save(save_manager: Any) -> Any:
    """Return the slot metadata for the most recent save, or None."""
    try:
        slots = save_manager.list_slots()
        existing = [s for s in slots if s.exists]
    except (OSError, AttributeError):
        return None
    if not existing:
        return None
    return max(existing, key=lambda s: s.saved_at or "")


def _summary_from_metadata(latest_meta: Any) -> ProgressSummary:
    """Build a ProgressSummary from slot metadata only (no full load)."""
    return ProgressSummary(
        has_save=True,
        character_name="",
        character_id="",
        grade=latest_meta.player_grade or 0,
        grade_label=_grade_label(latest_meta.player_grade or 0),
        missions_completed=0,
        missions_total=30,
        data_recovered=0,
        data_total=500,
        last_mission_id=latest_meta.mission_id or "",
        last_zone=latest_meta.current_stage or "",
        credits=latest_meta.credits or 0,
        playtime_minutes=(latest_meta.elapsed_seconds or 0) // 60,
    )


def _summary_from_save(latest_meta: Any, latest: Any) -> ProgressSummary:
    """Build a ProgressSummary from a fully-loaded SavedRun."""
    run_state: dict[str, object] = latest.run_state if isinstance(latest.run_state, dict) else {}
    app_state: dict[str, object] = latest.app_state if isinstance(latest.app_state, dict) else {}
    metadata: dict[str, object] = latest.metadata if isinstance(latest.metadata, dict) else {}

    character_id = str(app_state.get("character_id", metadata.get("character_id", "novice")))
    character_name = _CHARACTER_LABELS.get(character_id, "")

    grade_raw = metadata.get("player_grade", app_state.get("player_grade", 0))
    try:
        grade = int(str(grade_raw))
    except (ValueError, TypeError):
        grade = 0

    last_mission = str(run_state.get("mission_id", ""))
    last_zone = str(run_state.get("current_stage", ""))

    try:
        credits_val = int(str(metadata.get("credits", latest_meta.credits or 0)))
    except (ValueError, TypeError):
        credits_val = 0
    playtime_minutes = (latest.elapsed_seconds or 0) // 60

    missions_completed = 0
    completed_stages = run_state.get("completed_stages", [])
    if isinstance(completed_stages, list):
        missions_completed = len(completed_stages)

    data_recovered = 0
    try:
        data_recovered = int(str(metadata.get("data_recovered", 0)))
    except (ValueError, TypeError):
        data_recovered = 0

    return ProgressSummary(
        has_save=True,
        character_name=character_name,
        character_id=character_id,
        grade=grade,
        grade_label=_grade_label(grade),
        missions_completed=missions_completed,
        missions_total=30,
        data_recovered=data_recovered,
        data_total=500,
        last_mission_id=last_mission,
        last_zone=last_zone,
        credits=credits_val,
        playtime_minutes=playtime_minutes,
    )


def render_summary_lines(summary: ProgressSummary, t_lang: str = "ko") -> list[str]:
    """Render the progress summary as a list of text lines.

    Args:
        summary: The progress summary to render.
        t_lang: "ko" or "en" for label localization.

    Returns:
        List of formatted lines for display.
    """
    if not summary.has_save:
        if t_lang == "ko":
            return [
                "",
                "        세이브 파일이 없습니다.",
                "        NEW RUN으로 시작해 보세요.",
                "",
            ]
        return [
            "",
            "        No save file found.",
            "        Start with NEW RUN.",
            "",
        ]

    if t_lang == "ko":
        return [
            f"  자키: {summary.character_name}",
            f"  등급: {summary.grade_label}",
            (
                f"  미션 완료: {summary.missions_completed} / "
                f"{summary.missions_total} "
                f"({int(summary.missions_completed / max(summary.missions_total, 1) * 100)}%)"
            ),
            f"  데이터 회수: {summary.data_recovered} / {summary.data_total}",
            f"  마지막 의뢰: {summary.last_mission_id or '-'}",
            f"  마지막 위치: {summary.last_zone or '-'}",
            f"  플레이 시간: {summary.playtime_minutes}분",
            "",
        ]
    return [
        f"  Jockey: {summary.character_name}",
        f"  Grade: {summary.grade_label}",
        (
            f"  Missions: {summary.missions_completed} / "
            f"{summary.missions_total} "
            f"({int(summary.missions_completed / max(summary.missions_total, 1) * 100)}%)"
        ),
        f"  Data: {summary.data_recovered} / {summary.data_total}",
        f"  Last mission: {summary.last_mission_id or '-'}",
        f"  Last zone: {summary.last_zone or '-'}",
        f"  Playtime: {summary.playtime_minutes}m",
        "",
    ]
