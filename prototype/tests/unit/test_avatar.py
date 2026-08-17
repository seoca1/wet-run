"""Unit tests for the Jockey Avatar system (ADR-0016)."""

from __future__ import annotations


class TestAvatarHead:
    """Head shape changes with HP percentage."""

    def test_full_hp_renders_green_eyes(self) -> None:
        """100% HP shows ◉P◉ (full integrity)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(hp=100, max_hp=100, ppl=10, zdr=5)
        rendered = render_avatar_lines(state)
        head = rendered.lines[0][0]
        assert "◉P◉" in head
        assert "X" not in head

    def test_mid_hp_renders_tilted(self) -> None:
        """50% HP shows tilted head (◉P/)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(hp=50, max_hp=100, ppl=10, zdr=10)
        rendered = render_avatar_lines(state)
        head = rendered.lines[0][0]
        assert "/" in head

    def test_low_hp_renders_damaged(self) -> None:
        """25% HP shows damaged head (◉Px)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(hp=20, max_hp=100, ppl=5, zdr=15)
        rendered = render_avatar_lines(state)
        head = rendered.lines[0][0]
        assert "x" in head

    def test_zero_hp_renders_x_flatline(self) -> None:
        """0% HP shows X (flatline)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(hp=0, max_hp=100, ppl=10, zdr=5)
        rendered = render_avatar_lines(state)
        head = rendered.lines[0][0]
        assert "X" in head


class TestAvatarStatus:
    """Status pose changes with PPL/ZDR ratio."""

    def test_safe_status_upright(self) -> None:
        """PPL >> ZDR shows upright body."""
        from wet_run.avatar import Status, build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(hp=100, max_hp=100, ppl=20, zdr=5)
        assert state.status is Status.SAFE
        rendered = render_avatar_lines(state)
        # SAFE has full body
        assert "/|\\" in rendered.lines[1][0]

    def test_deadly_status_crouched(self) -> None:
        """PPL << ZDR shows crouched body."""
        from wet_run.avatar import Status, build_avatar_state

        state = build_avatar_state(hp=50, max_hp=100, ppl=5, zdr=20)
        assert state.status in (Status.DEADLY, Status.FUTILE)

    def test_futile_status_at_zero_hp(self) -> None:
        """0 HP forces FUTILE status regardless of PPL/ZDR."""
        from wet_run.avatar import Status, build_avatar_state

        state = build_avatar_state(hp=0, max_hp=100, ppl=20, zdr=5)
        assert state.status is Status.FUTILE


class TestAvatarPrograms:
    """Program arm slots render by tier and state."""

    def test_t5_renders_starred(self) -> None:
        """T5 program shows ★W★."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            programs=[("wisp", 5, False)],
        )
        rendered = render_avatar_lines(state)
        prog_line = rendered.lines[2][0]
        assert "★" in prog_line
        assert "W" in prog_line

    def test_t1_renders_faded(self) -> None:
        """T1 program shows ·W·."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            programs=[("hammer", 1, False)],
        )
        rendered = render_avatar_lines(state)
        prog_line = rendered.lines[2][0]
        assert "·" in prog_line

    def test_depleted_renders_tilde(self) -> None:
        """Depleted program shows ~W~."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            programs=[("shield", 3, True)],
        )
        rendered = render_avatar_lines(state)
        prog_line = rendered.lines[2][0]
        assert "~" in prog_line

    def test_empty_slot_renders_locked(self) -> None:
        """Empty program slot (tier=0) shows ═══ (locked)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            programs=[],
        )
        rendered = render_avatar_lines(state)
        prog_line = rendered.lines[2][0]
        # 3 empty slots = 3 ═══ markers
        assert prog_line.count("═══") == 3


class TestAvatarDeck:
    """Deck (torso) renders tier."""

    def test_deck_tier_4(self) -> None:
        """T4 deck shows ║DK4║."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            deck_tier=4,
        )
        rendered = render_avatar_lines(state)
        deck_line = rendered.lines[4][0]
        assert "DK4" in deck_line

    def test_deck_no_tier(self) -> None:
        """T0 deck shows ║X║ (broken)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            deck_tier=0,
        )
        rendered = render_avatar_lines(state)
        deck_line = rendered.lines[4][0]
        assert "X" in deck_line


class TestAvatarWetware:
    """Wetware (legs) renders tier as filled cells."""

    def test_t3_wetware_has_3_cells(self) -> None:
        """T3 wetware shows 3 ▓ cells."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            wetware_tier=3,
        )
        rendered = render_avatar_lines(state)
        leg_line = rendered.lines[5][0]
        assert leg_line.count("▓") == 3

    def test_t5_wetware_has_5_cells(self) -> None:
        """T5 wetware shows 5 ▓ cells."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            wetware_tier=5,
        )
        rendered = render_avatar_lines(state)
        leg_line = rendered.lines[5][0]
        assert leg_line.count("▓") == 5


class TestAvatarConstruct:
    """Construct companion echo renders when present."""

    def test_dixie_construct(self) -> None:
        """Dixie construct shows ◆D◆."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            construct_id="dixie",
        )
        rendered = render_avatar_lines(state)
        # Construct is line 6 (optional)
        construct_line = rendered.lines[-1][0]
        assert "◆D◆" in construct_line

    def test_no_construct_omits_line(self) -> None:
        """No construct does not add a line."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            construct_id=None,
        )
        rendered = render_avatar_lines(state)
        # Without construct: 6 lines (head, shoulders, programs, hips, deck, legs)
        assert len(rendered.lines) == 6

    def test_with_construct_adds_line(self) -> None:
        """With construct: 7 lines."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            construct_id="dixie",
        )
        rendered = render_avatar_lines(state)
        assert len(rendered.lines) == 7


class TestAvatarIntegration:
    """Integration scenarios from design spec."""

    def test_full_loadout(self) -> None:
        """PPL 25, HP 100% — full loadout example from spec."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=25,
            zdr=2,
            programs=[("wisp", 5, False), ("hammer", 2, False), ("probe", 3, False)],
            deck_tier=4,
            wetware_tier=4,
            construct_id="dixie",
        )
        rendered = render_avatar_lines(state)
        # Head: full
        assert "◉P◉" in rendered.lines[0][0]
        # Programs: 3 visible
        assert "★" in rendered.lines[2][0]  # T5 starred
        # Deck
        assert "DK4" in rendered.lines[4][0]
        # Wetware
        assert rendered.lines[5][0].count("▓") == 4
        # Construct
        assert "◆D◆" in rendered.lines[6][0]

    def test_damaged_50pct(self) -> None:
        """50% HP, TOUGH status — damaged example from spec."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=50,
            max_hp=100,
            ppl=25,
            zdr=20,
            programs=[("wisp", 1, True), ("hammer", 2, False), ("probe", 3, False)],
            deck_tier=4,
            wetware_tier=4,
            construct_id="dixie",
        )
        rendered = render_avatar_lines(state)
        # Head: tilted
        assert "/" in rendered.lines[0][0]
        # Programs: depleted first slot
        assert "~" in rendered.lines[2][0]

    def test_critical_25pct_with_lost_program(self) -> None:
        """25% HP, 1 program lost, DEADLY status."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=25,
            max_hp=100,
            ppl=17,
            zdr=30,
            programs=[("hammer", 2, False), ("probe", 3, False)],  # wisp LOST
            deck_tier=4,
            wetware_tier=4,
            construct_id="dixie",
        )
        rendered = render_avatar_lines(state)
        # Head: critical
        assert "x" in rendered.lines[0][0]

    def test_dead_avatar_has_x_head(self) -> None:
        """Death shows X head (flatline)."""
        from wet_run.avatar import build_avatar_state
        from wet_run.avatar.renderer import render_avatar_lines

        state = build_avatar_state(
            hp=0,
            max_hp=100,
            ppl=25,
            zdr=20,
            programs=[("wisp", 5, False), ("hammer", 2, False), ("probe", 3, False)],
            deck_tier=4,
            wetware_tier=4,
            construct_id="dixie",
        )
        rendered = render_avatar_lines(state)
        # Head: X
        assert "X" in rendered.lines[0][0]


class TestAvatarStateProperties:
    """AvatarState property tests."""

    def test_hp_pct_full(self) -> None:
        """100% HP returns 1.0."""
        from wet_run.avatar import build_avatar_state

        state = build_avatar_state(hp=100, max_hp=100, ppl=10, zdr=5)
        assert state.hp_pct == 1.0

    def test_hp_pct_half(self) -> None:
        """50% HP returns 0.5."""
        from wet_run.avatar import build_avatar_state

        state = build_avatar_state(hp=50, max_hp=100, ppl=10, zdr=5)
        assert state.hp_pct == 0.5

    def test_hp_pct_zero_max(self) -> None:
        """max_hp=0 returns 0.0 (avoids div by zero)."""
        from wet_run.avatar import build_avatar_state

        state = build_avatar_state(hp=0, max_hp=0, ppl=10, zdr=5)
        assert state.hp_pct == 0.0

    def test_hp_clamped_to_one(self) -> None:
        """HP > max_hp clamped to 1.0."""
        from wet_run.avatar import build_avatar_state

        state = build_avatar_state(hp=150, max_hp=100, ppl=10, zdr=5)
        assert state.hp_pct == 1.0

    def test_is_dead_at_zero(self) -> None:
        """is_dead True at 0 HP."""
        from wet_run.avatar import build_avatar_state

        state = build_avatar_state(hp=0, max_hp=100, ppl=10, zdr=5)
        assert state.is_dead is True

    def test_is_dead_false_at_positive_hp(self) -> None:
        """is_dead False at positive HP."""
        from wet_run.avatar import build_avatar_state

        state = build_avatar_state(hp=1, max_hp=100, ppl=10, zdr=5)
        assert state.is_dead is False
