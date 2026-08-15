"""Small, generic result-aggregation helpers for parallel capability calls."""

from __future__ import annotations

from collections.abc import Callable, Hashable


def flatten[T](results: list[list[T]]) -> list[T]:
    return [item for sublist in results for item in sublist]


def flatten_and_dedupe[T, K: Hashable](results: list[list[T]], *, key: Callable[[T], K]) -> list[T]:
    seen: set[K] = set()
    unique: list[T] = []
    for item in flatten(results):
        item_key = key(item)
        if item_key in seen:
            continue
        seen.add(item_key)
        unique.append(item)
    return unique
