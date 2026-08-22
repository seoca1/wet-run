"""BSP tree partitioning helpers for the procedural dungeon generator.

Pure functions operating on :class:`_BspNode` / :class:`_BspRoom` trees:

    bsp_partition  — recursively split a region until leaves are small enough.
    place_rooms    — place one room inside each leaf with padding for corridors.
    collect_leaves — walk the BSP and collect every leaf (depth-first, pre-order).

These were originally methods of
:class:`wet_run.matrix.dungeon_generator.procedural.ProceduralDungeonGenerator`;
factored into this sub-module per ADR-0110 (≤ 500 LOC per module).

Originally part of ``matrix/dungeon_generator.py`` (862 LOC).
"""

from __future__ import annotations

import random

from .models import _BspNode, _BspRoom


def bsp_partition(
    rng: random.Random,
    min_leaf_size: int,
    x: int,
    y: int,
    w: int,
    h: int,
) -> _BspNode:
    """Recursively split a region until leaves are small enough.

    Args:
        rng: RNG used to choose split orientation and cut position.
        min_leaf_size: Minimum dimension for a leaf; smaller regions stop splitting.
        x: region left.
        y: region top.
        w: region width.
        h: region height.

    Returns:
        A :class:`_BspNode` (root of the partition tree).  Leaves have
        ``left is None and right is None``.
    """
    node = _BspNode(x=x, y=y, w=w, h=h)

    # Stop splitting when region is too small to split further.
    # We need a minimum leaf size that, minus room padding, still
    # leaves room for a 1x1 actual room and a corridor on each side.
    min_size = min_leaf_size
    if w < min_size * 2 and h < min_size * 2:
        # Cannot split — leaf
        return node

    # Pick a split orientation that is feasible.  A split is feasible
    # when the chosen dimension is at least 2*min_size so both halves
    # satisfy the leaf threshold.
    can_vertical = w >= 2 * min_size
    can_horizontal = h >= 2 * min_size
    if not can_vertical and not can_horizontal:
        return node  # leaf — neither dim allows a split

    # Prefer vertical when clearly wider, horizontal when clearly taller,
    # otherwise choose at random among feasible options.
    if can_vertical and (not can_horizontal or w >= h * 1.25):
        split_vertical = True
    elif can_horizontal and (not can_vertical or h > w * 1.25):
        split_vertical = False
    else:
        split_vertical = rng.random() < 0.5

    if split_vertical:
        # Vertical split: choose cut between min_size and w-min_size.
        cut_min = min_size
        cut_max = w - min_size
        cut = rng.randint(cut_min, cut_max)
        left_w = cut
        right_w = w - cut
        node.left = bsp_partition(rng, min_leaf_size, x, y, left_w, h)
        node.right = bsp_partition(rng, min_leaf_size, x + cut, y, right_w, h)
    else:
        cut_min = min_size
        cut_max = h - min_size
        cut = rng.randint(cut_min, cut_max)
        top_h = cut
        bottom_h = h - cut
        node.left = bsp_partition(rng, min_leaf_size, x, y, w, top_h)
        node.right = bsp_partition(rng, min_leaf_size, x, y + cut, w, bottom_h)
    return node


def place_rooms(
    rng: random.Random,
    room_padding: int,
    node: _BspNode,
    counter: list[int] | None = None,
) -> int:
    """Place one room inside each leaf.  Returns next room counter.

    Args:
        rng: RNG used for room size and position jitter.
        room_padding: Border reserved for corridors on every side.
        node: BSP partition root to traverse.
        counter: Mutable single-element list holding the next room id index;
            pass ``None`` (default) to start a new sequence at 0.

    Returns:
        The next free room counter value (== number of rooms placed).
    """
    if counter is None:
        counter = [0]
    if node.is_leaf:
        padding = room_padding
        # Room must fit inside the region with padding for corridors.
        max_w = max(1, node.w - 2 * padding)
        max_h = max(1, node.h - 2 * padding)
        # Bias toward slightly larger rooms for visual readability.
        room_w = max(1, min(max_w, rng.randint(2, max(2, max_w))))
        room_h = max(1, min(max_h, rng.randint(2, max(2, max_h))))
        # Position room inside the region, leaving padding on sides.
        rx_min = node.x + padding
        rx_max = node.x + node.w - padding - room_w
        ry_min = node.y + padding
        ry_max = node.y + node.h - padding - room_h
        rx = rx_min if rx_max <= rx_min else rng.randint(rx_min, rx_max)
        ry = ry_min if ry_max <= ry_min else rng.randint(ry_min, ry_max)
        node.room = _BspRoom(
            x=rx,
            y=ry,
            w=room_w,
            h=room_h,
            room_id=f"r{counter[0]}",
        )
        counter[0] += 1
        return counter[0]
    # Internal node — recurse
    if node.left is not None:
        counter[0] = place_rooms(rng, room_padding, node.left, counter)
    if node.right is not None:
        counter[0] = place_rooms(rng, room_padding, node.right, counter)
    return counter[0]


def collect_leaves(
    node: _BspNode,
    out: list[_BspNode] | None = None,
) -> list[_BspNode]:
    """Walk BSP and collect every leaf node (depth-first, pre-order)."""
    if out is None:
        out = []
    if node.is_leaf:
        out.append(node)
    else:
        if node.left is not None:
            collect_leaves(node.left, out)
        if node.right is not None:
            collect_leaves(node.right, out)
    return out


__all__ = ["bsp_partition", "place_rooms", "collect_leaves"]
