"""Persistence helpers for audit plan workflow updates."""

from __future__ import annotations

from django.db import connection

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.serializers.plan import _update_sql_server_plan


def save_plan_update(plan: MasterAuditPlan, update_fields: list[str]) -> MasterAuditPlan:
    if connection.vendor == "microsoft":
        return _update_sql_server_plan(plan, update_fields)
    plan.save(update_fields=update_fields)
    return plan
