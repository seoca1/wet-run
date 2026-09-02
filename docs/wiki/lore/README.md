# Memory Fragments — Sprawl 지성체 회수 기록

> **ADR-0140 §Proposal 2** (Engagement Layer Phase 1).
> 게임 진행 중 발견하는 ambient lore 단편. 손실 없는 collection 동기.

## 발견 메커니즘

- Matrix node 진입 시 25% 확률로 ambient transmission 발생
- 발견 시 status message 표시: `>>> Memory fragment recovered: [title]`
- 회수된 fragment 는 `wiki/lore/memory_<id>.md` 에 영구 저장
- 메타: `data/lore/encounter_table.json` (per-zone 가중치)
- per-run 한도: 5~8 fragments (ADR-0140 세부 결정)

## 카테고리 (Pillar 정합)

| 카테고리 | 예시 | 의도 |
|---|---|---|
| **Signal Echo** | 과거 자키 trace echo | ghost-in-the-machine 톤 |
| **Construct Cache** | faction-aligned data fragment | Pillar 4 (unlock) |
| **Anomaly Log** | 비정상 matrix 패턴 | exploration 동기 |
| **Dead Channel** | 격리된 construct memory | 깁슨 "dead channel" |

## Primary source

깁슨 원작의 tone 만 차용 — *원문 인용은 Fiction wiki 참조*.
게임 측 lore fragment 는 *amplification* (확장/변형)으로 자키의 경험에 맞춤.

## 인덱스

- `memory_signal_echo_01.md` — 첫 잭인 잔향
- `memory_construct_cache_01.md` — Hosaka construct 잔재
- `memory_anomaly_log_01.md` — T-A 구역 이상 신호
- `memory_dead_channel_01.md` — 격리된 channel 기록

> **Phase 1 초기**: 4 fragments 만. v1.1.0 cycle 에서 점진적 확장.