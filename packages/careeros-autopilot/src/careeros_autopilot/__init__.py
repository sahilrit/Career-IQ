"""careeros_autopilot: the fully autonomous apply loop, composed from the
platform's existing discovery, authorization, browser, and handoff
machinery plus live form detection."""

from careeros_autopilot.cycle import RUN_ENTITY_TYPE, list_autopilot_runs, run_autopilot_cycle
from careeros_autopilot.page_analysis import (
    CAPTCHA_DETECTORS,
    DEFAULT_PROBLEM_DETECTORS,
    LOGIN_WALL_DETECTORS,
    ApplicationRoute,
    FormLocation,
    PreparationResult,
    classify_route,
    detect_form_mapping,
    detect_submit_selector,
    find_apply_url,
    locate_form,
    prepare_application,
    prepare_application_page,
)
from careeros_autopilot.readiness import (
    ApplicationReadiness,
    ApplicationRecommendation,
    assess_readiness,
)
from careeros_autopilot.resume_file import write_resume_pdf

__all__ = [
    "CAPTCHA_DETECTORS",
    "DEFAULT_PROBLEM_DETECTORS",
    "LOGIN_WALL_DETECTORS",
    "RUN_ENTITY_TYPE",
    "ApplicationReadiness",
    "ApplicationRecommendation",
    "ApplicationRoute",
    "FormLocation",
    "PreparationResult",
    "assess_readiness",
    "classify_route",
    "detect_form_mapping",
    "detect_submit_selector",
    "find_apply_url",
    "list_autopilot_runs",
    "locate_form",
    "prepare_application",
    "prepare_application_page",
    "run_autopilot_cycle",
    "write_resume_pdf",
]
