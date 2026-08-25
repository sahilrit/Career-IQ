"""Tests for best_option_index — choosing the right custom-dropdown option."""

from __future__ import annotations

from careeros_browser import best_option_index


def test_exact_match_wins():
    assert best_option_index(["Yes", "No"], "No") == 1
    assert best_option_index(["Yes", "No"], "yes") == 0  # case-insensitive


def test_word_prefix_match():
    # "Yes" should select "Yes, I am authorized to work"
    assert best_option_index(["Yes, I am authorized", "No, I am not"], "Yes") == 0


def test_no_does_not_match_not_authorized():
    # The dangerous case: "No" must NOT latch onto "Not authorized" (starts with
    # the letters n-o but is a different word). No clean match → leave it blank.
    assert best_option_index(["Not authorized to work", "Authorized"], "No") is None


def test_shared_words_match_longer_labels():
    idx = best_option_index(
        ["I need visa sponsorship", "I do not need sponsorship"],
        "I need visa sponsorship now",
    )
    assert idx == 0


def test_country_substring_match():
    options = ["United Kingdom", "United States", "United Arab Emirates"]
    assert best_option_index(options, "United States") == 1


def test_short_answer_never_substring_guesses():
    # "IN" (India's code) must not substring-match "Indiana" or "Singapore".
    assert best_option_index(["Indiana", "Singapore", "Finland"], "IN") is None


def test_no_match_returns_none():
    assert best_option_index(["Red", "Green", "Blue"], "Yellow") is None


def test_empty_inputs_return_none():
    assert best_option_index([], "Yes") is None
    assert best_option_index(["Yes"], "") is None


def test_ties_break_toward_shortest_option():
    # Both start with "Remote"; the plain "Remote" is the more specific choice.
    assert best_option_index(["Remote (anywhere)", "Remote"], "Remote") == 1
