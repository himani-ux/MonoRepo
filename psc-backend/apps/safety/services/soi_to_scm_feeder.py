from __future__ import annotations

from datetime import datetime

from django.db import DatabaseError, OperationalError, ProgrammingError, transaction
from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import SCMMeeting
from apps.safety.repositories.base import BaseRepository


class SOIToSCMFeeder:
    ALLOWED_OUTCOME_STATUSES = {"OPEN", "CARRIED_FORWARD", "CLOSED"}

    def __init__(
        self,
        *,
        meeting_model=SCMMeeting,
        repository: BaseRepository | None = None,
        now_func=timezone.now,
    ) -> None:
        self.meeting_model = meeting_model
        self.repository = repository or BaseRepository()
        self.now_func = now_func

    def fetch_for_meeting(self, meeting: SCMMeeting) -> dict[str, object]:
        cutoff_meeting = self._resolve_prior_cutoff_meeting(meeting)
        return self._build_payload(
            vessel_id=str(meeting.vessel_id),
            meeting_id=meeting.id,
            cutoff_meeting=cutoff_meeting,
            upper_bound_at=self.now_func(),
        )

    def fetch_for_vessel(self, vessel_id: str) -> dict[str, object]:
        cutoff_meeting = self._resolve_latest_cutoff_meeting(str(vessel_id))
        return self._build_payload(
            vessel_id=str(vessel_id),
            meeting_id=None,
            cutoff_meeting=cutoff_meeting,
            upper_bound_at=self.now_func(),
        )

    def apply_outcomes_for_meeting(
        self,
        meeting: SCMMeeting,
        *,
        outcomes: list[dict[str, object]],
        actor_id: str,
    ) -> dict[str, object]:
        if not outcomes:
            raise serializers.ValidationError({"outcomes": "At least one SOI finding outcome is required."})

        updated_finding_ids: list[int] = []
        now_value = self.now_func()

        with transaction.atomic():
            for outcome in outcomes:
                finding_id = self._coerce_int(outcome.get("finding_id"), field_name="finding_id")
                next_status = str(outcome.get("next_status") or "").strip().upper()
                decision_note = str(outcome.get("decision_note") or "").strip()

                if next_status not in self.ALLOWED_OUTCOME_STATUSES:
                    raise serializers.ValidationError(
                        {
                            "next_status": (
                                "Outcome status must be one of OPEN, CARRIED_FORWARD, or CLOSED "
                                "for the Step 3.8 auto-feed seam."
                            )
                        }
                    )

                current_row = self._fetch_single_finding_row(finding_id=finding_id)
                if current_row["vessel_id"] != str(meeting.vessel_id):
                    raise serializers.ValidationError(
                        {"finding_id": "SOI finding does not belong to the same vessel as this SCM meeting."}
                    )

                carried_forward_count = int(current_row["carried_forward_count"] or 0)
                if next_status == "CARRIED_FORWARD":
                    carried_forward_count += 1

                closure_note = self._append_decision_note(
                    existing_note=current_row["closure_note"],
                    next_status=next_status,
                    decision_note=decision_note,
                )
                closed_at = now_value if next_status == "CLOSED" else None

                with self.repository.connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE vims_safety_soi_finding
                        SET status = %s,
                            carried_forward_count = %s,
                            closed_at = %s,
                            closure_note = %s,
                            updated_by = %s,
                            updated_date = %s
                        WHERE id = %s
                        """,
                        [
                            next_status,
                            carried_forward_count,
                            closed_at,
                            closure_note,
                            actor_id,
                            now_value,
                            finding_id,
                        ],
                    )

                updated_finding_ids.append(finding_id)

        payload = self.fetch_for_meeting(meeting)
        payload["updated_finding_ids"] = updated_finding_ids
        return payload

    def _build_payload(
        self,
        *,
        vessel_id: str,
        meeting_id: int | None,
        cutoff_meeting: SCMMeeting | None,
        upper_bound_at,
    ) -> dict[str, object]:
        cutoff_at = cutoff_meeting.master_signed_off_at if cutoff_meeting and cutoff_meeting.master_signed_off_at else None
        new_findings = self._fetch_new_findings(
            vessel_id=vessel_id,
            cutoff_at=cutoff_at,
            upper_bound_at=upper_bound_at,
        )
        carried_forward_findings = self._fetch_carried_forward_findings(vessel_id=vessel_id)
        section8 = self._build_section8_summary(
            vessel_id=vessel_id,
            cutoff_at=cutoff_at,
            upper_bound_at=upper_bound_at,
        )

        return {
            "vessel_id": vessel_id,
            "meeting_id": meeting_id,
            "cutoff": self._serialize_cutoff(cutoff_meeting),
            "summary": {
                "new_count": len(new_findings),
                "carried_forward_count": len(carried_forward_findings),
                "total_count": len(new_findings) + len(carried_forward_findings),
            },
            "section8": section8,
            "new_findings": new_findings,
            "carried_forward_findings": carried_forward_findings,
            "empty_message": (
                "No open SOI findings are waiting to feed this SCM."
                if not new_findings and not carried_forward_findings
                else None
            ),
        }

    def _fetch_new_findings(
        self,
        *,
        vessel_id: str,
        cutoff_at,
        upper_bound_at,
    ) -> list[dict[str, object]]:
        params: list[object] = [str(vessel_id), False, False, "CLOSED", "CARRIED_FORWARD", "MASTER_APPROVED", upper_bound_at]
        cutoff_clause = ""
        if cutoff_at is not None:
            cutoff_clause = """
              AND COALESCE(
                    finding.created_date,
                    inspection.reported_at,
                    inspection.fieldwork_started_at,
                    inspection.checklist_generated_at,
                    inspection.planned_date
                  ) > %s
            """
            params.append(cutoff_at)

        rows = self.repository.execute_query(
            f"""
            SELECT
                finding.id AS finding_id,
                finding.area_id AS area_id,
                finding.title AS title,
                finding.description AS description,
                finding.severity AS severity,
                finding.priority AS priority,
                finding.status AS status,
                finding.due_date AS due_date,
                finding.proposed_action AS proposed_action,
                finding.carried_forward_count AS carried_forward_count,
                finding.created_date AS created_date,
                inspection.id AS inspection_id,
                inspection.public_id AS inspection_public_id,
                inspection.inspection_reference AS inspection_reference,
                inspection.checklist_unique_id AS checklist_unique_id
            FROM vims_safety_soi_finding AS finding
            INNER JOIN vims_safety_soi_inspection AS inspection
                ON inspection.id = finding.inspection_id
            WHERE inspection.vessel_id = %s
              AND inspection.is_deleted = %s
              AND finding.is_deleted = %s
              AND finding.status NOT IN (%s, %s, %s)
              AND COALESCE(
                    finding.created_date,
                    inspection.reported_at,
                    inspection.fieldwork_started_at,
                    inspection.checklist_generated_at,
                    inspection.planned_date
                  ) <= %s
              {cutoff_clause}
            ORDER BY
                COALESCE(
                    finding.created_date,
                    inspection.reported_at,
                    inspection.fieldwork_started_at,
                    inspection.checklist_generated_at,
                    inspection.planned_date
                ) DESC,
                finding.id DESC
            """,
            params,
        )
        return [self._serialize_finding_row(row) for row in rows]

    def _fetch_carried_forward_findings(self, *, vessel_id: str) -> list[dict[str, object]]:
        rows = self.repository.execute_query(
            """
            SELECT
                finding.id AS finding_id,
                finding.area_id AS area_id,
                finding.title AS title,
                finding.description AS description,
                finding.severity AS severity,
                finding.priority AS priority,
                finding.status AS status,
                finding.due_date AS due_date,
                finding.proposed_action AS proposed_action,
                finding.carried_forward_count AS carried_forward_count,
                finding.created_date AS created_date,
                inspection.id AS inspection_id,
                inspection.public_id AS inspection_public_id,
                inspection.inspection_reference AS inspection_reference,
                inspection.checklist_unique_id AS checklist_unique_id
            FROM vims_safety_soi_finding AS finding
            INNER JOIN vims_safety_soi_inspection AS inspection
                ON inspection.id = finding.inspection_id
            WHERE inspection.vessel_id = %s
              AND inspection.is_deleted = %s
              AND finding.is_deleted = %s
              AND finding.status = %s
            ORDER BY finding.carried_forward_count DESC, finding.id DESC
            """,
            [str(vessel_id), False, False, "CARRIED_FORWARD"],
        )
        return [self._serialize_finding_row(row) for row in rows]

    def _build_section8_summary(
        self,
        *,
        vessel_id: str,
        cutoff_at,
        upper_bound_at,
    ) -> dict[str, object]:
        inspected_area_count = self._count_inspected_areas(
            vessel_id=vessel_id,
            cutoff_at=cutoff_at,
            upper_bound_at=upper_bound_at,
        )
        applicable_area_count = int(
            self.repository.execute_scalar(
                """
                SELECT COUNT(*)
                FROM vims_safety_soi_vessel_area_map
                WHERE vessel_id = %s
                  AND applicable = %s
                """,
                [str(vessel_id), True],
            )
            or 0
        )
        inspection_count = self._count_inspections(
            vessel_id=vessel_id,
            cutoff_at=cutoff_at,
            upper_bound_at=upper_bound_at,
        )
        coverage_percent = round(
            (inspected_area_count / applicable_area_count) * 100,
            1,
        ) if applicable_area_count else 0.0
        answer = "YES" if inspection_count > 0 else "NO"
        if inspection_count > 0:
            summary_text = (
                f"Yes - {inspection_count} SOI inspection(s) recorded since the prior SCM "
                f"covering {coverage_percent}% of applicable areas."
            )
        else:
            summary_text = "No SOI inspections recorded since the prior SCM."

        return {
            "answer": answer,
            "inspection_count": inspection_count,
            "applicable_area_count": applicable_area_count,
            "inspected_area_count": inspected_area_count,
            "coverage_percent": coverage_percent,
            "summary_text": summary_text,
        }

    def _count_inspections(self, *, vessel_id: str, cutoff_at, upper_bound_at) -> int:
        params: list[object] = [str(vessel_id), False, upper_bound_at]
        cutoff_clause = ""
        if cutoff_at is not None:
            cutoff_clause = """
              AND COALESCE(
                    inspection.reported_at,
                    inspection.fieldwork_started_at,
                    inspection.checklist_generated_at,
                    inspection.planned_date
                  ) > %s
            """
            params.append(cutoff_at)

        value = self.repository.execute_scalar(
            f"""
            SELECT COUNT(*)
            FROM vims_safety_soi_inspection AS inspection
            WHERE inspection.vessel_id = %s
              AND inspection.is_deleted = %s
              AND COALESCE(
                    inspection.reported_at,
                    inspection.fieldwork_started_at,
                    inspection.checklist_generated_at,
                    inspection.planned_date
                  ) <= %s
              {cutoff_clause}
            """,
            params,
        )
        return int(value or 0)

    def _count_inspected_areas(self, *, vessel_id: str, cutoff_at, upper_bound_at) -> int:
        params: list[object] = [str(vessel_id), True, upper_bound_at]
        cutoff_clause = ""
        if cutoff_at is not None:
            cutoff_clause = "AND last_inspected_at > %s"
            params.append(cutoff_at)

        value = self.repository.execute_scalar(
            f"""
            SELECT COUNT(DISTINCT area_id)
            FROM vims_safety_soi_vessel_area_map
            WHERE vessel_id = %s
              AND applicable = %s
              AND last_inspected_at IS NOT NULL
              AND last_inspected_at <= %s
              {cutoff_clause}
            """,
            params,
        )
        return int(value or 0)

    def _fetch_single_finding_row(self, finding_id: int) -> dict[str, object]:
        rows = self.repository.execute_query(
            """
            SELECT
                finding.id AS finding_id,
                finding.status AS status,
                finding.carried_forward_count AS carried_forward_count,
                finding.closure_note AS closure_note,
                inspection.vessel_id AS vessel_id
            FROM vims_safety_soi_finding AS finding
            INNER JOIN vims_safety_soi_inspection AS inspection
                ON inspection.id = finding.inspection_id
            WHERE finding.id = %s
              AND finding.is_deleted = %s
              AND inspection.is_deleted = %s
            """,
            [finding_id, False, False],
        )
        if not rows:
            raise serializers.ValidationError({"finding_id": f"SOI finding {finding_id} does not exist."})
        return rows[0]

    def _resolve_prior_cutoff_meeting(self, meeting: SCMMeeting) -> SCMMeeting | None:
        queryset = (
            self.meeting_model.objects.filter(
                is_deleted=False,
                vessel_id=str(meeting.vessel_id),
                master_signed_off_at__isnull=False,
            )
            .defer("occasion", "ship_position", "ship_pos_from", "ship_pos_to", "comm_time", "comp_time")
            .exclude(pk=meeting.pk)
        )

        if meeting.master_signed_off_at is not None:
            queryset = queryset.filter(master_signed_off_at__lt=meeting.master_signed_off_at)
        else:
            queryset = queryset.filter(meeting_date__lte=meeting.meeting_date)

        try:
            return queryset.order_by("-master_signed_off_at", "-meeting_date", "-id").first()
        except (DatabaseError, OperationalError, ProgrammingError):
            return None

    def _resolve_latest_cutoff_meeting(self, vessel_id: str) -> SCMMeeting | None:
        try:
            return (
                self.meeting_model.objects.filter(
                    is_deleted=False,
                    vessel_id=str(vessel_id),
                    master_signed_off_at__isnull=False,
                )
                .defer("occasion", "ship_position", "ship_pos_from", "ship_pos_to", "comm_time", "comp_time")
                .order_by("-master_signed_off_at", "-meeting_date", "-id")
                .first()
            )
        except (DatabaseError, OperationalError, ProgrammingError):
            return None

    def _serialize_finding_row(self, row: dict[str, object]) -> dict[str, object]:
        inspection_id = int(row["inspection_id"])
        finding_id = int(row["finding_id"])
        return {
            "finding_id": finding_id,
            "inspection_id": inspection_id,
            "public_inspection_id": str(row["inspection_public_id"]),
            "inspection_reference": row["inspection_reference"],
            "checklist_unique_id": row["checklist_unique_id"],
            "title": row["title"],
            "description": row["description"],
            "severity": row["severity"],
            "priority": row["priority"],
            "status": row["status"],
            "area_id": int(row["area_id"]),
            "due_date": self._serialize_date(row.get("due_date")),
            "proposed_action": row.get("proposed_action"),
            "carried_forward_count": int(row["carried_forward_count"] or 0),
            "created_date": self._serialize_datetime(row.get("created_date")),
            "source_route": f"/safety/soi/{row['inspection_public_id']}/findings",
        }

    def _serialize_cutoff(self, meeting: SCMMeeting | None) -> dict[str, object] | None:
        if meeting is None or meeting.master_signed_off_at is None:
            return None
        return {
            "meeting_id": meeting.id,
            "scm_number": meeting.scm_number,
            "meeting_type": meeting.meeting_type,
            "closed_at": self._serialize_datetime(meeting.master_signed_off_at),
        }

    def _serialize_datetime(self, value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                value = timezone.make_aware(value, timezone.get_current_timezone())
            return value.isoformat()
        return str(value)

    def _serialize_date(self, value) -> str | None:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _coerce_int(self, value: object, *, field_name: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError({field_name: f"{field_name} must be an integer."}) from exc

    def _append_decision_note(
        self,
        *,
        existing_note,
        next_status: str,
        decision_note: str,
    ) -> str | None:
        prefix = {
            "OPEN": "Re-opened at SCM",
            "CARRIED_FORWARD": "Carry forward at SCM",
            "CLOSED": "Closed at SCM",
        }[next_status]
        normalized_note = prefix if not decision_note else f"{prefix}: {decision_note}"
        if existing_note in (None, ""):
            return normalized_note
        return f"{existing_note}\n{normalized_note}"
