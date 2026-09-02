# Short Story Metadata Schema

## Frontmatter Structure

```yaml
---
title: "Story Title"                    # English title
title_ko: "이야기 제목"                 # Korean title
subtitle: "Subtitle"                    # English subtitle
subtitle_ko: "부제"                     # Korean subtitle

original_title: "Source Work"          # Original work if derivative
author: "Author Name"                  # Author
publication_year: 1984                  # Year of original work

derivative_type: "short_story"         # short_story | excerpt | expansion
derivative_date: 2026-06-23            # Date of this derivative
genre: "Science Fiction, Cyberpunk"

series: "Sprawl Trilogy #1"           # Series reference
source_text: "Path/to/source.md"      # Original source reference

wiki_references:
  - "[[neuromancer]]"
  - "[[case]]"

language: "en"                         # Primary language (ISO 639-1)
languages_available:
  - en                                 # English version available
  - ko                                 # Korean version available

format: "First-person narrative"       # POV description
word_count: 2500                      # Approximate word count
word_count_ko: "~3000자"              # Korean character count

character:
  - id: "case"
    name: "Case"
    role: "protagonist"
    archetype: "console_cowboy"

setting:
  - location: "Sense/Net Boston Node"
    time: "0300"
    atmosphere: "corporate_midnight"

themes:
  - "corporate_surveillance"
  - "memory_and_trace"

game_integration:
  mission_id: "watchdog_patrol"
  arc: "case_arc"
  chapter: 1
  is_playable: false

version:
  en: "1.0"
  ko: "1.0"

status:
  en: "final"
  ko: "final"

related_stories:
  - id: "ice_run"
    relation: "sequel"
  - id: "sense_net_trace"
    relation: "parallel"

plot_summary:
  en: "..."
  ko: "..."
---

# Story Title

## Section 1: Title

Story content in English...

## Section 2: Development

More content...

---

## Connections

- **Wiki**: [[neuromancer]] [[case]]
- **Game**: Mission ID in missions.json
- **Themes**: [[corporate-power]] [[identity-and-the-matrix]]

## Notes

- *Translation notes*
- *World consistency notes*
```

## File Naming Convention

```
{date}_{story_id}.md          # English version (primary)
{date}_{story_id}.ko.md       # Korean version
```

Example:
```
2026-06-23_watchdog_patrol.md       # English
2026-06-23_watchdog_patrol.ko.md    # Korean
```

## Story ID Mapping

| ID | EN Title | KO Title | Character | Arc |
|----|----------|----------|-----------|-----|
| watchdog_patrol | Watchdog Patrol | 워치독 순찰 | Case | Case Arc Ch1 |
| ice_run | Ice Run | 얼음 달콤 | Case | Case Arc Ch1 |
| sense_net_trace | Sense/Net Trace | 센스/넷 추적 | Sil | Sil Arc Ch1 |
| yakuza_deal | Yakuza Deal | 야쿠자 거래 | Kas | Kas Arc Ch1 |
| sally_returns | Sally Returns | 살리의 귀환 | Sally | Case Arc Ch2 |
| black_ice_dream | Black Ice Dream | 블랙 아이스 드림 | Sil | Sil Arc Ch2 |
| dixies_last_run | Dixie's Last Run | 딕시의 마지막 运行 | Dixie | Case Arc Ch3 |
| loa_voodoo_contact | Loa Voodoo Contact | 부두 loa 연락 | Sil | Sil Arc Ch3 |
| the_choice | The Choice | 선택 | Sil | Sil Arc Ch4 |
| flatline_again | Flatline Again | 플랫라인 Again | Case | Case Arc Ch3 |
| case_jackout | Thirty Seconds After Jack-Out | 잭아웃 후 30초 | Case | Case Arc Ch4 |
| marly_louisiana | The God of Louisiana | 루이지아나의 신 | Marly | Sil Arc Ch5 |
| kumiko_manarase | Midnight at the Manarase | 매나리사의 자정 | Kumiko | Kas Arc Ch2 |
| wigan_zavijava | What Wigan Saw | 위건이 본 것 | Wigan | Kas Arc Ch3 |
| sally_sandii_3am | The New Rose Hotel, 3 AM | 로즈 호텔, 새벽 3시 | Sally | Kas Arc Ch4 |
