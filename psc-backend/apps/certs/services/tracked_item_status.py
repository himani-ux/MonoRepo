from __future__ import annotations

from datetime import date
from typing import Any


STICKY_STATUSES = {
    "superseded",
    "expired_at_onboarding",
    "pending_first_upload",
    "invalid_due_to_reflag",
    "pending_supersession",
    "expired",
}


def compute_tracked_item_status(row: dict[str, Any], *, today: date | None = None) -> str:
    current = today or date.today()
    stored = str(row.get("status") or "ok")
    if stored in STICKY_STATUSES:
        return stored

    postponed_until = _as_date(row.get("postponed_until"))
    if postponed_until and postponed_until >= current:
        return "postponed"

    if row.get("validity_type") == "permanent":
        return "permanent"

    window_open = _as_date(row.get("window_open"))
    window_close = _as_date(row.get("window_close"))
    if window_open and window_close:
        if current < window_open:
            return "window_opening"
        if window_open <= current <= window_close:
            return "window_closing" if (window_close - current).days <= 30 else "window_open"
        return "overdue"

    expiry_date = _as_date(row.get("expiry_date"))
    if expiry_date:
        days_to_expiry = (expiry_date - current).days
        if days_to_expiry < 0:
            return "expired"
        if days_to_expiry <= 7:
            return "window_closing"
        if days_to_expiry <= 90:
            return "window_opening"

    return stored


def _as_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
