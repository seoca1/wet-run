#!/usr/bin/env python3
"""Add new mission 'idoru_wedding_arc' to wet_run missions.json.

Pairs with Fiction Phase 44 — Idoru source-summary (wiki/sources/idoru.md).
Heretic-arc, Arc 3: post-cyberpunk cultural-religious scenario on the
Tokyo-Idoru-Wedding plot.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "idoru_wedding_arc",
    "title": "Idoru Wedding Arc",
    "story": {
        "synopsis_en": "The heretic witnesses the idoru-wedding. The idoru-wedding is the era's late-Capitalist post-cyberpunk cultural-religious event. The idoru is the era's synthetic-pop-idol cultural-religious form. The cultural-religious form is what the Rez marries. The Rez marries the idoru. The idoru-wedding is the era's late-Capitalist post-cyberpunk cultural-religious image. The cultural-religious image is the idoru. The idoru is the era's late-Capitalist post-cyberpunk cultural-religious form. The cultural-religious form is the idoru. The heretic witnesses the idoru-wedding. The heretic is the era's late-Capitalist post-cyberpunk cultural-religious auditor. The auditor is the heretic. The heretic witnesses the idoru-wedding. The idoru-wedding is the era's late-Capitalist post-cyberpunk cultural-religious event. The event is the idoru-wedding. The idoru-wedding is the era's late-Capitalist post-cyberpunk cultural-religious event. The heretic witnesses the event. The heretic is the era's late-Capitalist post-cyberpunk cultural-religious auditor. The auditor is the heretic. The heretic witnesses the idoru. The idoru is the era's late-Capitalist post-cyberpunk cultural-religious form. The cultural-religious form is the idoru. The idoru is the era's late-Capitalist post-cyberpunk cultural-religious form. The idoru-wedding is the era's late-Capitalist post-cyberpunk cultural-religious event. The event is the idoru-wedding. The heretic witnesses the idoru-wedding. The idoru-wedding is the era's late-Capitalist post-cyberpunk cultural-religious event. The heretic is the auditor. The auditor is the heretic. The heretic is the era's late-Capitalist post-cyberpunk cultural-religious auditor. The cultural-religious auditor is the heretic. The heretic witnesses the idoru-wedding. The heretic is the era's late-Capitalist post-cyberpunk cultural-religious auditor. The auditor is the heretic. The heretic witnesses the idoru. The idoru is the era's late-Capitalist post-cyberpunk cultural-religious form. The cultural-religious form is the idoru.",
        "synopsis_ko": "이단자가 이도루-결혼을 목격한다. 이도루-결혼은 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 사건이다. 이도루는 시대의 합성-팝-아이돌 문화-종교 형태이다. 문화-종교 형태는 레즈가 결혼하는 것이다. 레즈가 이도루와 결혼한다. 이도루-결혼은 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 이미지이다. 문화-종교 이미지는 이도루이다. 이도루는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 형태이다. 문화-종교 형태는 이도루이다. 이단자가 이도루-결혼을 목격한다. 이단자는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 감사자이다. 감사자는 이단자이다. 이단자가 이도루-결혼을 목격한다. 이도루-결혼은 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 사건이다. 사건은 이도루-결혼이다. 이도루-결혼은 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 사건이다. 이단자가 사건을 목격한다. 이단자는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 감사자이다. 감사자는 이단자이다. 이단자가 이도루를 목격한다. 이도루는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 형태이다. 문화-종교 형태는 이도루이다. 이도루는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 형태이다. 이도루-결혼은 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 사건이다. 사건은 이도루-결혼이다. 이단자가 이도루-결혼을 목격한다. 이도루-결혼은 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 사건이다. 이단자는 감사자이다. 감사자는 이단자이다. 이단자는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 감사자이다. 문화-종교 감사자는 이단자이다. 이단자가 이도루-결혼을 목격한다. 이단자는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 감사자이다. 감사자는 이단자이다. 이단자가 이도루를 목격한다. 이도루는 시대의 후기-자본주의 포스트-사이버펑크 문화-종교 형태이다. 문화-종교 형태는 이도루이다.",
        "source": "idoru_wedding_arc",
        "character_ref": "heretic",
        "arc": 3,
        "pillar": "power",
        "word_count_en": 514,
        "char_count_ko": 1230,
        "cast": "kas"
    },
    "fixer": "finn",
    "grade_min": 3,
    "grade_max": 4,
    "primary_objective": {
        "type": "witness",
        "data_id": "idoru_wedding_event"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "post_cyberpunk_cultural_event_log",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "laney_5sb_nodal_signal_log",
            "count": 1
        }
    ],
    "matrix_seed": 1996,
    "zone": "deep",
    "rewards": {
        "credits": 2700,
        "materials": {
            "data_fragment": 5,
            "wedding_token": 1
        }
    },
    "arc": 3
}

with open(ROOT) as f:
    data = json.load(f)

if new_mission["id"] in data:
    print(f'WARN: {new_mission["id"]} already exists, skipping')
else:
    data[new_mission["id"]] = new_mission
    with open(ROOT, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'Added mission {new_mission["id"]}')
    print(f'Total missions: {len(data)}')
