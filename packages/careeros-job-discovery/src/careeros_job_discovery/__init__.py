"""careeros_job_discovery: the end-to-end pipeline turning job postings
into scored Applications on a user's Career Brain, with events published
at every step.
"""

from careeros_job_discovery.llm_scoring import (
    PATCHABLE_FIELDS,
    JobBrief,
    JobFactPatch,
    LlmJobScorer,
    LlmScoreResult,
    apply_patches,
)
from careeros_job_discovery.pipeline import DiscoveryRun, JobDiscoveryPipeline
from careeros_job_discovery.posting_store import JobPostingRepository
from careeros_job_discovery.scoring import score_posting, skill_gap

__all__ = [
    "PATCHABLE_FIELDS",
    "DiscoveryRun",
    "JobBrief",
    "JobDiscoveryPipeline",
    "JobFactPatch",
    "JobPostingRepository",
    "LlmJobScorer",
    "LlmScoreResult",
    "apply_patches",
    "score_posting",
    "skill_gap",
]
