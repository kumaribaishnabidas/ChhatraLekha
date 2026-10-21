"""Repository layer: every MongoDB read and write lives here.

The routers never touch a collection directly. Keeping the query patterns in
one place makes the index strategy reviewable and keeps the routers thin.
"""

from app.repositories.anomalies import AnomalyRepository
from app.repositories.audit import AuditRepository
from app.repositories.consents import ConsentRepository
from app.repositories.institutions import InstitutionRepository
from app.repositories.programmes import ProgrammeRepository
from app.repositories.students import StudentRepository
from app.repositories.submissions import SubmissionRepository
from app.repositories.users import UserRepository

__all__ = [
    "AnomalyRepository",
    "AuditRepository",
    "ConsentRepository",
    "InstitutionRepository",
    "ProgrammeRepository",
    "StudentRepository",
    "SubmissionRepository",
    "UserRepository",
]
