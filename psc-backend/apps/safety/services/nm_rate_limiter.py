from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil

from django.db import connection
from django.utils import timezone

from apps.safety.models import Incident


@dataclass(frozen=True)
class NearMissRateLimitStatus:
    allowed: bool
    guidance_message: str | None
    limit: int
    remaining: int
    reset_at: object | None
    retry_after_seconds: int
    scope: str
    used: int


class NearMissRateLimiter:
    """Server-side near-miss submission throttling for Step 2.4."""

    limit = 5
    guidance_message = "Rate-limit reached. Next submission allowed after 00:00 LT."

    def get_status(
        self,
        *,
        actor_id: str,
        vessel_id: str | None = None,
        now=None,
    ) -> NearMissRateLimitStatus:
        current_time = now or timezone.now()
        queryset = Incident.objects.filter(
            is_deleted=False,
            record_type=Incident.RecordType.NEAR_MISS,
            created_by=str(actor_id),
        )

        timezone_offset_minutes = self._fetch_timezone_offset_minutes(
            vessel_id,
            as_of_date=current_time.date(),
        )
        if timezone_offset_minutes is not None:
            return self._build_vessel_local_day_status(
                queryset=queryset,
                current_time=current_time,
                timezone_offset_minutes=timezone_offset_minutes,
            )
        return self._build_rolling_24h_status(queryset=queryset, current_time=current_time)

    def check_allowed(
        self,
        *,
        actor_id: str,
        vessel_id: str | None = None,
        now=None,
    ) -> NearMissRateLimitStatus:
        return self.get_status(actor_id=actor_id, vessel_id=vessel_id, now=now)

    def record_submission(self, *, actor_id: str, created_at) -> None:
        return None

    def _build_vessel_local_day_status(
        self,
        *,
        queryset,
        current_time,
        timezone_offset_minutes: int,
    ) -> NearMissRateLimitStatus:
        offset = timedelta(minutes=timezone_offset_minutes)
        local_now = current_time + offset
        local_day_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        next_local_midnight = local_day_start + timedelta(days=1)
        window_start = local_day_start - offset
        window_end = next_local_midnight - offset

        used = queryset.filter(created_date__gte=window_start, created_date__lt=window_end).count()
        allowed = used < self.limit
        retry_after_seconds = 0
        if not allowed:
            retry_after_seconds = max(0, ceil((window_end - current_time).total_seconds()))

        return NearMissRateLimitStatus(
            allowed=allowed,
            guidance_message=None if allowed else self.guidance_message,
            limit=self.limit,
            remaining=max(0, self.limit - used),
            reset_at=window_end,
            retry_after_seconds=retry_after_seconds,
            scope="vessel_local_day",
            used=used,
        )

    def _build_rolling_24h_status(self, *, queryset, current_time) -> NearMissRateLimitStatus:
        window_start = current_time - timedelta(hours=24)
        recent_submissions = list(
            queryset.filter(created_date__gte=window_start).order_by("created_date").values_list("created_date", flat=True)
        )
        used = len(recent_submissions)
        allowed = used < self.limit
        reset_at = None
        retry_after_seconds = 0
        if not allowed and recent_submissions:
            reset_at = recent_submissions[0] + timedelta(hours=24)
            retry_after_seconds = max(0, ceil((reset_at - current_time).total_seconds()))

        return NearMissRateLimitStatus(
            allowed=allowed,
            guidance_message=None if allowed else "Near-miss submission limit reached (5 in 24h). Try again later or contact DPA.",
            limit=self.limit,
            remaining=max(0, self.limit - used),
            reset_at=reset_at,
            retry_after_seconds=retry_after_seconds,
            scope="rolling_24h",
            used=used,
        )

    def _fetch_timezone_offset_minutes(
        self,
        vessel_id: str | None,
        *,
        as_of_date: date | None = None,
    ) -> int | None:
        if not vessel_id:
            return None

        existing_tables = set(connection.introspection.table_names())
        if "wrh_ship_time_config" not in existing_tables:
            return None

        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor,
                    "wrh_ship_time_config",
                )
            }

            vendor = connection.vendor
            top_clause = "TOP 1 " if vendor == "microsoft" else ""
            limit_clause = "" if vendor == "microsoft" else " LIMIT 1"

            if "tz_offset_minutes" in columns:
                params: list[object] = [str(vessel_id)]
                where_clauses = ["vessel_id = %s"]
                if as_of_date is not None and "effective_date" in columns:
                    where_clauses.append("effective_date <= %s")
                    params.append(as_of_date.isoformat())

                order_parts: list[str] = []
                if "effective_date" in columns:
                    order_parts.append("effective_date DESC")
                if "id" in columns:
                    order_parts.append("id DESC")
                order_clause = f" ORDER BY {', '.join(order_parts)}" if order_parts else ""

                cursor.execute(
                    f"""
                    SELECT {top_clause}tz_offset_minutes
                    FROM wrh_ship_time_config
                    WHERE {' AND '.join(where_clauses)}{order_clause}{limit_clause}
                    """,
                    params,
                )
            elif "utc_offset_minutes" in columns:
                order_clause = " ORDER BY id DESC" if "id" in columns else ""
                cursor.execute(
                    f"""
                    SELECT {top_clause}utc_offset_minutes
                    FROM wrh_ship_time_config
                    WHERE vessel_id = %s{order_clause}{limit_clause}
                    """,
                    [str(vessel_id)],
                )
            else:
                return None

            row = cursor.fetchone()
        return None if row is None else int(row[0])
