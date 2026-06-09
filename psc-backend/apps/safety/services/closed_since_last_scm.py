from __future__ import annotations

from datetime import datetime

from django.db import DatabaseError, OperationalError, ProgrammingError
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.safety.models import CorrectiveAction, Incident, SCMAgendaItem, SCMMeeting
from apps.safety.repositories.base import BaseRepository


class ClosedSinceLastSCMService:
    def __init__(
        self,
        *,
        meeting_model=SCMMeeting,
        agenda_model=SCMAgendaItem,
        incident_model=Incident,
        corrective_action_model=CorrectiveAction,
        repository: BaseRepository | None = None,
        now_func=timezone.now,
    ) -> None:
        self.meeting_model = meeting_model
        self.agenda_model = agenda_model
        self.incident_model = incident_model
        self.corrective_action_model = corrective_action_model
        self.repository = repository or BaseRepository()
        self.now_func = now_func

    def fetch_for_meeting(self, meeting: SCMMeeting) -> dict[str, object]:
        cutoff_meeting = self._resolve_prior_cutoff_meeting(meeting)
        upper_bound_at = self._meeting_closed_at(meeting) or self.now_func()
        return self._build_payload(
            vessel_id=str(meeting.vessel_id),
            meeting_id=meeting.id,
            cutoff_meeting=cutoff_meeting,
            upper_bound_at=upper_bound_at,
        )

    def fetch_for_vessel(self, vessel_id: str) -> dict[str, object]:
        cutoff_meeting = self._resolve_latest_cutoff_meeting(str(vessel_id))
        return self._build_payload(
            vessel_id=str(vessel_id),
            meeting_id=None,
            cutoff_meeting=cutoff_meeting,
            upper_bound_at=self.now_func(),
        )

    def _resolve_prior_cutoff_meeting(self, meeting: SCMMeeting) -> SCMMeeting | None:
        queryset = (
            self.meeting_model.objects.filter(
                is_deleted=False,
                vessel_id=str(meeting.vessel_id),
            )
            .filter(Q(office_comment_at__isnull=False) | Q(master_signed_off_at__isnull=False))
            .annotate(closed_at_value=Coalesce("office_comment_at", "master_signed_off_at"))
            .defer("occasion", "ship_position", "ship_pos_from", "ship_pos_to", "comm_time", "comp_time")
            .exclude(pk=meeting.pk)
        )

        closed_at = self._meeting_closed_at(meeting)
        if closed_at is not None:
            queryset = queryset.filter(closed_at_value__lt=closed_at)
        else:
            queryset = queryset.filter(meeting_date__lte=meeting.meeting_date)

        try:
            return queryset.order_by("-closed_at_value", "-meeting_date", "-id").first()
        except (DatabaseError, OperationalError, ProgrammingError):
            return None

    def _resolve_latest_cutoff_meeting(self, vessel_id: str) -> SCMMeeting | None:
        try:
            return (
                self.meeting_model.objects.filter(
                    is_deleted=False,
                    vessel_id=str(vessel_id),
                )
                .filter(Q(office_comment_at__isnull=False) | Q(master_signed_off_at__isnull=False))
                .annotate(closed_at_value=Coalesce("office_comment_at", "master_signed_off_at"))
                .defer("occasion", "ship_position", "ship_pos_from", "ship_pos_to", "comm_time", "comp_time")
                .order_by("-closed_at_value", "-meeting_date", "-id")
                .first()
            )
        except (DatabaseError, OperationalError, ProgrammingError):
            return None

    def _build_payload(
        self,
        *,
        vessel_id: str,
        meeting_id: int | None,
        cutoff_meeting: SCMMeeting | None,
        upper_bound_at,
    ) -> dict[str, object]:
        items: list[dict[str, object]] = []
        cutoff_at = self._meeting_closed_at(cutoff_meeting)
        if cutoff_at is not None:
            items.extend(self._fetch_incident_items(vessel_id=vessel_id, cutoff_at=cutoff_at, upper_bound_at=upper_bound_at))
            items.extend(self._fetch_near_miss_items(vessel_id=vessel_id, cutoff_at=cutoff_at, upper_bound_at=upper_bound_at))
            items.extend(self._fetch_soi_finding_items(vessel_id=vessel_id, cutoff_at=cutoff_at, upper_bound_at=upper_bound_at))
            items.extend(
                self._fetch_corrective_action_items(
                    vessel_id=vessel_id,
                    cutoff_at=cutoff_at,
                    upper_bound_at=upper_bound_at,
                )
            )

        items.sort(key=self._sort_key, reverse=True)
        summary = {
            "incident_count": sum(1 for item in items if item["item_type"] == "INCIDENT"),
            "near_miss_count": sum(1 for item in items if item["item_type"] == "NEAR_MISS"),
            "soi_finding_count": sum(1 for item in items if item["item_type"] == "SOI_FINDING"),
            "corrective_action_count": sum(1 for item in items if item["item_type"] == "CORRECTIVE_ACTION"),
            "total_count": len(items),
        }
        return {
            "vessel_id": str(vessel_id),
            "meeting_id": meeting_id,
            "cutoff": self._serialize_cutoff(cutoff_meeting),
            "upper_bound_at": self._serialize_datetime(upper_bound_at),
            "summary": summary,
            "items": items,
            "empty_message": "Nothing closed since last SCM." if not items else None,
        }

    def _fetch_incident_items(self, *, vessel_id: str, cutoff_at, upper_bound_at) -> list[dict[str, object]]:
        rows = (
            self.incident_model.objects.filter(
                is_deleted=False,
                vessel_id=str(vessel_id),
                record_type=self.incident_model.RecordType.INCIDENT,
                state="CLOSED",
                closed_at__isnull=False,
                closed_at__gt=cutoff_at,
                closed_at__lte=upper_bound_at,
            )
            .order_by("-closed_at", "-id")
        )
        return [
            {
                "item_type": "INCIDENT",
                "source_id": row.id,
                "reference": row.incident_number,
                "title": row.narrative or row.incident_number,
                "status": row.state,
                "closed_at": self._serialize_datetime(row.closed_at),
                "source_route": f"/safety/incidents/{row.id}",
                "unique_id": None,
            }
            for row in rows
        ]

    def _fetch_near_miss_items(self, *, vessel_id: str, cutoff_at, upper_bound_at) -> list[dict[str, object]]:
        rows = (
            self.incident_model.objects.filter(
                is_deleted=False,
                vessel_id=str(vessel_id),
                record_type=self.incident_model.RecordType.NEAR_MISS,
                state="CLOSED",
                closed_at__isnull=False,
                closed_at__gt=cutoff_at,
                closed_at__lte=upper_bound_at,
            )
            .order_by("-closed_at", "-id")
        )
        return [
            {
                "item_type": "NEAR_MISS",
                "source_id": row.id,
                "reference": row.incident_number,
                "title": row.narrative or row.incident_number,
                "status": row.state,
                "closed_at": self._serialize_datetime(row.closed_at),
                "source_route": f"/safety/near-miss/{row.id}",
                "unique_id": None,
            }
            for row in rows
        ]

    def _fetch_corrective_action_items(
        self,
        *,
        vessel_id: str,
        cutoff_at,
        upper_bound_at,
    ) -> list[dict[str, object]]:
        incident_ids = list(
            self.incident_model.objects.filter(is_deleted=False, vessel_id=str(vessel_id)).values_list("id", flat=True)
        )
        incident_ids_by_id = {
            str(row["id"]): row["id"]
            for row in self.incident_model.objects.filter(is_deleted=False, vessel_id=str(vessel_id)).values("id")
        }
        meeting_ids = list(
            self.meeting_model.objects.filter(is_deleted=False, vessel_id=str(vessel_id)).values_list("id", flat=True)
        )
        meeting_ids_by_id = {
            str(row["id"]): row["id"]
            for row in self.meeting_model.objects.filter(is_deleted=False, vessel_id=str(vessel_id)).values("id")
        }
        agenda_rows = list(
            self.agenda_model.objects.filter(meeting_id__in=meeting_ids).values("id", "meeting_id")
        ) if meeting_ids else []
        agenda_ids = [row["id"] for row in agenda_rows]
        agenda_to_meeting_id = {str(row["id"]): str(row["meeting_id"]) for row in agenda_rows}

        vessel_filter = Q(recommendation__incident__vessel_id=str(vessel_id))
        if incident_ids:
            vessel_filter |= Q(source_table=self.incident_model._meta.db_table, source_id__in=incident_ids)
        if agenda_ids:
            vessel_filter |= Q(source_table=self.agenda_model._meta.db_table, source_id__in=agenda_ids)

        rows = (
            self.corrective_action_model.objects.filter(
                is_deleted=False,
                status=self.corrective_action_model.Status.CLOSED,
                closed_at__isnull=False,
                closed_at__gt=cutoff_at,
                closed_at__lte=upper_bound_at,
            )
            .filter(vessel_filter)
            .select_related("recommendation", "recommendation__incident")
            .order_by("-closed_at", "-id")
        )

        items: list[dict[str, object]] = []
        for row in rows:
            source_route = None
            if getattr(row, "recommendation_id", None) and getattr(row.recommendation, "incident_id", None):
                incident_id = incident_ids_by_id.get(str(row.recommendation.incident_id))
                source_route = f"/safety/incidents/{incident_id}/corrective-actions" if incident_id else None
            elif row.source_table == self.incident_model._meta.db_table:
                incident_id = incident_ids_by_id.get(str(row.source_id))
                source_route = f"/safety/incidents/{incident_id}/corrective-actions" if incident_id else None
            elif row.source_table == self.agenda_model._meta.db_table:
                meeting_id = agenda_to_meeting_id.get(str(row.source_id))
                if meeting_id is not None:
                    meeting_id = meeting_ids_by_id.get(meeting_id)
                    source_route = f"/safety/scm/{meeting_id}" if meeting_id else None

            items.append(
                {
                    "item_type": "CORRECTIVE_ACTION",
                    "source_id": row.id,
                    "reference": f"CA-{row.id}",
                    "title": row.title,
                    "status": row.status,
                    "closed_at": self._serialize_datetime(row.closed_at),
                    "source_route": source_route,
                    "unique_id": None,
                }
            )
        return items

    def _fetch_soi_finding_items(self, *, vessel_id: str, cutoff_at, upper_bound_at) -> list[dict[str, object]]:
        rows = self.repository.execute_query(
            """
            SELECT
                finding.id AS source_id,
                finding.title AS title,
                finding.status AS status,
                finding.closed_at AS closed_at,
                inspection.id AS inspection_id,
                inspection.inspection_reference AS inspection_reference,
                inspection.checklist_unique_id AS checklist_unique_id
            FROM vims_safety_soi_finding AS finding
            INNER JOIN vims_safety_soi_inspection AS inspection
                ON inspection.id = finding.inspection_id
            WHERE inspection.vessel_id = %s
              AND inspection.is_deleted = %s
              AND finding.is_deleted = %s
              AND finding.status = %s
              AND finding.closed_at IS NOT NULL
              AND finding.closed_at > %s
              AND finding.closed_at <= %s
            ORDER BY finding.closed_at DESC, finding.id DESC
            """,
            [
                str(vessel_id),
                False,
                False,
                "CLOSED",
                cutoff_at,
                upper_bound_at,
            ],
        )

        return [
            {
                "item_type": "SOI_FINDING",
                "source_id": row["source_id"],
                "reference": row["inspection_reference"],
                "title": row["title"],
                "status": row["status"],
                "closed_at": self._serialize_datetime(row["closed_at"]),
                "source_route": f"/safety/soi/{row['inspection_id']}/findings",
                "unique_id": row["checklist_unique_id"],
            }
            for row in rows
        ]

    def _serialize_cutoff(self, meeting: SCMMeeting | None) -> dict[str, object] | None:
        closed_at = self._meeting_closed_at(meeting)
        if meeting is None or closed_at is None:
            return None
        return {
            "meeting_id": meeting.id,
            "scm_number": meeting.scm_number,
            "meeting_type": meeting.meeting_type,
            "closed_at": self._serialize_datetime(closed_at),
        }

    def _meeting_closed_at(self, meeting: SCMMeeting | None):
        if meeting is None:
            return None
        return meeting.office_comment_at or meeting.master_signed_off_at

    def _serialize_datetime(self, value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                value = timezone.make_aware(value, timezone.get_current_timezone())
            return value.isoformat()
        return str(value)

    def _sort_key(self, item: dict[str, object]):
        closed_at = item.get("closed_at")
        if not isinstance(closed_at, str):
            return datetime.min.replace(tzinfo=timezone.get_current_timezone())
        return datetime.fromisoformat(closed_at)
