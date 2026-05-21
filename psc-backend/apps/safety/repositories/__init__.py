"""Safety data-access package."""

from .base import BaseRepository
from .exceptions import (
    AnonymityMaskError,
    PhaseTransitionError,
    SPDeadlockError,
    SPExecutionError,
    SPParameterError,
    SPTimeoutError,
)

__all__ = [
    "AnonymityMaskError",
    "BaseRepository",
    "CMSRepository",
    "FindingRepository",
    "IncidentRepository",
    "PhaseTransitionError",
    "PurchaseRepository",
    "ReportingRepository",
    "SCMRepository",
    "SOIRepository",
    "SPDeadlockError",
    "SPExecutionError",
    "SPParameterError",
    "SPTimeoutError",
    "WRHRepository",
]


def __getattr__(name: str):
    if name == "CMSRepository":
        from .cms_repo import CMSRepository

        return CMSRepository
    if name == "FindingRepository":
        from .finding_repo import FindingRepository

        return FindingRepository
    if name == "IncidentRepository":
        from .incident_repo import IncidentRepository

        return IncidentRepository
    if name == "PurchaseRepository":
        from .purchase_repo import PurchaseRepository

        return PurchaseRepository
    if name == "ReportingRepository":
        from .reporting_repo import ReportingRepository

        return ReportingRepository
    if name == "SCMRepository":
        from .scm_repo import SCMRepository

        return SCMRepository
    if name == "SOIRepository":
        from .soi_repo import SOIRepository

        return SOIRepository
    if name == "WRHRepository":
        from .wrh_repo import WRHRepository

        return WRHRepository
    raise AttributeError(name)
