"""Audit-side read adapter for linked Certs rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

from apps.certs.services.tracked_item_repository import TrackedItemRepository


@dataclass(frozen=True)
class CertSnapshot:
    vessel_cert_id: str
    version: int
    anniversary_date: date | None
    cadence_months: int | None
    cadence_custom_days: int | None
    window_open: date | None
    window_close: date | None
    issue_date: date | None
    expiry_date: date | None
    last_done_date: date | None
    next_due_date: date | None
    status: str
    lifecycle_status: str
    certificate_number: str


class CertRepository(Protocol):
    def get_item(self, tracked_item_id: str) -> dict[str, Any] | None: ...


def get_cert_snapshot(vessel_cert_id: str, *, repository: CertRepository | None = None) -> CertSnapshot | None:
    """Return Certs-owned date/window/version state without recomputing it in Audit."""

    repo = repository or TrackedItemRepository()
    row = repo.get_item(str(vessel_cert_id))
    if row is None:
        return None
    return CertSnapshot(
        vessel_cert_id=str(row.get("tracked_item_id") or vessel_cert_id),
        version=int(row.get("version") or 0),
        anniversary_date=row.get("anniversary_date"),
        cadence_months=_optional_int(row.get("cadence_months")),
        cadence_custom_days=_optional_int(row.get("cadence_custom_days")),
        window_open=row.get("window_open"),
        window_close=row.get("window_close"),
        issue_date=row.get("issue_date"),
        expiry_date=row.get("expiry_date"),
        last_done_date=row.get("last_done_date"),
        next_due_date=row.get("next_due_date"),
        status=str(row.get("status") or ""),
        lifecycle_status=str(row.get("lifecycle_status") or ""),
        certificate_number=str(row.get("certificate_number") or ""),
    )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
