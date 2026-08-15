"""Social content rendering: LinkedIn post, X thread, and blog post, all
derived deterministically from a CaseStudy. Each output respects the
real platform constraint it targets — an X thread's tweets are kept
under the real 280-character limit.
"""

from __future__ import annotations

from careeros_personal_brand.case_study import CaseStudy

_X_TWEET_MAX_CHARS = 280


def render_linkedin_post(case_study: CaseStudy) -> str:
    lines = [
        f"Just wrapped up {case_study.title}.",
        "",
        f"The problem: {case_study.problem}",
        f"The approach: {case_study.approach}",
        f"The result: {case_study.result}",
        "",
        "Always happy to talk shop about this one.",
    ]
    return "\n".join(lines) + "\n"


def render_x_thread(case_study: CaseStudy) -> list[str]:
    tweets = [
        f"{case_study.title} 🧵",
        f"The problem: {case_study.problem}",
        f"The approach: {case_study.approach}",
        f"The result: {case_study.result}",
    ]
    return [_truncate(tweet, _X_TWEET_MAX_CHARS) for tweet in tweets]


def render_blog_post(case_study: CaseStudy) -> str:
    lines = [
        f"# {case_study.title}",
        "",
        "## The Problem",
        "",
        case_study.problem,
        "",
        "## The Approach",
        "",
        case_study.approach,
        "",
        "## The Result",
        "",
        case_study.result,
    ]
    return "\n".join(lines) + "\n"


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"
