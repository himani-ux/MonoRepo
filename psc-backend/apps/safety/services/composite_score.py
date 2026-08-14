from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.safety.authentication.vessel_scope import get_scoped_vessel_ids, has_global_vessel_scope, user_has_vessel_access
from apps.safety.models import (
    CorrectiveAction,
    Incident,
    SafetyDashboardRollup,
    SCMAgendaItem,
    SCMMeeting,
    SOIFinding,
    SOIInspection,
    SOIVesselAreaMap,
)
from apps.safety.services.soi_compliance_calculator import SOIComplianceCalculator


@dataclass(frozen=True)
class RollupScope:
    scope_id: str
    scope_type: str


class CompositeScoreService:
    PERIOD_WINDOWS = {
        SafetyDashboardRollup.PeriodCode.DAYS_90: 90,
        SafetyDashboardRollup.PeriodCode.MONTHS_12: 365,
        SafetyDashboardRollup.PeriodCode.YEARS_3: 365 * 3,
    }

    def __init__(
        self,
        *,
        incident_model=Incident,
        corrective_action_model=CorrectiveAction,
        finding_model=SOIFinding,
        inspection_model=SOIInspection,
        meeting_model=SCMMeeting,
        agenda_model=SCMAgendaItem,
        soi_area_map_model=SOIVesselAreaMap,
        rollup_model=SafetyDashboardRollup,
        soi_compliance_calculator: SOIComplianceCalculator | None = None,
        now_func=timezone.now,
    ) -> None:
        self.incident_model = incident_model
        self.corrective_action_model = corrective_action_model
        self.finding_model = finding_model
        self.inspection_model = inspection_model
        self.meeting_model = meeting_model
        self.agenda_model = agenda_model
        self.soi_area_map_model = soi_area_map_model
        self.rollup_model = rollup_model
        self.soi_compliance_calculator = soi_compliance_calculator or SOIComplianceCalculator(now_func=now_func)
        self.now_func = now_func

    def list_known_vessel_ids(self) -> list[str]:
        vessel_ids = set(
            self.incident_model.objects.filter(is_deleted=False).exclude(vessel_id="").values_list("vessel_id", flat=True)
        )
        vessel_ids.update(
            self.inspection_model.objects.filter(is_deleted=False).exclude(vessel_id="").values_list("vessel_id", flat=True)
        )
        vessel_ids.update(
            self.meeting_model.objects.filter(is_deleted=False).exclude(vessel_id="").values_list("vessel_id", flat=True)
        )
        vessel_ids.update(
            self.soi_area_map_model.objects.exclude(vessel_id="").values_list("vessel_id", flat=True)
        )
        return sorted(str(value) for value in vessel_ids if value not in (None, ""))

    def build_rollup(
        self,
        *,
        scope: RollupScope,
        period_code: str = SafetyDashboardRollup.PeriodCode.YEARS_3,
        as_of=None,
    ) -> dict[str, object]:
        normalized_period_code = self._normalize_period_code(period_code)
        current_at = as_of or self.now_func()
        window_end = current_at.date()
        window_start = window_end - timedelta(days=self._window_days(normalized_period_code) - 1)

        open_incident_count = self._count_open_incidents(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        total_incident_count = self._count_total_incidents(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        open_near_miss_count = self._count_open_near_misses(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        total_near_miss_count = self._count_total_near_misses(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        open_finding_count = self._count_open_findings(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        total_finding_count = self._count_total_findings(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        overdue_ca_count = self._count_overdue_corrective_actions(scope=scope, as_of=current_at.date())
        total_ca_count = self._count_total_corrective_actions(
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )
        soi_summary = self._build_soi_summary(scope=scope)

        component_scores: dict[str, int] = {
            "open_incidents": self._score_penalty(open_incident_count, step=25),
            "open_near_misses": self._score_penalty(open_near_miss_count, step=15),
            "open_findings": self._score_penalty(open_finding_count, step=15),
            "overdue_corrective_actions": self._score_penalty(overdue_ca_count, step=20),
        }
        if soi_summary["compliance_percent"] is not None:
            component_scores["soi_compliance"] = int(soi_summary["compliance_percent"])

        composite_score = round(sum(component_scores.values()) / max(len(component_scores), 1))

        return {
            "scope_type": scope.scope_type,
            "scope_id": scope.scope_id,
            "period_code": normalized_period_code,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "calculated_at": current_at.isoformat(),
            "composite_score": composite_score,
            "score_status": self._score_status(composite_score),
            "metrics": {
                "open_incidents": open_incident_count,
                "total_incidents": total_incident_count,
                "open_near_misses": open_near_miss_count,
                "total_near_misses": total_near_miss_count,
                "open_findings": open_finding_count,
                "total_findings": total_finding_count,
                "overdue_corrective_actions": overdue_ca_count,
                "total_corrective_actions": total_ca_count,
                "soi_compliance_percent": soi_summary["compliance_percent"],
                "soi_compliance_display": soi_summary["display_value"],
                "soi_compliance_label": soi_summary["label"],
            },
            "component_scores": component_scores,
        }

    def save_rollup(
        self,
        *,
        scope: RollupScope,
        period_code: str = SafetyDashboardRollup.PeriodCode.YEARS_3,
        as_of=None,
    ) -> SafetyDashboardRollup:
        normalized_period_code = self._normalize_period_code(period_code)
        payload = self.build_rollup(scope=scope, period_code=period_code, as_of=as_of)
        calculated_at = as_of or self.now_func()
        rollup, _ = self.rollup_model.objects.update_or_create(
            scope_type=scope.scope_type,
            scope_id=scope.scope_id,
            period_code=normalized_period_code,
            defaults={
                "window_start": date.fromisoformat(str(payload["window_start"])),
                "window_end": date.fromisoformat(str(payload["window_end"])),
                "composite_score": payload["composite_score"],
                "score_status": payload["score_status"],
                "open_incident_count": payload["metrics"]["open_incidents"],
                "open_near_miss_count": payload["metrics"]["open_near_misses"],
                "open_finding_count": payload["metrics"]["open_findings"],
                "overdue_ca_count": payload["metrics"]["overdue_corrective_actions"],
                "soi_compliance_percent": payload["metrics"]["soi_compliance_percent"],
                "component_scores": payload["component_scores"],
                "calculated_at": calculated_at,
                "updated_by": "dashboard_rollup",
            },
        )
        return rollup

    def resolve_scope(self, *, vessel_id: str | None = None, user=None) -> RollupScope:
        if vessel_id not in (None, ""):
            if user is not None and not user_has_vessel_access(user, vessel_id):
                raise PermissionDenied("You are not assigned to this vessel.")
            return RollupScope(scope_type=SafetyDashboardRollup.ScopeType.VESSEL, scope_id=str(vessel_id))

        if user is not None and has_global_vessel_scope(user):
            return RollupScope(scope_type=SafetyDashboardRollup.ScopeType.FLEET, scope_id="")
        user_vessel_ids = sorted(get_scoped_vessel_ids(user))
        if user_vessel_ids:
            return RollupScope(scope_type=SafetyDashboardRollup.ScopeType.VESSEL, scope_id=user_vessel_ids[0])
        raise PermissionDenied("No vessel scope is assigned to this user.")

    def _normalize_period_code(self, period_code: str) -> str:
        normalized = str(period_code or SafetyDashboardRollup.PeriodCode.YEARS_3).strip().upper()
        if normalized not in self.PERIOD_WINDOWS:
            return SafetyDashboardRollup.PeriodCode.YEARS_3
        return normalized

    def _window_days(self, period_code: str) -> int:
        return self.PERIOD_WINDOWS[self._normalize_period_code(period_code)]

    def _count_open_incidents(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        queryset = self.incident_model.objects.filter(
            record_type=self.incident_model.RecordType.INCIDENT,
            is_deleted=False,
            superseded_by_id__isnull=True,
            closed_at__isnull=True,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        )
        if scope.scope_type == SafetyDashboardRollup.ScopeType.VESSEL:
            queryset = queryset.filter(vessel_id=scope.scope_id)
        return queryset.count()

    def _count_total_incidents(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        return self._count_total_records(
            record_type=self.incident_model.RecordType.INCIDENT,
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )

    def _count_open_near_misses(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        queryset = self.incident_model.objects.filter(
            record_type=self.incident_model.RecordType.NEAR_MISS,
            is_deleted=False,
            superseded_by_id__isnull=True,
            closed_at__isnull=True,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        )
        if scope.scope_type == SafetyDashboardRollup.ScopeType.VESSEL:
            queryset = queryset.filter(vessel_id=scope.scope_id)
        return queryset.count()

    def _count_total_near_misses(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        return self._count_total_records(
            record_type=self.incident_model.RecordType.NEAR_MISS,
            scope=scope,
            window_start=window_start,
            window_end=window_end,
        )

    def _count_total_records(self, *, record_type: str, scope: RollupScope, window_start: date, window_end: date) -> int:
        queryset = self.incident_model.objects.filter(
            record_type=record_type,
            is_deleted=False,
            superseded_by_id__isnull=True,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        )
        if scope.scope_type == SafetyDashboardRollup.ScopeType.VESSEL:
            queryset = queryset.filter(vessel_id=scope.scope_id)
        return queryset.count()

    def _count_open_findings(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        queryset = self.finding_model.objects.filter(
            is_deleted=False,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        ).exclude(status=self.finding_model.Status.CLOSED)
        if scope.scope_type == SafetyDashboardRollup.ScopeType.VESSEL:
            inspection_ids = self.inspection_model.objects.filter(
                is_deleted=False,
                vessel_id=scope.scope_id,
            ).values_list("id", flat=True)
            queryset = queryset.filter(inspection_id__in=inspection_ids)
        return queryset.count()

    def _count_total_findings(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        queryset = self.finding_model.objects.filter(
            is_deleted=False,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        )
        if scope.scope_type == SafetyDashboardRollup.ScopeType.VESSEL:
            inspection_ids = self.inspection_model.objects.filter(
                is_deleted=False,
                vessel_id=scope.scope_id,
            ).values_list("id", flat=True)
            queryset = queryset.filter(inspection_id__in=inspection_ids)
        return queryset.count()

    def _count_overdue_corrective_actions(self, *, scope: RollupScope, as_of: date) -> int:
        queryset = self.corrective_action_model.objects.filter(
            is_deleted=False,
            due_date__lt=as_of,
        ).exclude(status=self.corrective_action_model.Status.CLOSED)

        if scope.scope_type == SafetyDashboardRollup.ScopeType.FLEET:
            return queryset.count()

        incident_ids = list(
            self.incident_model.objects.filter(is_deleted=False, vessel_id=scope.scope_id).values_list("id", flat=True)
        )
        meeting_ids = list(
            self.meeting_model.objects.filter(is_deleted=False, vessel_id=scope.scope_id).values_list("id", flat=True)
        )
        agenda_ids = list(
            self.agenda_model.objects.filter(meeting_id__in=meeting_ids).values_list("id", flat=True)
        ) if meeting_ids else []

        vessel_filter = Q(recommendation__incident__vessel_id=scope.scope_id)
        if incident_ids:
            vessel_filter |= Q(source_table=self.incident_model._meta.db_table, source_id__in=incident_ids)
        if agenda_ids:
            vessel_filter |= Q(source_table=self.agenda_model._meta.db_table, source_id__in=agenda_ids)

        return queryset.filter(vessel_filter).count()

    def _count_total_corrective_actions(self, *, scope: RollupScope, window_start: date, window_end: date) -> int:
        queryset = self.corrective_action_model.objects.filter(
            is_deleted=False,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        )

        if scope.scope_type == SafetyDashboardRollup.ScopeType.FLEET:
            return queryset.count()

        incident_ids = list(
            self.incident_model.objects.filter(is_deleted=False, vessel_id=scope.scope_id).values_list("id", flat=True)
        )
        meeting_ids = list(
            self.meeting_model.objects.filter(is_deleted=False, vessel_id=scope.scope_id).values_list("id", flat=True)
        )
        agenda_ids = list(
            self.agenda_model.objects.filter(meeting_id__in=meeting_ids).values_list("id", flat=True)
        ) if meeting_ids else []

        vessel_filter = Q(recommendation__incident__vessel_id=scope.scope_id)
        if incident_ids:
            vessel_filter |= Q(source_table=self.incident_model._meta.db_table, source_id__in=incident_ids)
        if agenda_ids:
            vessel_filter |= Q(source_table=self.agenda_model._meta.db_table, source_id__in=agenda_ids)

        return queryset.filter(vessel_filter).count()

    def _build_soi_summary(self, *, scope: RollupScope) -> dict[str, object]:
        if scope.scope_type == SafetyDashboardRollup.ScopeType.VESSEL:
            return self.soi_compliance_calculator.get_summary(scope.scope_id)

        vessel_ids = self.list_known_vessel_ids()
        compliance_values = []
        for vessel_id in vessel_ids:
            summary = self.soi_compliance_calculator.get_summary(vessel_id)
            if summary["compliance_percent"] is not None:
                compliance_values.append(int(summary["compliance_percent"]))

        if not compliance_values:
            return {
                "label": "SOI Compliance %",
                "display_value": "N/A - awaiting first cycle",
                "compliance_percent": None,
            }

        compliance_percent = round(sum(compliance_values) / len(compliance_values))
        return {
            "label": "SOI Compliance %",
            "display_value": f"{compliance_percent}%",
            "compliance_percent": compliance_percent,
        }

    @staticmethod
    def _score_penalty(count: int, *, step: int) -> int:
        capped_count = min(max(count, 0), 5)
        return max(0, 100 - (capped_count * step))

    @staticmethod
    def _score_status(score: int) -> str:
        if score >= 85:
            return "GREEN"
        if score >= 70:
            return "AMBER"
        return "RED"
