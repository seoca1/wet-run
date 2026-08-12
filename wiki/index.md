# Roguelike Sprawl

> 🌆 깁슨 스프롤 3부작 세계관의 사이버펑크 로그라이크

플레이어는 console cowboy가 되어 사이버스페이스에서 ICE를 뚫고 임무를 수행한다.
깁슨 톤 (cold, detached, cinematic) — 한 줄, 단편, atmospheric.

## 둘러보기

- 🎮 **[게임 대시보드](https://seoca1.github.io/roguelike-sprawl/)** — 5개 대시보드 (Story, Stages, Combat, Equipment, Cyberspace)
- 📖 **[GitHub 저장소](https://github.com/seoca1/roguelike-sprawl)** — 소스 코드, 이슈, 릴리스
- 🌐 **세계관 위키** — 사이버스페이스, Faction, Glossary, Style Guide
- ⚙️ **디자인 노트** — GDD, Pillars, 시스템 명세
- 📋 **결정 기록** — 60+ ADR (libtcod, RT-MS 전투, Faction Reputation 등)
- 🗺️ **[[ROADMAP]]** — Phase 1~10 (Phase 7 완료, Phase 10 작업 중)
- 🔧 **[[IMPROVEMENTS]]** — 누적 개선 아이디어

## 세계관 위키 (world/)

게임 세계관의 요약/적응 위키. **Primary source**는 `../../../../Fiction/wiki/` (깁슨 분석 wiki).

| 페이지 | 주제 | Primary Source |
|---|---|---|
| [[cyberspace]] | 사이버스페이스 / 매트릭스 | `../../../../Fiction/wiki/settings/cyberspace.md` |
| [factions](world/factions.md) | Faction (Tessier-Ashpool, Yakuza 등) | `../../../../Fiction/wiki/works/neuromancer.md` |
| [glossary](world/glossary.md) | 용어집 (ICE, deck, construct 등) | `../../../../Fiction/wiki/works/` |
| [style_guide](world/style_guide.md) | 글쓰기 스타일 가이드 | `../../../../Fiction/wiki/authors/william-gibson.md` |
| [sprawl_universe](world/sprawl_universe.md) | Sprawl 세계관 개요 | `../../../../Fiction/wiki/works/` |
| [derivative_stories](world/derivative_stories.md) | 2차 창작 단편 목록 | (자체 작성) |
| [boss_ice_reference](world/boss-ice-reference.md) | 5개 보스 ICE 프로필 + Phase B-3 기능 | (Phase B-3) |
| [cross-project-integration](world/cross-project-integration.md) | Fiction ↔ roguelike_sprawl 양방향 통합 | (Phase α-J) |

> **경고**: Fiction wiki (`../../../../Fiction/wiki/`)는 이 프로젝트의 **읽기 전용** primary source입니다. 절대 수정하지 마세요.

## 메모리 조각 (lore/)

게임 진행 중 발견하는 ambient lore 단편 (ADR-0140, Engagement Layer Phase 1). 25% 확률로 Matrix node 진입 시 `>>> Memory fragment recovered: [title]` 표시 후 `wiki/lore/` 에 영구 저장. 손실 없는 collection 동기.

- [Memory Fragments — Sprawl 지성체 회수 기록](lore/README.md) — 메커니즘 + 카테고리 (Signal Echo / Construct Cache / Anomaly Log / Dead Channel)

> 4개 fragment 파일 (`memory_anomaly_log_01`, `memory_construct_cache_01`, `memory_dead_channel_01`, `memory_signal_echo_01`)은 **in-game discovery 전용** — 의도적으로 index 미노출. 자키가 직접 회수해야 wiki에 등장.

## 라이선스

본 프로젝트는 [MIT License](../LICENSE) 하에 공개됩니다.
깁슨 원작 (Neuromancer, Count Zero, Mona Lisa Overdrive)은 William Gibson의 저작물입니다.
이 프로젝트는 fan project이며 깁슨 원작의 어떤 텍스트도 포함하지 않습니다.

## 기여

이슈 / PR 환영. 깁슨 톤 자키 커뮤니티의 참여를 기다립니다.