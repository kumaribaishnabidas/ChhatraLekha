"""API routers."""

from app.api import (
    anomalies,
    auth,
    consent,
    dashboard,
    institutions,
    reports,
    students,
    verify,
)

ALL_ROUTERS = [
    auth.router,
    students.router,
    institutions.router,
    anomalies.router,
    verify.router,
    consent.router,
    reports.router,
    dashboard.router,
]
