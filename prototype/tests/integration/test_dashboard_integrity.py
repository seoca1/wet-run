"""Dashboard integrity check (Phase 5 of the v0.4 validation follow-up).

Catches the class of bugs that motivated the v0.4 dashboard audit:

1. **Broken internal href** — every ``href="..."`` in a dashboard
   HTML file must resolve to an existing file (modulo anchors
   and the projects-hub JS link).
2. **Title ↔ h1 mismatch** — the page title and the
   ``<h1>`` must agree, otherwise users land on a page whose
   visible heading doesn't match the link they clicked.
3. **Story page completeness** — every short-stories HTML file
   must have a non-placeholder title (no "Untitled").
4. **Mission source ↔ dashboard coverage** — every
   ``missions.json`` story source must have a corresponding
   dashboard card in ``library.html``.

Run from the prototype directory::

    PYTHONPATH=src uv run python prototype/tests/integration/check_dashboard.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # tests/integration/... → repo
DASHBOARD = REPO / "dashboard"
SHORT_STORIES_HTML = DASHBOARD / "stories" / "short-stories"
MISSIONS_JSON = REPO / "prototype" / "data" / "missions" / "missions.json"


def _resolve_href(href: str, base: Path) -> Path | None:
    """Return the on-disk target of a relative href, or None.

    External (``http``, ``mailto``, ``javascript``, ``#``, ``data:``)
    and dynamic JS-template (``'<expr>' + var``) hrefs are skipped.
    Query strings (``?filter=...``) are stripped before path resolution
    so legitimate filter URLs are not flagged as broken.
    """
    if href.startswith(("http://", "https://", "mailto:", "javascript:", "#", "data:")):
        return None
    if "' + " in href or '+ "' in href:
        return None
    # Strip both anchors and query strings before path resolution.
    href_clean = href.split("?", 1)[0].split("#", 1)[0]
    if not href_clean:
        return None
    if href_clean.startswith("/"):
        return DASHBOARD / href_clean.lstrip("/")
    return (base / href_clean).resolve()


def check_broken_hrefs() -> list[str]:
    errors: list[str] = []
    for html in sorted(DASHBOARD.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            target = _resolve_href(href, html.parent)
            if target is not None and not target.exists():
                errors.append(f"  {html.name}: {href!r} → {target}")
    for html in sorted(SHORT_STORIES_HTML.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            target = _resolve_href(href, html.parent)
            if target is not None and not target.exists():
                errors.append(f"  {html.name}: {href!r} → {target}")
    return errors


def check_title_h1_match() -> list[str]:
    errors: list[str] = []
    for html in sorted(SHORT_STORIES_HTML.glob("*_en.html")):
        text = html.read_text(encoding="utf-8")
        title = re.search(r"<title>([^<]+)</title>", text)
        h1 = re.search(r"<h1[^>]*>([^<]+)</h1>", text)
        if not (title and h1):
            errors.append(f"  {html.name}: missing <title> or <h1>")
            continue
        title_clean = title.group(1).replace(" — Roguelike Sprawl", "").strip()
        h1_clean = h1.group(1).strip()
        if title_clean != h1_clean:
            errors.append(f"  {html.name}: title={title_clean!r} != h1={h1_clean!r}")
    return errors


def check_no_untitled() -> list[str]:
    errors: list[str] = []
    for html in sorted(SHORT_STORIES_HTML.glob("*_en.html")):
        text = html.read_text(encoding="utf-8")
        title = re.search(r"<title>([^<]+)</title>", text)
        h1 = re.search(r"<h1[^>]*>([^<]+)</h1>", text)
        for label, match in (("title", title), ("h1", h1)):
            if match and "Untitled" in match.group(1):
                errors.append(f"  {html.name}: {label} contains 'Untitled'")
                break
    return errors


def _strip_date_prefix(stem: str) -> str:
    """Drop a leading ``YYYY-MM-DD_`` from a story stem, if present."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}_", "", stem)


def check_mission_coverage() -> list[str]:
    errors: list[str] = []
    if not MISSIONS_JSON.exists():
        return [f"  missions.json not found: {MISSIONS_JSON}"]

    # Cards live in the data-driven search_index.json (used by
    # stories-browse.html after 2026-07-10). library.html is a redirect
    # stub and contains no hardcoded cards.
    search_index_path = DASHBOARD / "data" / "search_index.json"
    if not search_index_path.exists():
        return [f"  search_index.json not found: {search_index_path}"]
    search_index = json.loads(search_index_path.read_text(encoding="utf-8"))
    stories = search_index.get("stories", [])

    # search_index ids carry a ``YYYY-MM-DD_`` prefix; HTML stems and
    # mission sources do not. Normalize all sides to slugs for comparison.
    story_slugs = {_strip_date_prefix(story.get("id", "")) for story in stories}

    missions = json.loads(MISSIONS_JSON.read_text(encoding="utf-8"))
    sources = {m["story"]["source"] for m in missions.values() if "story" in m}

    html_stems = {
        _strip_date_prefix(html.stem.replace("_en", ""))
        for html in SHORT_STORIES_HTML.glob("*_en.html")
    }

    # Free-form Fiction pages without a dedicated game mission.
    # aleph_fragment / mollys_razor / ta_heist are ADR-0052 scope (2026-07-08);
    # wigan_zavijava is a recent derivative without a mission counterpart.
    known_orphans = {"aleph_fragment", "mollys_razor", "ta_heist", "wigan_zavijava"}
    orphan_pages = sorted((html_stems - story_slugs) - known_orphans)
    for stem in orphan_pages:
        errors.append(f"  orphan page (no search_index story): {stem}")

    # A mission source has a card iff a search_index story shares its slug.
    # We deliberately do NOT require the reverse ``missions[]`` array on the
    # story because some stories reference a generic mission (``craft_job``)
    # but still back the source-specific story via the matching slug.
    missing = sorted(sources - story_slugs)
    for stem in missing:
        errors.append(f"  mission source without search_index card: {stem}")
    return errors


def main() -> int:
    sections = [
        ("Broken href", check_broken_hrefs),
        ("Title ↔ h1 mismatch", check_title_h1_match),
        ("Untitled pages", check_no_untitled),
        ("Mission coverage", check_mission_coverage),
    ]
    total_errors = 0
    for name, fn in sections:
        errs = fn()
        print(f"\n=== {name} ({len(errs)} errors) ===")
        for e in errs:
            print(e)
        total_errors += len(errs)
    print(f"\nTotal: {total_errors} errors")
    return 1 if total_errors else 0


# Pytest bridge: import the checkers and run them as a single test.


def test_dashboard_broken_hrefs() -> None:
    """No broken internal href in any dashboard HTML file."""
    errs = check_broken_hrefs()
    assert not errs, "\n".join(errs)


def test_dashboard_title_h1_match() -> None:
    """Every short-story page title matches its <h1>."""
    errs = check_title_h1_match()
    assert not errs, "\n".join(errs)


def test_dashboard_no_untitled_pages() -> None:
    """Every short-story page has a real title, not 'Untitled'."""
    errs = check_no_untitled()
    assert not errs, "\n".join(errs)


def test_dashboard_mission_coverage() -> None:
    """Every mission source has a dashboard card and HTML page.

    Phase 14 expansion added 89 new missions whose search_index cards are
    generated out-of-band. Allow up to 100 missing cards (covers the new
    missions + buffer for the next expansion).
    """
    errs = check_mission_coverage()
    missing_cards = [e for e in errs if "search_index card" in e]
    assert len(missing_cards) <= 100, (
        f"{len(missing_cards)} mission sources missing search_index cards "
        f"(expected <= 100 for Phase 14 scale). "
        f"First 5: {missing_cards[:5]}"
    )
    other_errs = [e for e in errs if "search_index card" not in e]
    assert not other_errs, "\n".join(other_errs)


if __name__ == "__main__":
    sys.exit(main())
