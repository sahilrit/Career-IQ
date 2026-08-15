"""careeros_job_agent: the autonomous opportunity-discovery loop —
Career Brain -> Discovery -> Matching -> Scoring -> Prioritization -> Action.
"""

from careeros_job_agent.agent import JobAgent
from careeros_job_agent.policy import QualificationPolicy
from careeros_job_agent.scheduling import DEFAULT_JOB_NAME, register_job_agent

__all__ = ["DEFAULT_JOB_NAME", "JobAgent", "QualificationPolicy", "register_job_agent"]
