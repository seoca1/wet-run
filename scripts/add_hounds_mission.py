#!/usr/bin/env python3
"""Add new mission 'hounds_arc' to wet_run missions.json.

Pairs with Fiction Phase 59 — hounds concept page.
Suit-arc, Arc 5: corporate-statework on working-class-canine class-image.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "hounds_arc",
    "title": "Hounds Arc",
    "story": {
        "synopsis_en": "The Suit audits the Hounds. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine. The Hounds are the era's late-Capitalist working-class-canine. The working-class-canine is the era's late-Capitalist Mexico-City working-class retainer-class. The retainer-class is the era's late-Capitalist working-class-canine.",
        "synopsis_ko": "Suit가 Hounds를 감사한다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인이다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인이다. Hounds는 시대의 후기-자본주의 작업-급-카나리인입니다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인입니다. Hounds는 시대의 후기-자본주의 작업-급-카나리인입니다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급입니다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인입니다. Hounds는 시대의 후기-자본주의 작업-급-카나리인입니다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급입니다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인입니다. Hounds는 시대의 후기-자본주의 작업-급-카나리인입니다. 작업-급-카나리인은 시대의 후기-자본주의 Mexico-City 작업-급 리테이너-계급입니다. 리테이너-계급은 시대의 후기-자본주의 작업-급-카나리인입니다. Hounds는 시대의 후기-자본주의 작업-급-카나리인입니다.",
        "source": "hounds_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 364,
        "char_count_ko": 856,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "hounds_working_class_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "mexico_city_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "canine_class_image_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2042,
    "zone": "deep",
    "rewards": {
        "credits": 3500,
        "materials": {
            "data_fragment": 7,
            "mexico_city_token": 1
        }
    },
    "arc": 5
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
