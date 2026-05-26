from __future__ import annotations

from typing import Any

from apps.safety.services.fts_engine import FtsUnavailableError, SafetyFtsEngine

from apps.safety.models import Incident, SCMMeeting, SOIFinding, SOIInspection
from apps.safety.serializers.near_miss import NearMissListSerializer
from apps.safety.serializers.vessel_display import resolve_vessel_display
from apps.safety.authentication.vessel_scope import get_scoped_vessel_ids, has_global_vessel_scope
from apps.safety.services.archive_state import archive_filter, is_archived_record


class CrossRecordSearchService:
    GROUP_ORDER = ("INCIDENT", "NEAR_MISS", "SCM", "SOI_FINDING")
    GROUP_LABELS = {
        "INCIDENT": "Incidents",
        "NEAR_MISS": "Near Miss",
        "SCM": "SCM",
        "SOI_FINDING": "SOI Findings",
    }
    RECORD_TYPE_ALIASES = {
        "INCIDENT": "INCIDENT",
        "NEAR_MISS": "NEAR_MISS",
        "SCM": "SCM",
        "SOI": "SOI_FINDING",
        "SOI_FINDING": "SOI_FINDING",
    }

    def __init__(
        self,
        *,
        incident_model=Incident,
        meeting_model=SCMMeeting,
        finding_model=SOIFinding,
        inspection_model=SOIInspection,
        near_miss_list_serializer_class=NearMissListSerializer,
        fts_engine: SafetyFtsEngine | None = None,
    ) -> None:
        self.incident_model = incident_model
        self.meeting_model = meeting_model
        self.finding_model = finding_model
        self.inspection_model = inspection_model
        self.near_miss_list_serializer_class = near_miss_list_serializer_class
        self.fts_engine = fts_engine or SafetyFtsEngine()

    def search(
        self,
        query: str,
        *,
        user=None,
        record_type: str | None = None,
        include_archived: bool = False,
        limit_per_group: int = 10,
    ) -> dict[str, Any]:
        normalized_query = str(query or "").strip()
        normalized_record_type = self.normalize_record_type(record_type)
        groups = {group_key: [] for group_key in self.GROUP_ORDER}

        if normalized_record_type in (None, "INCIDENT"):
            groups["INCIDENT"] = self._search_incidents(
                normalized_query,
                user=user,
                include_archived=include_archived,
                limit=limit_per_group,
            )
        if normalized_record_type in (None, "NEAR_MISS"):
            groups["NEAR_MISS"] = self._search_near_misses(
                normalized_query,
                user=user,
                include_archived=include_archived,
                limit=limit_per_group,
            )
        if normalized_record_type in (None, "SCM"):
            groups["SCM"] = self._search_scm(
                normalized_query,
                user=user,
                include_archived=include_archived,
                limit=limit_per_group,
            )
        if normalized_record_type in (None, "SOI_FINDING"):
            groups["SOI_FINDING"] = self._search_soi_findings(
                normalized_query,
                user=user,
                include_archived=include_archived,
                limit=limit_per_group,
            )

        counts = {
            group_key: len(groups[group_key])
            for group_key in self.GROUP_ORDER
        }
        return {
            "counts": counts,
            "groups": groups,
            "include_archived": include_archived,
            "labels": dict(self.GROUP_LABELS),
            "query": normalized_query,
            "record_type": normalized_record_type or "ALL",
            "total_count": sum(counts.values()),
        }

    def normalize_record_type(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        return self.RECORD_TYPE_ALIASES.get(str(value).strip().upper())

    def _search_incidents(
        self,
        query: str,
        *,
        user,
        include_archived: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        queryset = self.incident_model.objects.filter(
            is_deleted=False,
            record_type=self.incident_model.RecordType.INCIDENT,
        )
        queryset = self._apply_vessel_scope(queryset, user=user)
        if not include_archived:
            queryset = queryset.filter(archive_filter(archived=False))
        queryset = self._rank_incident_queryset(
            queryset,
            query=query,
            record_type=self.incident_model.RecordType.INCIDENT,
            include_archived=include_archived,
            user=user,
        )
        return [
            self._with_vessel_display(
                {
                "archived": is_archived_record(incident),
                "id": incident.pk,
                "id": str(incident.id),
                "record_label": "Incident",
                "record_type": "INCIDENT",
                "reference": incident.incident_number,
                "route": self._incident_route(incident),
                "snippet": self._build_snippet(
                    query,
                    incident.narrative,
                    fallback=incident.closure_reason,
                ),
                "state": incident.state,
                "title": incident.incident_number,
                "vessel_id": str(incident.vessel_id),
                "when": self._iso_datetime(incident.occurred_at or incident.created_date),
                },
                incident.vessel_id,
                user=user,
            )
            for incident in queryset[:limit]
        ]

    def _search_near_misses(
        self,
        query: str,
        *,
        user,
        include_archived: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        queryset = self.incident_model.objects.filter(
            is_deleted=False,
            record_type=self.incident_model.RecordType.NEAR_MISS,
        )
        queryset = self._apply_vessel_scope(queryset, user=user)
        if not include_archived:
            queryset = queryset.filter(archive_filter(archived=False))
        queryset = self._rank_near_miss_queryset(
            queryset,
            query=query,
            include_archived=include_archived,
            user=user,
        )
        items: list[dict[str, Any]] = []
        for near_miss in queryset[:limit]:
            base_payload = self.near_miss_list_serializer_class(
                near_miss,
                context={"user": user},
            ).data
            items.append(
                {
                    "archived": is_archived_record(near_miss),
                    "id": near_miss.pk,
                    "id": str(near_miss.id),
                    "near_miss_priority": near_miss.near_miss_priority,
                    "record_label": "Near Miss",
                    "record_type": "NEAR_MISS",
                    "reference": near_miss.incident_number,
                    "reporter_name": base_payload.get("reporter_name"),
                    "route": f"/safety/near-miss/{near_miss.id}",
                    "snippet": self._build_snippet(
                        query,
                        near_miss.narrative,
                        fallback=near_miss.closure_reason,
                    ),
                    "state": near_miss.state,
                    "title": near_miss.incident_number,
                    "vessel_id": str(near_miss.vessel_id),
                    "vessel_code": base_payload.get("vessel_code"),
                    "vessel_name": base_payload.get("vessel_name"),
                    "vessel_display_name": base_payload.get("vessel_display_name"),
                    "when": self._iso_datetime(near_miss.occurred_at or near_miss.created_date),
                }
            )
        return items

    def _search_scm(
        self,
        query: str,
        *,
        user,
        include_archived: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        queryset = self.meeting_model.objects.filter(is_deleted=False)
        queryset = self._apply_vessel_scope(queryset, user=user)
        if not include_archived:
            queryset = queryset.filter(archive_filter(archived=False))
        queryset = self._rank_scm_queryset(
            queryset,
            query=query,
            include_archived=include_archived,
            user=user,
        )
        return [
            self._with_vessel_display(
                {
                "archived": is_archived_record(meeting),
                "id": meeting.pk,
                "id": str(meeting.id),
                "record_label": "SCM",
                "record_type": "SCM",
                "reference": meeting.scm_number,
                "route": f"/safety/scm/{meeting.id}",
                "snippet": self._build_snippet(
                    query,
                    meeting.ad_hoc_trigger_reason,
                    fallback=meeting.office_comment or meeting.location,
                ),
                "state": meeting.state,
                "title": meeting.scm_number,
                "vessel_id": str(meeting.vessel_id),
                "when": meeting.meeting_date.isoformat(),
                },
                meeting.vessel_id,
                user=user,
            )
            for meeting in queryset[:limit]
        ]

    def _search_soi_findings(
        self,
        query: str,
        *,
        user,
        include_archived: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        inspections = self.inspection_model.objects.filter(is_deleted=False)
        vessel_ids = self._visible_vessel_ids(user)
        if vessel_ids is not None:
            inspections = inspections.filter(vessel_id__in=vessel_ids)
        if not include_archived:
            inspections = inspections.filter(archive_filter(archived=False))
        inspection_map = {
            inspection.pk: inspection
            for inspection in inspections
        }
        if not inspection_map:
            return []

        queryset = self.finding_model.objects.filter(
            is_deleted=False,
            inspection_id__in=inspection_map.keys(),
        )
        queryset = self._rank_soi_queryset(
            queryset,
            query=query,
            include_archived=include_archived,
            user=user,
        )
        items: list[dict[str, Any]] = []
        for finding in queryset[:limit]:
            inspection = inspection_map.get(finding.inspection_id)
            if inspection is None:
                continue
            items.append(
                self._with_vessel_display(
                    {
                    "archived": is_archived_record(inspection),
                    "id": finding.pk,
                    "id": str(finding.id),
                    "inspection_id": inspection.pk,
                    "inspection_id": str(inspection.id),
                    "record_label": "SOI Finding",
                    "record_type": "SOI_FINDING",
                    "reference": inspection.inspection_reference,
                    "route": f"/safety/soi/{inspection.id}/findings/{finding.id}",
                    "snippet": self._build_snippet(
                        query,
                        finding.description,
                        fallback=finding.proposed_action or finding.closure_note,
                    ),
                    "state": finding.status,
                    "title": finding.title,
                    "vessel_id": str(inspection.vessel_id),
                    "when": self._iso_datetime(finding.created_date),
                    },
                    inspection.vessel_id,
                    user=user,
                )
            )
        return items

    @staticmethod
    def _with_vessel_display(payload: dict[str, Any], vessel_id: object, *, user) -> dict[str, Any]:
        vessel = resolve_vessel_display(vessel_id, user=user)
        return {
            **payload,
            "vessel_code": vessel["vessel_code"],
            "vessel_name": vessel["vessel_name"],
            "vessel_display_name": vessel["vessel_display_name"],
        }

    def _apply_vessel_scope(self, queryset, *, user):
        vessel_ids = self._visible_vessel_ids(user)
        if vessel_ids is None:
            return queryset
        return queryset.filter(vessel_id__in=vessel_ids)

    @staticmethod
    def _visible_vessel_ids(user) -> list[str] | None:
        if has_global_vessel_scope(user):
            return None
        return sorted(get_scoped_vessel_ids(user))

    def _rank_incident_queryset(self, queryset, *, query: str, record_type: str, include_archived: bool, user):
        primary_keys = self._sql_server_incident_matches(
            query=query,
            record_type=record_type,
            include_archived=include_archived,
            user=user,
        )
        if primary_keys is not None:
            records = list(queryset.filter(pk__in=primary_keys).distinct())
            ordered_records = self.fts_engine.order_records(records, primary_keys)
            return ordered_records
        return self.fts_engine.rank_queryset_portable(
            queryset,
            query=query,
            identifier_fields=("incident_number",),
            text_fields=("narrative", "closure_reason"),
            related_identifier_fields=("cause_tags__mscat_subcode_id",),
            ordering=("-occurred_at", "-created_date", "-id"),
        )

    def _rank_near_miss_queryset(self, queryset, *, query: str, include_archived: bool, user):
        primary_keys = self._sql_server_incident_matches(
            query=query,
            record_type=self.incident_model.RecordType.NEAR_MISS,
            include_archived=include_archived,
            user=user,
            include_reporter_name=True,
        )
        if primary_keys is not None:
            records = list(queryset.filter(pk__in=primary_keys).distinct())
            return self.fts_engine.order_records(records, primary_keys)
        return self.fts_engine.rank_queryset_portable(
            queryset,
            query=query,
            identifier_fields=("incident_number",),
            text_fields=("narrative", "closure_reason", "reporter_name"),
            ordering=("-occurred_at", "-created_date", "-id"),
        )

    def _rank_scm_queryset(self, queryset, *, query: str, include_archived: bool, user):
        primary_keys = self._sql_server_scm_matches(
            query=query,
            include_archived=include_archived,
            user=user,
        )
        if primary_keys is not None:
            records = list(queryset.filter(pk__in=primary_keys).distinct())
            return self.fts_engine.order_records(records, primary_keys)
        return self.fts_engine.rank_queryset_portable(
            queryset,
            query=query,
            identifier_fields=("scm_number",),
            text_fields=("ad_hoc_trigger_reason", "office_comment", "location"),
            ordering=("-meeting_date", "-created_date", "-id"),
        )

    def _rank_soi_queryset(self, queryset, *, query: str, include_archived: bool, user):
        primary_keys = self._sql_server_soi_matches(
            query=query,
            include_archived=include_archived,
            user=user,
        )
        if primary_keys is not None:
            records = list(queryset.filter(pk__in=primary_keys).distinct())
            return self.fts_engine.order_records(records, primary_keys)
        return self.fts_engine.rank_queryset_portable(
            queryset,
            query=query,
            identifier_fields=(),
            text_fields=("title", "description", "closure_note", "proposed_action"),
            ordering=("-created_date", "-id"),
        )

    def _sql_server_incident_matches(
        self,
        *,
        query: str,
        record_type: str,
        include_archived: bool,
        user,
        include_reporter_name: bool = False,
    ) -> list[int] | None:
        if not self.fts_engine.supports_sql_server_fts():
            return None

        where_sql, where_params = self._incident_where_sql(
            record_type=record_type,
            include_archived=include_archived,
            user=user,
        )
        text_columns = ["incident_number", "narrative", "closure_reason"]
        if include_reporter_name:
            text_columns.append("reporter_name")
        try:
            return self.fts_engine.search_sql_server_primary_keys(
                query=query,
                source_table="vims_safety_incident",
                text_columns=text_columns,
                identifier_columns=("incident_number",),
                base_where_sql=where_sql,
                base_where_params=where_params,
                additional_match_clauses=(
                    (
                        "EXISTS (SELECT 1 FROM dbo.vims_safety_cause_tag ct WHERE ct.incident_id = src.id AND ct.mscat_subcode_id LIKE %s)",
                        (f"{query}%",),
                        4300.0,
                    ),
                ),
            )
        except FtsUnavailableError:
            return None

    def _sql_server_scm_matches(self, *, query: str, include_archived: bool, user) -> list[int] | None:
        if not self.fts_engine.supports_sql_server_fts():
            return None

        where_sql, where_params = self._base_record_where_sql(
            alias="src",
            include_archived=include_archived,
            user=user,
        )
        try:
            return self.fts_engine.search_sql_server_primary_keys(
                query=query,
                source_table="vims_safety_scm_meeting",
                text_columns=("scm_number", "ad_hoc_trigger_reason", "office_comment", "location"),
                identifier_columns=("scm_number",),
                base_where_sql=where_sql,
                base_where_params=where_params,
            )
        except FtsUnavailableError:
            return None

    def _sql_server_soi_matches(self, *, query: str, include_archived: bool, user) -> list[int] | None:
        if not self.fts_engine.supports_sql_server_fts():
            return None

        where_sql, where_params = self._soi_where_sql(
            include_archived=include_archived,
            user=user,
        )
        try:
            return self.fts_engine.search_sql_server_primary_keys(
                query=query,
                source_table="vims_safety_soi_finding",
                text_columns=("title", "description", "closure_note", "proposed_action"),
                identifier_columns=(),
                base_where_sql=where_sql,
                base_where_params=where_params,
                base_join_sql="JOIN dbo.vims_safety_soi_inspection inspection ON inspection.id = src.inspection_id",
            )
        except FtsUnavailableError:
            return None

    def _incident_where_sql(self, *, record_type: str, include_archived: bool, user) -> tuple[str, list[object]]:
        where_sql, params = self._base_record_where_sql(
            alias="src",
            include_archived=include_archived,
            user=user,
        )
        return f"{where_sql} AND src.record_type = %s", [*params, record_type]

    def _soi_where_sql(self, *, include_archived: bool, user) -> tuple[str, list[object]]:
        clauses = [
            "src.is_deleted = %s",
            "inspection.is_deleted = %s",
        ]
        params: list[object] = [False, False]
        if not include_archived:
            clauses.extend(
                [
                    "inspection.is_archived = %s",
                    "inspection.archived_at IS NULL",
                ]
            )
            params.append(False)
        vessel_ids = self._visible_vessel_ids(user)
        if vessel_ids is not None:
            if not vessel_ids:
                clauses.append("1 = 0")
            else:
                placeholders = ", ".join(["%s"] * len(vessel_ids))
                clauses.append(f"inspection.vessel_id IN ({placeholders})")
                params.extend(vessel_ids)
        return " AND ".join(clauses), params

    def _base_record_where_sql(self, *, alias: str, include_archived: bool, user) -> tuple[str, list[object]]:
        clauses = [f"{alias}.is_deleted = %s"]
        params: list[object] = [False]
        if not include_archived:
            clauses.extend(
                [
                    f"{alias}.is_archived = %s",
                    f"{alias}.archived_at IS NULL",
                ]
            )
            params.append(False)
        vessel_ids = self._visible_vessel_ids(user)
        if vessel_ids is not None:
            if not vessel_ids:
                clauses.append("1 = 0")
            else:
                placeholders = ", ".join(["%s"] * len(vessel_ids))
                clauses.append(f"{alias}.vessel_id IN ({placeholders})")
                params.extend(vessel_ids)
        return " AND ".join(clauses), params

    @staticmethod
    def _build_snippet(query: str, primary: str | None, *, fallback: str | None = None) -> str:
        candidate = str(primary or fallback or "").strip()
        if not candidate:
            return "Matched on record metadata."

        lowered = candidate.lower()
        query_lower = str(query or "").lower()
        if query_lower and query_lower in lowered:
            start = max(lowered.index(query_lower) - 36, 0)
        else:
            start = 0
        snippet = candidate[start : start + 140].strip()
        if start > 0:
            snippet = f"...{snippet}"
        if start + 140 < len(candidate):
            snippet = f"{snippet}..."
        return snippet

    @staticmethod
    def _incident_route(incident: Incident) -> str:
        phase_number = int(incident.current_phase or 1)
        phase_number = min(max(phase_number, 1), 8)
        return f"/safety/incidents/{incident.id}/phase-{phase_number}"

    @staticmethod
    def _iso_datetime(value) -> str | None:
        if value is None:
            return None
        return value.isoformat()
