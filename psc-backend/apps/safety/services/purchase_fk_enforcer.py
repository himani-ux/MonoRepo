from __future__ import annotations

from apps.safety.models import CorrectiveAction
from apps.safety.repositories import PurchaseRepository


OPEN_CA_STATUSES = (
    CorrectiveAction.Status.OPEN,
    CorrectiveAction.Status.IN_PROGRESS,
    CorrectiveAction.Status.PENDING_VERIFY,
)


class PurchaseFKEnforcerError(Exception):
    """Raised when the Purchase requisition hard-FK contract cannot be satisfied."""


class PurchaseFKEnforcer:
    def __init__(self, *, repository: PurchaseRepository | None = None) -> None:
        self.repository = repository or PurchaseRepository()

    def get_requisition(self, purchase_req_id: int, *, raise_if_missing: bool = True) -> dict[str, object] | None:
        if not self.repository.table_exists():
            if raise_if_missing:
                raise PurchaseFKEnforcerError(
                    "Purchase requisition integration is unavailable in this workspace because pur_requisition is absent."
                )
            return None

        requisition = self.repository.get_requisition(int(purchase_req_id))
        if requisition is None and raise_if_missing:
            raise PurchaseFKEnforcerError(
                "Corrective Action -> Purchase Requisition link must reference an existing requisition (hard FK per D-GAP-M12)."
            )
        return requisition

    def ensure_linkable(self, purchase_req_id: int) -> dict[str, object]:
        requisition = self.get_requisition(purchase_req_id)
        if requisition["is_archived"]:
            raise PurchaseFKEnforcerError(
                "Corrective Action -> Purchase Requisition link must reference an active requisition (hard FK per D-GAP-M12)."
            )
        return requisition

    def ensure_archive_allowed(self, purchase_req_id: int) -> None:
        open_link_exists = CorrectiveAction.objects.filter(
            purchase_req_id=int(purchase_req_id),
            is_deleted=False,
            status__in=OPEN_CA_STATUSES,
        ).exists()
        if open_link_exists:
            raise PurchaseFKEnforcerError(
                "Requisition cannot be archived while linked to an open Corrective Action (D-GAP-M12)."
            )
