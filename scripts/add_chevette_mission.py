#!/usr/bin/env python3
"""Add new mission 'chevette_nightshift_run' to wet_run missions.json.

Pairs with Fiction Phase 33 — Chevette Nightshift derivative
(derivative/bridge-trilogy/short-stories/{en,ko}/2026-07-19_chevette_nightshift.{md,.ko.md}).

Novice-arc, Arc 1: data-key pick-up mission.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "chevette_nightshift_run",
    "title": "Chevette Nightshift Run",
    "story": {
        "synopsis_en": "Chevette pedals along the bridge. The bridge is what the squatter community lives under. The squatter community is the bridge's working-class. The working-class is the bridge's. Chevette is the working-class. The working-class is the bridge's courier. The courier is Chevette. Chevette is the nightshift. The nightshift is what Chevette is doing. The nightshift is the courier's working-class operational image. The operational image is the data-key pick-up. The data-key is what the corporate-class has been trying to keep. The corporate-class has the data-key. The corporate-class has had the data-key for a long time. The data-key is the corporate-class's keep. The keep is what the corporate-class is doing. The corporate-class is doing the keep. The keep is the data-key. The data-key is in the bag. The bag is on the fixie. The fixie is on the bridge. The bridge is what Chevette is on. Chevette is on the bridge. The bridge is what the data-key is on. The data-key is on the bridge. The bridge is what the data-key is. The data-key is the bridge. The bridge is the data-key. The data-key is the corporate-class. The corporate-class is the data-key. The data-key is the corporate-class. The corporate-class is the bridge. The bridge is the corporate-class. The corporate-class is the bridge. The bridge is the corporate-class. The nightshift is what Chevette is doing. Chevette is doing the nightshift. The nightshift is the data-key. The data-key is the nightshift. The nightshift is the courier. The courier is the nightshift. The nightshift is what the working-class is. The working-class is the nightshift. The nightshift is the working-class. The working-class is the nightshift. The nightshift is the data-key pick-up. The data-key pick-up is what the working-class is. The working-class is the data-key pick-up. The data-key pick-up is what the working-class is doing. The working-class is doing the data-key pick-up. The data-key pick-up is the working-class's operational image. The operational image is what the working-class is. The working-class is the operational image. The operational image is the nightshift. The nightshift is the working-class's operational image. The operational image is the nightshift. The nightshift is the bridge. The bridge is the nightshift. The nightshift is the bridge. The bridge is the nightshift.",
        "synopsis_ko": "셰벳이 브리지를 따라 페달을 밟는다. 브리지는 불법 거주자 공동체가 사는 곳이다. 불법 거주자 공동체는 브리지의 작업-급이다. 작업-급은 브리지의 것이다. 셰벳은 작업-급이다. 작업-급은 브리지의 배달원이다. 배달원은 셰벳이다. 셰벳은 야간 교대이다. 야간 교대는 셰벳이 하는 것이다. 야간 교대는 배달원의 작업-급 운영 이미지이다. 운영 이미지는 데이터-키 픽업이다. 데이터-키는 기업-급이 지키고자 하는 것이다. 기업-급이 데이터-키를 가지고 있다. 기업-급이 한참 동안 데이터-키를 가지고 있다. 데이터-키는 기업-급의 지키는 것이다. 지키는 것이 기업-급이 하는 것이다. 기업-급이 지키는 것을 한다. 지키는 것은 데이터-키이다. 데이터-키는 가방에 있다. 가방은 픽시 위에 있다. 픽시는 브리지 위에 있다. 브리지가 셰벳이 있는 곳이다. 셰벳이 브리지에 있다. 브리지가 데이터-키가 있는 곳이다. 데이터-키가 브리지에 있다. 브리지가 데이터-키인 곳이다. 데이터-키는 브리지이다. 브리지는 데이터-키이다. 데이터-키는 기업-급이다. 기업-급이 데이터-키이다. 데이터-키는 기업-급이다. 기업-급이 브리지이다. 브리지가 기업-급이다. 기업-급이 브리지이다. 야간 교대가 셰벳이 하는 것이다. 셰벳이 야간 교대를 한다. 야간 교대는 데이터-키이다. 데이터-키가 야간 교대이다. 야간 교대가 배달원이다. 배달원이 야간 교대이다. 야간 교대가 작업-급인 곳이다. 작업-급이 야간 교대이다. 야간 교대가 데이터-키 픽업이다. 데이터-키 픽업이 작업-급인 곳이다. 작업-급이 데이터-키 픽업이다. 데이터-키 픽업이 작업-급이 하는 것이다. 작업-급이 데이터-키 픽업을 한다. 데이터-키 픽업이 작업-급의 운영 이미지이다. 운영 이미지가 작업-급인 곳이다. 작업-급이 운영 이미지이다. 운영 이미지가 야간 교대이다. 야간 교대가 작업-급의 운영 이미지이다. 운영 이미지가 야간 교대이다. 야간 교대가 브리지이다. 브리지가 야간 교대이다. 야간 교대가 브리지에 있다. 브리지가 야간 교대이다.",
        "source": "chevette_nightshift_run",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "people",
        "word_count_en": 503,
        "char_count_ko": 1186,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "extract_data",
        "data_id": "data_key_pickup"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "data_key_storage",
            "count": 1
        },
        {
            "type": "deliver",
            "target": "fixie_bag",
            "count": 1
        }
    ],
    "matrix_seed": 193,
    "zone": "surface",
    "rewards": {
        "credits": 400,
        "materials": {
            "data_fragment": 1,
            "data_key": 1
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
