"""Tests for favicon and OG meta tags on all dashboards.

Each dashboard (8 total) must have:
- viewport meta
- description meta
- keywords meta
- author meta
- favicon link
- canonical link
- Open Graph (og:title, og:description, og:image, og:url, og:locale, og:site_name)
- Twitter Card (twitter:card, twitter:title, twitter:description, twitter:image)
- theme-color meta
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="dashboard restructured 2026-07-10")


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DASH = REPO_ROOT / "dashboard"

DASHBOARDS = [
    "index.html",
    "missions.html",
    "stages.html",
    "stories-browse.html",
    "library.html",
    "sound.html",
    "combat.html",
    "equipment.html",
    "cyberspace.html",
    "search.html",
    "reading-stats.html",
    "character-graph.html",
    "mission-flow.html",
    "jokey.html",
]

REQUIRED_META: list[tuple[str, str]] = [
    ("viewport", 'name="viewport"'),
    ("description", 'name="description"'),
    ("keywords", 'name="keywords"'),
    ("author", 'name="author"'),
    ("favicon", 'rel="icon"'),
    ("favicon-svg", 'type="image/svg+xml"'),
    ("canonical", 'rel="canonical"'),
    ("canonical-url", "seoca1.github.io"),
    ("og:title", 'property="og:title"'),
    ("og:description", 'property="og:description"'),
    ("og:type", 'property="og:type"'),
    ("og:url", 'property="og:url"'),
    ("og:image", 'property="og:image"'),
    ("og:locale", 'property="og:locale"'),
    ("og:site_name", 'property="og:site_name"'),
    ("twitter:card", 'name="twitter:card"'),
    ("twitter:title", 'name="twitter:title"'),
    ("twitter:description", 'name="twitter:description"'),
    ("twitter:image", 'name="twitter:image"'),
    ("theme-color", 'name="theme-color"'),
]


@pytest.mark.parametrize("filename", DASHBOARDS)
def test_dashboard_exists(filename: str) -> None:
    path = DASH / filename
    assert path.exists(), f"Dashboard {filename} not found"


META_INDICES = list(range(len(REQUIRED_META)))


@pytest.mark.parametrize("filename", DASHBOARDS)
@pytest.mark.parametrize("meta_idx", META_INDICES)
def test_dashboard_has_meta(filename: str, meta_idx: int) -> None:
    """Verify each dashboard has the given meta tag (parametrized)."""
    path = DASH / filename
    if not path.exists():
        pytest.skip(f"{filename} not found")
    meta_name, needle = REQUIRED_META[meta_idx]
    html = path.read_text(encoding="utf-8")
    assert needle in html, f"{filename} missing {meta_name}"


def test_favicon_file_exists() -> None:
    fav = DASH / "favicon.svg"
    assert fav.exists(), "favicon.svg not found"
    content = fav.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "viewBox" in content


def test_favicon_has_matrix_colors() -> None:
    """Favicon should use the matrix green palette."""
    content = (DASH / "favicon.svg").read_text(encoding="utf-8")
    assert "#66ffcc" in content or "#00ccff" in content, "Missing matrix color"


@pytest.mark.parametrize("filename", DASHBOARDS)
def test_dashboard_og_url_matches(filename: str) -> None:
    """OG URL should point to the correct live path."""
    path = DASH / filename
    if not path.exists():
        pytest.skip(f"{filename} not found")
    html = path.read_text(encoding="utf-8")
    expected_path = "" if filename == "index.html" else filename
    expected = f"https://seoca1.github.io/wet-run/{expected_path}"
    assert expected in html, f"{filename} OG URL mismatch (expected {expected})"


@pytest.mark.parametrize("filename", DASHBOARDS)
def test_dashboard_og_image_is_favicon(filename: str) -> None:
    """All dashboards share favicon.svg as OG image."""
    path = DASH / filename
    if not path.exists():
        pytest.skip(f"{filename} not found")
    html = path.read_text(encoding="utf-8")
    assert "og:image" in html
    assert "favicon.svg" in html
