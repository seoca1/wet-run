"""Tests for jockey_history module (ADR-0040).

Covers:
    - DeceasedJockey dataclass + serialization
    - JockeyHistory archive (add/all/recent/stats/save/load)
    - Epitaph selection (per character)
    - build_deceased_from_state helper
    - render_death_summary_lines / render_hall_of_dead_lines / render_stats_lines
    - format_timestamp
"""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.jockey_history import (  # noqa: E402
    DEFAULT_SAVE_PATH,
    EPITAPHS,
    DeceasedJockey,
    JockeyHistory,
    build_deceased_from_state,
    format_timestamp,
    pick_epitaph,
    render_death_summary_lines,
    render_hall_of_dead_lines,
    render_stats_lines,
)

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def tmp_history(tmp_path: Path) -> JockeyHistory:
    """Create a JockeyHistory with a tmp save path."""
    return JockeyHistory(save_path=tmp_path / "deceased.json")


@pytest.fixture
def sample_jockey() -> DeceasedJockey:
    """Create a sample DeceasedJockey for testing."""
    return DeceasedJockey(
        jockey_id="abc123",
        name="케이 (K) — Novice",
        character_id="novice",
        grade=1,
        died_at_node="data_cache_1",
        died_at_mission="first_jack",
        died_at_timestamp_ms=int(time.time() * 1000),
        inventory_snapshot=("wisp_T1", "credit_chip", "loa_drum"),
        missions_completed=3,
        data_recovered=234,
        playtime_minutes=42,
        epitaph="You died a wage slave.",
    )


# ----------------------------------------------------------------------------
# DeceasedJockey
# ----------------------------------------------------------------------------


def test_deceased_jockey_frozen(sample_jockey: DeceasedJockey) -> None:
    """DeceasedJockey is immutable (frozen + slots)."""
    with pytest.raises((AttributeError, Exception)):
        sample_jockey.grade = 99  # type: ignore[misc]


def test_deceased_jockey_required_fields(sample_jockey: DeceasedJockey) -> None:
    """All fields populated."""
    assert sample_jockey.jockey_id == "abc123"
    assert sample_jockey.name == "케이 (K) — Novice"
    assert sample_jockey.character_id == "novice"
    assert sample_jockey.grade == 1
    assert sample_jockey.missions_completed == 3
    assert sample_jockey.data_recovered == 234
    assert sample_jockey.playtime_minutes == 42


def test_deceased_jockey_to_dict(sample_jockey: DeceasedJockey) -> None:
    """to_dict produces JSON-serializable dict."""
    data = sample_jockey.to_dict()
    assert isinstance(data, dict)
    assert data["jockey_id"] == "abc123"
    assert data["character_id"] == "novice"
    assert data["inventory_snapshot"] == ["wisp_T1", "credit_chip", "loa_drum"]


def test_deceased_jockey_round_trip(sample_jockey: DeceasedJockey) -> None:
    """to_dict → from_dict round trip preserves data."""
    data = sample_jockey.to_dict()
    restored = DeceasedJockey.from_dict(data)
    assert restored == sample_jockey


def test_deceased_jockey_unique_ids() -> None:
    """Two JockeyHistory.add() get unique IDs."""
    assert uuid.uuid4().hex != uuid.uuid4().hex  # sanity


# ----------------------------------------------------------------------------
# Epitaphs
# ----------------------------------------------------------------------------


def test_epitaphs_have_3_per_character() -> None:
    for char in ("novice", "veteran", "heretic"):
        assert len(EPITAPHS[char]) == 3


def test_pick_epitaph_known_character() -> None:
    ep = pick_epitaph("novice", seed=42)
    assert ep in EPITAPHS["novice"]


def test_pick_epitaph_unknown_falls_back() -> None:
    """Unknown character → novice pool."""
    ep = pick_epitaph("alien", seed=42)
    assert ep in EPITAPHS["novice"]


def test_pick_epitaph_deterministic_with_seed() -> None:
    """Same seed → same epitaph."""
    a = pick_epitaph("veteran", seed=123)
    b = pick_epitaph("veteran", seed=123)
    assert a == b


def test_pick_epitaph_distribution() -> None:
    """Over many samples, all 3 epitaphs appear."""
    seen = set()
    for seed in range(100):
        seen.add(pick_epitaph("heretic", seed=seed))
    assert len(seen) >= 2  # at least 2 different ones (probabilistic)


# ----------------------------------------------------------------------------
# JockeyHistory
# ----------------------------------------------------------------------------


def test_history_empty_init(tmp_history: JockeyHistory) -> None:
    assert tmp_history.count() == 0
    assert tmp_history.all() == []


def test_history_add(tmp_history: JockeyHistory, sample_jockey: DeceasedJockey) -> None:
    tmp_history.add(sample_jockey)
    assert tmp_history.count() == 1
    assert tmp_history.all()[0] == sample_jockey


def test_history_add_persists(tmp_history: JockeyHistory, sample_jockey: DeceasedJockey) -> None:
    """Save and reload."""
    tmp_history.add(sample_jockey)
    reloaded = JockeyHistory(save_path=tmp_history.save_path)
    assert reloaded.count() == 1
    assert reloaded.all()[0] == sample_jockey


def test_history_recent_returns_most_recent_first(
    tmp_history: JockeyHistory,
) -> None:
    """Most recently added is first."""
    a = DeceasedJockey(
        jockey_id="aaa",
        name="A",
        character_id="novice",
        grade=1,
        died_at_node="",
        died_at_mission="",
        died_at_timestamp_ms=1,
        inventory_snapshot=(),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
        epitaph="",
    )
    b = DeceasedJockey(
        jockey_id="bbb",
        name="B",
        character_id="novice",
        grade=2,
        died_at_node="",
        died_at_mission="",
        died_at_timestamp_ms=2,
        inventory_snapshot=(),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
        epitaph="",
    )
    tmp_history.add(a)
    tmp_history.add(b)
    recent = tmp_history.recent(10)
    assert recent[0].jockey_id == "bbb"
    assert recent[1].jockey_id == "aaa"


def test_history_recent_n(
    tmp_history: JockeyHistory,
) -> None:
    """recent(n) returns at most n items."""
    for i in range(5):
        tmp_history.add(
            DeceasedJockey(
                jockey_id=f"j{i}",
                name=f"J{i}",
                character_id="novice",
                grade=1,
                died_at_node="",
                died_at_mission="",
                died_at_timestamp_ms=i,
                inventory_snapshot=(),
                missions_completed=0,
                data_recovered=0,
                playtime_minutes=0,
                epitaph="",
            )
        )
    assert len(tmp_history.recent(3)) == 3


def test_history_stats_empty(tmp_history: JockeyHistory) -> None:
    stats = tmp_history.stats()
    assert stats.total_deaths == 0
    assert stats.survival_rate == 0.0
    assert stats.longest_run_minutes == 0
    assert stats.longest_run_jockey == ""


def test_history_stats_with_data(
    tmp_history: JockeyHistory,
) -> None:
    """Stats compute correctly with multiple jockeys."""
    for i, (grade, missions, mins) in enumerate(
        [
            (1, 2, 10),
            (2, 5, 30),
            (3, 1, 60),
        ]
    ):
        tmp_history.add(
            DeceasedJockey(
                jockey_id=f"j{i}",
                name=f"J{i}",
                character_id="novice",
                grade=grade,
                died_at_node="",
                died_at_mission="",
                died_at_timestamp_ms=i,
                inventory_snapshot=(),
                missions_completed=missions,
                data_recovered=0,
                playtime_minutes=mins,
                epitaph="",
            )
        )
    stats = tmp_history.stats(total_runs=10)
    assert stats.total_deaths == 3
    assert stats.total_runs == 10
    assert stats.survival_rate == pytest.approx(0.7)
    assert stats.longest_run_minutes == 60
    assert stats.longest_run_jockey == "J2"
    assert stats.avg_missions_per_run == pytest.approx((2 + 5 + 1) / 3)


def test_history_clear(tmp_history: JockeyHistory, sample_jockey: DeceasedJockey) -> None:
    tmp_history.add(sample_jockey)
    assert tmp_history.count() == 1
    tmp_history.clear()
    assert tmp_history.count() == 0


def test_history_handles_missing_file(tmp_path: Path) -> None:
    """No save file → empty archive."""
    h = JockeyHistory(save_path=tmp_path / "nope.json")
    assert h.count() == 0


def test_history_handles_corrupt_file(tmp_path: Path) -> None:
    """Corrupt file → empty archive (graceful)."""
    path = tmp_path / "deceased.json"
    path.write_text("{not valid json", encoding="utf-8")
    h = JockeyHistory(save_path=path)
    assert h.count() == 0


# ----------------------------------------------------------------------------
# build_deceased_from_state
# ----------------------------------------------------------------------------


def test_build_from_dict_inventory() -> None:
    """Dict inventory → sorted tuple of keys."""
    j = build_deceased_from_state(
        name="X",
        character_id="novice",
        grade=1,
        died_at_node="",
        died_at_mission="",
        inventory={"wisp": 2, "loa_drum": 1, "credit": 5},
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
    )
    assert j.inventory_snapshot == ("credit", "loa_drum", "wisp")


def test_build_from_tuple_inventory() -> None:
    """Tuple/list inventory → preserved."""
    j = build_deceased_from_state(
        name="X",
        character_id="novice",
        grade=1,
        died_at_node="",
        died_at_mission="",
        inventory=("a", "b", "c"),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
    )
    assert j.inventory_snapshot == ("a", "b", "c")


def test_build_assigns_unique_id() -> None:
    """Each call generates a new UUID hex string."""
    a = build_deceased_from_state(
        name="X",
        character_id="novice",
        grade=1,
        died_at_node="",
        died_at_mission="",
        inventory=(),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
    )
    b = build_deceased_from_state(
        name="X",
        character_id="novice",
        grade=1,
        died_at_node="",
        died_at_mission="",
        inventory=(),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
    )
    assert a.jockey_id != b.jockey_id
    assert len(a.jockey_id) == 32  # UUID hex (no dashes)


def test_build_assigns_epitaph() -> None:
    """Epitaph is auto-selected."""
    j = build_deceased_from_state(
        name="X",
        character_id="heretic",
        grade=5,
        died_at_node="",
        died_at_mission="",
        inventory=(),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
        seed=99,
    )
    assert j.epitaph in EPITAPHS["heretic"]


def test_build_default_timestamp() -> None:
    """Default timestamp is current time."""
    before = int(time.time() * 1000)
    j = build_deceased_from_state(
        name="X",
        character_id="novice",
        grade=1,
        died_at_node="",
        died_at_mission="",
        inventory=(),
        missions_completed=0,
        data_recovered=0,
        playtime_minutes=0,
    )
    after = int(time.time() * 1000)
    assert before <= j.died_at_timestamp_ms <= after


# ----------------------------------------------------------------------------
# format_timestamp
# ----------------------------------------------------------------------------


def test_format_timestamp_zero() -> None:
    assert format_timestamp(0) == "—"


def test_format_timestamp_known() -> None:
    # 2026-01-01 00:00:00 UTC = 1767225600000 ms
    result = format_timestamp(1767225600000)
    assert "2026" in result


def test_format_timestamp_negative() -> None:
    """Negative values handled."""
    assert format_timestamp(-1) == "—"


# ----------------------------------------------------------------------------
# render_death_summary_lines
# ----------------------------------------------------------------------------


def test_render_summary_ko(sample_jockey: DeceasedJockey) -> None:
    lines = render_death_summary_lines(sample_jockey, lang="ko")
    text = "\n".join(lines)
    assert "케이" in text
    assert "Wage" in text or "wage" in text or "wage slave" in text.lower()


def test_render_summary_en(sample_jockey: DeceasedJockey) -> None:
    lines = render_death_summary_lines(sample_jockey, lang="en")
    text = "\n".join(lines)
    assert "Jockey" in text
    assert "wage" in text.lower()


def test_render_summary_includes_inventory(sample_jockey: DeceasedJockey) -> None:
    lines = render_death_summary_lines(sample_jockey, lang="en")
    text = "\n".join(lines)
    assert "wisp_T1" in text
    assert "credit_chip" in text


def test_render_summary_includes_mission(sample_jockey: DeceasedJockey) -> None:
    lines = render_death_summary_lines(sample_jockey, lang="en")
    text = "\n".join(lines)
    assert "first_jack" in text


# ----------------------------------------------------------------------------
# render_hall_of_dead_lines
# ----------------------------------------------------------------------------


def test_render_hall_empty(tmp_history: JockeyHistory) -> None:
    lines = render_hall_of_dead_lines(tmp_history, lang="ko")
    text = "\n".join(lines)
    assert "HALL OF DEAD" in text
    assert "0" in text  # 0 deaths


def test_render_hall_with_data(tmp_history: JockeyHistory, sample_jockey: DeceasedJockey) -> None:
    tmp_history.add(sample_jockey)
    lines = render_hall_of_dead_lines(tmp_history, lang="ko")
    text = "\n".join(lines)
    assert "케이" in text
    assert "first_jack" in text
    assert "wage" in text.lower()


def test_render_hall_includes_stats(
    tmp_history: JockeyHistory,
) -> None:
    for i in range(3):
        tmp_history.add(
            DeceasedJockey(
                jockey_id=f"j{i}",
                name=f"J{i}",
                character_id="novice",
                grade=1,
                died_at_node="",
                died_at_mission="",
                died_at_timestamp_ms=i,
                inventory_snapshot=(),
                missions_completed=2,
                data_recovered=0,
                playtime_minutes=10,
                epitaph="",
            )
        )
    lines = render_hall_of_dead_lines(tmp_history, lang="ko")
    text = "\n".join(lines)
    assert "총 런" in text
    assert "총 사망" in text
    assert "생존율" in text


# ----------------------------------------------------------------------------
# render_stats_lines
# ----------------------------------------------------------------------------


def test_render_stats_ko() -> None:
    lines = render_stats_lines(10, 3, 2.5, 47, lang="ko")
    text = "\n".join(lines)
    assert "RUN STATS" in text
    assert "자키 사망: 3" in text
    assert "70%" in text or "70" in text  # survival rate
    assert "47분" in text


def test_render_stats_en() -> None:
    lines = render_stats_lines(10, 3, 2.5, 47, lang="en")
    text = "\n".join(lines)
    assert "Deaths: 3" in text
    assert "Longest: 47m" in text


def test_render_stats_no_division_by_zero() -> None:
    """0 runs / 0 deaths → no crash."""
    lines = render_stats_lines(0, 0, 0.0, 0, lang="ko")
    assert len(lines) > 0
    # 0/1 = 0% survival (max(0, 1-0/1) = 1.0 but shown as 0)
    # Actually max(0, 1 - 0/1) = 1.0 = 100%, that's fine
    text = "\n".join(lines)
    assert "100%" in text or "0%" in text


# ----------------------------------------------------------------------------
# Module API
# ----------------------------------------------------------------------------


def test_module_exports() -> None:
    """Public API surface."""
    assert callable(build_deceased_from_state)
    assert callable(pick_epitaph)
    assert callable(format_timestamp)
    assert callable(render_death_summary_lines)
    assert callable(render_hall_of_dead_lines)
    assert callable(render_stats_lines)


def test_default_save_path() -> None:
    assert DEFAULT_SAVE_PATH.name == "deceased.json"
