#!/usr/bin/env python
"""Probe every configured ATS board and report which ones actually answer.

This is what keeps ``careeros_ats_providers.boards`` honest: a slug that no
longer resolves is removed from the registry rather than left in hopefully,
because a board that always fails costs a request on every single search and
shows up as a permanent error in the per-source list.

    uv run python scripts/verify_ats_boards.py            # all ATSes
    uv run python scripts/verify_ats_boards.py greenhouse # one

Exit code is 0 even when boards fail — this is a report, not a gate.
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

from careeros_ats_providers import ADAPTER_CLASSES, AtsHttp
from careeros_ats_providers import __init__ as _pkg  # noqa: F401  (keeps import explicit)
from careeros_ats_providers.__init__ import _BOARD_LOADERS


def probe(args) -> tuple[str, str, int, str]:
    ats_id, adapter, entry, http = args
    try:
        jobs = adapter.fetch_board(entry, http)
    except Exception as exc:
        return ats_id, entry.slug, -1, str(exc)[:120]
    return ats_id, entry.slug, len(jobs), ""


def main() -> int:
    wanted = sys.argv[1:] or list(ADAPTER_CLASSES)
    http = AtsHttp(timeout=25.0)
    tasks = []
    for ats_id in wanted:
        if ats_id not in ADAPTER_CLASSES:
            print(f"unknown ATS: {ats_id}", file=sys.stderr)
            return 2
        adapter = ADAPTER_CLASSES[ats_id]()
        for entry in _BOARD_LOADERS[ats_id]():
            tasks.append((ats_id, adapter, entry, http))

    if not tasks:
        print("no boards configured")
        return 0

    live: dict[str, list[tuple[str, int]]] = {}
    dead: dict[str, list[tuple[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for ats_id, slug, count, error in pool.map(probe, tasks):
            if count >= 0:
                live.setdefault(ats_id, []).append((slug, count))
            else:
                dead.setdefault(ats_id, []).append((slug, error))

    total_jobs = 0
    for ats_id in wanted:
        ok = sorted(live.get(ats_id, []))
        bad = sorted(dead.get(ats_id, []))
        jobs = sum(c for _, c in ok)
        total_jobs += jobs
        print(f"\n=== {ats_id}: {len(ok)} live / {len(ok) + len(bad)} boards, {jobs} postings ===")
        for slug, count in ok:
            flag = "  (empty)" if count == 0 else ""
            print(f"  ok   {slug:24} {count:5}{flag}")
        for slug, error in bad:
            print(f"  DEAD {slug:24} {error}")
    print(f"\nTOTAL postings reachable: {total_jobs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
