"""Pick the option that best matches a desired answer in a custom dropdown.

Custom (React/ARIA) dropdowns render their choices as free text, not the
tidy ``value`` attributes a native ``<select>`` exposes — so choosing the
right one means matching the answer we want ("No", "Yes", "United States")
against the visible option labels. This is that matcher, kept pure and
browser-free so it can be reasoned about and tested exhaustively.

The bias is deliberately conservative: when nothing matches cleanly it
returns ``None`` so the caller leaves the field blank for a human, rather
than picking a plausible-but-wrong option. A wrong work-authorization or
visa answer is far worse than an unanswered one.
"""

from __future__ import annotations

import re


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text))


def _prefix_word(longer: str, shorter: str) -> bool:
    """``longer`` begins with the whole word(s) ``shorter`` (so "Yes" prefixes
    "Yes, I am authorized" but "No" does NOT prefix "Not authorized")."""
    if not longer.startswith(shorter):
        return False
    return len(longer) == len(shorter) or not longer[len(shorter)].isalnum()


def best_option_index(options: list[str], desired: str) -> int | None:
    """Index of the option best matching ``desired``, or ``None`` if none does.

    Matching, strongest first:
      1. exact (case-insensitive)
      2. one is a whole-word prefix of the other ("Yes" ~ "Yes, authorized")
      3. shared whole words ("Not authorized" ~ "Not authorized to work")
      4. substring — only when ``desired`` is long enough (>=4 chars) to make a
         substring hit meaningful, so a bare "No" never matches "Not sure".
    Ties break toward the shortest option (the most specific label).
    """
    desired_n = desired.strip().lower()
    if not desired_n or not options:
        return None
    norm = [(option or "").strip().lower() for option in options]

    for index, option in enumerate(norm):
        if option and option == desired_n:
            return index

    prefix_hits = [
        index
        for index, option in enumerate(norm)
        if option and (_prefix_word(option, desired_n) or _prefix_word(desired_n, option))
    ]
    if prefix_hits:
        return min(prefix_hits, key=lambda index: len(norm[index]))

    desired_words = _words(desired_n)
    best: tuple[int, int] | None = None  # (shared word count, index)
    for index, option in enumerate(norm):
        shared = len(desired_words & _words(option))
        if shared and (
            best is None
            or shared > best[0]
            or (shared == best[0] and len(option) < len(norm[best[1]]))
        ):
            best = (shared, index)
    if best is not None:
        return best[1]

    if len(desired_n) >= 4:
        substring_hits = [
            index for index, option in enumerate(norm) if option and desired_n in option
        ]
        if substring_hits:
            return min(substring_hits, key=lambda index: len(norm[index]))

    return None
