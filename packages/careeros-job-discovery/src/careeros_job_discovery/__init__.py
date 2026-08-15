"""careeros_job_discovery: the end-to-end pipeline turning job postings
into scored Applications on a user's Career Brain, with events published
at every step.
"""

from careeros_job_discovery.pipeline import JobDiscoveryPipeline
from careeros_job_discovery.scoring import score_posting

__all__ = ["JobDiscoveryPipeline", "score_posting"]
