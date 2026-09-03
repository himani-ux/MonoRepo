"""Serializers for Audit finding capture."""

from __future__ import annotations

from django.db import connection
from rest_framework import serializers

from apps.inspection.audit.models import AuditFindingClause
from apps.inspection.audit.services.finding import (
    FINDING_TYPES,
    NC_CATEGORIES,
    OBSERVATION_CATEGORIES,
    PRIORITIES,
    RULE_BOOK_TYPES,
)


CERTIFICATE_IMPACTS = {"NONE", "CERT_VALID", "RENEWAL_AT_RISK", "SUSPENDED", "WITHDRAWN"}


class AuditFindingClauseSerializer(serializers.Serializer):
    rule_book_type = serializers.ChoiceField(choices=tuple(sorted(RULE_BOOK_TYPES)))
    rule_clause_id = serializers.UUIDField(required=False, allow_null=True)
    clause_ref_text = serializers.CharField(required=False, allow_blank=True, max_length=200)
    clause_subref_text = serializers.CharField(required=False, allow_blank=True, max_length=200)
    is_primary = serializers.BooleanField(default=False)


class AuditFindingCreateSerializer(serializers.Serializer):
    finding_type = serializers.ChoiceField(choices=tuple(sorted(FINDING_TYPES)))
    nc_category = serializers.ChoiceField(choices=tuple(sorted(NC_CATEGORIES)), required=False, allow_blank=True)
    observation_category = serializers.ChoiceField(
        choices=tuple(sorted(OBSERVATION_CATEGORIES)),
        required=False,
        allow_blank=True,
    )
    standard_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
    description = serializers.CharField()
    objective_evidence = serializers.CharField(required=False, allow_blank=True)
    def_code_id = serializers.CharField(required=False, allow_blank=True, max_length=5)
    def_code = serializers.CharField(required=False, allow_blank=True, max_length=10)
    checklist_item_id = serializers.UUIDField(required=False, allow_null=True)
    clauses = AuditFindingClauseSerializer(many=True)
    psc_deficiency_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=tuple(sorted(PRIORITIES)), required=False, allow_blank=True)
    original_due_date = serializers.DateField(required=False, allow_null=True)
    certificate_impact = serializers.ChoiceField(
        choices=tuple(sorted(CERTIFICATE_IMPACTS)),
        required=False,
        allow_blank=True,
    )
    certificates_at_risk = serializers.CharField(required=False, allow_blank=True, max_length=100)
    is_fleetwide_relevance = serializers.BooleanField(required=False, default=False)

    def validate_clauses(self, value):
        if not value:
            raise serializers.ValidationError("At least one clause reference is required.")
        primary_count = sum(1 for clause in value if clause.get("is_primary"))
        if primary_count != 1:
            raise serializers.ValidationError("Exactly one clause reference must be marked primary.")
        return value


class AuditFindingResponseSerializer(serializers.Serializer):
    def to_representation(self, instance):
        finding = instance.finding
        deficiency = instance.deficiency
        car = instance.car
        clauses = _finding_clauses_for_response(finding.id)
        return {
            "id": str(finding.id),
            "audit_detail_id": str(finding.audit_detail_id),
            "finding_type": finding.finding_type,
            "nc_category": finding.nc_category,
            "observation_category": finding.observation_category,
            "standard_code": finding.standard_code,
            "rule_book_type": finding.rule_book_type,
            "rule_clause_id": str(finding.rule_clause_id) if finding.rule_clause_id else None,
            "clause_ref_text": finding.clause_ref_text,
            "description": finding.description or deficiency.description,
            "objective_evidence": finding.objective_evidence,
            "priority": finding.priority,
            "certificates_at_risk": finding.certificates_at_risk,
            "is_fleetwide_relevance": finding.is_fleetwide_relevance,
            "linked_circular_id": str(finding.linked_circular_id) if finding.linked_circular_id else None,
            "psc_deficiency_id": str(deficiency.id),
            "car_id": str(car.id),
            "car_number": car.car_number,
            "car_status": car.status,
            "created": instance.created,
            "clauses": [
                {
                    "id": str(clause.id),
                    "rule_book_type": clause.rule_book_type,
                    "rule_clause_id": str(clause.rule_clause_id) if clause.rule_clause_id else None,
                    "clause_ref_text": clause.clause_ref_text,
                    "clause_subref_text": clause.clause_subref_text,
                    "is_primary": clause.is_primary,
                }
                for clause in clauses
            ],
        }


def _finding_clauses_for_response(finding_id):
    if connection.vendor == "microsoft":
        return list(
            AuditFindingClause.objects.raw(
                f"""
                SELECT *
                FROM dbo.{AuditFindingClause._meta.db_table}
                WHERE audit_finding_id = CAST(%s AS uniqueidentifier)
                  AND is_deleted = 0
                ORDER BY is_primary DESC, created_date ASC, id ASC
                """,
                [str(finding_id)],
            )
        )
    return AuditFindingClause.objects.filter(audit_finding_id=finding_id).order_by(
        "-is_primary",
        "created_date",
        "id",
    )
