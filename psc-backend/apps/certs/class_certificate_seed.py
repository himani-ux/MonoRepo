from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


CLASS_SECTION_ID = 1
CLASS_SECTION_LABEL = "Class Certificates"
SEED_ACTOR_ID = "seed_class_certificates"


@dataclass(frozen=True)
class ClassCertificateSeedRow:
    canonical_code: str
    display_name: str
    short_name: str | None
    validity_type: str
    cadence_months: int | None
    print_order: int
    regulatory_anchor: str
    parent_code: str | None = None
    relationship_type_default: str | None = None
    age_gate_max_years: int | None = None
    legacy_remarks: str | None = None
    section_id: int = CLASS_SECTION_ID
    print_section_label: str = CLASS_SECTION_LABEL
    issuing_authority_type: str = "class"
    is_class_tracked: bool = True
    submission_scope: str = "master_only"
    applicable_ship_types: tuple[str, ...] = ("all",)
    mandatory_for_all_vessels: bool = True
    applicability_mode: str = "all_matching_type"
    parent_supports_dynamic_children: bool = False
    retain_all_versions: bool = False

    def insert_params(self, *, parent_id: str | None, actor_id: str) -> list[Any]:
        return [
            self.canonical_code,
            self.section_id,
            self.display_name,
            self.short_name,
            self.print_section_label,
            self.validity_type,
            self.cadence_months,
            None,
            self.issuing_authority_type,
            int(self.is_class_tracked),
            self.submission_scope,
            parent_id,
            self.relationship_type_default,
            json.dumps(list(self.applicable_ship_types)),
            int(self.mandatory_for_all_vessels),
            self.applicability_mode,
            None,
            int(self.parent_supports_dynamic_children),
            self.age_gate_max_years,
            int(self.retain_all_versions),
            None,
            None,
            self.regulatory_anchor,
            self.legacy_remarks,
            self.print_order,
            1,
            actor_id,
            actor_id,
        ]

    def audit_after_payload(self, *, catalog_id: str, parent_id: str | None) -> dict[str, Any]:
        return {
            "id": catalog_id,
            "canonicalCode": self.canonical_code,
            "sectionId": self.section_id,
            "sectionCode": "CLASS",
            "sectionName": CLASS_SECTION_LABEL,
            "displayName": self.display_name,
            "shortName": self.short_name,
            "printSectionLabel": self.print_section_label,
            "validityType": self.validity_type,
            "cadenceMonths": self.cadence_months,
            "cadenceCustomDays": None,
            "issuingAuthorityType": self.issuing_authority_type,
            "isClassTracked": self.is_class_tracked,
            "submissionScope": self.submission_scope,
            "parentId": parent_id,
            "relationshipTypeDefault": self.relationship_type_default,
            "applicableShipTypes": list(self.applicable_ship_types),
            "mandatoryForAllVessels": self.mandatory_for_all_vessels,
            "applicabilityMode": self.applicability_mode,
            "specificVesselIds": [],
            "parentSupportsDynamicChildren": self.parent_supports_dynamic_children,
            "ageGateMaxYears": self.age_gate_max_years,
            "retainAllVersions": self.retain_all_versions,
            "linkedPmsComponentId": None,
            "alertLeadOverrides": None,
            "regulatoryAnchor": self.regulatory_anchor,
            "legacyRemarks": self.legacy_remarks,
            "printOrder": self.print_order,
            "isActive": True,
        }


@dataclass(frozen=True)
class ClassCertificateSeedResult:
    created_codes: tuple[str, ...]
    skipped_codes: tuple[str, ...]

    @property
    def created_count(self) -> int:
        return len(self.created_codes)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_codes)


CLASS_CERTIFICATE_ROWS: tuple[ClassCertificateSeedRow, ...] = (
    ClassCertificateSeedRow(
        canonical_code="CLASS-COC",
        display_name="Certificate of Class",
        short_name="COC",
        validity_type="full",
        cadence_months=60,
        print_order=10,
        regulatory_anchor="D-CERT-014",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-CG2",
        display_name="Cargo Gear Certificate",
        short_name="CG2",
        validity_type="full",
        cadence_months=60,
        print_order=20,
        regulatory_anchor="D-CERT-014",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-LI",
        display_name="Loading Instrument Certificate",
        short_name="LI",
        validity_type="permanent",
        cadence_months=None,
        print_order=30,
        regulatory_anchor="D-CERT-014",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-NOTATIONS",
        display_name="Class Notations Record",
        short_name=None,
        validity_type="permanent",
        cadence_months=None,
        print_order=40,
        regulatory_anchor="D-CERT-014",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-SPECIAL-SURVEY",
        display_name="Class Special Survey",
        short_name=None,
        validity_type="conditional",
        cadence_months=60,
        print_order=11,
        regulatory_anchor="D-CERT-014",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-INTERMEDIATE-SURVEY",
        display_name="Class Intermediate Survey",
        short_name=None,
        validity_type="conditional",
        cadence_months=30,
        print_order=12,
        regulatory_anchor="D-CERT-014",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-ANNUAL-SURVEY",
        display_name="Class Annual Survey",
        short_name=None,
        validity_type="conditional",
        cadence_months=12,
        print_order=13,
        regulatory_anchor="D-CERT-014",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-DOCKING-SURVEY",
        display_name="Class Docking Survey",
        short_name=None,
        validity_type="conditional",
        cadence_months=60,
        print_order=14,
        regulatory_anchor="D-CERT-034",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-BOILER-SURVEY",
        display_name="Class Boiler Survey",
        short_name=None,
        validity_type="conditional",
        cadence_months=60,
        print_order=15,
        regulatory_anchor="D-CERT-033",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-PROP-SHAFT-SURVEY",
        display_name="Class Prop Shaft Survey",
        short_name=None,
        validity_type="conditional",
        cadence_months=60,
        print_order=16,
        regulatory_anchor="D-CERT-034",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
    ),
    ClassCertificateSeedRow(
        canonical_code="CLASS-IWS-SURVEY",
        display_name="Class In-Water Survey",
        short_name="IWS",
        validity_type="conditional",
        cadence_months=60,
        print_order=17,
        regulatory_anchor="D-CERT-034",
        parent_code="CLASS-COC",
        relationship_type_default="survey_of",
        age_gate_max_years=15,
        legacy_remarks="Vessels up to 15 years only; later auto-disable job owns vessel-age application.",
    ),
)


def seed_class_certificate_rows(cursor, *, actor_id: str = SEED_ACTOR_ID) -> ClassCertificateSeedResult:
    existing_ids = _load_existing_ids(cursor)
    created_codes: list[str] = []
    skipped_codes: list[str] = []

    for row in CLASS_CERTIFICATE_ROWS:
        if row.canonical_code in existing_ids:
            skipped_codes.append(row.canonical_code)
            continue

        parent_id = existing_ids.get(row.parent_code) if row.parent_code else None
        if row.parent_code and parent_id is None:
            raise RuntimeError(f"Parent row {row.parent_code} must exist before seeding {row.canonical_code}.")

        cursor.execute(_insert_sql(), row.insert_params(parent_id=parent_id, actor_id=actor_id))
        catalog_id = str(cursor.fetchone()[0])
        existing_ids[row.canonical_code] = catalog_id
        created_codes.append(row.canonical_code)
        _record_create_audit(cursor, row=row, catalog_id=catalog_id, parent_id=parent_id, actor_id=actor_id)

    return ClassCertificateSeedResult(
        created_codes=tuple(created_codes),
        skipped_codes=tuple(skipped_codes),
    )

def _load_existing_ids(cursor) -> dict[str, str]:
    placeholders = ", ".join(["%s"] * len(CLASS_CERTIFICATE_ROWS))
    cursor.execute(
        f"""
        SELECT canonical_code, CONVERT(NVARCHAR(36), catalog_id)
        FROM dbo.vims_certs_catalog_row
        WHERE canonical_code IN ({placeholders})
        """,
        [row.canonical_code for row in CLASS_CERTIFICATE_ROWS],
    )
    return {str(code): str(catalog_id) for code, catalog_id in cursor.fetchall()}


def _insert_sql() -> str:
    return """
        INSERT INTO dbo.vims_certs_catalog_row (
            canonical_code, section_id, display_name, short_name, print_section_label,
            validity_type, cadence_months, cadence_custom_days, issuing_authority_type,
            is_class_tracked, submission_scope, parent_id, relationship_type_default,
            applicable_ship_types, mandatory_for_all_vessels, applicability_mode,
            specific_vessel_ids, parent_supports_dynamic_children, age_gate_max_years,
            retain_all_versions, linked_pms_component_id, alert_lead_overrides,
            regulatory_anchor, legacy_remarks, print_order, is_active, created_by, updated_by
        )
        OUTPUT inserted.catalog_id
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """


def _record_create_audit(
    cursor,
    *,
    row: ClassCertificateSeedRow,
    catalog_id: str,
    parent_id: str | None,
    actor_id: str,
) -> None:
    cursor.execute(
        """
        INSERT INTO dbo.vims_certs_audit_log (
            actor_user_id, actor_role, action, entity_type, entity_id,
            before_json, after_json, reason, event_metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            actor_id,
            "SYSTEM",
            "create_catalog_row",
            "catalog_row",
            catalog_id,
            None,
            json.dumps(row.audit_after_payload(catalog_id=catalog_id, parent_id=parent_id), default=str),
            "Phase 1.4 Class Certificates baseline seed.",
            json.dumps({"source": "management.seed_class_certificates", "phase": "1.4"}),
        ],
    )
