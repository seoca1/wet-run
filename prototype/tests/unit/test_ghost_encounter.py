"""Tests for the ghost_encounter stage (v0.5 expansion)."""

from __future__ import annotations

from wet_run.ghost_encounter import (
    GHOST_CATALOG,
    GhostChoice,
    get_for_zone,
)


class TestGhostCatalog:
    def test_nonempty(self) -> None:
        assert len(GHOST_CATALOG) >= 1, "Should have at least 1 ghost encounter"

    def test_all_have_required_fields(self) -> None:
        for gid, ghost in GHOST_CATALOG.items():
            assert ghost.id == gid
            assert ghost.name_en
            assert ghost.name_ko
            assert ghost.zone_requirement in {"SURFACE", "MID", "DEEP", "CORE", "TA"}
            assert len(ghost.ascii_art) >= 3, "Ghost should have ASCII portrait"
            assert ghost.dialogue_en
            assert ghost.dialogue_ko

    def test_morrison_exists(self) -> None:
        assert "loa.morrison" in GHOST_CATALOG
        morrison = GHOST_CATALOG["loa.morrison"]
        assert morrison.fragment_id == "fragment.morrison_echo"
        assert ("voodoo", 5) in morrison.faction_rep_delta


class TestGetForZone:
    def test_deep_zone_has_morrison(self) -> None:
        ghosts = get_for_zone("DEEP")
        ids = {g.id for g in ghosts}
        assert "loa.morrison" in ids, "DEEP should include Morrison"

    def test_surface_zone_empty(self) -> None:
        ghosts = get_for_zone("SURFACE")
        assert all(g.zone_requirement == "SURFACE" for g in ghosts), (
            "Surface only has surface ghosts"
        )

    def test_unknown_zone_falls_back(self) -> None:
        # Unknown zone names default to SURFACE
        ghosts = get_for_zone("UNKNOWN")
        assert ghosts == [] or all(g.zone_requirement == "SURFACE" for g in ghosts)

    def test_ta_zone_includes_all(self) -> None:
        """TA is the deepest zone; should include all ghosts available at lower zones."""
        ghosts = get_for_zone("TA")
        ghost_ids = {g.id for g in ghosts}
        # TA should include at least the same ghosts as CORE (since TA >= CORE)
        core_ghosts = {g.id for g in get_for_zone("CORE")}
        assert core_ghosts.issubset(ghost_ids)


class TestGhostChoice:
    def test_choices_distinct(self) -> None:
        assert GhostChoice.TALK != GhostChoice.FIGHT
        assert GhostChoice.TALK != GhostChoice.LEAVE
        assert GhostChoice.FIGHT != GhostChoice.LEAVE

    def test_choice_values(self) -> None:
        assert GhostChoice.TALK.value == "talk"
        assert GhostChoice.FIGHT.value == "fight"
        assert GhostChoice.LEAVE.value == "leave"
