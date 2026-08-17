"""Sanity tests for the project structure."""

from __future__ import annotations


def test_import_main_package() -> None:
    """The main package can be imported."""
    import wet_run  # noqa: F401

    assert wet_run.__version__ == "0.1.0"


def test_import_subpackages() -> None:
    """All major subpackages can be imported."""
    from wet_run import (
        data,  # noqa: F401
        ecs,  # noqa: F401
        engine,  # noqa: F401
        i18n,  # noqa: F401
        portraits,  # noqa: F401
    )


def test_engine_config_constants() -> None:
    """Engine config exposes the expected constants."""
    from wet_run.engine.config import (
        DEFAULT_LANGUAGE,
        FONT_PATH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
        SCREEN_WIDTH,
    )

    assert SCREEN_WIDTH > 0
    assert SCREEN_HEIGHT > 0
    assert SCREEN_TITLE  # non-empty
    assert DEFAULT_LANGUAGE in ("en", "ko")
    assert FONT_PATH.name.endswith(".png")
