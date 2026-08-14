"""Audit finding creation service for the PSC CAR handoff."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import (
    AuditDetail,
    AuditFinding,
    AuditFindingClause,
    MasterColregRule,
    MasterIsmClause,
    MasterIspsClause,
    MasterKsmSmsChapter,
    MasterMarpolAnnex,
    MasterMlcTitle,
    MasterSolasChapter,
    MasterStcwSection,
)
from apps.inspection.deficiency_models import CAR, Deficiency
from apps.inspection.models import Inspection


OPEN_FINDING_STATUSES = {"IN_PROGRESS"}
FINDING_TYPES = {"NC", "OBSERVATION"}
NC_CATEGORIES = {"MAJOR_NC", "MINOR_NC"}
OBSERVATION_CATEGORIES = {"OBSERVATION", "IMPROVEMENT_SUGGESTION", "OFI"}
PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
CRITICAL_CERTIFICATE_IMPACTS = {"SUSPENDED", "WITHDRAWN"}
RULE_BOOK_MASTER_MODELS = {
    "ISM": MasterIsmClause,
    "ISPS": MasterIspsClause,
    "MLC": MasterMlcTitle,
    "SOLAS": MasterSolasChapter,
    "STCW": MasterStcwSection,
    "MARPOL": MasterMarpolAnnex,
    "COLREG": MasterColregRule,
    "KSM_SMS": MasterKsmSmsChapter,
}
TEXT_ONLY_RULE_BOOK_TYPES = {"FLAG", "OTHER"}
RULE_BOOK_TYPES = set(RULE_BOOK_MASTER_MODELS) | TEXT_ONLY_RULE_BOOK_TYPES


class AuditFindingError(ValueError):
    """Base error for Audit finding creation failures."""


class AuditFindingStateError(AuditFindingError):
    """Raised when an audit state forbids finding creation."""


class AuditFindingValidationError(AuditFindingError):
    """Raised when a finding payload violates the Audit finding contract."""


@dataclass(frozen=True)
class AuditFindingCreateResult:
    finding: AuditFinding
    deficiency: Deficiency
    car: CAR
    created: bool


@dataclass(frozen=True)
class AuditFindingClauseInput:
    rule_book_type: str
    rule_clause_id: uuid.UUID | None
    clause_ref_text: str | None
    clause_subref_text: str | None
    is_primary: bool


def create_audit_finding(
    *,
    audit_detail_id: uuid.UUID | str,
    finding_type: str,
    description: str,
    def_code_id: str,
    def_code: str | None = None,
    psc_deficiency_id: uuid.UUID | str | None = None,
    nc_category: str | None = None,
    observation_category: str | None = None,
    standard_code: str | None = None,
    rule_book_type: str | None = None,
    rule_clause_id: uuid.UUID | str | None = None,
    clause_ref_text: str | None = None,
    clauses: list[dict] | None = None,
    objective_evidence: str | None = None,
    checklist_item_id: uuid.UUID | str | None = None,
    priority: str | None = None,
    original_due_date=None,
    extended_due_date=None,
    extension_reason: str | None = None,
    certificates_at_risk: str | None = None,
    certificate_impact: str | None = None,
    is_fleetwide_relevance: bool = False,
    linked_circular_id: uuid.UUID | str | None = None,
    applies_to_cert_ids_csv: str | None = None,
    action_code_id: int | None = None,
    action_code: str | None = None,
    assigned_crew_id: str | None = None,
    created_by: str | None = None,
) -> AuditFindingCreateResult:
    """
    Create one Audit finding and let the existing Deficiency post-save path create its CAR.

    Pass a stable ``psc_deficiency_id`` from the caller when retry safety is required.
    A repeat call with the same key returns the existing finding/CAR and inserts no
    second legacy deficiency.
    """

    finding_type = _required_choice("finding_type", finding_type, FINDING_TYPES)
    nc_category = _validate_category(
        finding_type=finding_type,
        nc_category=nc_category,
        observation_category=observation_category,
    )
    observation_category = _normalize_observation_category(
        finding_type=finding_type,
        observation_category=observation_category,
    )
    priority = _required_choice("priority", priority, PRIORITIES) if priority else None
    if is_fleetwide_relevance and finding_type != "NC":
        raise AuditFindingValidationError("is_fleetwide_relevance is valid only for NC findings.")
    description = _required_text("description", description)
    def_code_id = _required_text("def_code_id", def_code_id)
    def_code = def_code or def_code_id
    deficiency_uuid = _coerce_uuid(psc_deficiency_id) if psc_deficiency_id else uuid.uuid4()
    legacy_deficiency_key = deficiency_uuid.hex

    with transaction.atomic():
        audit_detail = (
            AuditDetail.objects.select_for_update()
            .get(id=_coerce_uuid(audit_detail_id))
        )
        _assert_audit_accepts_findings(audit_detail)
        clause_inputs = _normalize_clause_inputs(
            rule_book_type=rule_book_type,
            rule_clause_id=rule_clause_id,
            clause_ref_text=clause_ref_text,
            clauses=clauses,
        )
        primary_clause = _primary_clause(clause_inputs)

        existing = AuditFinding.all_objects.filter(psc_deficiency_id=legacy_deficiency_key).first()
        if existing:
            if existing.is_deleted:
                raise AuditFindingStateError("Audit finding retry key belongs to a deleted finding.")
            deficiency = Deficiency.objects.select_related("car").get(id=deficiency_uuid)
            return AuditFindingCreateResult(
                finding=existing,
                deficiency=deficiency,
                car=_require_car(deficiency),
                created=False,
            )

        inspection = _get_audit_inspection(audit_detail)
        existing_deficiency = Deficiency.objects.filter(id=deficiency_uuid).first()
        if existing_deficiency:
            deficiency = existing_deficiency
            _assert_deficiency_matches_audit(deficiency, inspection)
        else:
            due_date = original_due_date or _default_due_date(finding_type, nc_category)
            deficiency = Deficiency.objects.create(
                id=deficiency_uuid,
                inspection=inspection,
                def_code_id=def_code_id,
                def_code=def_code,
                description=description,
                action_code_id=action_code_id,
                action_code=action_code or (str(action_code_id) if action_code_id else None),
                target_date=due_date,
                sequence_no=_next_deficiency_sequence(inspection),
                assigned_crew_id=assigned_crew_id,
                created_by=created_by,
                updated_by=created_by,
            )

        deficiency.refresh_from_db()
        finding = AuditFinding.objects.create(
            psc_deficiency_id=legacy_deficiency_key,
            audit_detail_id=audit_detail.id,
            audit_classification=audit_detail.audit_classification,
            finding_type=finding_type,
            nc_category=nc_category,
            observation_category=observation_category,
            standard_code=standard_code,
            rule_book_type=primary_clause.rule_book_type if primary_clause else rule_book_type,
            rule_clause_id=primary_clause.rule_clause_id if primary_clause else None,
            clause_ref_text=primary_clause.clause_ref_text if primary_clause else clause_ref_text,
            objective_evidence=objective_evidence,
            description=description,
            checklist_item_id=_coerce_uuid(checklist_item_id) if checklist_item_id else None,
            priority=_resolve_priority(
                audit_detail=audit_detail,
                finding_type=finding_type,
                nc_category=nc_category,
                priority=priority,
                certificate_impact=certificate_impact,
            ),
            original_due_date=original_due_date or deficiency.target_date,
            extended_due_date=extended_due_date,
            extension_reason=extension_reason,
            certificates_at_risk=certificates_at_risk,
            is_fleetwide_relevance=is_fleetwide_relevance,
            linked_circular_id=_coerce_uuid(linked_circular_id) if linked_circular_id else None,
            is_external=audit_detail.audit_classification == "EXTERNAL",
            applies_to_cert_ids_csv=applies_to_cert_ids_csv,
            created_by=created_by,
        )
        for clause_input in clause_inputs:
            AuditFindingClause.objects.create(
                audit_finding_id=finding.id,
                rule_book_type=clause_input.rule_book_type,
                rule_clause_id=clause_input.rule_clause_id,
                clause_ref_text=clause_input.clause_ref_text,
                clause_subref_text=clause_input.clause_subref_text,
                is_primary=clause_input.is_primary,
                created_by=created_by,
            )

        return AuditFindingCreateResult(
            finding=finding,
            deficiency=deficiency,
            car=_require_car(deficiency),
            created=True,
        )


def _assert_audit_accepts_findings(audit_detail: AuditDetail) -> None:
    if audit_detail.status not in OPEN_FINDING_STATUSES:
        raise AuditFindingStateError("Findings can be added only while the audit is IN_PROGRESS.")


def _get_audit_inspection(audit_detail: AuditDetail) -> Inspection:
    inspection = Inspection.objects.select_for_update().get(
        id=_coerce_uuid(audit_detail.psc_inspection_id),
        is_deleted=False,
    )
    if inspection.inspection_type != "AUDIT":
        raise AuditFindingValidationError("Audit detail must reference an AUDIT psc_inspection row.")
    return inspection


def _assert_deficiency_matches_audit(deficiency: Deficiency, inspection: Inspection) -> None:
    if deficiency.inspection_id != inspection.id:
        raise AuditFindingValidationError("Retry deficiency key belongs to a different inspection.")
    if deficiency.is_deleted:
        raise AuditFindingStateError("Retry deficiency key belongs to a deleted deficiency.")


def _require_car(deficiency: Deficiency) -> CAR:
    if not deficiency.car_id:
        raise AuditFindingStateError("Existing CAR creation path did not create a CAR.")
    return deficiency.car


def _next_deficiency_sequence(inspection: Inspection) -> int:
    last_deficiency = (
        Deficiency.objects.filter(inspection=inspection, is_deleted=False)
        .order_by("-sequence_no")
        .first()
    )
    return (last_deficiency.sequence_no + 1) if last_deficiency else 1


def _default_due_date(finding_type: str, nc_category: str | None):
    days = 90 if finding_type == "NC" and nc_category == "MAJOR_NC" else 30
    return timezone.localdate() + timedelta(days=days)


def _resolve_priority(
    *,
    audit_detail: AuditDetail,
    finding_type: str,
    nc_category: str | None,
    priority: str | None,
    certificate_impact: str | None,
) -> str:
    impact = certificate_impact or audit_detail.certificate_impact
    if finding_type == "NC" and nc_category == "MAJOR_NC" and impact in CRITICAL_CERTIFICATE_IMPACTS:
        return "CRITICAL"
    return priority or "MEDIUM"


def _validate_category(
    *,
    finding_type: str,
    nc_category: str | None,
    observation_category: str | None,
) -> str | None:
    if finding_type == "NC":
        return _required_choice("nc_category", nc_category, NC_CATEGORIES)
    if nc_category:
        raise AuditFindingValidationError("nc_category is valid only for NC findings.")
    if observation_category is not None:
        _required_choice("observation_category", observation_category, OBSERVATION_CATEGORIES)
    return None


def _normalize_observation_category(
    *,
    finding_type: str,
    observation_category: str | None,
) -> str | None:
    if finding_type != "OBSERVATION":
        if observation_category:
            raise AuditFindingValidationError(
                "observation_category is valid only for OBSERVATION findings."
            )
        return None
    return _required_choice(
        "observation_category",
        observation_category or "OBSERVATION",
        OBSERVATION_CATEGORIES,
    )


def _normalize_clause_inputs(
    *,
    rule_book_type: str | None,
    rule_clause_id: uuid.UUID | str | None,
    clause_ref_text: str | None,
    clauses: list[dict] | None,
) -> list[AuditFindingClauseInput]:
    if clauses is None:
        if not any((rule_book_type, rule_clause_id, clause_ref_text)):
            return []
        clauses = [
            {
                "rule_book_type": rule_book_type,
                "rule_clause_id": rule_clause_id,
                "clause_ref_text": clause_ref_text,
                "is_primary": True,
            }
        ]

    if not clauses:
        raise AuditFindingValidationError("At least one clause reference is required.")

    normalized = [_normalize_clause_input(clause) for clause in clauses]
    primary_count = sum(1 for clause in normalized if clause.is_primary)
    if primary_count != 1:
        raise AuditFindingValidationError("Exactly one clause reference must be marked primary.")
    return normalized


def _normalize_clause_input(clause: dict) -> AuditFindingClauseInput:
    rule_book_type = _required_choice(
        "rule_book_type",
        clause.get("rule_book_type"),
        RULE_BOOK_TYPES,
    )
    clause_subref_text = _optional_bounded_text("clause_subref_text", clause.get("clause_subref_text"), max_length=200)
    clause_ref_text = _optional_bounded_text("clause_ref_text", clause.get("clause_ref_text"), max_length=200)

    if rule_book_type in TEXT_ONLY_RULE_BOOK_TYPES:
        if clause.get("rule_clause_id"):
            raise AuditFindingValidationError(f"{rule_book_type} clause references cannot carry rule_clause_id.")
        clause_ref_text = _bounded_required_text("clause_ref_text", clause_ref_text, min_length=5, max_length=200)
        return AuditFindingClauseInput(
            rule_book_type=rule_book_type,
            rule_clause_id=None,
            clause_ref_text=clause_ref_text,
            clause_subref_text=clause_subref_text,
            is_primary=bool(clause.get("is_primary")),
        )

    rule_clause_id = _coerce_uuid(clause.get("rule_clause_id"))
    master_model = RULE_BOOK_MASTER_MODELS[rule_book_type]
    if not master_model.objects.filter(id=rule_clause_id).exists():
        raise AuditFindingValidationError(f"rule_clause_id is not valid for {rule_book_type}.")

    return AuditFindingClauseInput(
        rule_book_type=rule_book_type,
        rule_clause_id=rule_clause_id,
        clause_ref_text=clause_ref_text or _clause_display(master_model.objects.get(id=rule_clause_id), rule_book_type),
        clause_subref_text=clause_subref_text,
        is_primary=bool(clause.get("is_primary")),
    )


def _primary_clause(clause_inputs: list[AuditFindingClauseInput]) -> AuditFindingClauseInput | None:
    for clause_input in clause_inputs:
        if clause_input.is_primary:
            return clause_input
    return None


def _clause_display(master_row, rule_book_type: str) -> str:
    if rule_book_type == "ISM":
        return f"ISM {master_row.clause_no}"
    if rule_book_type == "ISPS":
        return f"ISPS {master_row.section_no}"
    if rule_book_type == "MLC":
        return f"MLC {master_row.title_no}"
    if rule_book_type == "SOLAS":
        parts = [master_row.chapter_no, master_row.regulation_no]
        return "SOLAS " + " Reg ".join(part for part in parts if part)
    if rule_book_type == "STCW":
        return f"STCW {master_row.section_no}"
    if rule_book_type == "MARPOL":
        parts = [master_row.annex_no, master_row.regulation_no]
        return "MARPOL " + " Reg ".join(part for part in parts if part)
    if rule_book_type == "COLREG":
        return f"COLREG {master_row.rule_no}"
    if rule_book_type == "KSM_SMS":
        return f"KSM SMS {master_row.chapter_code}"
    return rule_book_type


def _required_choice(field_name: str, value: str | None, allowed: set[str]) -> str:
    text = _required_text(field_name, value).upper()
    if text not in allowed:
        raise AuditFindingValidationError(
            f"{field_name} must be one of: {', '.join(sorted(allowed))}."
        )
    return text


def _required_text(field_name: str, value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        raise AuditFindingValidationError(f"{field_name} is required.")
    return text


def _bounded_required_text(field_name: str, value: str | None, *, min_length: int, max_length: int) -> str:
    text = _required_text(field_name, value)
    if len(text) < min_length or len(text) > max_length:
        raise AuditFindingValidationError(
            f"{field_name} must be between {min_length} and {max_length} characters."
        )
    return text


def _optional_bounded_text(field_name: str, value: str | None, *, max_length: int) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if len(text) > max_length:
        raise AuditFindingValidationError(f"{field_name} must be {max_length} characters or fewer.")
    return text


def _coerce_uuid(value: uuid.UUID | str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise AuditFindingValidationError("Expected a valid UUID value.") from exc
