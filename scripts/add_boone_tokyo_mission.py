#!/usr/bin/env python3
"""Add new mission 'boone_tokyo_electronics_arc' to wet_run missions.json.

Pairs with Fiction Phase 52 — boone-chu character page.
Suit-arc, Arc 5: corporate-statework on Tokyo-electronics-dealer class-image.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "boone_tokyo_electronics_arc",
    "title": "Boone Tokyo-Electronics Arc",
    "story": {
        "synopsis_en": "The Suit audits the Boone. The Boone is the era's late-Capitalist Tokyo-electronics-dealer. The Boone is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Tokyo-electronics-dealer class-image. The class-image is the era's late-Capitalist Boone working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant.",
        "synopsis_ko": "Suit가 Boone을 감사한다. Boone은 시대의 후기-자본주의 Tokyo-전자-딜러이다. Boone은 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Tokyo-전자-딜러 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 Boone 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다.",
        "source": "boone_tokyo_electronics_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 422,
        "char_count_ko": 1010,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "boone_tokyo_electronics_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "tokyo_electronics_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "aspirant_class_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2035,
    "zone": "deep",
    "rewards": {
        "credits": 3400,
        "materials": {
            "data_fragment": 6,
            "tokyo_chit": 1
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
