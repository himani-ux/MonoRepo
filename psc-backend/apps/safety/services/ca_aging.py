from __future__ import annotations

from datetime import date, datetime

from django.utils import timezone


class CorrectiveActionAgingService:
    def aging_bucket(self, action, *, as_of: datetime | None = None) -> str:
        days_open = self.days_open(action, as_of=as_of)
        if days_open <= 15:
            return "0-15"
        if days_open <= 30:
            return "15-30"
        if days_open <= 45:
            return "30-45"
        return "45+"

    def days_open(self, action, *, as_of: datetime | None = None) -> int:
        created_at = self._normalize_datetime(getattr(action, "created_date", None))
        end_at = self._normalize_datetime(getattr(action, "closed_at", None)) or as_of or timezone.now()
        return max((end_at.date() - created_at.date()).days, 0)

    def sync_bucket(self, action) -> str:
        bucket = self.aging_bucket(action)
        if getattr(action, "aging_bucket", None) != bucket:
            action.aging_bucket = bucket
            action.save(update_fields=["aging_bucket"])
        return bucket

    def sync_actions(self, actions) -> None:
        for action in actions:
            self.sync_bucket(action)

    @staticmethod
    def _normalize_datetime(value: datetime | date | None) -> datetime:
        if value is None:
            return timezone.now()
        if isinstance(value, datetime):
            return value
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
