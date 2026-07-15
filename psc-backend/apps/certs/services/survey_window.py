from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Any


SurveyWindowTuple = tuple[date | None, date | None, date | None]

WINDOW_RULES = {
    "renewal": {"open_months_before": 3, "close_months_after": 0},
    "intermediate": {"open_months_before": 3, "close_months_after": 3},
    "annual": {"open_months_before": 2, "close_months_after": 2},
    "periodic": {"open_months_before": 0, "close_months_after": 0},
}


def compute_window(tracked_item: dict[str, Any]) -> SurveyWindowTuple:
    anniversary_date = _as_date(tracked_item.get("anniversary_date"))
    if not anniversary_date or str(tracked_item.get("validity_type") or "") == "permanent":
        return None, None, None

    next_due_date = _compute_next_due_date(
        anniversary_date=anniversary_date,
        cadence_months=tracked_item.get("cadence_months"),
        cadence_custom_days=tracked_item.get("cadence_custom_days"),
    )
    if next_due_date is None:
        return None, None, None

    rule = WINDOW_RULES[_infer_rule(tracked_item)]
    window_open = _add_months(next_due_date, -rule["open_months_before"])
    window_close = _add_months(next_due_date, rule["close_months_after"])
    return window_open, window_close, next_due_date


def computed_window_payload(tracked_item: dict[str, Any]) -> dict[str, date | None]:
    window_open, window_close, next_due_date = compute_window(tracked_item)
    return {
        "window_open": window_open,
        "window_close": window_close,
        "next_due_date": next_due_date,
    }


def _compute_next_due_date(
    *,
    anniversary_date: date,
    cadence_months: Any,
    cadence_custom_days: Any,
) -> date | None:
    custom_days = _as_positive_int(cadence_custom_days)
    if custom_days is not None:
        return anniversary_date + timedelta(days=custom_days)

    months = _as_positive_int(cadence_months)
    if months is None:
        return None
    return _add_months(anniversary_date, months)


def _infer_rule(tracked_item: dict[str, Any]) -> str:
    label = " ".join(
        str(tracked_item.get(key) or "").lower()
        for key in ("catalog_code", "catalog_display_name", "catalog_short_name", "type", "relationship_type")
    )
    if "annual" in label:
        return "annual"
    if "intermediate" in label:
        return "intermediate"
    if "renewal" in label or "special" in label:
        return "renewal"

    months = _as_positive_int(tracked_item.get("cadence_months"))
    if months == 12:
        return "annual"
    if months in {24, 30, 36}:
        return "intermediate"
    if months is not None and months >= 60:
        return "renewal"
    return "periodic"


def _as_positive_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _as_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)
