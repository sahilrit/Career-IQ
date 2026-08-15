"""careeros_dashboard: the Dashboard / SaaS Control Center.

The product UI over the platform: a main dashboard (opportunities,
applications, interviews, offers, freelance leads, clients, revenue,
network, pending tasks), an opportunity page, and a Career Brain
manager (experience, skills, projects, achievements, preferences,
goals, portfolio). Run with ``streamlit run src/careeros_dashboard/app.py``.
"""

from careeros_dashboard.data_access import (
    DEFAULT_DATA_DIR,
    DashboardSummary,
    build_dashboard_summary,
    list_applications,
    list_pending_client_acquisition_tasks,
    list_upcoming_interviews,
    open_store,
    primary_brain,
)
from careeros_dashboard.exceptions import DashboardError

__all__ = [
    "DEFAULT_DATA_DIR",
    "DashboardError",
    "DashboardSummary",
    "build_dashboard_summary",
    "list_applications",
    "list_pending_client_acquisition_tasks",
    "list_upcoming_interviews",
    "open_store",
    "primary_brain",
]
