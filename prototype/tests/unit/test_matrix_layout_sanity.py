"""Sanity test: generated matrices fit within the screen bounds.

Validates the layout used by the matrix screen (80x50).
"""

from __future__ import annotations

from wet_run.engine.matrix_view import BOX_HEIGHT, BOX_WIDTH
from wet_run.matrix import MatrixGenerator, compute_layout

SCREEN_W = 80
SCREEN_H = 50
MARGIN_X = 2
MARGIN_Y = 2


def _fits_in_screen(layout: dict[str, tuple[int, int]]) -> bool:
    for col, row in layout.values():
        if col < MARGIN_X or col + BOX_WIDTH > SCREEN_W - MARGIN_X:
            return False
        if row < MARGIN_Y or row + BOX_HEIGHT > SCREEN_H - MARGIN_Y:
            return False
    return True


def test_generated_graphs_fit_in_screen() -> None:
    gen = MatrixGenerator()
    for seed in (1, 7, 42, 99, 256, 1337, 65535):
        g = gen.generate(seed=seed, mission_grade=1)
        layout = compute_layout(g)
        assert _fits_in_screen(layout), (
            f"seed={seed}: layout {layout} does not fit in {SCREEN_W}x{SCREEN_H}"
        )
