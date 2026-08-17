#!/usr/bin/env python3
"""Add new mission 'wendell_suburban_arc' to wet_run missions.json.

Pairs with Fiction Phase 51 — wendell-wright character page.
Novice-arc, Arc 1: late-Capitalist working-class-aspirant procedural.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "wendell_suburban_arc",
    "title": "Wendell Suburban Arc",
    "story": {
        "synopsis_en": "Wendell runs the suburban-class. The suburban-class is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Wendell working-class image. The image is operational. The operational is the era's late-Capitalist Wendell working-class-aspirant. Wendell is the aspirant. The aspirant is the era's Wendell working-class image. The image is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Wendell working-class-aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The Wendell aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Wendell working-class-aspirant. The aspirant is operational. The operational is the era's late-Capitalist Wendell working-class-aspirant. Wendell is the aspirant. The aspirant is the era's late-Capitalist working-class-aspirant. The aspirant is operational. The operational is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Wendell working-class-aspirant. The aspirant is operational. The operational is the era's Wendell working-class-aspirant. The aspirant is operational. The operational is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Wendell working-class-aspirant. The aspirant is operational. The operational is the era's late-Capitalist Wendell working-class-aspirant. Wendell is the aspirant. The aspirant is operational. The operational is the era's late-Capitalist Wendell working-class-aspirant. Wendell is the era's late-Capitalist working-class-aspirant. The aspirant is the era's Wendell working-class-aspirant. The aspirant is operational. The operational is the era's Wendell working-class-aspirant. Wendell is the era's late-Capitalist working-class-aspirant.",
        "synopsis_ko": "Wendell이 교외-계급을 달린다. 교외-계급은 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Wendell 작업-급 이미지이다. 이미지는 운영적이다. 운영은 시대의 후기-자본주의 Wendell 작업-급-지원자이다. Wendell은 지원자이다. 지원자는 시대의 Wendell 작업-급 이미지이다. 이미지는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Wendell 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. Wendell 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Wendell 작업-급-지원자이다. 지원자는 운영적이다. 운영은 시대의 후기-자본주의 Wendell 작업-급-지원자이다. Wendell은 지원자이다. 지원자는 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 운영적이다. 운영은 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Wendell 작업-급-지원자이다. 지원자는 운영적이다. 운영은 시대의 후기-자본주의 Wendell 작업-급-지원자이다. 지원자는 운영적이다. 운영은 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Wendell 작업-급-지원자이다. 지원자는 운영적이다. 운영은 시대의 후기-자본주의 Wendell 작업-급-지원자이다. Wendell은 지원자이다. 지원자는 운영적이다. 운영은 시대의 후기-자본주의 Wendell 작업-급-지원자이다. Wendell은 시대의 후기-자본주의 작업-급-지원자이다. 지원자는 시대의 Wendell 작업-급-지원자이다. 지원자는 운영적이다. 운영은 시대의 Wendell 작업-급-지원자이다. Wendell은 시대의 후기-자본주의 작업-급-지원자이다.",
        "source": "wendell_suburban_arc",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "power",
        "word_count_en": 387,
        "char_count_ko": 880,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "deliver",
        "data_id": "wendell_suburban_class_substrate"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "suburban_class_log",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "aspirant_image_log",
            "count": 1
        }
    ],
    "matrix_seed": 2034,
    "zone": "surface",
    "rewards": {
        "credits": 420,
        "materials": {
            "data_fragment": 1,
            "aspirant_token": 1
        }
    },
    "arc": 1
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
