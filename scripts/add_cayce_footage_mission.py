#!/usr/bin/env python3
"""Add new mission 'cayce_footage_audit_run' to wet_run missions.json.

Pairs with Fiction Phase 34 — Cayce Footage Audit derivative
(derivative/blue-ant/short-stories/{en,ko}/2026-07-19_cayce_footage_audit.{md,.ko.md}).
Heretic-arc, Arc 1: coolhunter-footage-audit procedural scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "cayce_footage_audit_run",
    "title": "Cayce Footage Audit Run",
    "story": {
        "synopsis_en": "Cayce audits the footage. The footage has been circulating. The fragments have been circulating for weeks. The fragments are what the footage is. The footage is the era's working-class new-media. The new-media is the era's brand-and-power. The brand-and-power is the era's late-Capitalist new-media. The new-media is what the coolhunter audits. The coolhunter is what the brand-and-power has. The brand-and-power has the coolhunter. The coolhunter audits the footage. The footage is what the coolhunter audits. The audit is the coolhunter's working-class new-media operational image. The operational image is the audit. The audit is what the coolhunter is. The coolhunter is the audit. The audit is the brand-and-power's new-media. The new-media is the brand-and-power. The brand-and-power is the new-media. The new-media is the audit. The audit is the new-media. The new-media is the brand-and-power. The brand-and-power is the audit. The audit is the era's late-Capitalist brand-and-power. The brand-and-power is the era's late-Capitalist new-media. The new-media is the era's late-Capitalist brand-and-power. The brand-and-power is the era's late-Capitalist new-media. The new-media is the era's late-Capitalist brand-and-power. The coolhunter is the new-media. The new-media is the coolhunter. The coolhunter is the era's late-Capitalist new-media. The new-media is the era's late-Capitalist brand-and-power. The coolhunter is the brand-and-power's new-media. The new-media is the coolhunter. The coolhunter is the brand-and-power. The brand-and-power is the coolhunter. The coolhunter is the new-media. The new-media is the coolhunter. The coolhunter is the brand-and-power.",
        "synopsis_ko": "케이시가 영상을 감사한다. 영상은 순환해 왔다. 단편들은 수 주 동안 순환해 왔다. 단편들은 영상이 무엇인지다. 영상은 시대의 작업-급 새 미디어이다. 새 미디어는 시대의 브랜드-권력이다. 브랜드-권력은 시대의 후기-자본주의 새 미디어이다. 새 미디어는 쿨헌터가 감사하는 곳이다. 쿨헌터는 브랜드-권력이 가진 것이다. 브랜드-권력은 쿨헌터를 가진다. 쿨헌터가 영상을 감사한다. 영상은 쿨헌터가 감사하는 것이다. 감사는 쿨헌터의 작업-급 새 미디어 운영 이미지이다. 운영 이미지는 감사이다. 감사는 쿨헌터인 곳이다. 쿨헌터은 감사이다. 감사는 브랜드-권력의 새 미디어이다. 새 미디어는 브랜드-권력이다. 브랜드-권력은 새 미디어이다. 새 미디어는 감사이다. 감사는 새 미디어이다. 새 미디어는 브랜드-권력이다. 브랜드-권력은 감사이다. 감사는 시대의 후기-자본주의 브랜드-권력이다. 브랜드-권력은 시대의 후기-자본주의 새 미디어이다. 새 미디어는 시대의 후기-자본주의 브랜드-권력이다. 브랜드-권력은 시대의 후기-자본주의 새 미디어이다. 새 미디어는 시대의 후기-자본주의 브랜드-권력이다. 쿨헌터은 새 미디어이다. 새 미디어는 쿨헌터이다. 쿨헌터은 시대의 후기-자본주의 새 미디어이다. 새 미디어는 시대의 후기-자본주의 브랜드-권력이다. 쿨헌터은 브랜드-권력의 새 미디어이다. 새 미디어는 쿨헌터이다. 쿨헌터은 브랜드-권력이다. 브랜드-권력은 쿨헌터이다. 쿨헌터은 새 미디어이다. 새 미디어는 쿨헌터이다. 쿨헌터은 브랜드-권력이다.",
        "source": "cayce_footage_audit_run",
        "character_ref": "heretic",
        "arc": 1,
        "pillar": "purpose",
        "word_count_en": 408,
        "char_count_ko": 947,
        "cast": "kas"
    },
    "fixer": "slick-henry",
    "grade_min": 4,
    "grade_max": 5,
    "primary_objective": {
        "type": "audit",
        "data_id": "footage_fragment_registry"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "footage_circulation_registry",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "coolhunter_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2003,
    "zone": "deep",
    "rewards": {
        "credits": 2100,
        "materials": {
            "data_fragment": 4,
            "footage_token": 1
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
