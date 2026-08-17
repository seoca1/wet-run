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
   dashboard card in ``stories.html``.

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
    """
    if href.startswith(("http://", "https://", "mailto:", "javascript:", "#", "data:")):
        return None
    if "' + " in href or '+ "' in href:
        return None
    href_clean = href.split("#", 1)[0]
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
        title_clean = title.group(1).replace(" — Wet Run", "").strip()
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


def check_mission_coverage() -> list[str]:
    errors: list[str] = []
    if not MISSIONS_JSON.exists():
        return [f"  missions.json not found: {MISSIONS_JSON}"]
    missions = json.loads(MISSIONS_JSON.read_text(encoding="utf-8"))
    sources = {m["story"]["source"] for m in missions.values() if "story" in m}

    # Available HTML files.
    html_stems = {html.stem.replace("_en", "") for html in SHORT_STORIES_HTML.glob("*_en.html")}

    # HTML pages whose source doesn't exist.
    # aleph_fragment, mollys_razor, ta_heist are free-form Fiction stories
    # created 2026-07-08 without dedicated game missions (ADR-0052 scope).
    # They are intentionally un-owned; tolerated here.
    known_orphans = {"aleph_fragment", "mollys_razor", "ta_heist"}
    orphan_pages = sorted((html_stems - sources) - known_orphans)
    for stem in orphan_pages:
        errors.append(f"  orphan page (no mission source): {stem}")

    # Mission sources that have no card in library.html.
    library_html = (DASHBOARD / "library.html").read_text(encoding="utf-8")
    cards = set()
    for href in re.findall(r'href="stories/short-stories/([^"]+)"', library_html):
        cards.add(href.replace("_en.html", "").replace("_ko.html", ""))
    missing = sorted(sources - cards)
    for stem in missing:
        errors.append(f"  mission source without library.html card: {stem}")
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


if __name__ == "__main__":
    sys.exit(main())
