"""Frames: the part of a page that a selector cannot reach.

A CSS selector is scoped to one document. An ``<iframe>`` is a *different*
document, so ``page.fill("#email")`` cannot see a field inside one no matter
how correct the selector is — which is why an application form rendered in an
iframe looks, to every layer above, exactly like a page with no form on it.

The fix is not a cleverer selector. It is being able to say which document you
are talking to. ``BrowserSession.frame(...)`` returns another
``BrowserSession`` scoped to a frame, so every existing caller — form
detection, field mapping, filling, read-back validation — works inside a frame
without knowing frames exist. Nesting falls out of the same idea: a frame
session can hand back one of its own children.

Deliberately generic. Nothing here knows what an application form is, and
nothing here mentions a specific ATS.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameHandle:
    """One frame on the page, as something a caller can identify and pick.

    ``url`` is the frame's own document URL — the only reliably meaningful
    thing about most frames, since ``name`` is usually empty and the element
    selector is a property of the *parent* document rather than of the frame.
    """

    #: Position in this listing. Stable for one listing, not across reloads.
    index: int
    #: The frame's document URL ("" for a src-less, script-written frame).
    url: str = ""
    #: The frame element's name/id attribute, when it has one.
    name: str = ""
    #: Depth below the session that listed it: 1 for a direct child.
    depth: int = 1

    def matches(self, *, url_contains: str | None = None, name: str | None = None) -> bool:
        if url_contains is not None and url_contains.lower() not in (self.url or "").lower():
            return False
        return not (name is not None and name != self.name)

    def describe(self) -> str:
        label = self.name or "(unnamed)"
        return f"frame[{self.index}] {label} depth={self.depth} url={self.url or '(no url)'}"
