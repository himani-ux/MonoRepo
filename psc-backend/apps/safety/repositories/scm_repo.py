from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
import json
from typing import TYPE_CHECKING
from uuid import UUID

from django.core.exceptions import FieldError
from django.db import connection, transaction
from django.db import DatabaseError, OperationalError, ProgrammingError
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.safety.models import CorrectiveAction, Incident, SCMAgendaItem, SCMAttendance, SCMLegacyField, SCMMeeting, SCMSignature
from apps.safety.models import SOIFinding, SOIInspection
from apps.safety.repositories.exceptions import SPExecutionError, SPTimeoutError

from .base import BaseRepository
from .cms_repo import CMSRepository

if TYPE_CHECKING:
    from apps.safety.services.closed_since_last_scm import ClosedSinceLastSCMService
    from apps.safety.services.overdue_soi_blocker import OverdueSOIBlocker
    from apps.safety.services.wrh_snapshot_fetcher import WRHSnapshotFetcher


class SCMRepository(BaseRepository):
    def __init__(
        self,
        *,
        meeting_model=SCMMeeting,
        agenda_model=SCMAgendaItem,
        attendance_model=SCMAttendance,
        legacy_field_model=SCMLegacyField,
        signature_model=SCMSignature,
        cms_repository: CMSRepository | None = None,
        closed_since_last_service: ClosedSinceLastSCMService | None = None,
        overdue_soi_blocker: OverdueSOIBlocker | None = None,
        wrh_snapshot_fetcher: WRHSnapshotFetcher | None = None,
        **kwargs,
    ) -> None:
        from apps.safety.services.closed_since_last_scm import ClosedSinceLastSCMService
        from apps.safety.services.overdue_soi_blocker import OverdueSOIBlocker
        from apps.safety.services.wrh_snapshot_fetcher import WRHSnapshotFetcher

        super().__init__(**kwargs)
        self.meeting_model = meeting_model
        self.agenda_model = agenda_model
        self.attendance_model = attendance_model
        self.legacy_field_model = legacy_field_model
        self.signature_model = signature_model
        self.cms_repository = cms_repository or CMSRepository()
        self.closed_since_last_service = closed_since_last_service or ClosedSinceLastSCMService()
        self.overdue_soi_blocker = overdue_soi_blocker or OverdueSOIBlocker(repository=self)
        self.wrh_snapshot_fetcher = wrh_snapshot_fetcher or WRHSnapshotFetcher()

    def create(self, payload: Mapping[str, object]) -> SCMMeeting:
        from apps.safety.serializers.scm import normalize_scm_sections

        data = dict(payload)
        legacy_columns_available = self._scm_meeting_legacy_columns_available()
        if not legacy_columns_available:
            for field_name in self._legacy_header_field_names():
                data.pop(field_name, None)
        attendance_rows = data.pop("attendance_rows", None)
        sections = normalize_scm_sections(data.pop("sections", None))
        meeting_date = self._coerce_meeting_date(data.get("meeting_date"))
        vessel_code = self._normalize_vessel_code(data.pop("vessel_code", None), data.get("vessel_id"))

        data.setdefault("meeting_type", SCMMeeting.MeetingType.REGULAR)
        data.setdefault("state", SCMMeeting.State.DRAFT)
        data.setdefault("schema_version", 1)
        data.setdefault("updated_by", data.get("created_by"))
        data.setdefault("prepared_by_crew_id", data.get("created_by"))
        data["meeting_date"] = meeting_date
        data["scm_number"] = self.assign_scm_number(vessel_code=vessel_code, meeting_date=meeting_date)

        with transaction.atomic():
            if legacy_columns_available:
                meeting = self.meeting_model.objects.create(**data)
            else:
                meeting_id = self._create_meeting_without_legacy_header_columns(data)
                meeting = self.read(meeting_id)
            self._replace_sections(meeting.id, sections)
            if isinstance(attendance_rows, list) and attendance_rows:
                meeting = self.read(meeting.id)
                self.save_attendance(meeting=meeting, rows=attendance_rows)

        return self.read(meeting.id)

    def update_meeting(
        self,
        *,
        meeting: SCMMeeting,
        payload: Mapping[str, object],
        actor_id: str,
    ) -> SCMMeeting:
        from apps.safety.serializers.scm import normalize_scm_sections

        data = dict(payload)
        legacy_columns_available = self._scm_meeting_legacy_columns_available()
        if not legacy_columns_available:
            for field_name in self._legacy_header_field_names():
                data.pop(field_name, None)

        attendance_rows = data.pop("attendance_rows", None)
        sections = normalize_scm_sections(data.pop("sections", None))
        data.pop("vessel_code", None)
        data.pop("vessel_id", None)
        data.pop("scm_number", None)
        data.pop("state", None)

        allowed_fields = {
            "meeting_type",
            "meeting_date",
            "meeting_time_local",
            "location",
            "latitude",
            "longitude",
            "voyage_no",
            "occasion",
            "ship_position",
            "ship_pos_from",
            "ship_pos_to",
            "comm_time",
            "comp_time",
            "chair_crew_id",
            "prepared_by_crew_id",
            "ad_hoc_trigger_reason",
            "schema_version",
        }

        with transaction.atomic():
            update_fields: list[str] = []
            for field_name in allowed_fields:
                if field_name not in data:
                    continue
                setattr(meeting, field_name, data[field_name])
                update_fields.append(field_name)
            meeting.updated_by = actor_id
            meeting.updated_date = timezone.now()
            update_fields.extend(["updated_by", "updated_date"])
            if update_fields:
                meeting.save(update_fields=sorted(set(update_fields)))

            self.update_agenda(meeting=meeting, rows=sections, actor_id=actor_id)
            if isinstance(attendance_rows, list):
                self.save_attendance(meeting=meeting, rows=attendance_rows)

        return self.read(meeting.id)

    def read(self, meeting_id: int) -> SCMMeeting:
        queryset = self.meeting_model.objects
        if not self._scm_meeting_legacy_columns_available():
            queryset = queryset.defer(*self._legacy_header_field_names())
        meeting = queryset.get(pk=meeting_id, is_deleted=False)
        meeting._agenda_rows = list(self.list_sections(meeting.id))
        meeting._legacy_fields = list(self.list_legacy_fields(meeting.id))
        return meeting

    def list(self, *, filters: Mapping[str, object] | None = None):
        queryset = self.meeting_model.objects.filter(is_deleted=False)
        if not self._scm_meeting_legacy_columns_available():
            queryset = queryset.defer(*self._legacy_header_field_names())
        filters = filters or {}

        if vessel_id := filters.get("vessel_id"):
            queryset = queryset.filter(vessel_id=str(vessel_id))
        if meeting_type := filters.get("meeting_type"):
            queryset = queryset.filter(meeting_type=str(meeting_type).strip().upper())
        if date_from := filters.get("date_from"):
            queryset = queryset.filter(meeting_date__gte=date_from)
        if date_to := filters.get("date_to"):
            queryset = queryset.filter(meeting_date__lte=date_to)

        return queryset.order_by("-meeting_date", "-id")

    def list_sections(self, meeting_id: int):
        return self.agenda_model.objects.filter(meeting_id=meeting_id).order_by("agenda_item_number", "id")

    def list_legacy_fields(self, meeting_id: int):
        if not self._scm_legacy_field_table_available():
            return self.legacy_field_model.objects.none()
        return self.legacy_field_model.objects.filter(meeting_id=meeting_id).order_by("agenda_item_number", "id")

    def list_attendance(self, meeting_id: int):
        return self.attendance_model.objects.filter(meeting_id=meeting_id).order_by("id", "crew_id")

    def save_attendance(self, *, meeting: SCMMeeting, rows: list[dict[str, object]]) -> dict[str, object]:
        timezone_offset_minutes = None
        runtime_warning_details: dict[str, dict[str, object]] = {}

        with transaction.atomic():
            for row in rows:
                crew_id = str(row["crew_id"])
                identity = self.resolve_crew_identity(
                    vessel_id=str(meeting.vessel_id),
                    crew_id=crew_id,
                    active_on=meeting.meeting_date,
                    fallback=row,
                )
                snapshot = self.wrh_snapshot_fetcher.fetch_24h_and_7d(
                    crew_id=crew_id,
                    meeting_date=meeting.meeting_date,
                    vessel_id=str(meeting.vessel_id),
                )
                if timezone_offset_minutes is None and snapshot.get("timezone_offset_minutes") is not None:
                    timezone_offset_minutes = int(snapshot["timezone_offset_minutes"])
                runtime_warning_details[crew_id] = {
                    "display_name": identity["display_name"],
                    "warning_codes": list(snapshot.get("warning_codes") or []),
                }

                self.attendance_model.objects.update_or_create(
                    meeting_id=meeting.id,
                    crew_id=crew_id,
                    defaults={
                        "rank_name": identity["rank_name"],
                        "display_name": identity["display_name"],
                        "present": bool(row.get("present", True)),
                        "absence_reason": row.get("absence_reason"),
                        "wrh_data_available": bool(snapshot["wrh_data_available"]),
                        "wrh_rest_hours_24h": snapshot["wrh_rest_hours_24h"],
                        "wrh_rest_hours_7d": snapshot["wrh_rest_hours_7d"],
                        "wrh_non_compliance_flag": bool(snapshot["wrh_non_compliance_flag"]),
                        "remarks": row.get("remarks"),
                        "schema_version": int(row.get("schema_version", 1)),
                    },
                )

        return self.build_attendance_payload(
            meeting=meeting,
            timezone_offset_minutes=timezone_offset_minutes,
            runtime_warning_details=runtime_warning_details,
        )

    def resolve_crew_identity(
        self,
        *,
        vessel_id: str,
        crew_id: str,
        active_on: date,
        fallback: Mapping[str, object] | None = None,
    ) -> dict[str, str]:
        try:
            snapshot = self.cms_repository.get_current_crew_snapshot(
                vessel_id=vessel_id,
                crew_id=crew_id,
                active_on=active_on,
            )
        except (DatabaseError, OperationalError, ProgrammingError, SPExecutionError, SPTimeoutError):
            snapshot = None

        if snapshot is not None:
            return {
                "rank_name": str(snapshot.get("rank") or "").strip(),
                "display_name": str(snapshot.get("crew_name") or crew_id).strip(),
            }

        fallback = fallback or {}
        return {
            "rank_name": str(fallback.get("rank_name") or "").strip(),
            "display_name": str(fallback.get("display_name") or crew_id).strip(),
        }

    def resolve_current_master_id(self, *, vessel_id: str, active_on: date) -> str:
        try:
            crew_rows = self.cms_repository.list_current_vessel_crew(vessel_id=vessel_id, active_on=active_on)
        except (DatabaseError, OperationalError, ProgrammingError, SPExecutionError, SPTimeoutError):
            crew_rows = []
        for row in crew_rows:
            rank = str(row.get("rank") or "").upper()
            if "MASTER" in rank:
                crew_id = str(row.get("crew_id") or "").strip()
                if crew_id:
                    return crew_id
        return f"master-{vessel_id}"

    def resolve_regular_co_signature_crew_id(
        self,
        meeting: SCMMeeting,
        *,
        attendance_rows: Iterable[SCMAttendance] | None = None,
    ) -> str:
        prepared_by_crew_id = str(meeting.prepared_by_crew_id).strip()
        rows = list(attendance_rows) if attendance_rows is not None else list(self.list_attendance(meeting.id))

        for row in rows:
            if str(row.crew_id).strip() == prepared_by_crew_id and self._is_chief_officer_rank(row.rank_name):
                return prepared_by_crew_id

        for row in rows:
            if row.present and self._is_chief_officer_rank(row.rank_name):
                return str(row.crew_id).strip()

        for row in rows:
            if self._is_chief_officer_rank(row.rank_name):
                return str(row.crew_id).strip()

        return prepared_by_crew_id

    @staticmethod
    def _is_chief_officer_rank(rank_name: str | None) -> bool:
        rank = str(rank_name or "").strip().upper()
        compact = "".join(ch for ch in rank if ch.isalnum())
        return compact in {"CO", "CHIEFOFFICER", "CHIEFMATE"} or "CHIEF OFFICER" in rank or "CHIEF MATE" in rank

    def build_attendance_payload(
        self,
        *,
        meeting: SCMMeeting,
        timezone_offset_minutes: int | None = None,
        runtime_warning_details: Mapping[str, Mapping[str, object]] | None = None,
    ) -> dict[str, object]:
        from apps.safety.serializers.scm_attendance import SCMAttendanceSerializer

        rows = list(self.list_attendance(meeting.id))
        signatures = list(self.list_signatures(meeting.id))
        co_signer_crew_id = self.resolve_regular_co_signature_crew_id(meeting, attendance_rows=rows)
        co_signature = next(
            (
                signature
                for signature in signatures
                if signature.signer_role == SCMSignature.SignerRole.CO
                and str(signature.signer_crew_id) == co_signer_crew_id
            ),
            None,
        )
        attendee_signature_map = {
            str(signature.signer_crew_id): signature
            for signature in signatures
            if signature.signer_role == SCMSignature.SignerRole.ATTENDEE
        }
        if timezone_offset_minutes is None:
            timezone_offset_minutes = self.wrh_snapshot_fetcher.fetch_timezone_offset(
                vessel_id=str(meeting.vessel_id),
                meeting_date=meeting.meeting_date,
            )

        warnings = self._build_attendance_warnings(
            rows=rows,
            timezone_offset_minutes=timezone_offset_minutes,
            runtime_warning_details=runtime_warning_details,
        )
        serialized_rows = SCMAttendanceSerializer(rows, many=True).data
        present_count = sum(1 for row in rows if row.present)
        signed_attendee_count = 0
        for row, row_payload in zip(rows, serialized_rows):
            signature = attendee_signature_map.get(str(row.crew_id))
            signature_role = SCMSignature.SignerRole.ATTENDEE
            if signature is None and str(row.crew_id) == co_signer_crew_id:
                signature = co_signature
                signature_role = SCMSignature.SignerRole.CO
            row_payload["signature"] = self._serialize_signature_status(
                signature,
                required=bool(row.present),
                signer_role=signature_role,
                signer_crew_id=str(row.crew_id),
            )
            if row.present and signature is not None:
                signed_attendee_count += 1

        return {
            "meeting_id": meeting.id,
            "meeting_date": meeting.meeting_date.isoformat(),
            "meeting_state": meeting.state,
            "co_signature": self._serialize_signature_status(
                co_signature,
                required=meeting.meeting_type == SCMMeeting.MeetingType.REGULAR,
                signer_role=SCMSignature.SignerRole.CO,
                signer_crew_id=co_signer_crew_id,
            ),
            "signature_summary": {
                "attendee_signature_count": signed_attendee_count,
                "co_signature_required": meeting.meeting_type == SCMMeeting.MeetingType.REGULAR,
                "present_attendee_count": present_count,
                "signatures_complete": (
                    self.signature_preflight_complete(meeting)[0]
                    if meeting.state != SCMMeeting.State.DRAFT
                    else signed_attendee_count == present_count
                    and (
                        meeting.meeting_type != SCMMeeting.MeetingType.REGULAR
                        or co_signature is not None
                    )
                ),
            },
            "timezone_offset_minutes": timezone_offset_minutes,
            "warnings": warnings,
            "rows": serialized_rows,
        }

    def build_cadence_warning(self, *, vessel_id: str, meeting_date: date | None = None) -> dict[str, object] | None:
        # APP_FLOW/PRD anchor cadence and Closed-Since-Last on the latest
        # signed-off SCM closure regardless of SCM type. Ad-Hoc still does not
        # satisfy the monthly Regular SCM obligation; it only moves the closure
        # anchor used for warning/cutoff calculations.
        try:
            last_closure = (
                self.meeting_model.objects.filter(
                    is_deleted=False,
                    vessel_id=str(vessel_id),
                    master_signed_off_at__isnull=False,
                )
                .defer(*self._legacy_header_field_names())
                .order_by("-master_signed_off_at", "-meeting_date", "-id")
                .first()
            )
        except (DatabaseError, OperationalError, ProgrammingError):
            return None
        if last_closure is None or last_closure.master_signed_off_at is None:
            return None

        anchor_date = meeting_date or timezone.localdate()
        days_since_closure = (anchor_date - last_closure.master_signed_off_at.date()).days
        if days_since_closure <= 30:
            return None

        return {
            "days_since_last_regular_closure": days_since_closure,
            "last_regular_closed_at": last_closure.master_signed_off_at.isoformat(),
            "last_scm_type": last_closure.meeting_type,
            "message": (
                "Regular SCM overdue: more than 30 days have passed since the last "
                "signed-off SCM meeting. Creation stays allowed, but schedule immediately."
            ),
            "severity": "warning",
        }

    def build_empty_closed_since_last_payload(self) -> dict[str, object]:
        return {
            "vessel_id": "",
            "meeting_id": None,
            "cutoff": None,
            "upper_bound_at": timezone.now().isoformat(),
            "summary": {
                "incident_count": 0,
                "near_miss_count": 0,
                "soi_finding_count": 0,
                "corrective_action_count": 0,
                "total_count": 0,
            },
            "items": [],
            "empty_message": "Nothing closed since last SCM.",
        }

    def _build_cadence_status(
        self,
        *,
        vessel_id: str,
        meeting_date: date,
    ) -> dict[str, object]:
        if not vessel_id:
            return {
                "days_since_last_regular_closure": None,
                "is_overdue": False,
                "last_regular_closed_at": None,
                "last_scm_type": None,
                "next_due_date": None,
            }

        try:
            last_closure = (
                self.meeting_model.objects.filter(
                    is_deleted=False,
                    vessel_id=vessel_id,
                    master_signed_off_at__isnull=False,
                )
                .defer(*self._legacy_header_field_names())
                .order_by("-master_signed_off_at", "-meeting_date", "-id")
                .first()
            )
        except (DatabaseError, OperationalError, ProgrammingError):
            last_closure = None
        if last_closure is None or last_closure.master_signed_off_at is None:
            return {
                "days_since_last_regular_closure": None,
                "is_overdue": False,
                "last_regular_closed_at": None,
                "last_scm_type": None,
                "next_due_date": None,
            }

        last_closed_date = last_closure.master_signed_off_at.date()
        days_since = (meeting_date - last_closed_date).days
        next_due_date = last_closed_date + timedelta(days=30)
        return {
            "days_since_last_regular_closure": days_since,
            "is_overdue": days_since > 30,
            "last_regular_closed_at": last_closure.master_signed_off_at.isoformat(),
            "last_scm_type": last_closure.meeting_type,
            "next_due_date": next_due_date.isoformat(),
        }

    def _resolve_prepared_by_snapshot(
        self,
        *,
        vessel_id: str,
        actor_id: str | None,
        active_on: date,
    ) -> dict[str, object] | None:
        if not vessel_id or not actor_id:
            return None
        try:
            snapshot = self.cms_repository.get_current_crew_snapshot(
                vessel_id=vessel_id,
                crew_id=str(actor_id),
                active_on=active_on,
            )
        except (SPExecutionError, SPTimeoutError):
            snapshot = None
        if snapshot is None:
            return {
                "crew_id": str(actor_id),
                "crew_name": str(actor_id),
                "department": "",
                "rank": "",
            }
        return snapshot

    def _resolve_chair_snapshot(
        self,
        *,
        actor_id: str | None,
        crew_roster: list[dict[str, object]],
        prepared_by: dict[str, object] | None,
    ) -> dict[str, object] | None:
        for crew_member in crew_roster:
            if str(crew_member.get("rank") or "").strip().upper() == "MASTER":
                return crew_member

        if prepared_by is not None:
            return prepared_by

        if actor_id in (None, ""):
            return None

        return {
            "crew_id": str(actor_id),
            "crew_name": str(actor_id),
            "department": "",
            "rank": "",
        }

    def _build_attendee_preview_rows(
        self,
        *,
        vessel_id: str,
        meeting_date: date,
        crew_roster: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        preview_rows: list[dict[str, object]] = []
        for crew_member in crew_roster:
            crew_id = str(crew_member.get("crew_id") or "").strip()
            snapshot = self.wrh_snapshot_fetcher.fetch_24h_and_7d(
                crew_id=crew_id,
                meeting_date=meeting_date,
                vessel_id=vessel_id,
            )
            preview_rows.append(
                {
                    "crew_id": crew_id,
                    "department": str(crew_member.get("department") or "").strip(),
                    "display_name": str(crew_member.get("crew_name") or crew_id).strip(),
                    "present": True,
                    "rank_name": str(crew_member.get("rank") or "").strip(),
                    "remarks": "",
                    "absence_reason": None,
                    "schema_version": 1,
                    "wrh_data_available": bool(snapshot.get("wrh_data_available")),
                    "wrh_flag": str(snapshot.get("wrh_flag") or "RED"),
                    "wrh_non_compliance_flag": bool(snapshot.get("wrh_non_compliance_flag")),
                    "wrh_rest_hours_24h": snapshot.get("wrh_rest_hours_24h"),
                    "wrh_rest_hours_7d": snapshot.get("wrh_rest_hours_7d"),
                    "warning_codes": list(snapshot.get("warning_codes") or []),
                    "warnings": list(snapshot.get("warnings") or []),
                }
            )
        return preview_rows

    def _resolve_vessel_snapshot(self, *, vessel_id: str, user) -> dict[str, str]:
        if user is not None:
            direct_vessel_id = str(getattr(user, "vessel_id", "") or "").strip()
            direct_vessel_code = str(getattr(user, "vessel_code", "") or "").strip()
            direct_vessel_name = str(getattr(user, "vessel_name", "") or "").strip()
            if vessel_id and vessel_id == direct_vessel_id and (direct_vessel_code or direct_vessel_name):
                return {
                    "id": vessel_id,
                    "vessel_code": direct_vessel_code or vessel_id,
                    "vessel_name": direct_vessel_name or f"Vessel {vessel_id}",
                }

        try:
            if self.connection.vendor == "sqlite":
                rows = self.execute_query(
                    """
                    SELECT id, vesselCode, vesselName
                    FROM VesselData
                    WHERE id = %s
                      AND COALESCE(is_deleted, 0) = 0
                    """,
                    [vessel_id],
                )
            else:
                rows = self.execute_query(
                    """
                    SELECT TOP 1 id, vesselCode, vesselName
                    FROM VesselData
                    WHERE id = CAST(%s AS uniqueidentifier)
                      AND is_deleted = 0
                    """,
                    [vessel_id],
                )
        except (DatabaseError, OperationalError, ProgrammingError, SPExecutionError, SPTimeoutError, ValueError):
            rows = []

        if rows:
            row = rows[0]
            return {
                "id": str(row.get("id") or vessel_id).strip(),
                "vessel_code": str(row.get("vesselCode") or vessel_id).strip(),
                "vessel_name": str(row.get("vesselName") or f"Vessel {vessel_id}").strip(),
            }

        return {
            "id": vessel_id,
            "vessel_code": vessel_id,
            "vessel_name": f"Vessel {vessel_id}" if vessel_id else "",
        }

    def _safe_list_current_vessel_crew(
        self,
        *,
        vessel_id: str,
        active_on: date,
    ) -> list[dict[str, object]]:
        try:
            return self.cms_repository.list_current_vessel_crew(
                vessel_id=vessel_id,
                active_on=active_on,
            )
        except (SPExecutionError, SPTimeoutError):
            return []

    def _safe_closed_since_last_payload(self, *, vessel_id: str) -> dict[str, object]:
        try:
            return self.closed_since_last_service.fetch_for_vessel(vessel_id)
        except (DatabaseError, OperationalError, ProgrammingError, SPExecutionError, SPTimeoutError):
            return self.build_empty_closed_since_last_payload()

    def _safe_overdue_soi_areas(self, *, vessel_id: str) -> list[dict[str, object]]:
        try:
            return self.overdue_soi_blocker.check_overdue_soi(vessel_id)
        except (DatabaseError, OperationalError, ProgrammingError, SPExecutionError, SPTimeoutError):
            return []

    def _build_carried_forward_preview(
        self,
        *,
        vessel_id: str,
        meeting_date: date,
    ) -> list[dict[str, object]]:
        if not vessel_id:
            return []

        try:
            prior_meetings = list(
                self.meeting_model.objects.filter(
                    is_deleted=False,
                    vessel_id=vessel_id,
                    meeting_date__lt=meeting_date,
                )
                .defer(*self._legacy_header_field_names())
                .order_by("-meeting_date", "-id")
            )
        except (DatabaseError, OperationalError, ProgrammingError):
            return []
        if not prior_meetings:
            return []

        meeting_ids = [prior.id for prior in prior_meetings]
        agenda_rows = list(
            self.agenda_model.objects.filter(meeting_id__in=meeting_ids).order_by("meeting_id", "agenda_item_number")
        )
        if not agenda_rows:
            return []

        agenda_row_map = {row.id: row for row in agenda_rows}
        meeting_map = {prior.id: prior for prior in prior_meetings}
        actions = (
            CorrectiveAction.objects.filter(
                is_deleted=False,
                source_table=self.agenda_model._meta.db_table,
                source_id__in=list(agenda_row_map.keys()),
            )
            .exclude(status=CorrectiveAction.Status.CLOSED)
            .order_by("-updated_date", "-id")
        )

        carried_forward: list[dict[str, object]] = []
        for action in actions:
            agenda_row = agenda_row_map.get(action.source_id)
            if agenda_row is None:
                continue
            source_meeting = meeting_map.get(agenda_row.meeting_id)
            if source_meeting is None:
                continue
            carried_forward.append(
                self._serialize_action_item(
                    action,
                    carried_forward=True,
                    agenda_row=agenda_row,
                    source_meeting=source_meeting,
                )
            )
        return carried_forward

    def fetch_latest_msc_circulars(
        self,
        *,
        vessel_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        normalized_vessel_id = str(vessel_id or "").strip()
        row_limit = max(1, min(int(limit or 5), 10))
        vessel_pattern = f"%{normalized_vessel_id}%"

        try:
            if self.connection.vendor == "sqlite":
                rows = self.execute_query(
                    """
                    SELECT
                        id,
                        sr_no,
                        NULL AS msc_type,
                        title,
                        category,
                        office_instructions,
                        hashtags,
                        attachment_name,
                        attachment_path,
                        publish_status,
                        published_on,
                        created_at,
                        vessel_id
                    FROM msc_data
                    WHERE COALESCE(is_deleted, 0) = 0
                      AND COALESCE(is_active, 1) = 1
                      AND COALESCE(is_superseeded, 0) = 0
                      AND publish_status = 2
                      AND (
                        %s = ''
                        OR vessel_id IS NULL
                        OR TRIM(CAST(vessel_id AS TEXT)) = ''
                        OR CAST(vessel_id AS TEXT) LIKE %s
                      )
                    ORDER BY COALESCE(published_on, created_at) DESC
                    LIMIT %s
                    """,
                    [normalized_vessel_id, vessel_pattern, row_limit],
                )
            else:
                rows = self.execute_query(
                    f"""
                    SELECT TOP ({row_limit})
                        CAST(id AS NVARCHAR(64)) AS id,
                        sr_no,
                        msc_type,
                        title,
                        category,
                        office_instructions,
                        hashtags,
                        attachment_name,
                        attachment_path,
                        publish_status,
                        published_on,
                        created_at,
                        vessel_id
                    FROM dbo.msc_data
                    WHERE ISNULL(is_deleted, 0) = 0
                      AND ISNULL(is_active, 1) = 1
                      AND ISNULL(is_superseeded, 0) = 0
                      AND publish_status = 2
                      AND (
                        %s = ''
                        OR vessel_id IS NULL
                        OR LTRIM(RTRIM(CAST(vessel_id AS NVARCHAR(MAX)))) = ''
                        OR CAST(vessel_id AS NVARCHAR(MAX)) LIKE %s
                      )
                    ORDER BY COALESCE(published_on, created_at) DESC
                    """,
                    [normalized_vessel_id, vessel_pattern],
                )
        except (DatabaseError, OperationalError, ProgrammingError, SPExecutionError, SPTimeoutError):
            return []

        return [self._serialize_msc_circular(row) for row in rows]

    def fetch_latest_near_misses(
        self,
        *,
        vessel_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        normalized_vessel_id = str(vessel_id or "").strip()
        row_limit = max(1, min(int(limit or 5), 10))
        if not normalized_vessel_id:
            return []

        try:
            rows = (
                Incident.objects.filter(
                    is_deleted=False,
                    vessel_id=normalized_vessel_id,
                    record_type=Incident.RecordType.NEAR_MISS,
                )
                .order_by("-occurred_at", "-reported_at", "-created_date", "-id")[:row_limit]
            )
        except (DatabaseError, OperationalError, ProgrammingError):
            return []

        return [self._serialize_near_miss(row) for row in rows]

    def fetch_latest_psc_cars(
        self,
        *,
        vessel_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        normalized_vessel_id = str(vessel_id or "").strip()
        row_limit = max(1, min(int(limit or 5), 10))
        if not normalized_vessel_id:
            return []

        try:
            vessel_uuid = UUID(normalized_vessel_id)
        except (TypeError, ValueError):
            return []

        try:
            from apps.inspection.deficiency_models import CAR

            cutoff_meeting = (
                self.meeting_model.objects.filter(
                    vessel_id=normalized_vessel_id,
                    master_signed_off_at__isnull=False,
                )
                .order_by("-master_signed_off_at", "-meeting_date", "-created_date")
                .first()
            )
            queryset = CAR.objects.select_related("deficiency__inspection").filter(
                is_deleted=False,
                deficiency__is_deleted=False,
                deficiency__inspection__is_deleted=False,
                deficiency__inspection__vessel_id=vessel_uuid,
                deficiency__inspection__inspection_type="PSC",
            )
            if cutoff_meeting and cutoff_meeting.master_signed_off_at:
                queryset = queryset.filter(created_date__gt=cutoff_meeting.master_signed_off_at)
            rows = queryset.order_by("-created_date", "-id")[:row_limit]
        except (DatabaseError, OperationalError, ProgrammingError, ImportError, ValueError, FieldError):
            return []

        return [self._serialize_psc_car(row) for row in rows]

    def _serialize_near_miss(self, row: Incident) -> dict[str, object]:
        occurred_at = row.occurred_at
        reported_at = row.reported_at
        closed_at = row.closed_at
        return {
            "id": str(row.id),
            "incident_number": row.incident_number,
            "title": (row.narrative or "").strip() or row.incident_number,
            "state": row.state,
            "severity": row.near_miss_severity or "",
            "priority": row.near_miss_priority or "",
            "occurred_at": occurred_at.isoformat() if hasattr(occurred_at, "isoformat") else occurred_at,
            "reported_at": reported_at.isoformat() if hasattr(reported_at, "isoformat") else reported_at,
            "closed_at": closed_at.isoformat() if hasattr(closed_at, "isoformat") else closed_at,
            "source_route": f"/safety/near-miss/{row.id}",
        }

    @staticmethod
    def _serialize_psc_car(row) -> dict[str, object]:
        deficiency = getattr(row, "deficiency", None)
        inspection = getattr(deficiency, "inspection", None)
        inspection_date = getattr(inspection, "inspection_date", None)
        target_date = getattr(row, "target_date", None) or getattr(deficiency, "target_date", None)
        return {
            "action_code": str(getattr(deficiency, "action_code", None) or getattr(row, "initial_action_code", None) or "").strip(),
            "car_number": str(getattr(row, "car_number", "") or "").strip(),
            "def_code": str(getattr(deficiency, "def_code", "") or "").strip(),
            "deficiency_description": str(getattr(deficiency, "description", "") or "").strip(),
            "id": str(getattr(row, "id", "") or "").strip(),
            "inspection_date": inspection_date.isoformat() if hasattr(inspection_date, "isoformat") else inspection_date,
            "port_place": str(getattr(inspection, "port_place", "") or "").strip(),
            "source_route": f"/cars/{getattr(row, 'id', '')}",
            "status": str(getattr(row, "status", "") or "").strip(),
            "target_date": target_date.isoformat() if hasattr(target_date, "isoformat") else target_date,
        }

    def _serialize_msc_circular(self, row: Mapping[str, object]) -> dict[str, object]:
        published_on = row.get("published_on")
        created_at = row.get("created_at")
        return {
            "id": str(row.get("id") or "").strip(),
            "sr_no": str(row.get("sr_no") or "").strip(),
            "msc_type": str(row.get("msc_type") or "").strip(),
            "title": str(row.get("title") or "").strip(),
            "category": str(row.get("category") or "").strip(),
            "office_instructions": str(row.get("office_instructions") or "").strip(),
            "hashtags": str(row.get("hashtags") or "").strip(),
            "attachment_name": str(row.get("attachment_name") or "").strip(),
            "attachment_path": str(row.get("attachment_path") or "").strip(),
            "publish_status": row.get("publish_status"),
            "published_on": published_on.isoformat() if hasattr(published_on, "isoformat") else published_on,
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
            "vessel_id": str(row.get("vessel_id") or "").strip(),
        }

    def build_form_config(
        self,
        *,
        vessel_id: str | None,
        meeting_type: str = SCMMeeting.MeetingType.REGULAR,
        actor_id: str | None = None,
        user=None,
        meeting_date: date | datetime | str | None = None,
        ) -> dict[str, object]:
        from apps.safety.serializers.scm import build_default_scm_sections

        normalized_vessel_id = str(vessel_id or "").strip()
        anchor_date = self._coerce_meeting_date(meeting_date)
        crew_roster = (
            self._safe_list_current_vessel_crew(
                vessel_id=normalized_vessel_id,
                active_on=anchor_date,
            )
            if normalized_vessel_id
            else []
        )
        prepared_by = self._resolve_prepared_by_snapshot(
            vessel_id=normalized_vessel_id,
            actor_id=actor_id,
            active_on=anchor_date,
        )
        chair = self._resolve_chair_snapshot(
            actor_id=actor_id,
            crew_roster=crew_roster,
            prepared_by=prepared_by,
        )

        return {
            "attendee_rows": self._build_attendee_preview_rows(
                vessel_id=normalized_vessel_id,
                meeting_date=anchor_date,
                crew_roster=crew_roster,
            ),
            "cadence_status": self._build_cadence_status(
                vessel_id=normalized_vessel_id,
                meeting_date=anchor_date,
            ),
            "cadence_warning": self.build_cadence_warning(
                vessel_id=normalized_vessel_id,
                meeting_date=anchor_date,
            ),
            "chair": chair,
            "closed_since_last": (
                self._safe_closed_since_last_payload(vessel_id=normalized_vessel_id)
                if normalized_vessel_id
                else self.build_empty_closed_since_last_payload()
            ),
            "generated_at": timezone.now().isoformat(),
            "latest_circulars": self.fetch_latest_msc_circulars(
                vessel_id=normalized_vessel_id,
                limit=5,
            ),
            "latest_near_misses": self.fetch_latest_near_misses(
                vessel_id=normalized_vessel_id,
                limit=5,
            ),
            "latest_psc_cars": self.fetch_latest_psc_cars(
                vessel_id=normalized_vessel_id,
                limit=5,
            ),
            "meeting_date_default": anchor_date.isoformat(),
            "meeting_type": str(meeting_type or SCMMeeting.MeetingType.REGULAR).strip().upper(),
            "overdue_soi_areas": (
                self._safe_overdue_soi_areas(vessel_id=normalized_vessel_id)
                if normalized_vessel_id
                else []
            ),
            "prepared_by": prepared_by,
            "sections": build_default_scm_sections(),
            "unresolved_previous_actions": self._build_carried_forward_preview(
                vessel_id=normalized_vessel_id,
                meeting_date=anchor_date,
            ),
            "vessel": self._resolve_vessel_snapshot(vessel_id=normalized_vessel_id, user=user),
        }

    def build_agenda_payload(self, *, meeting: SCMMeeting) -> dict[str, object]:
        rows = list(self.list_sections(meeting.id))
        legacy_fields = list(self.list_legacy_fields(meeting.id))
        legacy_map: dict[int, dict[str, object]] = {}
        for field in legacy_fields:
            legacy_map.setdefault(int(field.agenda_item_number), {})[str(field.field_key)] = field
        action_map = self._action_map_for_rows(rows)
        carried_forward_items = self._build_carried_forward_items(meeting=meeting)

        current_action_count = sum(1 for action in action_map.values() if action is not None)
        open_action_count = sum(
            1
            for action in action_map.values()
            if action is not None and action.status != CorrectiveAction.Status.CLOSED
        )

        return {
            "meeting_date": meeting.meeting_date.isoformat(),
            "meeting_id": meeting.id,
            "meeting_state": meeting.state,
            "meeting_type": meeting.meeting_type,
            "rows": [
                self._serialize_agenda_row(row, action_map.get(row.id), legacy_map.get(row.agenda_item_number, {}))
                for row in rows
            ],
            "carried_forward_items": carried_forward_items,
            "summary": {
                "carried_forward_count": len(carried_forward_items),
                "current_action_item_count": current_action_count,
                "open_action_item_count": open_action_count,
            },
        }

    def list_signatures(self, meeting_id: int):
        return self.signature_model.objects.filter(meeting_id=meeting_id).order_by("signer_role", "signed_at", "id")

    def signature_preflight_complete(self, meeting: SCMMeeting) -> tuple[bool, list[str], dict[str, object]]:
        attendance_rows = list(self.list_attendance(meeting.id))
        signatures = list(self.list_signatures(meeting.id))
        co_signer_crew_id = self.resolve_regular_co_signature_crew_id(meeting, attendance_rows=attendance_rows)
        co_signature = next(
            (
                signature
                for signature in signatures
                if signature.signer_role == SCMSignature.SignerRole.CO
                and str(signature.signer_crew_id) == co_signer_crew_id
            ),
            None,
        )
        attendee_signature_ids = {
            str(signature.signer_crew_id)
            for signature in signatures
            if signature.signer_role == SCMSignature.SignerRole.ATTENDEE
        }

        errors: list[str] = []
        present_rows = [row for row in attendance_rows if row.present]
        if not attendance_rows:
            errors.append("SCM attendance must be recorded before final sign-off.")

        if meeting.meeting_type == SCMMeeting.MeetingType.REGULAR and co_signature is None:
            errors.append("Regular SCM requires the Chief Officer co-signature before Master sign-off.")

        missing_attendees = []
        for row in present_rows:
            crew_id = str(row.crew_id)
            if crew_id in attendee_signature_ids:
                continue
            if crew_id == co_signer_crew_id and co_signature is not None:
                continue
            missing_attendees.append(row.display_name or crew_id)
        if missing_attendees:
            errors.append(
                "Present attendee digital signatures missing: "
                + ", ".join(missing_attendees)
                + "."
            )

        summary = {
            "co_signature_required": meeting.meeting_type == SCMMeeting.MeetingType.REGULAR,
            "co_signature_present": co_signature is not None,
            "missing_attendee_signatures": missing_attendees,
            "present_attendee_count": len(present_rows),
            "signed_attendee_count": len(present_rows) - len(missing_attendees),
        }
        return not errors, errors, summary

    def agenda_preflight_complete(self, meeting_id: int) -> tuple[bool, list[str]]:
        from apps.safety.serializers.scm import SCM_LEGACY_FIELD_TEMPLATE, _coerce_legacy_value

        rows = list(self.list_sections(meeting_id))
        legacy_map: dict[int, dict[str, object]] = {}
        for field in self.list_legacy_fields(meeting_id):
            legacy_map.setdefault(int(field.agenda_item_number), {})[str(field.field_key)] = _coerce_legacy_value(
                field.field_value,
                str(field.field_type),
            )

        errors: list[str] = []
        if len(rows) != 9:
            errors.append("SCM agenda must contain the locked SCM section structure.")
        for row in rows:
            section_number = int(row.agenda_item_number)
            if section_number == 9:
                continue
            if not SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ()):
                continue

            section_fields = legacy_map.get(section_number, {})
            has_legacy_values = any(value not in (None, "") for value in section_fields.values())
            for field in SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ()):
                if not field.get("required"):
                    continue
                value = section_fields.get(str(field["field_key"]))
                if value in (None, ""):
                    errors.append(f"Section {section_number} requires {field['field_label']}.")

            if section_number == 1 and self._discussion_has_missing_reason(
                section_fields.get("near_miss_discussion_status"),
                section_fields.get("near_miss_not_discussed_reason"),
            ):
                errors.append("Section 1 requires a reason for each near miss marked not discussed.")

            if section_number == 2 and self._discussion_has_missing_reason(
                section_fields.get("circular_discussion_status"),
                section_fields.get("circular_not_discussed_reason"),
            ):
                errors.append("Section 2 requires a reason for each circular / safety alert / work instruction marked not discussed.")

            if not has_legacy_values and not str(row.content or "").strip():
                errors.append(f"Section {row.agenda_item_number} requires discussion content.")
            if not str(row.decision or "").strip() and not self._legacy_section_supplies_decision(
                section_number,
                section_fields,
            ):
                errors.append(f"Section {row.agenda_item_number} requires recommendation / suggestions.")
        return not errors, errors

    @staticmethod
    def _legacy_section_supplies_decision(
        section_number: int,
        section_fields: Mapping[str, object],
    ) -> bool:
        if section_number == 8:
            return section_fields.get("miscellaneous_comments") not in (None, "")

        if section_number != 7:
            return False

        return any(
            section_fields.get(f"findings{index}") not in (None, "")
            and section_fields.get(f"correctivemeasure{index}") not in (None, "")
            for index in range(1, 11)
        )

    @staticmethod
    def _discussion_has_missing_reason(status_value: object, reason_value: object) -> bool:
        raw_status = str(status_value or "").strip()
        if not raw_status:
            return False
        if raw_status.upper() == "NOT_DISCUSSED":
            return not str(reason_value or "").strip()
        if not raw_status.startswith("["):
            return False
        try:
            rows = json.loads(raw_status)
        except (TypeError, ValueError):
            return False
        if not isinstance(rows, list):
            return False
        return any(
            str(row.get("status") or "").strip().upper() == "NOT_DISCUSSED"
            and not str(row.get("reason") or "").strip()
            for row in rows
            if isinstance(row, Mapping)
        )

    @staticmethod
    def _serialize_signature_status(
        signature: SCMSignature | None,
        *,
        required: bool,
        signer_role: str,
        signer_crew_id: str,
    ) -> dict[str, object]:
        if signature is None:
            return {
                "display_name": None,
                "required": required,
                "signed_at": None,
                "signer_crew_id": signer_crew_id,
                "signer_role": signer_role,
                "status": "NOT_SIGNED" if required else "NOT_REQUIRED",
                "typed_name": None,
            }
        return {
            "display_name": signature.display_name,
            "required": required,
            "signed_at": signature.signed_at.isoformat() if signature.signed_at else None,
            "signer_crew_id": signature.signer_crew_id,
            "signer_role": signature.signer_role,
            "status": "SIGNED",
            "typed_name": signature.typed_name,
        }

    def update_agenda(
        self,
        *,
        meeting: SCMMeeting,
        rows: list[dict[str, object]],
        actor_id: str,
    ) -> SCMMeeting:
        if not rows:
            return self.read(meeting.id)

        section_map = {
            row.agenda_item_number: row
            for row in self.agenda_model.objects.filter(meeting_id=meeting.id)
        }

        with transaction.atomic():
            for row_payload in rows:
                agenda_item_number = int(row_payload["agenda_item_number"])
                agenda_row = section_map[agenda_item_number]

                updated_fields: list[str] = []
                if "legacy_fields" in row_payload:
                    legacy_content = self._save_legacy_fields(
                        meeting_id=meeting.id,
                        agenda_item_number=agenda_item_number,
                        values=row_payload.get("legacy_fields"),
                    )
                    agenda_row.content = legacy_content or str(row_payload.get("content", "") or "")
                    updated_fields.append("content")
                if "content" in row_payload:
                    if "legacy_fields" not in row_payload:
                        agenda_row.content = str(row_payload.get("content", "") or "")
                        updated_fields.append("content")
                if "decision" in row_payload:
                    decision_value = row_payload.get("decision")
                    agenda_row.decision = (
                        None if decision_value in (None, "") else str(decision_value)
                    )
                    updated_fields.append("decision")
                if "linked_finding_ids" in row_payload:
                    finding_ids = self._coerce_id_list(row_payload.get("linked_finding_ids"))
                    self._validate_linked_findings(finding_ids, vessel_id=str(meeting.vessel_id))
                    agenda_row.linked_finding_ids = self._join_id_list(finding_ids)
                    updated_fields.append("linked_finding_ids")
                if "linked_incident_ids" in row_payload:
                    incident_ids = self._coerce_id_list(row_payload.get("linked_incident_ids"))
                    self._validate_linked_incidents(incident_ids, vessel_id=str(meeting.vessel_id))
                    agenda_row.linked_incident_ids = self._join_id_list(incident_ids)
                    updated_fields.append("linked_incident_ids")
                if updated_fields:
                    agenda_row.save(update_fields=updated_fields)

                action_payload = row_payload.get("action_item")
                if isinstance(action_payload, dict) and action_payload.get("enabled"):
                    self._upsert_agenda_action_item(
                        agenda_row=agenda_row,
                        action_payload=action_payload,
                        actor_id=actor_id,
                    )

        return self.read(meeting.id)

    def assign_scm_number(self, *, vessel_code: str, meeting_date: date) -> str:
        base_number = f"{vessel_code}-{meeting_date.strftime('%d-%b-%Y')}"

        with transaction.atomic():
            existing_numbers = list(
                self.meeting_model.objects.select_for_update()
                .filter(scm_number__startswith=base_number)
                .values_list("scm_number", flat=True)
            )
            if base_number not in existing_numbers:
                return base_number

            suffix = 2
            while f"{base_number}-{suffix:02d}" in existing_numbers:
                suffix += 1
            return f"{base_number}-{suffix:02d}"

    def _replace_sections(self, meeting_id: int, sections: list[dict[str, object]]) -> None:
        self.agenda_model.objects.filter(meeting_id=meeting_id).delete()
        self.legacy_field_model.objects.filter(meeting_id=meeting_id).delete()
        agenda_rows = []
        for section in sections:
            agenda_item_number = int(section["agenda_item_number"])
            legacy_content = self._save_legacy_fields(
                meeting_id=meeting_id,
                agenda_item_number=agenda_item_number,
                values=section.get("legacy_fields"),
            )
            agenda_rows.append(
                self.agenda_model(
                    meeting_id=meeting_id,
                    agenda_item_number=agenda_item_number,
                    section_label=str(section["section_label"]),
                    auto_populated=bool(section.get("auto_populated", False)),
                    content=legacy_content or str(section.get("content", "")),
                    decision=str(section["decision"]) if section.get("decision") not in (None, "") else None,
                    schema_version=int(section.get("schema_version", 1)),
                )
            )
        self.agenda_model.objects.bulk_create(agenda_rows)

    def _save_legacy_fields(
        self,
        *,
        meeting_id: int,
        agenda_item_number: int,
        values: object,
    ) -> str:
        from apps.safety.serializers.scm import (
            SCM_LEGACY_FIELD_TEMPLATE,
            build_legacy_section_content,
            legacy_value_for_storage,
            normalize_legacy_fields,
        )

        normalized = normalize_legacy_fields(agenda_item_number, values)
        if not self._scm_legacy_field_table_available():
            return build_legacy_section_content(agenda_item_number, normalized)
        for field in SCM_LEGACY_FIELD_TEMPLATE.get(agenda_item_number, ()):
            field_key = str(field["field_key"])
            self.legacy_field_model.objects.update_or_create(
                meeting_id=meeting_id,
                agenda_item_number=agenda_item_number,
                field_key=field_key,
                defaults={
                    "field_label": str(field["field_label"]),
                    "field_type": str(field["field_type"]),
                    "field_value": legacy_value_for_storage(normalized.get(field_key), str(field["field_type"])),
                    "schema_version": 1,
                },
            )
        return build_legacy_section_content(agenda_item_number, normalized)

    def _coerce_meeting_date(self, value: object) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        return timezone.localdate()

    def _normalize_vessel_code(self, explicit_code: object, vessel_id: object) -> str:
        for candidate in (explicit_code, vessel_id):
            if candidate is None:
                continue
            text = str(candidate).strip().upper()
            if text:
                return text
        return "UNKNOWN"

    def _create_meeting_without_legacy_header_columns(self, data: Mapping[str, object]) -> int:
        now = timezone.now()
        columns = [
            "vessel_id",
            "scm_number",
            "meeting_type",
            "meeting_date",
            "meeting_time_local",
            "location",
            "latitude",
            "longitude",
            "voyage_no",
            "chair_crew_id",
            "prepared_by_crew_id",
            "ad_hoc_trigger_reason",
            "office_comment",
            "office_comment_by",
            "office_comment_at",
            "state",
            "master_signed_off_at",
            "master_signed_off_by",
            "attendance_warnings_acknowledged_at",
            "attendance_warnings_acknowledged_by",
            "pdf_export_path",
            "schema_version",
            "is_deleted",
            "is_archived",
            "archived_at",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        ]
        values = [
            data.get("vessel_id"),
            data.get("scm_number"),
            data.get("meeting_type", SCMMeeting.MeetingType.REGULAR),
            data.get("meeting_date"),
            data.get("meeting_time_local"),
            data.get("location"),
            data.get("latitude"),
            data.get("longitude"),
            data.get("voyage_no"),
            data.get("chair_crew_id"),
            data.get("prepared_by_crew_id"),
            data.get("ad_hoc_trigger_reason"),
            data.get("office_comment"),
            data.get("office_comment_by"),
            data.get("office_comment_at"),
            data.get("state", SCMMeeting.State.DRAFT),
            data.get("master_signed_off_at"),
            data.get("master_signed_off_by"),
            data.get("attendance_warnings_acknowledged_at"),
            data.get("attendance_warnings_acknowledged_by"),
            data.get("pdf_export_path"),
            int(data.get("schema_version", 1)),
            bool(data.get("is_deleted", False)),
            bool(data.get("is_archived", False)),
            data.get("archived_at"),
            data.get("created_by"),
            data.get("created_date") or now,
            data.get("updated_by"),
            data.get("updated_date"),
        ]
        quoted_columns = ", ".join(f"[{column}]" for column in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        statement = (
            f"INSERT INTO [{self.meeting_model._meta.db_table}] ({quoted_columns}) "
            f"OUTPUT INSERTED.[id] VALUES ({placeholders})"
        )
        with connection.cursor() as cursor:
            cursor.execute(statement, values)
            row = cursor.fetchone()
        return int(row[0])

    @staticmethod
    def _legacy_header_field_names() -> tuple[str, ...]:
        return (
            "occasion",
            "ship_position",
            "ship_pos_from",
            "ship_pos_to",
            "comm_time",
            "comp_time",
        )

    def _scm_meeting_legacy_columns_available(self) -> bool:
        if hasattr(self, "_legacy_columns_available"):
            return bool(self._legacy_columns_available)
        required = set(self._legacy_header_field_names())
        try:
            with connection.cursor() as cursor:
                existing = {
                    column.name
                    for column in connection.introspection.get_table_description(
                        cursor,
                        self.meeting_model._meta.db_table,
                    )
                }
        except Exception:
            self._legacy_columns_available = False
            return False
        self._legacy_columns_available = required.issubset(existing)
        return bool(self._legacy_columns_available)

    def _scm_legacy_field_table_available(self) -> bool:
        if hasattr(self, "_legacy_field_table_available"):
            return bool(self._legacy_field_table_available)
        try:
            existing = set(connection.introspection.table_names())
        except Exception:
            self._legacy_field_table_available = True
            return True
        self._legacy_field_table_available = self.legacy_field_model._meta.db_table in existing
        return bool(self._legacy_field_table_available)

    def _build_attendance_warnings(
        self,
        *,
        rows: list[SCMAttendance],
        timezone_offset_minutes: int | None,
        runtime_warning_details: Mapping[str, Mapping[str, object]] | None = None,
    ) -> list[str]:
        warnings: list[str] = []
        if timezone_offset_minutes is None:
            warnings.append(
                "Warning: WRH ship-time configuration unavailable for this vessel/date. "
                "Attendance rows remain editable and submission proceeds."
            )

        runtime_warning_details = runtime_warning_details or {}
        for row in rows:
            row_runtime_detail = runtime_warning_details.get(str(row.crew_id)) or {}
            row_display_name = str(row_runtime_detail.get("display_name") or row.display_name)
            warning_codes = {str(code) for code in row_runtime_detail.get("warning_codes", [])}

            if "lookup_timeout" in warning_codes:
                warnings.append(
                    f"Warning: WRH lookup timed out for '{row_display_name}'. Row flagged; submission proceeds (D-GAP-M11)."
                )
            elif "lookup_failed" in warning_codes:
                warnings.append(
                    f"Warning: WRH lookup failed for '{row_display_name}'. Row flagged; submission proceeds (D-GAP-M11)."
                )
            elif "missing_data" in warning_codes or not row.wrh_data_available:
                warnings.append(
                    f"Warning: WRH data unavailable for '{row_display_name}'. Row flagged; submission proceeds (D-GAP-M11)."
                )

            if row.wrh_non_compliance_flag:
                warnings.append(
                    f"Warning: WRH non-compliance for '{row_display_name}'. Meeting may proceed (D-GAP-M11)."
                )
        return warnings

    def _action_map_for_rows(
        self,
        rows: list[SCMAgendaItem],
    ) -> dict[int, CorrectiveAction | None]:
        if not rows:
            return {}

        actions = (
            CorrectiveAction.objects.filter(
                is_deleted=False,
                source_table=self.agenda_model._meta.db_table,
                source_id__in=[row.id for row in rows],
            )
            .order_by("source_id", "-id")
        )

        action_map: dict[object, CorrectiveAction | None] = {row.id: None for row in rows}
        for action in actions:
            action_map.setdefault(action.source_id, action)
            if action_map[action.source_id] is None:
                action_map[action.source_id] = action
        return action_map

    def _build_carried_forward_items(self, *, meeting: SCMMeeting) -> list[dict[str, object]]:
        return self._build_carried_forward_preview(
            vessel_id=str(meeting.vessel_id),
            meeting_date=meeting.meeting_date,
        )

    def _serialize_agenda_row(
        self,
        row: SCMAgendaItem,
        action: CorrectiveAction | None,
        legacy_fields: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        from apps.safety.serializers.scm import _blank_legacy_fields, _coerce_legacy_value, _legacy_field_meta

        section_number = int(row.agenda_item_number)
        normalized_legacy_fields = _blank_legacy_fields(section_number)
        for field_key, field in (legacy_fields or {}).items():
            normalized_legacy_fields[str(field_key)] = _coerce_legacy_value(field.field_value, str(field.field_type))
        return {
            "id": row.id,
            "agenda_item_number": row.agenda_item_number,
            "section_label": row.section_label,
            "auto_populated": row.auto_populated,
            "content": row.content,
            "decision": row.decision,
            "legacy_field_meta": _legacy_field_meta(section_number),
            "legacy_fields": normalized_legacy_fields,
            "linked_finding_ids": self._split_id_list(row.linked_finding_ids),
            "linked_incident_ids": self._split_id_list(row.linked_incident_ids),
            "action_item": self._serialize_action_item(action, agenda_row=row) if action is not None else None,
        }

    @staticmethod
    def _split_id_list(value: object) -> list[str]:
        if value in (None, ""):
            return []
        items: list[str] = []
        for part in str(value).split(","):
            part = part.strip()
            if not part:
                continue
            items.append(part)
        return items

    @staticmethod
    def _join_id_list(value: object) -> str | None:
        ids = SCMRepository._coerce_id_list(value)
        if not ids:
            return None
        return ",".join(str(item) for item in ids)

    @staticmethod
    def _coerce_id_list(value: object) -> list[str]:
        if value in (None, ""):
            return []
        if not isinstance(value, (list, tuple, set)):
            value = [part.strip() for part in str(value).split(",") if part.strip()]
        normalized: list[str] = []
        for item in value:
            item_value = str(item or "").strip()
            if item_value:
                normalized.append(item_value)
        return normalized

    def _validate_linked_incidents(self, incident_ids: list[str], *, vessel_id: str) -> None:
        if not incident_ids:
            return
        found = set(
            Incident.objects.filter(
                id__in=incident_ids,
                vessel_id=vessel_id,
                is_deleted=False,
            ).values_list("id", flat=True)
        )
        found_ids = {str(item) for item in found}
        missing = sorted(set(incident_ids) - found_ids)
        if missing:
            raise ValidationError({"linked_incident_ids": [f"Invalid or out-of-scope incident ids: {missing}."]})

    def _validate_linked_findings(self, finding_ids: list[str], *, vessel_id: str) -> None:
        if not finding_ids:
            return
        inspection_ids = SOIInspection.objects.filter(
            vessel_id=vessel_id,
            is_deleted=False,
        ).values_list("id", flat=True)
        found = set(
            SOIFinding.objects.filter(
                id__in=finding_ids,
                inspection_id__in=inspection_ids,
                is_deleted=False,
            ).values_list("id", flat=True)
        )
        found_ids = {str(item) for item in found}
        missing = sorted(set(finding_ids) - found_ids)
        if missing:
            raise ValidationError({"linked_finding_ids": [f"Invalid or out-of-scope SOI finding ids: {missing}."]})

    def _serialize_action_item(
        self,
        action: CorrectiveAction,
        *,
        carried_forward: bool = False,
        agenda_row: SCMAgendaItem | None = None,
        source_meeting: SCMMeeting | None = None,
    ) -> dict[str, object]:
        payload = {
            "id": action.id,
            "title": action.title,
            "description": action.description,
            "assigned_crew_id": action.assigned_crew_id,
            "assigned_office_user_id": action.assigned_office_user_id,
            "due_date": action.due_date.isoformat() if action.due_date else None,
            "status": action.status,
            "display_status": self._display_action_status(action.status, carried_forward=carried_forward),
            "source_route": f"/api/safety/corrective-actions/{action.id}/",
        }
        if agenda_row is not None:
            payload["agenda_item_number"] = agenda_row.agenda_item_number
            payload["section_label"] = agenda_row.section_label
        if source_meeting is not None:
            payload["source_meeting_id"] = source_meeting.id
            payload["source_scm_number"] = source_meeting.scm_number
        return payload

    def _display_action_status(self, status: str, *, carried_forward: bool) -> str:
        if carried_forward and status != CorrectiveAction.Status.CLOSED:
            return "CARRIED_FORWARD"
        if status in {CorrectiveAction.Status.PENDING_VERIFY, CorrectiveAction.Status.REOPENED}:
            return CorrectiveAction.Status.IN_PROGRESS
        return status

    def _upsert_agenda_action_item(
        self,
        *,
        agenda_row: SCMAgendaItem,
        action_payload: dict[str, object],
        actor_id: str,
    ) -> CorrectiveAction:
        action = (
            CorrectiveAction.objects.filter(
                is_deleted=False,
                source_table=self.agenda_model._meta.db_table,
                source_id=agenda_row.id,
            )
            .order_by("-id")
            .first()
        )

        defaults = {
            "title": str(action_payload["title"]),
            "description": str(action_payload["description"]),
            "assigned_crew_id": action_payload.get("assigned_crew_id"),
            "assigned_office_user_id": action_payload.get("assigned_office_user_id"),
            "due_date": action_payload.get("due_date"),
            "updated_by": actor_id,
            "updated_date": timezone.now(),
        }

        if action is None:
            action = CorrectiveAction.objects.create(
                source_table=self.agenda_model._meta.db_table,
                source_id=agenda_row.id,
                status=CorrectiveAction.Status.OPEN,
                created_by=actor_id,
                schema_version=1,
                **defaults,
            )
            return action

        for field_name, value in defaults.items():
            setattr(action, field_name, value)
        action.save(update_fields=list(defaults.keys()))
        return action
