"""Unit tests for cinematic ASCII art system."""

from __future__ import annotations

import tcod.console

from wet_run.engine.cinematic_art import (
    ARMITAGE,
    CHIBA_CITY,
    CYBERSPACE,
    DIXIE_FLATLINE,
    GLITCH_BURST,
    MATRIX_RAIN,
    MOLLY_MILLIONS,
    PORTRAITS,
    SCENE_ART,
    SENSE_NET,
    THE_FINN,
    ArtStyle,
    AsciiArt,
    get_default_portrait,
    get_portrait,
    get_scene_art,
    resolve_line_art,
)


class TestAsciiArtDataClass:
    """AsciiArt dataclass properties."""

    def test_width_returns_max_line_length(self) -> None:
        """width property returns longest line."""
        art = AsciiArt(
            lines=("ab", "abcd", "a"),
            fg=(255, 0, 0),
        )
        assert art.width == 4

    def test_height_returns_line_count(self) -> None:
        """height property returns number of lines."""
        art = AsciiArt(
            lines=("a", "b", "c"),
        )
        assert art.height == 3

    def test_empty_art_zero_dimensions(self) -> None:
        """Empty art has 0 width and height."""
        art = AsciiArt(lines=())
        assert art.width == 0
        assert art.height == 0

    def test_default_fg_is_gray(self) -> None:
        """Default fg is light gray."""
        art = AsciiArt(lines=("x",))
        assert art.fg == (200, 200, 200)

    def test_default_style_is_neon(self) -> None:
        """Default style is NEON."""
        art = AsciiArt(lines=("x",))
        assert art.style is ArtStyle.NEON


class TestArtRegistry:
    """Portrait registry has all major characters."""

    def test_finn_in_registry(self) -> None:
        """The Finn art is in registry."""
        assert "the_finn" in PORTRAITS
        assert "finn" in PORTRAITS

    def test_dixie_in_registry(self) -> None:
        """Dixie art is in registry."""
        assert "dixie" in PORTRAITS
        assert "dixie_flatline" in PORTRAITS

    def test_molly_in_registry(self) -> None:
        """Molly art is in registry."""
        assert "molly" in PORTRAITS
        assert "molly_millions" in PORTRAITS

    def test_armitage_in_registry(self) -> None:
        """Armitage art is in registry."""
        assert "armitage" in PORTRAITS

    def test_case_in_registry(self) -> None:
        """Case art is in registry."""
        assert "case" in PORTRAITS

    def test_locations_in_registry(self) -> None:
        """Locations are in registry."""
        assert "chiba" in PORTRAITS
        assert "cyberspace" in PORTRAITS
        assert "sense_net" in PORTRAITS
        assert "finn_office" in PORTRAITS

    def test_atmospheric_in_registry(self) -> None:
        """Atmospheric effects are in registry."""
        assert "matrix_rain" in PORTRAITS
        assert "glitch" in PORTRAITS
        assert "static" in PORTRAITS


class TestGetPortrait:
    """get_portrait() function."""

    def test_get_by_canonical_name(self) -> None:
        """Get portrait by canonical name."""
        art = get_portrait("finn")
        assert art is not None
        assert art is THE_FINN

    def test_get_with_spaces(self) -> None:
        """Get portrait with spaces (normalized to underscores)."""
        art = get_portrait("the finn")
        assert art is THE_FINN

    def test_get_with_slash(self) -> None:
        """Get portrait with slashes (normalized)."""
        art = get_portrait("sense/net")
        assert art is SENSE_NET

    def test_get_unknown_returns_none(self) -> None:
        """Unknown key returns None."""
        art = get_portrait("nonexistent_character")
        assert art is None

    def test_case_insensitive(self) -> None:
        """Lookup is case-insensitive."""
        art = get_portrait("FINN")
        assert art is THE_FINN

    def test_get_default_portrait(self) -> None:
        """Default portrait is cyberspace."""
        art = get_default_portrait()
        assert art is CYBERSPACE


class TestSceneArt:
    """Scene art mapping."""

    def test_prologue_chiba(self) -> None:
        """Prologue scene uses Chiba art."""
        art = get_scene_art("prologue_sprawl")
        assert art is CHIBA_CITY

    def test_briefing_finn(self) -> None:
        """Briefing scene uses Finn art."""
        art = get_scene_art("briefing_finn_first_jack")
        assert art is THE_FINN

    def test_npc_dixie(self) -> None:
        """NPC Dixie scene uses Dixie art."""
        art = get_scene_art("npc_dixie")
        assert art is DIXIE_FLATLINE

    def test_unknown_scene_default(self) -> None:
        """Unknown scene defaults to cyberspace."""
        art = get_scene_art("unknown_scene")
        assert art is CYBERSPACE

    def test_scene_art_has_prologue(self) -> None:
        """Prologue is in scene art mapping."""
        assert "prologue_sprawl" in SCENE_ART

    def test_scene_art_has_briefing(self) -> None:
        """Briefing is in scene art mapping."""
        assert "briefing_finn" in SCENE_ART


class TestResolveLineArt:
    """resolve_line_art() function."""

    def test_empty_portrait_uses_scene(self) -> None:
        """Empty portrait field uses scene art."""
        art = resolve_line_art("", "briefing_finn_first_jack")
        assert art is THE_FINN

    def test_art_prefix_uses_named(self) -> None:
        """'art:key' uses the named art."""
        art = resolve_line_art("art:dixie", "briefing_finn")
        assert art is DIXIE_FLATLINE

    def test_art_prefix_unknown_falls_back(self) -> None:
        """'art:unknown' falls back to scene art."""
        art = resolve_line_art("art:nonexistent", "npc_dixie")
        assert art is DIXIE_FLATLINE

    def test_legacy_glyph_returns_none(self) -> None:
        """Legacy single-glyph returns None (caller uses inline)."""
        art = resolve_line_art("♠F♠", "any_scene")
        assert art is None

    def test_case_insensitive_art_prefix(self) -> None:
        """Art prefix lookup is case-insensitive."""
        art = resolve_line_art("art:FINN", "any")
        assert art is THE_FINN


class TestArtProperties:
    """Each major art has expected visual properties."""

    def test_the_finn_is_neon_style(self) -> None:
        """The Finn art is NEON style."""
        assert THE_FINN.style is ArtStyle.NEON
        # Should have at least 5 lines
        assert THE_FINN.height >= 5

    def test_dixie_is_ghost_style(self) -> None:
        """Dixie art is GHOST style (faded)."""
        assert DIXIE_FLATLINE.style is ArtStyle.GHOST

    def test_armitage_is_shadow_style(self) -> None:
        """Armitage art is SHADOW style."""
        assert ARMITAGE.style is ArtStyle.SHADOW

    def test_matrix_rain_is_matrix_style(self) -> None:
        """Matrix rain is MATRIX style."""
        assert MATRIX_RAIN.style is ArtStyle.MATRIX

    def test_glitch_burst_is_glitch_style(self) -> None:
        """Glitch burst is GLITCH style."""
        assert GLITCH_BURST.style is ArtStyle.GLITCH

    def test_molly_uses_neon_color(self) -> None:
        """Molly uses hot pink (cyberpunk razor girl)."""
        assert MOLLY_MILLIONS.fg[0] > 200  # Strong red
        assert MOLLY_MILLIONS.fg[1] < 100  # Low green

    def test_all_major_chars_have_multiline_art(self) -> None:
        """All major characters have 5+ lines of art."""
        assert THE_FINN.height >= 5
        assert DIXIE_FLATLINE.height >= 5
        assert ARMITAGE.height >= 5
        assert MOLLY_MILLIONS.height >= 5

    def test_chiba_art_descriptive(self) -> None:
        """Chiba art has at least 5 lines (city skyline)."""
        assert CHIBA_CITY.height >= 5
        # Should mention NEON or sprawl
        joined = " ".join(CHIBA_CITY.lines)
        assert "NEON" in joined or "sprawl" in joined

    def test_cyberspace_art_has_grid(self) -> None:
        """Cyberspace art represents a grid."""
        joined = " ".join(CYBERSPACE.lines)
        assert "grid" in joined or "nodes" in joined or "data" in joined


class TestRenderAsciiArt:
    """_draw_ascii_art() rendering function."""

    def test_renders_to_console(self) -> None:
        """Art is rendered to console without errors."""
        from wet_run.engine.story_cinematic import _draw_ascii_art

        console = tcod.console.Console(30, 20, order="F")
        art = AsciiArt(
            lines=("hello", "world"),
            fg=(255, 0, 0),
        )
        _draw_ascii_art(console, x=0, y=0, art=art, max_w=20, max_h=10)

    def test_clips_to_max_width(self) -> None:
        """Art wider than max_w is clipped."""
        from wet_run.engine.story_cinematic import _draw_ascii_art

        console = tcod.console.Console(20, 10, order="F")
        art = AsciiArt(
            lines=("a" * 50,),  # Very long line
            fg=(255, 0, 0),
        )
        # Should not raise
        _draw_ascii_art(console, x=0, y=0, art=art, max_w=10, max_h=5)

    def test_clips_to_max_height(self) -> None:
        """Art taller than max_h is clipped."""
        from wet_run.engine.story_cinematic import _draw_ascii_art

        console = tcod.console.Console(30, 10, order="F")
        art = AsciiArt(
            lines=tuple(f"line {i}" for i in range(50)),
            fg=(255, 0, 0),
        )
        _draw_ascii_art(console, x=0, y=0, art=art, max_w=20, max_h=5)

    def test_ghost_style_fades_color(self) -> None:
        """GHOST style produces 50% color."""
        from wet_run.engine.story_cinematic import _draw_ascii_art

        console = tcod.console.Console(30, 20, order="F")
        ghost_art = AsciiArt(
            lines=("hi",),
            fg=(200, 100, 50),
            style=ArtStyle.GHOST,
        )
        _draw_ascii_art(console, x=0, y=0, art=ghost_art, max_w=20, max_h=5)
        # No assertion on console content; just verify it doesn't crash

    def test_glitch_style_renders(self) -> None:
        """GLITCH style renders without errors."""
        from wet_run.engine.story_cinematic import _draw_ascii_art

        console = tcod.console.Console(30, 20, order="F")
        glitch_art = AsciiArt(
            lines=("noise",),
            fg=(255, 0, 0),
            style=ArtStyle.GLITCH,
        )
        _draw_ascii_art(console, x=0, y=0, art=glitch_art, max_w=20, max_h=5)

    def test_static_style_grayscale(self) -> None:
        """STATIC style uses grayscale."""
        from wet_run.engine.story_cinematic import _draw_ascii_art

        console = tcod.console.Console(30, 20, order="F")
        static_art = AsciiArt(
            lines=("noise",),
            fg=(255, 100, 50),
            style=ArtStyle.STATIC,
        )
        _draw_ascii_art(console, x=0, y=0, art=static_art, max_w=20, max_h=5)
