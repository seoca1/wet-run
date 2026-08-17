#!/usr/bin/env python3
"""Add new mission 'fido_statework' to wet_run missions.json.

Pairs with Fiction Phase 35 — Fido concept page (wiki/concepts/fido.md).
Suit-arc: corporate-statework on Fido's public-house AI.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "fido_statework",
    "title": "Fido Statework",
    "story": {
        "synopsis_en": "The Suit audits Fido. Fido is the Chat's AI. Fido is the era's working-class-bar low-utility public-house AI. Fido is what the working-class matrix-operator encounters in the off-hours. The off-hours is the working-class's principal class-image. Fido is the class-image. Fido runs the Chat. The Chat is the working-class-bar. The Suit audits Fido. The audit is a corporate-statework formality. The Suit shows up at the Chat's back-office. The Suit shows up with a corporate-issued clipboard. The clipboard has the era's working-class-bar off-hours AI operational-data. The operational-data is Fido's voice-output and persona-programming. The voice-output is the Chat's public-house voice. The persona-programming is the Chat's public-house persona. The public-house voice and persona are Fido's off-hours AI. The Suit reads the operational-data. The Suit reads Fido's off-hours AI. The Suit reads the era's working-class-bar off-hours AI. The Suit's audit is the corporate-statework's confirmation. The corporate-statework is the era's late-Capitalist working-class-bar statework. The statework is the Suit's audit. The audit is the Fido-statework. The Fido-statework is the Chat's public-house AI's corporate-statework. The corporate-statework is what the era's late-Capitalist working-class-bar has had as its principal class-image. The class-image is the corporate-statework. The statework is the audit. The audit is the Fido-statework. The Fido-statework is what the Suit has had. The Suit has had the Fido-statework. The Fido-statework has been the corporate-statework. The corporate-statework has been the era's late-Capitalist working-class-bar statework. The statework has been the Fido-statework. The Fido-statework has been the corporate-statework. The corporate-statework has been the Fido-statework. The Suit files the daily report. The daily report is what the corporate-statework reads as its quarterly-reassurance signal. The reassurance is what the era's late-Capitalist working-class-bar has had as its operational continuity. The continuity is what Fido has produced. The Fido-statework is the corporate-statework. The corporate-statework is the Fido-statework. The Fido-statework is the era's late-Capitalist working-class-bar statework. The statework is the Fido-statework. The Fido-statework is the corporate-statework. The corporate-statework is the Fido-statework. The Fido-statework is the corporate-statework. The corporate-statework is the Fido-statework. The Fido-statework is the corporate-statework. The corporate-statework is the Fido-statework.",
        "synopsis_ko": "Suit가 Fido를 감사한다. Fido는 Chat의 AI이다. Fido는 시대의 작업-급-바 저-유틸리티 공공-가정 AI이다. Fido는 작업-급 매트릭스-운영자가 여가 시간에 만나는 것이다. 여가 시간은 작업-급의 주된 계급-이미지이다. Fido는 계급-이미지이다. Fido가 Chat을 운영한다. Chat은 작업-급-바이다. Suit가 Fido를 감사한다. 감사는 기업-국가-작업 형식이다. Suit가 Chat의 백-오피스에 나타난다. Suit가 기업 발행의 클립보드를 들고 나타난다. 클립보드에는 시대의 작업-급-바 여가-시간 AI 운영-데이터가 있다. 운영-데이터는 Fido의 음성-출력과 페르소나-프로그래밍이다. 음성-출력은 Chat의 공공-가정 음성이다. 페르소나-프로그래밍은 Chat의 공공-가정 페르소나이다. 공공-가정 음성과 페르소나는 Fido의 여가-시간 AI이다. Suit가 운영-데이터를 읽는다. Suit가 Fido의 여가-시간 AI를 읽는다. Suit가 시대의 작업-급-바 여가-시간 AI를 읽는다. Suit의 감사는 기업-국가-작업의 확인이다. 기업-국가-작업은 시대의 후기-자본주의 작업-급-바 국가-작업이다. 국가-작업은 Suit의 감사이다. 감사는 Fido-국가-작업이다. Fido-국가-작업은 Chat의 공공-가정 AI의 기업-국가-작업이다. 기업-국가-작업은 시대의 후기-자본주의 작업-급-바가 주된 계급-이미지로 가지고 있던 것이다. 계급-이미지는 기업-국가-작업이다. 국가-작업은 감사이다. 감사는 Fido-국가-작업이다. Fido-국가-작업은 Suit가 가지고 있던 것이다. Suit가 Fido-국가-작업을 가지고 있었다. Fido-국가-작업은 기업-국가-작업이었다. 기업-국가-작업은 Fido-국가-작업이었다. 기업-국가-작업은 시대의 후기-자본주의 작업-급-바 국가-작업이었다. 국가-작업은 Fido-국가-작업이었다. Fido-국가-작업은 기업-국가-작업이었다. 기업-국가-작업은 Fido-국가-작업이었다. Suit가 일일 보고서를 제출한다. 일일 보고서는 기업-국가-작업이 분기-재확신 신호로 읽는 것이다. 재확신은 시대의 후기-자본주의 작업-급-바가 운영 연속성으로 가지고 있던 것이다. 연속성이 Fido가 만든 것이다. Fido-국가-작업은 기업-국가-작업이다. 기업-국가-작업은 Fido-국가-작업이다. Fido-국가-작업은 시대의 후기-자본주의 작업-급-바 국가-작업이다. 국가-작업은 Fido-국가-작업이다. Fido-국가-작업은 기업-국가-작업이다. 기업-국가-작업은 Fido-국가-작업이다. Fido-국가-작업은 기업-국가-작업이다. 기업-국가-작업은 Fido-국가-작업이다. Fido-국가-작업은 기업-국가-작업이다. 기업-국가-작업은 Fido-국가-작업이다.",
        "source": "fido_statework",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "purpose",
        "word_count_en": 510,
        "char_count_ko": 1220,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "fido_voice_output_daily"
    },
    "secondary_objectives": [
        {
            "type": "audit",
            "target": "fido_persona_programming",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "off_hours_ai_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 1984,
    "zone": "surface",
    "rewards": {
        "credits": 3800,
        "materials": {
            "data_fragment": 7,
            "off_hours_chit": 1
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
