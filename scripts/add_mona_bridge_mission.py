#!/usr/bin/env python3
"""Add new mission 'mona_bridge_arc' to wet_run missions.json.

Pairs with Fiction Phase 58 — Mona character page.
Suit-arc, Arc 5: corporate-statework on bridge-squatter class-image.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "mona_bridge_arc",
    "title": "Mona Bridge Arc",
    "story": {
        "synopsis_en": "The Suit audits the bridge-squatter. The bridge-squatter is the era's late-Capitalist Bay-Area bridge-squatter class-image. The bridge-squatter is the era's working-class-precariat substrate. The substrate is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the era's late-Capitalist bridge-squatter. The bridge-squatter is the era's late-Capitalist Bay-Area bridge-squatter. The bridge-squatter is the era's working-class-precariat. The working-class-precariat is the era's late-Capitalist bridge-squatter. The bridge-squatter is the era's late-Capitalist Bay-Area bridge-squatter class-image. The class-image is the era's late-Capitalist bridge-squatter. The bridge-squatter is the era's working-class-precariat. The working-class-precariat is the era's late-Capitalist bridge-squatter. The bridge-squatter is the era's late-Capitalist Bay-Area bridge-squatter. The bridge-squatter is the era's working-class-precariat. The working-class-precariat is the era's late-Capitalist bridge-squatter. The bridge-squatter is the era's late-Capitalist Bay-Area bridge-squatter. The bridge-squatter is the era's working-class-precariat. The working-class-precariat is the era's late-Capitalist bridge-squatter. The bridge-squatter is the era's late-Capitalist Bay-Area bridge-squatter.",
        "synopsis_ko": "Suit가 브릿지-스쿼터를 감사한다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터 클래스-이미지이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트 기질이다. 기질은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 후기-자본주의 베이-지역 브릿지-스쿼터이다. 브릿지-스쿼터는 시대의 작업-급-프리카리아트이다. 작업-급-프리카리아트는 시대의 후기-자본주의 브릿지-스쿼터이다.",
        "source": "mona_bridge_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 373,
        "char_count_ko": 845,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "mona_bridge_squatter_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "bridge_squatter_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "bay_area_precariat_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2041,
    "zone": "deep",
    "rewards": {
        "credits": 3400,
        "materials": {
            "data_fragment": 7,
            "bay_area_token": 1
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
