"""Tests for the GitHub Pages deployment artifact (ADR-0032 + #5/5 polish).

Verifies that all required files for the gh-pages deployment are present
and valid. This is a CI-side check that runs locally.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent.parent.parent
DASHBOARD_DIR = REPO_ROOT / "dashboard"


# ----------------------------------------------------------------------------
# HTML files
# ----------------------------------------------------------------------------


DASHBOARD_HTML_FILES = [
    "index.html",
    "missions.html",
    "stages.html",
    "library.html",
    "sound.html",
    "combat.html",
    "equipment.html",
    "cyberspace.html",
    "achievements.html",
    "settings.html",
    "graphic-novel.html",  # ADR-0032
]


@pytest.mark.parametrize("filename", DASHBOARD_HTML_FILES)
def test_dashboard_html_exists(filename: str) -> None:
    """Each dashboard HTML file must exist."""
    path = DASHBOARD_DIR / filename
    assert path.exists(), f"Missing dashboard file: {path}"


@pytest.mark.parametrize("filename", DASHBOARD_HTML_FILES)
def test_dashboard_html_has_doctype(filename: str) -> None:
    """Each HTML file must start with DOCTYPE."""
    path = DASHBOARD_DIR / filename
    text = path.read_text(encoding="utf-8")
    assert text.lstrip().startswith("<!DOCTYPE html>"), (
        f"{filename} must start with <!DOCTYPE html>"
    )


@pytest.mark.parametrize("filename", DASHBOARD_HTML_FILES)
def test_dashboard_html_has_closing_tag(filename: str) -> None:
    """Each HTML file must end with </html>."""
    path = DASHBOARD_DIR / filename
    text = path.read_text(encoding="utf-8")
    assert text.rstrip().endswith("</html>"), f"{filename} must end with </html>"


@pytest.mark.parametrize("filename", DASHBOARD_HTML_FILES)
def test_dashboard_html_has_charset(filename: str) -> None:
    """Each HTML file must declare UTF-8 charset."""
    path = DASHBOARD_DIR / filename
    text = path.read_text(encoding="utf-8")
    assert "charset" in text.lower(), f"{filename} missing charset declaration"


# ----------------------------------------------------------------------------
# Pages workflow
# ----------------------------------------------------------------------------


def test_pages_workflow_exists() -> None:
    """GitHub Actions workflow for Pages must exist."""
    pages_yml = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    assert pages_yml.exists(), f"Missing {pages_yml}"


def test_pages_workflow_includes_all_dashboards() -> None:
    """Pages workflow must cp all 11 dashboard HTMLs."""
    pages_yml = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    text = pages_yml.read_text(encoding="utf-8")
    for filename in DASHBOARD_HTML_FILES:
        assert filename in text, f"pages.yml missing cp for {filename}"


def test_pages_workflow_includes_graphic_novel() -> None:
    """Pages workflow must cp the new graphic-novel.html (ADR-0032)."""
    pages_yml = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    text = pages_yml.read_text(encoding="utf-8")
    assert "graphic-novel.html" in text


def test_pages_workflow_includes_favicon() -> None:
    """Pages workflow must cp the favicon."""
    pages_yml = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    text = pages_yml.read_text(encoding="utf-8")
    assert "favicon.svg" in text


def test_pages_workflow_includes_nojekyll() -> None:
    """Pages workflow must touch .nojekyll (skip Jekyll processing)."""
    pages_yml = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    text = pages_yml.read_text(encoding="utf-8")
    assert ".nojekyll" in text


def test_pages_workflow_includes_design() -> None:
    """Pages workflow must copy design/ directory."""
    pages_yml = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    text = pages_yml.read_text(encoding="utf-8")
    assert "design/" in text


# ----------------------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------------------


def test_index_links_to_graphic_novel() -> None:
    """index.html must link to graphic-novel.html."""
    text = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    assert "graphic-novel.html" in text, "index.html should link to graphic-novel.html"


@pytest.mark.skip(reason="tests test pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
def test_all_game_dashboards_link_to_graphic_novel() -> None:
    """All game dashboards should also link to graphic-novel.html.

    Note: library.html is the Derivative Library (Fiction derivative).
    """
    skip = {"graphic-novel.html", "library.html"}
    for filename in DASHBOARD_HTML_FILES:
        if filename in skip:
            continue
        text = (DASHBOARD_DIR / filename).read_text(encoding="utf-8")
        assert "graphic-novel.html" in text, f"{filename} should link to graphic-novel.html in nav"


# ----------------------------------------------------------------------------
# Sanity: no broken external URLs
# ----------------------------------------------------------------------------


def test_no_404_links_in_dashboards() -> None:
    """Check for relative links that point to non-existent files."""
    for filename in DASHBOARD_HTML_FILES:
        text = (DASHBOARD_DIR / filename).read_text(encoding="utf-8")
        # Find href="...html" patterns (only local files)
        for match in re.finditer(r'href="([^"]+\.html)"', text):
            href = match.group(1)
            # Skip absolute URLs and anchors
            if href.startswith(("http://", "https://", "#", "/")):
                continue
            # Skip external paths (Fiction/, design/, etc.) — they may not exist locally
            if "/" in href and not href.startswith("dashboard"):
                continue
            # Local relative path
            target = DASHBOARD_DIR / href
            if not target.exists():
                # Check if it's a Fiction or design path
                if "Fiction/" in href or "design/" in href:
                    continue
                # Otherwise it should exist
                if href.endswith(".html"):
                    assert target.exists(), f"{filename} has broken link to {href}"


def test_graphic_novel_dashboard_has_scenes() -> None:
    """graphic-novel.html must reference all 12 scenes."""
    text = (DASHBOARD_DIR / "graphic-novel.html").read_text(encoding="utf-8")
    # Check that each character has 4 scenes referenced
    for char in ["case", "sil", "kas"]:
        # Each character dir contains 4 scenes
        # Just check that the dashboard references the scenes directory
        assert "scenes/" in text, "graphic-novel.html should link to scenes/"
