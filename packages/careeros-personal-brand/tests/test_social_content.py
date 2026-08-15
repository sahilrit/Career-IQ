"""Tests for render_linkedin_post / render_x_thread / render_blog_post."""

from __future__ import annotations

from careeros_personal_brand import (
    generate_case_study,
    render_blog_post,
    render_linkedin_post,
    render_x_thread,
)


def test_linkedin_post_mentions_title_and_result(brain, project):
    case_study = generate_case_study(brain, project)
    post = render_linkedin_post(case_study)
    assert case_study.title in post
    assert case_study.result in post


def test_x_thread_returns_multiple_tweets_within_length_limit(brain, project):
    case_study = generate_case_study(brain, project)
    thread = render_x_thread(case_study)
    assert len(thread) > 1
    assert all(len(tweet) <= 280 for tweet in thread)


def test_x_thread_truncates_overly_long_tweets(brain, project):
    case_study = generate_case_study(brain, project)
    long_case_study = case_study.model_copy(update={"approach": "x" * 400})
    thread = render_x_thread(long_case_study)
    assert all(len(tweet) <= 280 for tweet in thread)
    assert any(tweet.endswith("…") for tweet in thread)


def test_blog_post_includes_headed_sections(brain, project):
    case_study = generate_case_study(brain, project)
    post = render_blog_post(case_study)
    assert "## The Problem" in post
    assert "## The Approach" in post
    assert "## The Result" in post
