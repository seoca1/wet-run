"""Tests for save_progress module (ADR-0032).

Covers:
    - ProgressSummary dataclass
    - get_progress_summary with various save states
    - render_summary_lines formatting
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.save_progress import (  # noqa: E402
    ProgressSummary,
    _grade_label,
    get_progress_summary,
    render_summary_lines,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ----------------------------------------------------------------------------
# ProgressSummary
# ----------------------------------------------------------------------------


def test_progress_summary_frozen() -> None:
    s = ProgressSummary(
        has_save=True,
        character_name="K — Novice",
        character_id="novice",
        grade=3,
        grade_label="3-up",
        missions_completed=10,
        missions_total=30,
        data_recovered=100,
        data_total=500,
        last_mission_id="first_jack",
        last_zone="Sense/Net",
        credits=234,
        playtime_minutes=42,
    )
    with pytest.raises((AttributeError, Exception)):
        s.grade = 99  # type: ignore[misc]


def test_progress_summary_required_fields() -> None:
    s = ProgressSummary(
        has_save=True,
        character_name="",
        character_id="novice",
        grade=1,
        grade_label="1-up",
        missions_completed=0,
        missions_total=30,
        data_recovered=0,
        data_total=500,
        last_mission_id="",
        last_zone="",
        credits=0,
        playtime_minutes=0,
    )
    assert s.has_save is True
    assert s.grade == 1


# ----------------------------------------------------------------------------
# _grade_label
# ----------------------------------------------------------------------------


def test_grade_label_zero() -> None:
    assert _grade_label(0) == "-"


def test_grade_label_one() -> None:
    assert _grade_label(1) == "1-up"


def test_grade_label_five() -> None:
    assert _grade_label(5) == "5-up"


# ----------------------------------------------------------------------------
# get_progress_summary
# ----------------------------------------------------------------------------


def test_get_progress_summary_no_save(tmp_path: Path) -> None:
    """No save file → empty summary."""
    summary = get_progress_summary(save_dir=tmp_path)
    assert summary.has_save is False
    assert summary.grade == 0
    assert summary.missions_completed == 0


def test_get_progress_summary_with_save(tmp_path: Path) -> None:
    """A save with metadata → populated summary."""
    from types import SimpleNamespace

    saved_run = SimpleNamespace(
        version="1.0",
        saved_at="2026-06-20T10:00:00Z",
        elapsed_seconds=89 * 60,
        run_state={
            "mission_id": "watchdog_patrol",
            "current_stage": "Tessier-Ashpool",
            "completed_stages": [
                "s1",
                "s2",
                "s3",
                "s4",
                "s5",
                "s6",
                "s7",
                "s8",
                "s9",
                "s10",
                "s11",
                "s12",
            ],
        },
        mission=None,
        app_state={"character_id": "veteran"},
        metadata={"player_grade": 3, "credits": 567, "data_recovered": 234},
    )
    meta = SimpleNamespace(
        slot=1,
        exists=True,
        version="1.0",
        saved_at="2026-06-20T10:00:00Z",
        elapsed_seconds=89 * 60,
        mission_id="watchdog_patrol",
        current_stage="Tessier-Ashpool",
        player_grade=3,
        credits=567,
        size_bytes=1024,
        is_compatible=True,
    )

    class FakeSM:
        def list_slots(self):
            return [meta]

        def load(self, slot):
            return saved_run

    summary = get_progress_summary(save_manager=FakeSM(), save_dir=tmp_path)
    assert summary.has_save is True
    assert summary.character_id == "veteran"
    assert summary.character_name == "Sil — Veteran"
    assert summary.grade == 3
    assert summary.grade_label == "3-up"
    assert summary.missions_completed == 12  # length of completed_stages
    assert summary.data_recovered == 234
    assert summary.last_mission_id == "watchdog_patrol"
    assert summary.last_zone == "Tessier-Ashpool"
    assert summary.credits == 567
    assert summary.playtime_minutes == 89


def test_get_progress_summary_empty_save(tmp_path: Path) -> None:
    """Save with only minimal fields."""
    from types import SimpleNamespace

    saved_run = SimpleNamespace(
        version="1.0",
        saved_at="",
        elapsed_seconds=0,
        run_state={},
        mission=None,
        app_state={"character_id": "novice"},
        metadata={},
    )
    meta = SimpleNamespace(
        slot=1,
        exists=True,
        version="1.0",
        saved_at="",
        elapsed_seconds=0,
        mission_id=None,
        current_stage=None,
        player_grade=0,
        credits=0,
        size_bytes=0,
        is_compatible=True,
    )

    class FakeSM:
        def list_slots(self):
            return [meta]

        def load(self, slot):
            return saved_run

    summary = get_progress_summary(save_manager=FakeSM(), save_dir=tmp_path)
    assert summary.has_save is True
    assert summary.character_id == "novice"
    assert summary.grade == 0
    assert summary.missions_completed == 0


def test_get_progress_summary_unknown_character(tmp_path: Path) -> None:
    """Unknown character_id → empty character name."""
    from types import SimpleNamespace

    saved_run = SimpleNamespace(
        version="1.0",
        saved_at="2026-06-20",
        elapsed_seconds=0,
        run_state={},
        mission=None,
        app_state={"character_id": "alien"},
        metadata={"player_grade": 1},
    )
    meta = SimpleNamespace(
        slot=1,
        exists=True,
        version="1.0",
        saved_at="2026-06-20",
        elapsed_seconds=0,
        mission_id=None,
        current_stage=None,
        player_grade=1,
        credits=0,
        size_bytes=0,
        is_compatible=True,
    )

    class FakeSM:
        def list_slots(self):
            return [meta]

        def load(self, slot):
            return saved_run

    summary = get_progress_summary(save_manager=FakeSM(), save_dir=tmp_path)
    assert summary.character_id == "alien"
    assert summary.character_name == ""


def test_get_progress_summary_metadata_fallback(tmp_path: Path) -> None:
    """If load fails, use metadata only."""
    from types import SimpleNamespace

    meta = SimpleNamespace(
        slot=1,
        exists=True,
        version="1.0",
        saved_at="2026-06-20",
        elapsed_seconds=120,
        mission_id="first_jack",
        current_stage="HUB",
        player_grade=2,
        credits=100,
        size_bytes=512,
        is_compatible=True,
    )

    class FakeSM:
        def list_slots(self):
            return [meta]

        def load(self, slot):
            raise RuntimeError("corrupted")

    summary = get_progress_summary(save_manager=FakeSM(), save_dir=tmp_path)
    assert summary.has_save is True
    assert summary.grade == 2
    assert summary.last_mission_id == "first_jack"
    assert summary.last_zone == "HUB"
    assert summary.credits == 100
    assert summary.playtime_minutes == 2  # 120s / 60


def test_get_progress_summary_no_slots(tmp_path: Path) -> None:
    """No slots at all → empty summary."""

    class FakeSM:
        def list_slots(self):
            return []

    summary = get_progress_summary(save_manager=FakeSM(), save_dir=tmp_path)
    assert summary.has_save is False


# ----------------------------------------------------------------------------
# render_summary_lines
# ----------------------------------------------------------------------------


def test_render_summary_no_save_ko() -> None:
    summary = ProgressSummary(
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
    lines = render_summary_lines(summary, t_lang="ko")
    text = "\n".join(lines)
    assert "세이브" in text or "없습니다" in text


def test_render_summary_no_save_en() -> None:
    summary = ProgressSummary(
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
    lines = render_summary_lines(summary, t_lang="en")
    text = "\n".join(lines)
    assert "No save" in text


def test_render_summary_with_save_ko() -> None:
    summary = ProgressSummary(
        has_save=True,
        character_name="실 (Sil) — Veteran",
        character_id="veteran",
        grade=3,
        grade_label="3-up",
        missions_completed=12,
        missions_total=30,
        data_recovered=234,
        data_total=500,
        last_mission_id="watchdog_patrol",
        last_zone="Tessier-Ashpool",
        credits=567,
        playtime_minutes=89,
    )
    lines = render_summary_lines(summary, t_lang="ko")
    text = "\n".join(lines)
    assert "자키" in text
    assert "등급" in text
    assert "3-up" in text
    assert "12" in text
    assert "30" in text
    assert "234" in text


def test_render_summary_with_save_en() -> None:
    summary = ProgressSummary(
        has_save=True,
        character_name="Sil — Veteran",
        character_id="veteran",
        grade=3,
        grade_label="3-up",
        missions_completed=12,
        missions_total=30,
        data_recovered=234,
        data_total=500,
        last_mission_id="watchdog_patrol",
        last_zone="Tessier-Ashpool",
        credits=567,
        playtime_minutes=89,
    )
    lines = render_summary_lines(summary, t_lang="en")
    text = "\n".join(lines)
    assert "Jockey" in text
    assert "Grade" in text
    assert "Missions" in text


def test_render_summary_zero_missions() -> None:
    """Edge case: 0/30 = 0%."""
    summary = ProgressSummary(
        has_save=True,
        character_name="K — Novice",
        character_id="novice",
        grade=1,
        grade_label="1-up",
        missions_completed=0,
        missions_total=30,
        data_recovered=0,
        data_total=500,
        last_mission_id="",
        last_zone="",
        credits=0,
        playtime_minutes=0,
    )
    lines = render_summary_lines(summary, t_lang="ko")
    text = "\n".join(lines)
    assert "0 / 30" in text
    assert "0%" in text
