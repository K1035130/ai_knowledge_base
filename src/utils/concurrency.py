"""Shared fan-out helper for the project's I/O-bound API calls (embedding batches, monthly highlights)."""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def map_ordered(fn: Callable[[T], R], items: Iterable[T], max_workers: int) -> list[R]:
    """Run `fn` over `items` concurrently and return the results in the original order.

    Threads rather than processes: every caller here spends its time waiting on an HTTP round
    trip, so the GIL is irrelevant and process overhead would only hurt.

    Executor.map is what makes this safe to drop in: it yields results in submission order no
    matter which call finishes first, so each result stays matched to its input -- the invariant
    that quietly breaks if you reach for as_completed instead. It also re-raises the first
    exception, so a call that exhausted its retries aborts the whole fan-out rather than leaving
    a hole in the results.
    """
    items = list(items)
    if len(items) <= 1:  # no thread pool worth building
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as pool:
        return list(pool.map(fn, items))
