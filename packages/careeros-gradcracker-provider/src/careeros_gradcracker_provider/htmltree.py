"""A minimal HTML-to-tree parser, stdlib only.

Gradcracker's job cards mix nested markup (an image's ``alt`` inside a
``figure``) with label/value pairs (``<dt>Salary</dt><dd>...</dd>``) that
a flat sub-selector map can't express — the same reason the LinkedIn and
Adzuna providers reach for a custom parser instead of a generic HTML
library. Building a small real tree (rather than flat event handling)
makes the dt/dd pairing in ``parser.py`` straightforward: read a ``<dl>``
node's direct children in order.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from html.parser import HTMLParser

# Void elements never receive a matching end tag, so they must not be
# pushed onto the open-element stack or every following sibling would be
# misparsed as their child.
_VOID_TAGS = frozenset(
    {"img", "br", "hr", "input", "meta", "link", "source", "col", "area", "base"}
)


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)

    def find_first(self, tag: str) -> Node | None:
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    return child
                found = child.find_first(tag)
                if found is not None:
                    return found
        return None

    def find_all(self, tag: str) -> list[Node]:
        results: list[Node] = []
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    results.append(child)
                results.extend(child.find_all(tag))
        return results

    def text(self) -> str:
        parts: list[str] = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return " ".join(" ".join(parts).split())


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node(tag="#root")
        self._stack: list[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag=tag, attrs={k: v or "" for k, v in attrs})
        self._stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # e.g. <img .../> — same as a start tag that never opens.
        node = Node(tag=tag, attrs={k: v or "" for k, v in attrs})
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        # Pop back to (and including) the matching open tag, tolerating HTML
        # that never closes something like a stray <dd> — real-world markup
        # is not always well-formed, and this must never raise over it.
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._stack[-1].children.append(data)


def parse_html(html: str) -> Node:
    """Parse a fragment into a tree rooted at a synthetic ``#root`` node.

    Never raises — malformed input just produces whatever tree the parser
    managed to build before giving up, same tolerance stdlib
    ``html.parser`` itself has for bad markup.
    """
    builder = _TreeBuilder()
    with suppress(Exception):  # a parse failure yields a partial tree, not a crash
        builder.feed(html)
    return builder.root
