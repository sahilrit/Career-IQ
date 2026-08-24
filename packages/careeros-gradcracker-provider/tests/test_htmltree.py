"""Tests for the minimal HTML tree parser, independent of Gradcracker's
domain shapes."""

from __future__ import annotations

from careeros_gradcracker_provider.htmltree import parse_html


def test_find_first_locates_a_nested_tag():
    root = parse_html("<div><section><h2>Title</h2></section></div>")
    node = root.find_first("h2")
    assert node is not None
    assert node.text() == "Title"


def test_find_first_returns_none_when_absent():
    root = parse_html("<div>hello</div>")
    assert root.find_first("h2") is None


def test_find_all_finds_every_match_in_document_order():
    root = parse_html("<dl><dt>A</dt><dd>1</dd><dt>B</dt><dd>2</dd></dl>")
    dts = root.find_all("dt")
    assert [n.text() for n in dts] == ["A", "B"]


def test_attrs_are_captured():
    root = parse_html('<a href="/x" data-id="9">link</a>')
    node = root.find_first("a")
    assert node is not None
    assert node.attrs["href"] == "/x"
    assert node.attrs["data-id"] == "9"


def test_void_elements_do_not_swallow_following_siblings():
    """<img> has no closing tag; a naive stack-based parser that pushes it
    would misparse everything after it as the image's child."""
    root = parse_html('<figure><img src="x.png" alt="Acme"><a href="/y">Acme</a></figure>')
    figure = root.find_first("figure")
    assert figure is not None
    assert len(figure.children) == 2
    img, anchor = figure.children
    assert img.tag == "img"
    assert anchor.tag == "a"


def test_self_closing_tag_syntax_is_also_handled():
    root = parse_html('<figure><img src="x.png" alt="Acme" /></figure>')
    img = root.find_first("img")
    assert img is not None
    assert img.attrs["alt"] == "Acme"


def test_text_collapses_whitespace_across_nested_elements():
    root = parse_html("<div>\n  Hello   <b>world</b>\n</div>")
    assert root.find_first("div").text() == "Hello world"


def test_an_unclosed_tag_does_not_raise():
    # Real-world HTML sometimes omits a closing </dd>; this must degrade
    # gracefully rather than crash the whole parse.
    root = parse_html("<dl><dt>Salary</dt><dd>£30k<dt>Location</dt><dd>Leeds</dd></dl>")
    assert [n.text() for n in root.find_all("dt")] == ["Salary", "Location"]


def test_empty_input_produces_an_empty_tree():
    root = parse_html("")
    assert root.children == []


def test_malformed_input_does_not_raise():
    parse_html("<div><a href=")  # must not raise
