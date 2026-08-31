"""Every ATS adapter, keyed by its id."""

from careeros_ats_providers.adapters.ashby import AshbyAdapter
from careeros_ats_providers.adapters.bamboohr import BambooHrAdapter
from careeros_ats_providers.adapters.greenhouse import GreenhouseAdapter
from careeros_ats_providers.adapters.lever import LeverAdapter
from careeros_ats_providers.adapters.personio import PersonioAdapter
from careeros_ats_providers.adapters.recruitee import RecruiteeAdapter
from careeros_ats_providers.adapters.smartrecruiters import SmartRecruitersAdapter
from careeros_ats_providers.adapters.workable import WorkableAdapter
from careeros_ats_providers.adapters.workday import WorkdayAdapter

ADAPTER_CLASSES = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "ashby": AshbyAdapter,
    "smartrecruiters": SmartRecruitersAdapter,
    "workable": WorkableAdapter,
    "recruitee": RecruiteeAdapter,
    "personio": PersonioAdapter,
    "bamboohr": BambooHrAdapter,
    "workday": WorkdayAdapter,
}

__all__ = [
    "ADAPTER_CLASSES",
    "AshbyAdapter",
    "BambooHrAdapter",
    "GreenhouseAdapter",
    "LeverAdapter",
    "PersonioAdapter",
    "RecruiteeAdapter",
    "SmartRecruitersAdapter",
    "WorkableAdapter",
    "WorkdayAdapter",
]
