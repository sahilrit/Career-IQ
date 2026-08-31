"""Frames: a selector reaches one document, so a frame needs its own session.

The bug this exists to fix: an application form rendered inside an ``<iframe>``
is invisible to every selector on the page, so it looks identical to a page
with no form on it — and got reported as "no fillable form found" rather than
"the form is somewhere this code cannot reach".
"""

from __future__ import annotations

from careeros_browser import FakeBrowserSession, FrameHandle, PlaywrightBrowserSession


class FakeFrame:
    """The slice of Playwright's ``Frame`` surface this layer uses."""

    def __init__(self, url="", name="", parent=None, children=None):
        self.url = url
        self.name = name
        self._parent = parent
        self.child_frames = children or []
        self.filled: dict[str, str] = {}
        self.values: dict[str, str] = {}
        self.visible: set[str] = set()

    def parent_frame(self):
        return self._parent

    def fill(self, selector, value):
        self.filled[selector] = value
        self.values[selector] = value

    def input_value(self, selector):
        return self.values.get(selector, "")

    def is_visible(self, selector):
        return selector in self.visible

    def query_selector_all(self, selector):
        return []

    def query_selector(self, selector):
        return None


class FakeElement:
    def __init__(self, frame):
        self._frame = frame

    def content_frame(self):
        return self._frame


class FakePage:
    def __init__(self, main, others):
        self.main_frame = main
        self.frames = [main, *others]
        self.url = "https://example.test/job"
        self._elements: dict[str, FakeElement] = {}
        self.filled: dict[str, str] = {}
        self.visible: set[str] = set()

    def register_iframe(self, selector, frame):
        self._elements[selector] = FakeElement(frame)

    def query_selector(self, selector):
        return self._elements.get(selector)

    def fill(self, selector, value):
        self.filled[selector] = value

    def is_visible(self, selector):
        return selector in self.visible


class TestPlaywrightFrames:
    def build(self):
        main = FakeFrame(url="https://example.test/job")
        inner = FakeFrame(url="https://apply.example.test/form", name="applyFrame", parent=main)
        nested = FakeFrame(url="https://apply.example.test/upload", parent=inner)
        inner.child_frames = [nested]
        main.child_frames = [inner]
        page = FakePage(main, [inner, nested])
        page.register_iframe("iframe#apply", inner)
        return page, inner, nested

    def test_a_page_with_no_frames_lists_none(self):
        main = FakeFrame(url="https://example.test/job")
        session = PlaywrightBrowserSession(FakePage(main, []))
        assert session.frames() == []
        # And an ordinary page session is not "in" a frame.
        assert session.frame_path == ()

    def test_frames_are_listed_with_url_and_name(self):
        page, _, _ = self.build()
        handles = PlaywrightBrowserSession(page).frames()
        assert [h.url for h in handles] == [
            "https://apply.example.test/form",
            "https://apply.example.test/upload",
        ]
        assert handles[0].name == "applyFrame"
        # The main frame is never listed — you are already in it.
        assert all("example.test/job" not in h.url for h in handles)

    def test_scoping_by_url_fragment(self):
        page, inner, _ = self.build()
        scoped = PlaywrightBrowserSession(page).frame(url_contains="apply.example.test/form")
        assert scoped is not None
        scoped.fill("#email", "a@b.test")
        # The value landed in the FRAME, not on the page.
        assert inner.filled["#email"] == "a@b.test"
        assert page.filled == {}

    def test_scoping_by_frame_name(self):
        page, inner, _ = self.build()
        scoped = PlaywrightBrowserSession(page).frame(name="applyFrame")
        assert scoped is not None
        scoped.fill("#x", "1")
        assert inner.filled == {"#x": "1"}

    def test_scoping_by_the_iframe_elements_selector(self):
        # The only way to pick a specific frame when several share an origin.
        page, inner, _ = self.build()
        scoped = PlaywrightBrowserSession(page).frame(selector="iframe#apply")
        assert scoped is not None
        scoped.fill("#y", "2")
        assert inner.filled == {"#y": "2"}

    def test_no_match_returns_none_rather_than_the_page(self):
        # Silently falling back to the page would fill the wrong document and
        # report success.
        page, _, _ = self.build()
        assert PlaywrightBrowserSession(page).frame(url_contains="nowhere") is None
        assert PlaywrightBrowserSession(page).frame(selector="iframe#missing") is None
        assert PlaywrightBrowserSession(page).frame(index=9) is None

    def test_nested_frames_are_reachable_from_their_parent(self):
        page, _inner, nested = self.build()
        scoped = PlaywrightBrowserSession(page).frame(url_contains="/form")
        assert [h.url for h in scoped.frames()] == ["https://apply.example.test/upload"]
        deep = scoped.frame(url_contains="/upload")
        assert deep is not None
        deep.fill("#deep", "3")
        assert nested.filled == {"#deep": "3"}

    def test_frame_path_records_how_the_frame_was_reached(self):
        page, _, _ = self.build()
        scoped = PlaywrightBrowserSession(page).frame(url_contains="/form")
        deep = scoped.frame(url_contains="/upload")
        # Without this, "the field was not filled" cannot be told apart from
        # "not filled IN THE FRAME WE WERE LOOKING AT".
        assert deep.frame_path == ("url~/form", "url~/upload")

    def test_read_back_reads_the_frames_own_value(self):
        page, _inner, _ = self.build()
        scoped = PlaywrightBrowserSession(page).frame(url_contains="/form")
        scoped.fill("#email", "a@b.test")
        assert scoped.input_value("#email") == "a@b.test"

    def test_a_frame_session_reports_the_frames_url(self):
        page, _, _ = self.build()
        scoped = PlaywrightBrowserSession(page).frame(url_contains="/form")
        assert scoped.current_url == "https://apply.example.test/form"
        # while the page session still reports the page.
        assert PlaywrightBrowserSession(page).current_url == "https://example.test/job"

    def test_page_level_operations_still_work_inside_a_frame(self):
        # A frame has no screenshot/cookies of its own; a frame session must
        # still be able to capture evidence of the page it lives on.
        page, _, _ = self.build()
        captured = {}
        page.screenshot = lambda path, full_page: captured.setdefault("path", path)
        scoped = PlaywrightBrowserSession(page).frame(url_contains="/form")
        scoped.screenshot("/tmp/x.png")
        assert captured["path"] == "/tmp/x.png"


class TestFakeSessionFrames:
    def test_an_ordinary_fake_session_has_no_frames(self):
        assert FakeBrowserSession().frames() == []

    def test_a_frame_is_a_separate_document(self):
        page = FakeBrowserSession()
        page.set_visible("#page-field")
        frame = page.add_frame(url="https://apply.test/form", selector="iframe#apply")
        frame.set_visible("#email")

        # The page cannot see into the frame...
        assert not page.is_visible("#email")
        # ...and the frame does not inherit the page's elements.
        assert not frame.is_visible("#page-field")
        # The <iframe> element itself IS on the page.
        assert page.is_visible("iframe#apply")

    def test_filling_in_a_frame_does_not_touch_the_page(self):
        page = FakeBrowserSession()
        frame = page.add_frame(url="https://apply.test/form")
        scoped = page.frame(url_contains="apply.test")
        scoped.fill("#email", "a@b.test")
        assert frame.field_value("#email") == "a@b.test"
        assert page.field_value("#email") is None

    def test_nested_frames_are_listed_with_their_depth(self):
        page = FakeBrowserSession()
        outer = page.add_frame(url="https://apply.test/form")
        outer.add_frame(url="https://apply.test/upload")
        depths = {h.url: h.depth for h in page.frames()}
        assert depths == {"https://apply.test/form": 1, "https://apply.test/upload": 2}

    def test_lookup_by_selector_and_index(self):
        page = FakeBrowserSession()
        page.add_frame(url="https://ads.test/banner")
        wanted = page.add_frame(url="https://apply.test/form", selector="iframe.apply")
        assert page.frame(selector="iframe.apply") is wanted
        assert page.frame(index=1) is wanted
        assert page.frame(index=5) is None


class TestFrameHandle:
    def test_url_matching_is_case_insensitive(self):
        handle = FrameHandle(index=0, url="https://Apply.Example.test/Form")
        assert handle.matches(url_contains="apply.example")

    def test_describe_is_readable_for_an_unnamed_frame(self):
        assert "(unnamed)" in FrameHandle(index=0, url="https://x.test").describe()


class TestBothImplementationsAgree:
    """The fake and the real session must enumerate and index frames the same
    way, or a test that passes against the fake proves nothing about a browser.

    Playwright's ``page.frames`` is a FLAT list of every frame at any depth, so
    the fake's must be too — otherwise a form in a nested frame is listed by
    ``frames()`` and then unreachable by the index it was listed under, and
    ``locate_form`` silently skips it in production while tests stay green.
    """

    def test_a_nested_frame_is_reachable_by_the_index_it_was_listed_under(self):
        page = FakeBrowserSession()
        outer = page.add_frame(url="https://apply.test/form")
        nested = outer.add_frame(url="https://apply.test/upload")
        nested.set_visible("#deep")

        handles = page.frames()
        deep = next(h for h in handles if h.url.endswith("/upload"))
        scoped = page.frame(index=deep.index)
        assert scoped is not None
        assert scoped.is_visible("#deep")

    def test_every_listed_frame_is_reachable_by_its_index(self):
        page = FakeBrowserSession()
        first = page.add_frame(url="https://a.test/1")
        page.add_frame(url="https://b.test/2")
        first.add_frame(url="https://a.test/nested")

        for handle in page.frames():
            assert page.frame(index=handle.index) is not None, handle.describe()

    def test_lookup_by_url_reaches_a_nested_frame_too(self):
        page = FakeBrowserSession()
        outer = page.add_frame(url="https://apply.test/form")
        outer.add_frame(url="https://apply.test/upload")
        assert page.frame(url_contains="/upload") is not None
