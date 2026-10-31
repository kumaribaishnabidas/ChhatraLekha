"""API routers."""

from app.api import (
    anomalies,
    auth,
    consent,
    corrections,
    dashboard,
    institutions,
    me,
    reports,
    students,
    tokens,
    verify,
)

ALL_ROUTERS = [
    auth.router,
    me.router,
    students.router,
    institutions.router,
    anomalies.router,
    verify.router,
    consent.router,
    reports.router,
    dashboard.router,
    corrections.router,
    tokens.router,
]
