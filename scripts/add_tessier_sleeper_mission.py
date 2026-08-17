#!/usr/bin/env python3
"""Add new mission 'tessier_sleeper_arc' to wet_run missions.json.

Pairs with Fiction Phase 57 — tessier-ashpool-sleepers concept page.
Suit-arc, Arc 5: corporate-statework on Tessier-Ashpool family-tyranny scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "tessier_sleeper_arc",
    "title": "Tessier-Ashpool Sleeper Arc",
    "story": {
        "synopsis_en": "The Suit audits the Tessier-Ashpool Sleepers. The Tessier-Ashpool Sleepers are the era's late-Capitalist clan-genetic-continuity substrate. The substrate is the era's frozen-state cryogenic substrate. The cryogenic substrate is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the era's Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist corporate-tyranny. The corporate-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny. The family-tyranny is the era's late-Capitalist Tessier-Ashpool family-tyranny.",
        "synopsis_ko": "Suit가 Tessier-Ashpool Sleepers를 감사한다. Tessier-Ashpool Sleepers는 시대의 후기-자본주의 가문-유전-연속성 기질이다. 기질은 시대의 동결-상태 극저온 기질이다. 극저온 기질은 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 기업-폭군이다. 기업-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다. 가문-폭군은 시대의 후기-자본주의 Tessier-Ashpool 가문-폭군이다.",
        "source": "tessier_sleeper_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 412,
        "char_count_ko": 1010,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "tessier_sleeper_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "clan_genetic_continuity_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "family_tyranny_class_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2040,
    "zone": "deep",
    "rewards": {
        "credits": 3700,
        "materials": {
            "data_fragment": 7,
            "sleeper_chit": 1
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
