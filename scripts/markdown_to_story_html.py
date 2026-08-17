#!/usr/bin/env python3
"""Convert short story markdown to e-book style HTML."""

import re
import sys
from pathlib import Path


# Map Fiction-stem → dashboard-stem.  Each Fiction stem is the
# authoritative identifier; aliases exist only for legacy reasons and
# each must keep a 1:1 mapping (no two Fiction stems may share a
# dashboard page).  Empty dicts default to identity (the Fiction stem
# becomes the dashboard stem verbatim).
STORY_ID_MAP: dict[str, str] = {
    # Legacy aliases kept ONLY because dashboard/stories.html still
    # links to these names.  Each alias points at a single Fiction
    # stem — never at another alias — so the page title and the URL
    # always agree.
    'case_jackout-30sec': 'case_jackout-30sec',
    'dixies_last_run': 'dixies_last_run',
    'wigan_zavijava': 'wigan_zavijava',
    'loa_voodoo_contact': 'loa_voodoo_contact',
    'the_choice': 'the_choice',
    'flatline_again': 'flatline_again',
    'kumiko_manarase-midnight': 'kumiko_manarase-midnight',
    'marly_louisiana-god': 'marly_louisiana-god',
    'sally_sandii-3am': 'sally_sandii-3am',
    'sally_returns': 'sally_returns',
    'sense_net_trace': 'sense_net_trace',
    # v0.4 (2026-07-01) added 5 fresh stories; no alias needed.
    'sense_net_infiltration': 'sense_net_infiltration',
    'wigan_call': 'wigan_call',
    'hosaka_core': 'hosaka_core',
    'straylight_approach': 'straylight_approach',
    'maas_heist': 'maas_heist',
}


STORY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Roguelike Sprawl</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #faf8f5;
            --text-color: #2c2c2c;
            --accent-color: #e94560;
            --meta-color: #666666;
            --font-serif: "Crimson Pro", "Source Serif 4", Georgia, serif;
            --max-width: 680px;
            --line-height: 1.8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ font-size: 18px; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-serif);
            line-height: var(--line-height);
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{ max-width: var(--max-width); margin: 0 auto; padding: 4rem 2rem 8rem; }}

        .story-header {{ margin-bottom: 3rem; padding-bottom: 2rem; border-bottom: 1px solid #e0ddd8; }}
        .character-badge {{
            display: inline-block;
            font-family: monospace;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--accent-color);
            background: #1a1a2e15;
            padding: 0.25rem 0.75rem;
            border-radius: 2px;
            margin-bottom: 1rem;
        }}
        .story-title {{ font-size: 2.25rem; font-weight: 600; line-height: 1.2; margin-bottom: 0.5rem; }}
        .story-subtitle {{ font-size: 1.1rem; font-style: italic; color: var(--meta-color); }}
        .story-meta {{ margin-top: 1rem; font-size: 0.85rem; color: var(--meta-color); }}
        .story-meta span {{ margin-right: 1rem; }}

        .story-body {{ text-align: justify; hyphens: auto; }}
        .story-body p {{ margin-bottom: 1.5rem; }}
        .story-body h2 {{
            font-size: 1.4rem; font-weight: 600;
            color: var(--accent-color); margin: 2.5rem 0 1rem;
        }}
        .story-body blockquote {{
            font-style: italic; color: var(--meta-color);
            border-left: 3px solid var(--accent-color);
            padding-left: 1rem; margin: 2rem 0;
        }}
        .story-body hr {{ border: none; border-top: 1px solid #e0ddd8; margin: 2rem 0; }}
        .story-body ul {{ margin: 1.5rem 0; padding-left: 1.5rem; }}
        .story-body li {{ margin-bottom: 0.5rem; }}
        em {{ font-style: italic; }}
        strong {{ font-weight: 600; }}

        .story-footer {{ margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #e0ddd8; text-align: center; }}
        .story-footer p {{ font-size: 0.85rem; color: var(--meta-color); font-family: monospace; text-transform: uppercase; letter-spacing: 0.1em; }}

        .lang-indicator {{
            position: fixed; top: 1rem; right: 1rem;
            font-family: monospace; font-size: 0.7rem;
            text-transform: uppercase; letter-spacing: 0.1em;
            color: var(--meta-color); background: var(--bg-color);
            padding: 0.25rem 0.5rem; border-radius: 2px; opacity: 0.7;
        }}
        .lang-indicator a {{ color: inherit; text-decoration: none; }}
        .lang-indicator a:hover {{ text-decoration: underline; }}

        @media (max-width: 600px) {{ html {{ font-size: 16px; }} .container {{ padding: 2rem 1.5rem 6rem; }} .story-title {{ font-size: 1.75rem; }} }}
    </style>
</head>
<body>
    <div class="lang-indicator">{lang_indicator}</div>
    <div class="container">
        <header class="story-header">
            <div class="character-badge">{character_badge}</div>
            <h1 class="story-title">{title}</h1>
            <p class="story-subtitle">{subtitle}</p>
            <div class="story-meta"><span>{word_count} words</span><span>Sprawl Trilogy</span></div>
        </header>
        <article class="story-body">
{body}
        </article>
        <footer class="story-footer">
            <p>Roguelike Sprawl — Derivative Fiction</p>
            <p>Based on William Gibson's Sprawl Trilogy</p>
        </footer>
    </div>
</body>
</html>"""


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    import yaml
    try:
        frontmatter = yaml.safe_load(parts[1])
    except:
        frontmatter = {}

    return frontmatter, parts[2].strip()


def markdown_to_html(text: str, lang: str) -> str:
    """Convert markdown to HTML."""
    html_parts = []
    lines = text.strip().split('\n')
    in_blockquote = False
    blockquote_content = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Horizontal rule
        if re.match(r'^---+$', line.strip()):
            if blockquote_content:
                html_parts.append(f'<blockquote>{"".join(blockquote_content)}</blockquote>')
                blockquote_content = []
                in_blockquote = False
            html_parts.append('<hr>')
            i += 1
            continue

        # Headers - skip H1 title at start (already in header)
        if i == 0:
            h1_match = re.match(r'^# (.+)$', line.strip())
            if h1_match:
                i += 1
                continue

        header_match = re.match(r'^## (.+)$', line.strip())
        if header_match:
            if blockquote_content:
                html_parts.append(f'<blockquote>{"".join(blockquote_content)}</blockquote>')
                blockquote_content = []
                in_blockquote = False
            title = header_match.group(1)
            title = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', title)
            title = re.sub(r'\*(.+?)\*', r'<em>\1</em>', title)
            html_parts.append(f'<h2>{title}</h2>')
            i += 1
            continue

        # Blockquote lines
        if line.strip().startswith('>'):
            if blockquote_content:
                html_parts.append(f'<blockquote>{"".join(blockquote_content)}</blockquote>')
                blockquote_content = []
            blockquote_content.append(f'<p>{line.strip()[1:].strip()}</p>')
            in_blockquote = True
            i += 1
            continue
        elif in_blockquote and not line.strip():
            html_parts.append(f'<blockquote>{"".join(blockquote_content)}</blockquote>')
            blockquote_content = []
            in_blockquote = False
            i += 1
            continue
        elif in_blockquote:
            html_parts.append(f'<blockquote>{"".join(blockquote_content)}</blockquote>')
            blockquote_content = []
            in_blockquote = False
            continue

        # List items
        list_match = re.match(r'^(- .+)$', line.strip())
        if list_match:
            items = []
            while i < len(lines) and re.match(r'^(- .+)$', lines[i].strip()):
                item_text = lines[i].strip()[2:]
                item_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item_text)
                item_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', item_text)
                item_text = re.sub(r'\[\[(.+?)\]\]', r'<em>\1</em>', item_text)
                items.append(f'<li>{item_text}</li>')
                i += 1
            html_parts.append(f'<ul>{"".join(items)}</ul>')
            continue

        # Regular paragraph
        if line.strip():
            para = line.strip()
            para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', para)
            para = re.sub(r'\*(.+?)\*', r'<em>\1</em>', para)
            para = re.sub(r'\[\[(.+?)\]\]', r'<em>\1</em>', para)
            html_parts.append(f'<p>{para}</p>')
        elif html_parts and html_parts[-1].endswith('</p>'):
            pass  # Skip empty lines between paragraphs
        i += 1

    if blockquote_content:
        html_parts.append(f'<blockquote>{"".join(blockquote_content)}</blockquote>')

    return '\n'.join(html_parts)


def get_story_id(md_path: Path) -> str:
    """Extract the dashboard story-id from a markdown filename.

    Strips the ``YYYY-MM-DD_`` date prefix and the ``.ko`` suffix
    (if present) and applies the ``STORY_ID_MAP`` for the rare
    legacy alias cases.  As of v0.4 (2026-07-01) the map is
    1:1, so almost every Fiction stem becomes its own dashboard
    page; see ``STORY_ID_MAP`` for the few remaining aliases.
    """
    stem = md_path.stem
    if stem.endswith('.ko'):
        stem = stem[:-3]

    # Direct match (the common case after v0.4).
    if stem in STORY_ID_MAP:
        return STORY_ID_MAP[stem]

    # Legacy date-prefixed filenames ("2026-06-23_case_jackout-30sec"):
    # the story-id is whatever comes after "YYYY-MM-DD_".
    for md_id, html_id in STORY_ID_MAP.items():
        if stem.endswith(md_id):
            return html_id

    # Unknown stem → strip the date prefix if present.
    if stem.startswith("20") and "-" in stem[:10]:
        return stem[11:]

    return stem


def _pick_localised(value: object, lang: str, fallback: str = "") -> str:
    """Resolve a possibly-bilingual frontmatter value.

    Frontmatter in the short-stories directory uses two patterns:

    1. ``title: "Plain string"`` — works for either language.
    2. ``title: { en: "...", ko: "..." }`` — used for stories with
       explicit per-language titles.

    The builder must always return a string; otherwise the format()
    call would print the dict repr (e.g. ``{'en': 'Foo'}``) into the
    HTML, which is exactly the dashboard regression the v0.4 audit
    flagged.
    """
    if value is None:
        return fallback
    if isinstance(value, dict):
        chosen = value.get(lang)
        if chosen is None:
            chosen = value.get("en") or value.get("ko")
        return str(chosen) if chosen else fallback
    return str(value)


def convert_markdown_to_html(md_path: Path, output_dir: Path, lang: str) -> Path:
    """Convert a single markdown file to HTML."""
    content = md_path.read_text(encoding='utf-8')
    frontmatter, body = parse_frontmatter(content)

    title = _pick_localised(
        frontmatter.get(f"title_{lang}") or frontmatter.get("title"),
        lang,
        fallback="Untitled",
    )
    subtitle = _pick_localised(
        frontmatter.get(f"subtitle_{lang}") or frontmatter.get("subtitle"),
        lang,
        fallback="",
    )
    word_count = frontmatter.get('word_count', 0)

    character = frontmatter.get('character', [{}])
    if isinstance(character, list) and character:
        char_info = character[0]
        char_id = char_info.get('id', 'unknown')
        char_archetype = char_info.get('archetype', '')
    else:
        char_id = 'unknown'
        char_archetype = ''

    char_badge = char_id.capitalize()
    if char_archetype:
        char_badge = f"{char_badge} — {char_archetype.capitalize()}"

    other_lang = 'ko' if lang == 'en' else 'en'
    story_id = get_story_id(md_path)
    lang_indicator = f'{lang.upper()} · <a href="{story_id}_{other_lang}.html">{other_lang.upper()}</a>'

    body_html = markdown_to_html(body, lang)

    html = STORY_HTML_TEMPLATE.format(
        lang=lang,
        title=title,
        subtitle=subtitle,
        character_badge=char_badge,
        word_count=word_count,
        lang_indicator=lang_indicator,
        body=body_html
    )

    output_path = output_dir / f"{story_id}_{lang}.html"
    output_path.write_text(html, encoding='utf-8')

    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert short story markdown to HTML')
    parser.add_argument('--source-dir', default='/Users/emilio/projects/Projects/Fiction/derivative/sprawl-trilogy/short-stories', help='Source markdown directory')
    parser.add_argument('--output-dir', default='/Users/emilio/projects/Projects/Game/wet_run/dashboard/stories/short-stories', help='Output HTML directory')
    parser.add_argument('--lang', choices=['en', 'ko', 'both'], default='both', help='Language to convert')
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    languages = ['en', 'ko'] if args.lang == 'both' else [args.lang]

    # Match any date-prefixed story file (2026-06-*, 2026-07-01, ...).
    # Earlier this glob was hardcoded to 2026-06-*, which silently
    # dropped every story added after the original cut-off (Phase B
    # CONTENT_EXPANSION added 5 stories in 2026-07-01).  See the
    # dashboard validation follow-up for details.
    en_files = sorted(
        f for f in source_dir.glob('20*-*-*_*.md') if '.ko.' not in f.name and '.tone-prompt' not in f.name
    )
    ko_files = sorted(source_dir.glob('20*-*-*_*.ko.md'))

    # De-dup: only the *latest* markdown wins per dashboard stem.
    # Two date-prefixed files with the same story-id (alias map)
    # would otherwise overwrite each other and the printed log would
    # be misleading.  Sorting newest-first by mtime keeps behaviour
    # predictable.
    en_seen: set[str] = set()
    en_unique: list[Path] = []
    for md_path in sorted(en_files, key=lambda p: p.stat().st_mtime, reverse=True):
        sid = get_story_id(md_path)
        if sid in en_seen:
            print(f"  skip (dup): {md_path.name}  →  {sid}_en.html")
            continue
        en_seen.add(sid)
        en_unique.append(md_path)

    ko_seen: set[str] = set()
    ko_unique: list[Path] = []
    for md_path in sorted(ko_files, key=lambda p: p.stat().st_mtime, reverse=True):
        sid = get_story_id(md_path)
        if sid in ko_seen:
            print(f"  skip (dup): {md_path.name}  →  {sid}_ko.html")
            continue
        ko_seen.add(sid)
        ko_unique.append(md_path)

    for md_path in en_unique:
        if 'en' in languages:
            try:
                output_path = convert_markdown_to_html(md_path, output_dir, 'en')
                print(f"Generated: {output_path.name}")
            except Exception as e:
                print(f"Error processing {md_path.name}: {e}")

    for md_path in ko_unique:
        if 'ko' in languages:
            try:
                output_path = convert_markdown_to_html(md_path, output_dir, 'ko')
                print(f"Generated: {output_path.name}")
            except Exception as e:
                print(f"Error processing {md_path.name}: {e}")


if __name__ == '__main__':
    main()