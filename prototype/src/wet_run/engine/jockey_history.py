"""Jockey history (Hall of Dead Jockeys) — ADR-0040.

Manages the archive of deceased jockeys. Each jockey that flatlines
gets added to the archive with their final stats, inventory, and
a Sprawl-style epitaph.

Data flow:
    1. Player flatlines → trigger_death()
    2. DEATH_SUMMARY screen shows the new entry
    3. Player can view the Hall of Dead Jockeys from MENU
    4. All data is persisted to data/jockeys/deceased.json

Module structure:
    - DeceasedJockey: immutable record of one jockey's death
    - JockeyStats: aggregated statistics across all runs
    - EPITAPHS: per-character epitaph pools (Sprawl's last words)
    - JockeyHistory: archive manager (add/all/recent/stats/save/load)
    - render_hall_of_dead_lines: format jockey for display
    - render_summary_lines: format summary for death screen
"""

from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ============================================================================
# Epitaphs (Sprawl's final words) — ADR-0040
# ============================================================================


EPITAPHS: dict[str, tuple[str, ...]] = {
    "novice": (
        "You died a wage slave.",
        "Sprawl is short on memory.",
        "Cash for the next, then.",
    ),
    "veteran": (
        "Old scores die hard.",
        "Mara's not waiting.",
        "T-A doesn't forget.",
    ),
    "heretic": (
        "The wheel keeps turning.",
        "Loa hears you still.",
        "One spoke, not the wheel.",
    ),
}


def pick_epitaph(character_id: str, seed: int | None = None) -> str:
    """Pick a random epitaph for the given character.

    Args:
        character_id: "novice" | "veteran" | "heretic"
        seed: Optional random seed for reproducibility.

    Returns:
        One of the character-specific epitaphs.
    """
    pool = EPITAPHS.get(character_id, EPITAPHS["novice"])
    rng = random.Random(seed)
    return rng.choice(pool)


# ============================================================================
# DeceasedJockey record
# ============================================================================


@dataclass(frozen=True, slots=True)
class DeceasedJockey:
    """A record of a jockey who flatlined (ADR-0040).

    Immutable — once added to the archive, never modified.

    Attributes:
        jockey_id: Unique ID (UUID hex string).
        name: Display name (e.g. "케이 (K) — Novice").
        character_id: "novice" | "veteran" | "heretic".
        grade: Final grade at death.
        died_at_node: Matrix node id where they died.
        died_at_mission: Mission id at time of death.
        died_at_timestamp_ms: Epoch ms when they died.
        inventory_snapshot: Tuple of inventory item ids at death.
        missions_completed: Missions completed in this run.
        data_recovered: Total data extracted this run.
        playtime_minutes: Run playtime in minutes.
        epitaph: Sprawl's final words for this jockey.
    """

    jockey_id: str
    name: str
    character_id: str
    grade: int
    died_at_node: str
    died_at_mission: str
    died_at_timestamp_ms: int
    inventory_snapshot: tuple[str, ...]
    missions_completed: int
    data_recovered: int
    playtime_minutes: int
    epitaph: str

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-compatible dict."""
        return {
            "jockey_id": self.jockey_id,
            "name": self.name,
            "character_id": self.character_id,
            "grade": self.grade,
            "died_at_node": self.died_at_node,
            "died_at_mission": self.died_at_mission,
            "died_at_timestamp_ms": self.died_at_timestamp_ms,
            "inventory_snapshot": list(self.inventory_snapshot),
            "missions_completed": self.missions_completed,
            "data_recovered": self.data_recovered,
            "playtime_minutes": self.playtime_minutes,
            "epitaph": self.epitaph,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DeceasedJockey:
        """Deserialize from JSON dict."""
        raw_inv = data.get("inventory_snapshot", [])
        inv_list: list[str] = []
        if isinstance(raw_inv, list):
            inv_list = [str(x) for x in raw_inv]
        return cls(
            jockey_id=str(data.get("jockey_id", uuid.uuid4().hex)),
            name=str(data.get("name", "Unknown")),
            character_id=str(data.get("character_id", "novice")),
            grade=int(str(data.get("grade", 1))),
            died_at_node=str(data.get("died_at_node", "")),
            died_at_mission=str(data.get("died_at_mission", "")),
            died_at_timestamp_ms=int(str(data.get("died_at_timestamp_ms", 0))),
            inventory_snapshot=tuple(inv_list),
            missions_completed=int(str(data.get("missions_completed", 0))),
            data_recovered=int(str(data.get("data_recovered", 0))),
            playtime_minutes=int(str(data.get("playtime_minutes", 0))),
            epitaph=str(data.get("epitaph", "")),
        )


# ============================================================================
# JockeyStats (aggregated)
# ============================================================================


@dataclass(frozen=True, slots=True)
class JockeyStats:
    """Aggregated statistics across all runs.

    Attributes:
        total_runs: Total runs (deaths + successes).
        total_deaths: Total flatlines.
        survival_rate: Deaths / runs (0.0 to 1.0).
        avg_missions_per_run: Average missions completed per run.
        longest_run_minutes: Longest single run in minutes.
        longest_run_jockey: Name of jockey with longest run.
    """

    total_runs: int
    total_deaths: int
    survival_rate: float
    avg_missions_per_run: float
    longest_run_minutes: int
    longest_run_jockey: str


# ============================================================================
# JockeyHistory (archive manager)
# ============================================================================


DEFAULT_SAVE_PATH = Path("data/jockeys/deceased.json")


class JockeyHistory:
    """Manages the Hall of Dead Jockeys archive (ADR-0040).

    Loads from / saves to a JSON file. In-memory list of DeceasedJockey
    records, ordered by death time (most recent first).
    """

    def __init__(self, save_path: Path | None = None) -> None:
        """Initialize the archive.

        Args:
            save_path: Path to the deceased.json file. Defaults to
                data/jockeys/deceased.json.
        """
        self.save_path = save_path or DEFAULT_SAVE_PATH
        self._archive: list[DeceasedJockey] = []
        self._load()

    def _load(self) -> None:
        """Load archive from disk if file exists."""
        if not self.save_path.exists():
            self._archive = []
            return
        try:
            raw = json.loads(self.save_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                self._archive = [DeceasedJockey.from_dict(d) for d in raw]
            else:
                self._archive = []
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
            self._archive = []

    def save(self) -> None:
        """Persist archive to disk."""
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        data = [j.to_dict() for j in self._archive]
        self.save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, jockey: DeceasedJockey) -> None:
        """Add a deceased jockey to the archive.

        Args:
            jockey: The deceased jockey to add.
        """
        # Insert at front (most recent first)
        self._archive.insert(0, jockey)
        self.save()

    def all(self) -> list[DeceasedJockey]:
        """Return all archived jockeys (most recent first)."""
        return list(self._archive)

    def recent(self, n: int = 10) -> list[DeceasedJockey]:
        """Return the N most recent deceased jockeys."""
        return self._archive[:n]

    def count(self) -> int:
        """Return total count of deceased jockeys."""
        return len(self._archive)

    def stats(self, total_runs: int = 0) -> JockeyStats:
        """Compute aggregate statistics.

        Args:
            total_runs: Optional override for total runs (from AppState).

        Returns:
            JockeyStats with aggregated metrics.
        """
        total = total_runs if total_runs > 0 else self.count()
        deaths = self.count()
        if total <= 0:
            survival = 0.0
        else:
            survival = max(0.0, 1.0 - (deaths / total))

        if deaths > 0:
            total_missions = sum(j.missions_completed for j in self._archive)
            avg = total_missions / deaths
            longest = max(self._archive, key=lambda j: j.playtime_minutes)
            longest_min = longest.playtime_minutes
            longest_name = longest.name
        else:
            avg = 0.0
            longest_min = 0
            longest_name = ""

        return JockeyStats(
            total_runs=total,
            total_deaths=deaths,
            survival_rate=survival,
            avg_missions_per_run=avg,
            longest_run_minutes=longest_min,
            longest_run_jockey=longest_name,
        )

    def clear(self) -> None:
        """Clear the archive (for tests)."""
        self._archive = []


# ============================================================================
# Builder helper
# ============================================================================


def build_deceased_from_state(
    name: str,
    character_id: str,
    grade: int,
    died_at_node: str,
    died_at_mission: str,
    inventory: dict[str, int] | tuple[str, ...] | list[str],
    missions_completed: int,
    data_recovered: int,
    playtime_minutes: int,
    *,
    timestamp_ms: int | None = None,
    seed: int | None = None,
) -> DeceasedJockey:
    """Build a DeceasedJockey from current run state (ADR-0040).

    Args:
        name: Display name.
        character_id: Character id.
        grade: Current grade.
        died_at_node: Where they died.
        died_at_mission: Which mission.
        inventory: Current inventory (dict or tuple).
        missions_completed: Total missions this run.
        data_recovered: Total data this run.
        playtime_minutes: Play time this run.
        timestamp_ms: Optional timestamp (defaults to now).
        seed: Optional seed for epitaph selection.

    Returns:
        A new DeceasedJockey record.
    """
    if isinstance(inventory, dict):
        inv_snapshot: tuple[str, ...] = tuple(sorted(inventory.keys()))
    else:
        inv_snapshot = tuple(inventory)

    return DeceasedJockey(
        jockey_id=uuid.uuid4().hex,
        name=name,
        character_id=character_id,
        grade=grade,
        died_at_node=died_at_node,
        died_at_mission=died_at_mission,
        died_at_timestamp_ms=timestamp_ms if timestamp_ms is not None else int(time.time() * 1000),
        inventory_snapshot=inv_snapshot,
        missions_completed=missions_completed,
        data_recovered=data_recovered,
        playtime_minutes=playtime_minutes,
        epitaph=pick_epitaph(character_id, seed=seed),
    )


# ============================================================================
# Rendering helpers
# ============================================================================


def format_timestamp(ms: int) -> str:
    """Format an epoch ms timestamp as a date string.

    Args:
        ms: Epoch milliseconds.

    Returns:
        ISO date (YYYY-MM-DD HH:MM) string.
    """
    if ms <= 0:
        return "—"
    try:
        t = time.gmtime(ms / 1000)
        return time.strftime("%Y-%m-%d %H:%M", t)
    except (OSError, OverflowError, ValueError):
        return "—"


def render_death_summary_lines(jockey: DeceasedJockey, lang: str = "ko") -> list[str]:
    """Render the death summary lines for the screen.

    Args:
        jockey: The deceased jockey.
        lang: "ko" or "en".

    Returns:
        List of formatted lines (one per row).
    """
    if lang == "ko":
        return [
            f"  자키: {jockey.name}",
            f"  등급: {jockey.grade}-up",
            f"  사망 위치: {jockey.died_at_node or 'unknown'}",
            f"  사망 의뢰: {jockey.died_at_mission or 'unknown'}",
            f"  런 #{(jockey.jockey_id or '')[:4]}",
            f"  시간: {format_timestamp(jockey.died_at_timestamp_ms)}",
            "",
            "  ═══ 런 통계 ═══",
            f"  미션 완료: {jockey.missions_completed}",
            f"  데이터 회수: {jockey.data_recovered}",
            f"  인벤토리: {len(jockey.inventory_snapshot)}개",
            f"  플레이 시간: {jockey.playtime_minutes}분",
            "",
            "  ═══ 죽을 때 들고 있던 것 ═══",
            *(f"  - {item}" for item in jockey.inventory_snapshot[:5]),
            "",
            "",
            f'      "{jockey.epitaph}"',
            "",
        ]
    return [
        f"  Jockey: {jockey.name}",
        f"  Grade: {jockey.grade}-up",
        f"  Died at: {jockey.died_at_node or 'unknown'}",
        f"  Mission: {jockey.died_at_mission or 'unknown'}",
        f"  Run #{(jockey.jockey_id or '')[:4]}",
        f"  Time: {format_timestamp(jockey.died_at_timestamp_ms)}",
        "",
        "  ═══ Run Stats ═══",
        f"  Missions: {jockey.missions_completed}",
        f"  Data: {jockey.data_recovered}",
        f"  Inventory: {len(jockey.inventory_snapshot)} items",
        f"  Playtime: {jockey.playtime_minutes}m",
        "",
        "  ═══ Inventory at Death ═══",
        *(f"  - {item}" for item in jockey.inventory_snapshot[:5]),
        "",
        "",
        f'      "{jockey.epitaph}"',
        "",
    ]


def render_hall_of_dead_lines(
    history: JockeyHistory,
    selected: int = 0,
    lang: str = "ko",
) -> list[str]:
    """Render the Hall of Dead Jockeys screen lines.

    Args:
        history: The JockeyHistory archive.
        selected: Index of selected jockey (0 = most recent).
        lang: "ko" or "en".

    Returns:
        List of formatted lines.
    """
    recent = history.recent(10)
    stats = history.stats()

    lines: list[str] = []
    if lang == "ko":
        lines.append("  HALL OF DEAD JOCKEYS")
        lines.append('  "The Sprawl remembers everyone."')
        lines.append("")
        lines.append(f"  당신이 살아남은 자키: {stats.total_deaths}")
        lines.append(
            f"  최장 런: {stats.longest_run_minutes}분 ({stats.longest_run_jockey or '—'})"
        )
        lines.append("")
        lines.append("  ─── 최근에 쓰러진 자키들 ───")
        lines.append("")
        if not recent:
            lines.append("  (아직 자키가 쓰러지지 않았습니다)")
        else:
            for i, j in enumerate(recent):
                marker = ">" if i == selected else " "
                timestamp = format_timestamp(j.died_at_timestamp_ms)
                lines.append(f"  {marker} {i + 1}. {j.name}, {j.grade}-up")
                lines.append(f"       {j.died_at_mission or '?'} · {timestamp}")
                lines.append(f'       "{j.epitaph}"')
                lines.append("")
        lines.append("  ─── 아카이브 통계 ───")
        lines.append(f"  총 런: {stats.total_runs}")
        lines.append(f"  총 사망: {stats.total_deaths}")
        lines.append(f"  생존율: {stats.survival_rate * 100:.0f}%")
        lines.append(f"  평균 미션/런: {stats.avg_missions_per_run:.1f}")
    else:
        lines.append("  HALL OF DEAD JOCKEYS")
        lines.append('  "The Sprawl remembers everyone."')
        lines.append("")
        lines.append(f"  Jockeys outlived: {stats.total_deaths}")
        lines.append(
            f"  Longest run: {stats.longest_run_minutes}m ({stats.longest_run_jockey or '—'})"
        )
        lines.append("")
        lines.append("  ─── Recently Fallen ───")
        lines.append("")
        if not recent:
            lines.append("  (No jockeys have flatlined yet)")
        else:
            for i, j in enumerate(recent):
                marker = ">" if i == selected else " "
                timestamp = format_timestamp(j.died_at_timestamp_ms)
                lines.append(f"  {marker} {i + 1}. {j.name}, {j.grade}-up")
                lines.append(f"       {j.died_at_mission or '?'} · {timestamp}")
                lines.append(f'       "{j.epitaph}"')
                lines.append("")
        lines.append("  ─── Archive Stats ───")
        lines.append(f"  Total runs: {stats.total_runs}")
        lines.append(f"  Total deaths: {stats.total_deaths}")
        lines.append(f"  Survival rate: {stats.survival_rate * 100:.0f}%")
        lines.append(f"  Avg missions/run: {stats.avg_missions_per_run:.1f}")
    return lines


def render_stats_lines(
    total_runs: int,
    total_deaths: int,
    avg_missions: float,
    longest_run: int,
    lang: str = "ko",
) -> list[str]:
    """Render compact RUN STATS lines for the MENU side panel.

    Args:
        total_runs: Total runs played.
        total_deaths: Total flatlines.
        avg_missions: Average missions per run.
        longest_run: Longest run in minutes.
        lang: "ko" or "en".

    Returns:
        List of formatted lines.
    """
    if lang == "ko":
        return [
            "RUN STATS",
            "─────────",
            f"자키 사망: {total_deaths}",
            f"총 런: {total_runs}",
            f"생존율: {(1 - total_deaths / max(total_runs, 1)) * 100:.0f}%",
            f"최장 런: {longest_run}분",
            f"평균 미션: {avg_missions:.1f}",
            "",
            "[6] Hall of Dead",
        ]
    return [
        "RUN STATS",
        "─────────",
        f"Deaths: {total_deaths}",
        f"Total runs: {total_runs}",
        f"Survival: {(1 - total_deaths / max(total_runs, 1)) * 100:.0f}%",
        f"Longest: {longest_run}m",
        f"Avg missions: {avg_missions:.1f}",
        "",
        "[6] Hall of Dead",
    ]


__all__ = [
    "DEFAULT_SAVE_PATH",
    "DeceasedJockey",
    "EPITAPHS",
    "JockeyHistory",
    "JockeyStats",
    "build_deceased_from_state",
    "format_timestamp",
    "pick_epitaph",
    "render_death_summary_lines",
    "render_hall_of_dead_lines",
    "render_stats_lines",
]
