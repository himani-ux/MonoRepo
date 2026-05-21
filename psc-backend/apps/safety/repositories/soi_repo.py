from __future__ import annotations

from collections.abc import Mapping
import re
import uuid

from django.db import transaction
from django.utils import timezone

from apps.safety.models import (
    SOIApplicabilityLog,
    SOIInspection,
    SOIInspectionArea,
    SOITrainee,
    SOIVesselAreaMap,
)
from apps.safety.services.soi_schema_guard import ensure_soi_runtime_schema

from .base import BaseRepository


_VESSEL_CODE_SANITIZE_RE = re.compile(r"[^A-Z0-9]")
_DIGIT_RE = re.compile(r"\D")


class SOIRepository(BaseRepository):
    def __init__(
        self,
        *,
        inspection_model=SOIInspection,
        inspection_area_model=SOIInspectionArea,
        trainee_model=SOITrainee,
        area_map_model=SOIVesselAreaMap,
        applicability_log_model=SOIApplicabilityLog,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.inspection_model = inspection_model
        self.inspection_area_model = inspection_area_model
        self.trainee_model = trainee_model
        self.area_map_model = area_map_model
        self.applicability_log_model = applicability_log_model

    def create(self, payload: Mapping[str, object]) -> SOIInspection:
        ensure_soi_runtime_schema()
        data = dict(payload)
        data.setdefault("state", SOIInspection.State.PLANNED)
        data.setdefault("master_crew_id", None)
        data.setdefault("checklist_unique_id", None)
        data.setdefault("checklist_generated_at", None)
        data.setdefault("checklist_format", None)
        data.setdefault("fieldwork_started_at", None)
        data.setdefault("reported_at", None)
        data.setdefault("closed_at", None)
        data.setdefault("lost_paper_flag", False)
        data.setdefault("lost_paper_note", None)
        data.setdefault("section_12_included", False)
        data.setdefault("schema_version", 1)
        data.setdefault("public_id", uuid.uuid4().hex)
        data.setdefault("is_deleted", False)
        data.setdefault("is_archived", False)
        data.setdefault("archived_at", None)
        data.setdefault("created_date", timezone.now())
        data.setdefault("updated_by", data.get("created_by"))
        data.setdefault("updated_date", None)
        self._insert_without_returning(data)
        return self.inspection_model.objects.get(
            inspection_reference=str(data["inspection_reference"]),
            is_deleted=False,
        )

    def _build_initial_checklist_unique_id(self, data: Mapping[str, object]) -> str:
        vessel_id = str(data.get("vessel_id") or "")
        planned_date = data.get("planned_date") or timezone.localdate()
        inspection_reference = str(data.get("inspection_reference") or "")
        sequence = (
            self.inspection_model.objects.filter(
                vessel_id=vessel_id,
                planned_date=planned_date,
                checklist_unique_id__isnull=False,
                is_deleted=False,
            ).count()
            + 1
        )
        imo_number = self._resolve_imo_number(
            vessel_id=vessel_id,
            inspection_reference=inspection_reference,
        )
        unique_id = self._format_checklist_unique_id(
            imo_number=imo_number,
            planned_date=planned_date,
            sequence=sequence,
        )
        while self.inspection_model.objects.filter(checklist_unique_id=unique_id).exists():
            sequence += 1
            unique_id = self._format_checklist_unique_id(
                imo_number=imo_number,
                planned_date=planned_date,
                sequence=sequence,
            )
        return unique_id

    def _resolve_imo_number(self, *, vessel_id: str, inspection_reference: str) -> str:
        candidates = [self._query_vessel_imo(vessel_id), vessel_id, inspection_reference]
        for candidate in candidates:
            digits = _DIGIT_RE.sub("", str(candidate or ""))
            if len(digits) >= 7:
                return digits[:7]
        for candidate in candidates:
            digits = _DIGIT_RE.sub("", str(candidate or ""))
            if digits:
                return digits[-7:].zfill(7)
        return "0000000"

    def _query_vessel_imo(self, vessel_id: str) -> str | None:
        try:
            with self.connection.cursor() as cursor:
                table_names = self.connection.introspection.table_names(cursor)
                if "VesselData" not in table_names:
                    return None
                cursor.execute(
                    """
                    SELECT TOP 1 imoNumber
                    FROM VesselData
                    WHERE (CAST(id AS NVARCHAR(64)) = %s OR vesselCode = %s)
                      AND (is_deleted = 0 OR is_deleted IS NULL)
                    """,
                    [vessel_id, vessel_id],
                )
                row = cursor.fetchone()
        except Exception:
            return None
        return str(row[0]) if row and row[0] not in (None, "") else None

    @staticmethod
    def _format_checklist_unique_id(*, imo_number: str, planned_date, sequence: int) -> str:
        return f"SOI-{imo_number}-{planned_date:%Y%m%d}-{sequence:04d}"

    def _insert_without_returning(self, data: Mapping[str, object]) -> None:
        field_names = [
            "public_id",
            "vessel_id",
            "inspection_reference",
            "cycle_label",
            "state",
            "planned_date",
            "safety_officer_crew_id",
            "safety_officer_department",
            "assistant_crew_id",
            "assistant_department",
            "master_crew_id",
            "checklist_unique_id",
            "checklist_generated_at",
            "checklist_format",
            "fieldwork_started_at",
            "reported_at",
            "closed_at",
            "lost_paper_flag",
            "lost_paper_note",
            "section_12_included",
            "schema_version",
            "is_deleted",
            "is_archived",
            "archived_at",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        ]
        model_fields = {field.name: field for field in self.inspection_model._meta.concrete_fields}
        quote_name = self.connection.ops.quote_name
        table_name = quote_name(self.inspection_model._meta.db_table)
        columns = ", ".join(quote_name(model_fields[field_name].column) for field_name in field_names)
        placeholders = ", ".join(["%s"] * len(field_names))
        values = [data.get(field_name) for field_name in field_names]
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                values,
            )

    def create_planned_inspection(
        self,
        *,
        inspection_payload: Mapping[str, object],
        area_ids: list[int],
        trainee_crew_ids: list[str],
    ) -> SOIInspection:
        with transaction.atomic():
            inspection = self.create(inspection_payload)
            self._replace_selected_areas(inspection_id=inspection.id, area_ids=area_ids)
            self._replace_trainees(inspection_id=inspection.id, trainee_crew_ids=trainee_crew_ids)
        return self.read(inspection.id)

    def resolve_vessel_reference_code(self, *, vessel_id: str) -> str:
        normalized_vessel_id = str(vessel_id or "").strip()
        vessel_code = ""
        if normalized_vessel_id:
            try:
                vessel_code = str(
                    self.execute_scalar(
                        """
                        SELECT vesselCode
                        FROM VesselData
                        WHERE CAST(id AS VARCHAR(64)) = %s
                           OR vesselCode = %s
                        ORDER BY vesselCode
                        """,
                        [normalized_vessel_id, normalized_vessel_id],
                    )
                    or ""
                ).strip()
            except Exception:
                vessel_code = ""

        return self._short_reference_token(vessel_code or normalized_vessel_id or "VESSEL")

    @staticmethod
    def _short_reference_token(value: object) -> str:
        token = _VESSEL_CODE_SANITIZE_RE.sub("", str(value or "").upper())[:8]
        return token or "VESSEL"

    def read(self, inspection_id: int) -> SOIInspection:
        return self.inspection_model.objects.get(pk=inspection_id, is_deleted=False)

    def mark_checklist_downloaded(
        self,
        *,
        inspection_id: int,
        requested_format: str,
    ) -> SOIInspection:
        normalized_format = str(requested_format).strip().upper()
        if normalized_format not in {
            SOIInspection.ChecklistFormat.PDF,
            SOIInspection.ChecklistFormat.XLSX,
        }:
            raise ValueError("SOI checklist downloads only support PDF or XLSX.")

        with transaction.atomic():
            inspection = self.inspection_model.objects.select_for_update().get(
                pk=int(inspection_id),
                is_deleted=False,
            )
            update_fields: dict[str, object] = {}

            if inspection.checklist_format != normalized_format:
                update_fields["checklist_format"] = normalized_format
            if inspection.checklist_generated_at is None:
                update_fields["checklist_generated_at"] = timezone.now()
            if inspection.state == SOIInspection.State.PLANNED:
                update_fields["state"] = SOIInspection.State.DOWNLOADED

            if update_fields:
                self.inspection_model.objects.filter(pk=inspection.pk).update(**update_fields)

        return self.read(int(inspection_id))

    def log_lost_paper_recovery(
        self,
        *,
        inspection_id: int,
        actor_id: str,
        reason: str,
    ) -> SOIInspection:
        normalized_reason = str(reason).strip()
        if not normalized_reason:
            raise ValueError("Lost-paper recovery requires a reason.")

        with transaction.atomic():
            inspection = self.inspection_model.objects.select_for_update().get(
                pk=int(inspection_id),
                is_deleted=False,
            )
            if not inspection.checklist_unique_id or inspection.checklist_generated_at is None:
                raise ValueError("Lost-paper recovery is only available after the checklist has been downloaded.")

            timestamp = timezone.now()
            entry = self._build_lost_paper_entry(
                actor_id=actor_id,
                reason=normalized_reason,
                timestamp=timestamp,
            )
            if inspection.lost_paper_note:
                combined_note = f"{inspection.lost_paper_note.rstrip()}\n{entry}"
            else:
                combined_note = entry

            self.inspection_model.objects.filter(pk=inspection.pk).update(
                lost_paper_flag=True,
                lost_paper_note=combined_note,
                updated_by=actor_id,
                updated_date=timestamp,
            )

        return self.read(int(inspection_id))

    def list(self, *, filters: Mapping[str, object] | None = None):
        queryset = self.inspection_model.objects.filter(is_deleted=False)
        filters = filters or {}

        if vessel_id := filters.get("vessel_id"):
            queryset = queryset.filter(vessel_id=str(vessel_id))
        if state := filters.get("state"):
            queryset = queryset.filter(state=str(state).strip().upper())
        if cycle_label := filters.get("cycle_label"):
            queryset = queryset.filter(cycle_label=str(cycle_label))
        if date_from := filters.get("date_from"):
            queryset = queryset.filter(planned_date__gte=date_from)
        if date_to := filters.get("date_to"):
            queryset = queryset.filter(planned_date__lte=date_to)
        return queryset.order_by("-planned_date", "-id")

    def list_available_areas(self, *, vessel_id: str) -> list[dict[str, object]]:
        return [row for row in self.list_applicability(vessel_id=vessel_id) if row["applicable"]]

    def list_applicability(self, *, vessel_id: str) -> list[dict[str, object]]:
        rows = self.execute_query(
            """
            SELECT
                map.id AS map_id,
                area.area_id AS area_id,
                area.area_name AS area_name,
                area.section_12_flag AS section_12_flag,
                area.display_order AS display_order,
                COALESCE(map.applicable, 1) AS applicable,
                map.last_inspected_at AS last_inspected_at,
                map.due_at AS due_at,
                COALESCE(map.schema_version, 1) AS schema_version
            FROM master_soi_area AS area
            LEFT JOIN vims_safety_soi_vessel_area_map AS map
                ON map.area_id = area.area_id
               AND map.vessel_id = %s
            WHERE area.active = %s
            ORDER BY area.display_order ASC, area.area_id ASC
            """,
            [str(vessel_id), True],
        )
        return [
            {
                **row,
                "map_id": None if row.get("map_id") in (None, "") else int(row["map_id"]),
                "area_id": int(row["area_id"]),
                "section_12_flag": bool(row["section_12_flag"]),
                "applicable": bool(row["applicable"]),
                "schema_version": int(row["schema_version"] or 1),
            }
            for row in rows
        ]

    def list_selected_areas(self, inspection_id: int) -> list[dict[str, object]]:
        rows = self.execute_query(
            """
            SELECT
                selection.id AS selection_id,
                selection.inspection_id AS inspection_id,
                selection.area_id AS area_id,
                area.area_name AS area_name,
                area.section_12_flag AS section_12_flag,
                area.display_order AS display_order,
                selection.inspected AS inspected,
                selection.last_inspected_at AS last_inspected_at,
                selection.notes AS notes,
                COALESCE(selection.schema_version, 1) AS schema_version
            FROM vims_safety_soi_inspection_area AS selection
            JOIN master_soi_area AS area
                ON area.area_id = selection.area_id
            WHERE selection.inspection_id = %s
            ORDER BY area.display_order ASC, selection.area_id ASC
            """,
            [int(inspection_id)],
        )
        return [
            {
                "area_id": int(row["area_id"]),
                "area_name": row["area_name"],
                "display_order": int(row["display_order"]),
                "inspected": bool(row["inspected"]),
                "inspection_id": int(row["inspection_id"]),
                "last_inspected_at": row["last_inspected_at"],
                "notes": row["notes"],
                "schema_version": int(row["schema_version"] or 1),
                "section_12_flag": bool(row["section_12_flag"]),
                "selection_id": int(row["selection_id"]),
            }
            for row in rows
        ]

    def list_checklist_items_for_areas(self, *, area_ids: list[int]) -> list[dict[str, object]]:
        normalized_area_ids = sorted({int(area_id) for area_id in area_ids})
        if not normalized_area_ids:
            return []
        placeholders = ", ".join(["%s"] * len(normalized_area_ids))
        rows = self.execute_query(
            f"""
            SELECT
                id,
                legacy_int_id,
                area_id,
                area_name,
                subsection_id,
                subsection_name,
                item_number,
                description,
                tier
            FROM master_soi_area_item
            WHERE active = %s
              AND area_id IN ({placeholders})
            ORDER BY area_id ASC, subsection_id ASC, item_number ASC, id ASC
            """,
            [True, *normalized_area_ids],
        )
        return [
            {
                "id": str(row["id"]),
                "legacy_int_id": int(row["legacy_int_id"]),
                "area_id": int(row["area_id"]),
                "area_name": row["area_name"],
                "subsection_id": int(row["subsection_id"]),
                "subsection_name": row["subsection_name"],
                "item_number": str(row["item_number"]),
                "description": row["description"],
                "tier": row["tier"],
            }
            for row in rows
        ]

    def resolve_checklist_item_legacy_id(self, *, item_id: object, area_id: int) -> int | None:
        raw_item_id = str(item_id or "").strip()
        if not raw_item_id:
            return None
        where_sql = "id = %s"
        value: object = raw_item_id.replace("-", "").lower()
        if raw_item_id.isdigit():
            where_sql = "legacy_int_id = %s"
            value = int(raw_item_id)
        row_value = self.execute_scalar(
            f"""
            SELECT legacy_int_id
            FROM master_soi_area_item
            WHERE {where_sql}
              AND area_id = %s
              AND active = %s
            """,
            [value, int(area_id), True],
        )
        return int(row_value) if row_value not in (None, "") else None

    def checklist_item_belongs_to_area(self, *, item_id: object, area_id: int) -> bool:
        return self.resolve_checklist_item_legacy_id(item_id=item_id, area_id=area_id) is not None

    def checklist_item_belongs_to_area_legacy(self, *, item_id: int, area_id: int) -> bool:
        value = self.execute_scalar(
            """
            SELECT COUNT(*)
            FROM master_soi_area_item
            WHERE legacy_int_id = %s
              AND area_id = %s
              AND active = %s
            """,
            [int(item_id), int(area_id), True],
        )
        return int(value or 0) > 0

    def replace_selected_areas(
        self,
        *,
        inspection_id: int,
        area_ids: list[int],
        section_12_included: bool,
    ) -> dict[str, object]:
        with transaction.atomic():
            self._replace_selected_areas(inspection_id=inspection_id, area_ids=area_ids)
            self.inspection_model.objects.filter(pk=int(inspection_id), is_deleted=False).update(
                section_12_included=bool(section_12_included)
            )
        return self.build_pick_areas_payload(inspection_id=inspection_id)

    def build_pick_areas_payload(self, *, inspection_id: int) -> dict[str, object]:
        inspection = self.read(inspection_id)
        return {
            "available_areas": self.list_available_areas(vessel_id=inspection.vessel_id),
            "inspection_id": inspection.id,
            "section_12_included": bool(inspection.section_12_included),
            "selected_areas": self.list_selected_areas(inspection.id),
            "vessel_id": inspection.vessel_id,
        }

    def list_pending_applicability_requests(self, *, vessel_id: str) -> list[dict[str, object]]:
        rows = self.execute_query(
            """
            SELECT
                log.id AS request_id,
                log.vessel_id AS vessel_id,
                log.area_id AS area_id,
                area.area_name AS area_name,
                area.section_12_flag AS section_12_flag,
                log.old_applicable AS old_applicable,
                log.new_applicable AS new_applicable,
                log.reason AS reason,
                log.master_requested_by AS master_requested_by,
                log.master_requested_at AS master_requested_at,
                log.master_signature AS master_signature
            FROM vims_safety_soi_applicability_log AS log
            JOIN master_soi_area AS area
                ON area.area_id = log.area_id
            WHERE log.vessel_id = %s
              AND log.dpa_decision IS NULL
            ORDER BY log.master_requested_at DESC, log.id DESC
            """,
            [str(vessel_id)],
        )
        return [
            {
                "request_id": int(row["request_id"]),
                "vessel_id": str(row["vessel_id"]),
                "area_id": int(row["area_id"]),
                "area_name": row["area_name"],
                "section_12_flag": bool(row["section_12_flag"]),
                "old_applicable": bool(row["old_applicable"]),
                "new_applicable": bool(row["new_applicable"]),
                "reason": row["reason"],
                "master_requested_by": row["master_requested_by"],
                "master_requested_at": row["master_requested_at"],
                "master_signature": row["master_signature"],
            }
            for row in rows
        ]

    def list_trainees(self, inspection_id: int) -> list[dict[str, object]]:
        return [
            {
                "crew_id": row.crew_id,
                "inspection_id": row.inspection_id,
                "schema_version": row.schema_version,
                "trainee_slot": row.trainee_slot,
            }
            for row in self.trainee_model.objects.filter(inspection_id=int(inspection_id)).order_by("trainee_slot", "id")
        ]

    def replace_trainees(self, *, inspection_id: int, trainee_crew_ids: list[str]) -> dict[str, object]:
        with transaction.atomic():
            self._replace_trainees(inspection_id=inspection_id, trainee_crew_ids=trainee_crew_ids)
        return {"inspection_id": int(inspection_id), "trainees": self.list_trainees(int(inspection_id))}

    def create_applicability_request(
        self,
        *,
        vessel_id: str,
        area_id: int,
        new_applicable: bool,
        actor_id: str,
        reason: str,
        master_signature: str,
    ) -> dict[str, object]:
        normalized_reason = str(reason).strip()
        normalized_signature = str(master_signature).strip()
        requested_applicable = bool(new_applicable)
        existing = self.area_map_model.objects.filter(vessel_id=str(vessel_id), area_id=int(area_id)).first()
        current_applicable = True if existing is None else bool(existing.applicable)

        if requested_applicable == current_applicable:
            state_label = "applicable" if current_applicable else "non-applicable"
            raise ValueError(f"Area already marked {state_label} for this vessel.")

        with transaction.atomic():
            pending_request = (
                self.applicability_log_model.objects.select_for_update()
                .filter(
                    vessel_id=str(vessel_id),
                    area_id=int(area_id),
                    dpa_decision__isnull=True,
                )
                .order_by("-master_requested_at", "-id")
                .first()
            )
            if pending_request is not None:
                raise ValueError("An applicability request is already pending DPA decision for this area.")

            log_row = self.applicability_log_model.objects.create(
                vessel_id=str(vessel_id),
                area_id=int(area_id),
                old_applicable=current_applicable,
                new_applicable=requested_applicable,
                reason=normalized_reason,
                master_requested_by=actor_id,
                master_signature=normalized_signature,
                schema_version=1,
            )

        area_name = self.execute_scalar(
            "SELECT area_name FROM master_soi_area WHERE area_id = %s",
            [int(area_id)],
        )
        return {
            "request_id": log_row.id,
            "status": "PENDING_APPROVAL",
            "vessel_id": str(vessel_id),
            "area_id": int(area_id),
            "area_name": area_name,
            "current_applicable": current_applicable,
            "requested_applicable": requested_applicable,
            "reason": normalized_reason,
            "master_requested_by": actor_id,
            "master_requested_at": log_row.master_requested_at,
        }

    def decide_applicability_request(
        self,
        *,
        vessel_id: str,
        area_id: int,
        actor_id: str,
        dpa_signature: str,
        dpa_decision: str,
        decision_note: str,
    ) -> dict[str, object]:
        normalized_signature = str(dpa_signature).strip()
        normalized_decision = str(dpa_decision).strip().upper()
        normalized_note = str(decision_note).strip()

        if normalized_decision not in {
            self.applicability_log_model.Decision.APPROVED,
            self.applicability_log_model.Decision.REJECTED,
        }:
            raise ValueError("Applicability approval must be APPROVED or REJECTED.")

        with transaction.atomic():
            pending_request = (
                self.applicability_log_model.objects.select_for_update()
                .filter(
                    vessel_id=str(vessel_id),
                    area_id=int(area_id),
                    dpa_decision__isnull=True,
                )
                .order_by("-master_requested_at", "-id")
                .first()
            )
            if pending_request is None:
                raise ValueError("No pending applicability request found for this vessel area.")

            current_map = (
                self.area_map_model.objects.select_for_update()
                .filter(vessel_id=str(vessel_id), area_id=int(area_id))
                .first()
            )
            current_applicable = True if current_map is None else bool(current_map.applicable)
            decision_timestamp = timezone.now()
            pending_request.reason = self._append_dpa_decision_note(
                existing_reason=pending_request.reason,
                actor_id=actor_id,
                decision=normalized_decision,
                note=normalized_note,
                timestamp=decision_timestamp,
            )
            pending_request.dpa_approved_by = actor_id
            pending_request.dpa_approved_at = decision_timestamp
            pending_request.dpa_signature = normalized_signature
            pending_request.dpa_decision = normalized_decision
            pending_request.save(
                update_fields=[
                    "reason",
                    "dpa_approved_by",
                    "dpa_approved_at",
                    "dpa_signature",
                    "dpa_decision",
                ]
            )

            map_row = current_map
            if normalized_decision == self.applicability_log_model.Decision.APPROVED:
                map_row, _created = self.area_map_model.objects.update_or_create(
                    vessel_id=str(vessel_id),
                    area_id=int(area_id),
                    defaults={
                        "applicable": bool(pending_request.new_applicable),
                        "schema_version": 1 if current_map is None else current_map.schema_version,
                    },
                )

        area_name = self.execute_scalar(
            "SELECT area_name FROM master_soi_area WHERE area_id = %s",
            [int(area_id)],
        )
        resulting_applicable = (
            bool(map_row.applicable)
            if map_row is not None
            else current_applicable
        )
        return {
            "request_id": pending_request.id,
            "status": normalized_decision,
            "decision": normalized_decision,
            "vessel_id": str(vessel_id),
            "area_id": int(area_id),
            "area_name": area_name,
            "current_applicable": current_applicable,
            "applicable": resulting_applicable,
            "requested_applicable": bool(pending_request.new_applicable),
            "reason": pending_request.reason,
            "dpa_approved_by": actor_id,
            "dpa_approved_at": pending_request.dpa_approved_at,
            "map_id": map_row.id if map_row is not None else None,
        }

    def update_applicability(
        self,
        *,
        vessel_id: str,
        area_id: int,
        applicable: bool,
        actor_id: str,
        reason: str,
        master_signature: str,
        dpa_approved_by: str | None = None,
        dpa_signature: str | None = None,
        dpa_decision: str | None = None,
    ) -> dict[str, object]:
        existing = self.area_map_model.objects.filter(vessel_id=str(vessel_id), area_id=int(area_id)).first()
        old_applicable = True if existing is None else bool(existing.applicable)
        now_value = timezone.now()
        normalized_decision = None if dpa_decision in (None, "") else str(dpa_decision).strip().upper()

        with transaction.atomic():
            map_row, _created = self.area_map_model.objects.update_or_create(
                vessel_id=str(vessel_id),
                area_id=int(area_id),
                defaults={
                    "applicable": bool(applicable),
                    "schema_version": 1 if existing is None else existing.schema_version,
                },
            )
            self.applicability_log_model.objects.create(
                vessel_id=str(vessel_id),
                area_id=int(area_id),
                old_applicable=old_applicable,
                new_applicable=bool(applicable),
                reason=reason,
                master_requested_by=actor_id,
                master_requested_at=now_value,
                master_signature=master_signature,
                dpa_approved_by=dpa_approved_by,
                dpa_approved_at=now_value if dpa_approved_by else None,
                dpa_signature=dpa_signature,
                dpa_decision=normalized_decision,
                schema_version=1,
            )

        area_name = self.execute_scalar(
            "SELECT area_name FROM master_soi_area WHERE area_id = %s",
            [int(area_id)],
        )
        return {
            "map_id": map_row.id,
            "vessel_id": str(vessel_id),
            "area_id": int(area_id),
            "area_name": area_name,
            "applicable": bool(map_row.applicable),
            "last_inspected_at": map_row.last_inspected_at.isoformat() if map_row.last_inspected_at else None,
            "due_at": map_row.due_at.isoformat() if map_row.due_at else None,
            "schema_version": map_row.schema_version,
        }

    def _replace_selected_areas(self, *, inspection_id: int, area_ids: list[int]) -> None:
        selected_ids = [int(area_id) for area_id in area_ids]
        self.inspection_area_model.objects.filter(inspection_id=int(inspection_id)).exclude(
            area_id__in=selected_ids
        ).delete()

        existing_ids = set(
            self.inspection_area_model.objects.filter(inspection_id=int(inspection_id)).values_list("area_id", flat=True)
        )
        create_rows = [
            self.inspection_area_model(
                inspection_id=int(inspection_id),
                area_id=area_id,
                schema_version=1,
            )
            for area_id in selected_ids
            if area_id not in existing_ids
        ]
        if create_rows:
            self.inspection_area_model.objects.bulk_create(create_rows)

    def _replace_trainees(self, *, inspection_id: int, trainee_crew_ids: list[str]) -> None:
        self.trainee_model.objects.filter(inspection_id=int(inspection_id)).delete()
        rows = [
            self.trainee_model(
                inspection_id=int(inspection_id),
                crew_id=str(crew_id),
                trainee_slot=index + 1,
                schema_version=1,
            )
            for index, crew_id in enumerate(trainee_crew_ids)
        ]
        if rows:
            self.trainee_model.objects.bulk_create(rows)

    @staticmethod
    def _build_lost_paper_entry(
        *,
        actor_id: str,
        reason: str,
        timestamp,
    ) -> str:
        return (
            f"[{timestamp.isoformat(timespec='seconds')}] "
            f"Lost/damaged paper reported by {actor_id}: {reason}"
        )

    @staticmethod
    def _append_dpa_decision_note(
        *,
        existing_reason: str,
        actor_id: str,
        decision: str,
        note: str,
        timestamp,
    ) -> str:
        base_reason = str(existing_reason).rstrip()
        suffix = (
            f"[{timestamp.isoformat(timespec='seconds')}] "
            f"DPA {decision} by {actor_id}: {note}"
        )
        return f"{base_reason}\n{suffix}" if base_reason else suffix
