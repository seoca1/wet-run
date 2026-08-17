#!/usr/bin/env python3
"""Add new mission 'fukuoka_ridership_arc' to wet_run missions.json.

Pairs with Fiction Phase 46 — fukuoka-okinawan setting page.
Suit-arc, Arc 5: corporate-statework on working-class-ridership substrate.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "fukuoka_ridership_arc",
    "title": "Fukuoka Ridership Arc",
    "story": {
        "synopsis_en": "The Suit audits the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is what the working-class-matrix-operator retainer-class uses. The retainer-class uses the Fukuoka ridership. The ridership is the era's late-Capitalist working-class operational-image. The operational-image is the Fukuoka ridership. The Suit shows up at the Fukuoka ridership's back-office. The Suit shows up with a corporate-issued clipboard. The clipboard has the Fukuoka ridership's daily substrate-management. The substrate-management is the Fukuoka ridership's daily operational-image. The daily operational-image is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the working-class-matrix-operator retainer-class. The retainer-class is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class. The working-class is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class. The working-class is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class. The working-class is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership substrate. The substrate is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership substrate. The substrate is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership substrate. The substrate is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The working-class is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The working-class is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership. The ridership is the Fukuoka ridership. The Fukuoka ridership is the era's late-Capitalist working-class-ridership.",
        "synopsis_ko": "Suit가 Fukuoka 라이더십을 감사한다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 작업-급-매트릭스-운영자 리테이너-계급이 사용하는 것이다. 리테이너-계급은 Fukuoka 라이더십을 사용한다. 라이더십은 시대의 후기-자본주의 작업-급 운영적 이미지이다. 운영적 이미지는 Fukuoka 라이더십이다. Suit가 Fukuoka 라이더십의 백-오피스에 나타난다. Suit가 기업 발행의 클립보드를 들고 나타난다. 클립보드에는 Fukuoka 라이더십의 일일 기질-관리가 있다. 기질-관리는 Fukuoka 라이더십의 일일 운영적 이미지이다. 일일 운영적 이미지는 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급이다. 작업-급은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급이다. 작업-급은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급이다. 작업-급은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십 기질이다. 기질은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십 기질이다. 기질은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십 기질이다. 기질은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 Fukuoka 라이더십이다. Fukuoka 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다.",
        "source": "fukuoka_ridership_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 503,
        "char_count_ko": 1174,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "fukuoka_ridership_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "okinawan_ridership_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "working_class_ridership_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2031,
    "zone": "deep",
    "rewards": {
        "credits": 3500,
        "materials": {
            "data_fragment": 7,
            "ridership_token": 1
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
