#!/usr/bin/env python3
"""Add new mission 'finn_factory_labour_run' to wet_run missions.json."""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "finn_factory_labour_run",
    "title": "Finn's Factory Labour Run",
    "story": {
        "synopsis_en": "The Suit audits the Finn's labor market every quarter. The audit is a statework formality. The Suit shows up at the Finn's Cheap Hotel bar with a corporate-issued clipboard. The clipboard has seventeen names. The Suit reads the names that the working-class matrix-operators have been matched with for the past quarter. The Suit reads seventeen working-class matrix-operator matches. The matches are the working-class-matrix-labor market's daily processing. Seventeen is the matched-operative count that the Suit's clipboard has registered for two years. Seventeen is the Finn's labor-market throughput. Seventeen is the working-class matrix-labor market's daily operational image. The Suit's quarterly audit is the corporate-statework's confirmation. The corporate-statework is what the era's late-Capitalist working-class-matrix-labor market has had as its industrial-class operational continuation. The Finn's labor market is what the working-class-matrix-labor market's operational image has been. The Finn's labor market is what the era's late-Capitalist working-class-matrix-labor market has had as its standard operational image. The Suit's quarterly audit is the corporate-statework's most-arcanely-technocratic work. The Suit, in this run, has done the corporate-statework's most-arcanely-technocratic work. The Suit's working-day is the Finn's labor-market. The Suit gets paid. The Suit goes home. The Finn's labor market continues. The working-class-matrix-labor market's operational continuation continues. The audit is the matching. The matching is the Finn's factory-labor. The factory-labor is what the working-class matrix-labor market has had as its principal operational image. The operational image is the era's late-Capitalist working-class matrix-labor market's standard operating procedure. The procedure is what the Finn matches for. The matching is what the Finn's factory-labor is. The factory-labor is what the Finn's labor-market is for. The labor-market is what the working-class-matrix-labor market has had as its standard operating image. The image is what the working-class-matrix-labor market has produced as its operational image. The operational image is what the Suit has been auditing. The audit is the corporate-statework's quarterly-reassurance signal. The signal is what the corporate-statework has had as its operational confirmation. The confirmation is what the Suit's audit produces. The Suit produces the audit. The audit produces the signal. The signal produces the corporate-statework's confirmation. The confirmation is what the era's late-Capitalist working-class-matrix-labor market has had as its industrial-class operational continuation. The continuation is what the Suit's audit has confirmed. The confirmation is what the working-class-matrix-labor market has had. The labor market has had the operational image. The image is what the Finn's labor market is. The labor market is what the working-class-matrix-labor market has been for nineteen years. The nineteen years is the Finn's factory-labor. The factory-labor is what the working-class-matrix-labor market has been. The market has been the operational. The operational is the era. The era is late-Capitalist. The late-Capitalist is the Suit. The Suit is the audit. The audit is the corporate-statework. The corporate-statework is the working-class matrix-labor market. The market is the Finn. The Finn is the factory-labor. The factory-labor is the matching. The matching is the era.",
        "synopsis_ko": "Suit는 매 분기 핀의 노동 시장을 감사한다. 감사는 국가-작업 형식이다. Suit가 핀의 싼 호텔 바로 기업 발행의 클립보드를 들고 나타난다. 클립보드에는 17 개의 이름이 있다. Suit는 이름을 읽는다. Suit는 지난 분기 동안 작업-급 매트릭스 운영자가 매치된 이름들을 읽는다. Suit는 17 개의 작업-급 매트릭스-운영자 매치를 읽는다. 매치는 작업-급-매트릭스-노동 시장의 일일 처리다. 17 은 Suit의 클립보드가 등록한 매치-운영자 수다. Suit의 클립보드는 2 년 동안 분기당 17 개의 매치를 등록해 왔다. 17 은 핀의 노동-시장 처리량이다. 17 은 작업-급 매트릭스-노동 시장의 일일 운영적 이미지다. Suit의 분기 감사는 기업-국가-작업의 확인이다. 기업-국가-작업은 시대의 후기-자본주의 작업-급-매트릭스-노동 시장이 산업-급 운영 연속성으로 가지고 있던 것이다. 핀의 노동 시장은 작업-급-매트릭스-노동 시장의 운영적 이미지로 가지고 있던 것이다. 핀의 노동 시장은 시대의 후기-자본주의 작업-급-매트릭스-노동 시장이 표준 운영적 이미지로 가지고 있던 것이다. Suit의 분기 감사는 기업-국가-작업의 가장-신비롭게-기술관료적인 작업이다. Suit는 이번 런에서 기업-국가-작업의 가장-신비롭게-기술관료적인 작업을 했다. Suit의 작업-일은 핀의 노동-시장이다. Suit는 급여를 받는다. Suit는 집에 간다. 핀의 노동 시장이 계속된다. 작업-급-매트릭스-노동 시장의 운영 연속성이 계속된다. 감사는 매칭이다. 매칭은 핀의 공장-노동이다. 공장-노동이 작업-급 매트릭스-노동 시장이 주된 운영적 이미지로 가지고 있던 것이다.",
        "source": "finn_factory_labour_run",
        "character_ref": "suit",
        "arc": 2,
        "pillar": "purpose",
        "word_count_en": 412,
        "char_count_ko": 988,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 4,
    "grade_max": 5,
    "primary_objective": {
        "type": "audit",
        "data_id": "finn_labor_market_throughput"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "finn_match_registry",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "labor_market_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 1984,
    "zone": "surface",
    "rewards": {
        "credits": 2400,
        "materials": {
            "data_fragment": 5,
            "audit_chit": 1
        }
    },
    "arc": 2
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
