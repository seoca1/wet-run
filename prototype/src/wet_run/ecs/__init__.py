"""ECS-lite: Entity, World, Components (ADR-0004, ADR-0194).

**Status (ADR-0194)**: 선택적 도구 — dungeon/room 도메인에서만 사용 권장.

Production systems (`engine/state.py`, `combat/*`, `missions/*`, etc.)
use OOP/dataclass. ECS-lite is reserved for `matrix/` + `engine/dungeon_view.py`
where Entity = room mapping is natural.

Tests + demos (`tests/unit/test_ecs.py`, `tests/unit/test_dungeon_ecs.py`,
`scripts/play_ecs_dungeon.py`, `scripts/play_arc_bsp.py`) preserved as
experimental reference for future expansion.
"""
