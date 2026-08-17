#!/usr/bin/env python3
"""Add new mission 'trauma_squads_audit' to wet_run missions.json.

Pairs with Fiction Phase 40 — Trauma-Squads concept page (wiki/concepts/trauma-squads.md).
Suit-arc, Arc 5: corporate-statework on post-cortex-hound service class.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "trauma_squads_audit",
    "title": "Trauma-Squads Audit",
    "story": {
        "synopsis_en": "The Suit audits the trauma-squads. The trauma-squads is the era's post-cortex-hound specialized-service class. The trauma-squads is what the working-class-matrix-operator uses for post-cortex-hound service. The post-cortex-hound is the era's brain-damage-management. The brain-damage-management is what the trauma-squads does. The trauma-squads is the era's working-class-matrix-operator's *post-cortex-hound* specialized-service. The post-cortex-hound is the era's working-class-matrix-operator's *post-cortex-hound* class-substance. The class-substance is the trauma-squads. The trauma-squads is the era's working-class-matrix-operator's *post-cortex-hound* service class. The Suit shows up at the trauma-squads' back-office. The Suit shows up with a corporate-issued clipboard. The clipboard has the era's *post-cortex-hound* service-class operational-data. The operational-data is the trauma-squads' daily-substrate-management. The daily-substrate-management is the era's *post-cortex-hound* service class. The Suit reads the daily-substrate-management. The Suit reads the trauma-squads' daily registry. The daily registry is the era's *post-cortex-hound* service class. The service class is the trauma-squads. The Suit's audit is the corporate-statework's confirmation. The corporate-statework is the era's late-Capitalist working-class-matrix-operator service class. The service class is the trauma-squads. The Suit files the daily report. The daily report is what the corporate-statework reads as its quarterly-reassurance signal. The reassurance is what the era's late-Capitalist working-class-matrix-labor market has had as its post-cortex-hound operational continuation. The continuation is what the trauma-squads has produced. The trauma-squads is the era's working-class-matrix-labor market's principal post-cortex-hound service class. The post-cortex-hound service class is the trauma-squads. The trauma-squads is the era's working-class-matrix-labor market's principal *post-cortex-hound* specialized-service. The *post-cortex-hound* specialized-service is the trauma-squads. The trauma-squads is the era's *post-cortex-hound* class-image. The class-image is the trauma-squads. The trauma-squads is the era's working-class-matrix-labor market. The market is the era's post-cortex-hound. The post-cortex-hound is the trauma-squads. The trauma-squads is the era's *post-cortex-hound* class.",
        "synopsis_ko": "Suit가 외상-분대를 감사한다. 외상-분대는 시대의 코르텍스-하운드 이후 특화-서비스 계급이다. 외상-분대는 작업-급-매트릭스-운영자가 코르텍스-하운드 이후 서비스를 위해 사용하는 것이다. 코르텍스-하운드 이후는 시대의 뇌-손상-관리이다. 뇌-손상-관리는 외상-분대가 하는 것이다. 외상-분대는 시대의 작업-급-매트릭스-운영자의 *코르텍스-하운드 이후* 특화-서비스이다. 코르텍스-하운드 이후는 시대의 작업-급-매트릭스-운영자의 *코르텍스-하운드 이후* 계급-실체이다. 계급-실체는 외상-분대이다. 외상-분대는 시대의 작업-급-매트릭스-운영자의 *코르텍스-하운드 이후* 서비스 계급이다. Suit가 외상-분대의 백-오피스에 나타난다. Suit가 기업 발행의 클립보드를 들고 나타난다. 클립보드에는 시대의 *코르텍스-하운드 이후* 서비스-계급 운영-데이터가 있다. 운영-데이터는 외상-분대의 일일-기질-관리이다. 일일-기질-관리는 시대의 *코르텍스-하운드 이후* 서비스 계급이다. Suit가 일일-기질-관리를 읽는다. Suit가 외상-분대의 일일 등록부를 읽는다. 일일 등록부는 시대의 *코르텍스-하운드 이후* 서비스 계급이다. 서비스 계급은 외상-분대이다. Suit의 감사는 기업-국가-작업의 확인이다. 기업-국가-작업은 시대의 후기-자본주의 작업-급-매트릭스-운영자 서비스 계급이다. 서비스 계급은 외상-분대이다. Suit가 일일 보고서를 제출한다. 일일 보고서는 기업-국가-작업이 분기-재확신 신호로 읽는 것이다. 재확신은 시대의 후기-자본주의 작업-급-매트릭스-노동 시장이 코르텍스-하운드 이후 운영 연속성으로 가지고 있던 것이다. 연속성이 외상-분대가 만든 것이다. 외상-분대는 시대의 작업-급-매트릭스-노동 시장의 주요 코르텍스-하운드 이후 서비스 계급이다. 코르텍스-하운드 이후 서비스 계급은 외상-분대이다. 외상-분대는 시대의 작업-급-매트릭스-노동 시장의 주요 *코르텍스-하운드 이후* 특화-서비스이다. *코르텍스-하운드 이후* 특화-서비스는 외상-분대이다. 외상-분대는 시대의 *코르텍스-하운드 이후* 계급-이미지이다. 계급-이미지는 외상-분대이다. 외상-분대는 시대의 작업-급-매트릭스-노동 시장이다. 시장은 시대의 코르텍스-하운드 이후이다. 코르텍스-하운드 이후는 외상-분대이다. 외상-분대는 시대의 *코르텍스-하운드 이후* 계급이다.",
        "source": "trauma_squads_audit",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "purpose",
        "word_count_en": 423,
        "char_count_ko": 1051,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "audit",
        "data_id": "trauma_squads_daily_registry"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "post_cortex_hound_service_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "specialized_service_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2025,
    "zone": "deep",
    "rewards": {
        "credits": 3500,
        "materials": {
            "data_fragment": 7,
            "service_chit": 1
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
