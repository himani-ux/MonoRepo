from __future__ import annotations

from .purchase_fk_enforcer import OPEN_CA_STATUSES, PurchaseFKEnforcer, PurchaseFKEnforcerError


PurchaseRequisitionGuard = PurchaseFKEnforcer
PurchaseRequisitionGuardError = PurchaseFKEnforcerError

__all__ = [
    "OPEN_CA_STATUSES",
    "PurchaseRequisitionGuard",
    "PurchaseRequisitionGuardError",
]
